const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret, defineString } = require("firebase-functions/params");

// Optional outside watchdog for the Kalshi bot. Put KALSHI_WATCHDOG_URL=<ping url> in
// functions/.env (gitignored) before deploying. Empty means no alerts, nothing else changes.
const KALSHI_WATCHDOG_URL = defineString("KALSHI_WATCHDOG_URL", { default: "" });

// Set once via: firebase functions:secrets:set FINNHUB_API_KEY
// Never committed -- this is the only place the real key lives now.
const FINNHUB_API_KEY = defineSecret("FINNHUB_API_KEY");

// The LIVE test order (real money). The switch is off until the owner sets KALSHI_LIVE_ENABLED=on in
// functions/.env and redeploys: deploying alone cannot place an order.
//   firebase functions:secrets:set KALSHI_LIVE_KEY_ID
//   firebase functions:secrets:set KALSHI_LIVE_PRIVATE_KEY   (--data-file, never paste the PEM into a chat)
const KALSHI_LIVE_KEY_ID = defineSecret("KALSHI_LIVE_KEY_ID");
const KALSHI_LIVE_PRIVATE_KEY = defineSecret("KALSHI_LIVE_PRIVATE_KEY");
const KALSHI_LIVE_ENABLED = defineString("KALSHI_LIVE_ENABLED", { default: "off" });

// Invite-gated, not single-owner: anyone with a real Firebase Auth
// token may call these (matches firestore.rules, which lets any signed-in
// account read/write only its own users/{uid} doc -- account creation
// itself is what's gated, via the invite-code system, not access to
// these functions once an account exists).
function assertSignedIn(auth) {
  if (!auth) {
    throw new HttpsError("permission-denied", "Sign in required.");
  }
}

async function finnhubGet(path, params) {
  const url = new URL("https://finnhub.io/api/v1/" + path);
  Object.keys(params).forEach((key) => url.searchParams.set(key, params[key]));
  url.searchParams.set("token", FINNHUB_API_KEY.value());
  const res = await fetch(url);
  if (!res.ok) {
    throw new HttpsError("unavailable", "Finnhub " + path + " HTTP " + res.status);
  }
  return res.json();
}

exports.finnhubQuote = onCall({ secrets: [FINNHUB_API_KEY] }, async (request) => {
  assertSignedIn(request.auth);
  const symbol = request.data && request.data.symbol;
  if (!symbol || typeof symbol !== "string") {
    throw new HttpsError("invalid-argument", "symbol is required");
  }
  return finnhubGet("quote", { symbol });
});

// finnhubNews and finnhubEarningsCalendar used to sit here. Nothing called
// them: index.html wires exactly two callables (finnhubQuote,
// finnhubCompanyNews), and general news and the earnings calendar now arrive
// through the backend's shared market snapshot instead.
//
// They were deployed functions holding a binding on the Finnhub API key, so
// removing them narrows what can spend that key -- which is why this is worth
// doing rather than leaving two harmless dead exports.
//
// NOTE: deleting them here does not undeploy them. `firebase deploy --only
// functions` does not remove functions absent from source either; they have
// to go with `firebase functions:delete finnhubNews finnhubEarningsCalendar`.

exports.finnhubCompanyNews = onCall({ secrets: [FINNHUB_API_KEY] }, async (request) => {
  assertSignedIn(request.auth);
  const { symbol, from, to } = request.data || {};
  if (!symbol || !from || !to) {
    throw new HttpsError("invalid-argument", "symbol, from, and to are required");
  }
  return finnhubGet("company-news", { symbol, from, to });
});

// ---- Kalshi read-only relay and recorder -----------------------------------
// Kalshi's API answers 403 to any request carrying a browser Origin header and
// sends no CORS headers, so the page cannot call it directly. This relays the
// public order-book fields the Kalshi page needs.
//
// Deliberately narrow: two fixed series, GET only, no caller-supplied path or
// query, and no Kalshi credentials anywhere. It cannot place or cancel an order
// and must not be widened into something that can without a separate review.
const { initializeApp, getApps } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");
const { onSchedule } = require("firebase-functions/v2/scheduler");
const botRun = require("./kalshiBotRun");
const alerts = require("./kalshiAlertLib");
const live = require("./kalshiLiveLib");
const account = require("./kalshiAccountLib");
const kalshi = require("./kalshiLib");

// The first host is the one Kalshi's API documentation gives. api.elections sits
// behind a CDN that refuses Google Cloud addresses (HTTP 403), so it is only the
// fallback. Both serve the same read-only public data.
const KALSHI_HOSTS = [
  "https://external-api.kalshi.com/trade-api/v2",
  "https://api.elections.kalshi.com/trade-api/v2",
];
const KALSHI_CACHE_MS = 2000;
let kalshiCache = { at: 0, body: null };

// The Kalshi page is for the owner only. Two independent checks, both required:
// the token's email, and the isAdmin flag on the user document that
// firestore.rules already treats as the single source of truth for admin. The
// email alone would not follow a change of admin account; the flag alone would
// let a second admin in by accident. The page hides itself for anyone else, but
// hiding is not the control, this is.
const KALSHI_OWNER_EMAIL = "heiszcam@gmail.com";

// getFirestore() needs the DEFAULT app. "Is any app initialised?" is the wrong
// question: the functions runtime can already hold another app, so a check on
// getApps().length skips initialisation and getFirestore() then throws
// "The default Firebase app does not exist". That is exactly what the first
// deploy did. Ask for the default app by name, and never initialise it twice
// (a second initializeApp() with the same name throws too).
function ensureDefaultAdminApp() {
  if (!getApps().some((a) => a.name === "[DEFAULT]")) initializeApp();
}
async function assertKalshiAdmin(auth) {
  assertSignedIn(auth);
  if (!auth.token || auth.token.email !== KALSHI_OWNER_EMAIL) {
    throw new HttpsError("permission-denied", "Not available for this account.");
  }
  // The email already matched, so only the owner can reach this line. A failure
  // to read the user document must still deny (fail closed), but it must say why:
  // an unnamed error here reaches the page as "INTERNAL" and hides the cause.
  let snap;
  try {
    ensureDefaultAdminApp();
    snap = await getFirestore().collection("users").doc(auth.uid).get();
  } catch (e) {
    console.error("kalshi admin check could not read the user document:", e);
    throw new HttpsError("unavailable", "Admin check failed: " + String((e && e.message) || e).slice(0, 120));
  }
  if (!snap.exists || snap.data().isAdmin !== true) {
    throw new HttpsError("permission-denied", "Not available for this account.");
  }
}

async function kalshiFetchSeries(series, status, limit) {
  const failures = [];
  for (const base of KALSHI_HOSTS) {
    const host = base.replace("https://", "").split("/")[0];
    const url = base + "/markets?series_ticker=" + series + "&status=" + status + "&limit=" + limit;
    // One host failing, for any reason (a refusal, a timeout, a dropped
    // connection, a body that is not JSON), is a reason to try the next one,
    // never a crash. An error that escapes here reaches the page as the useless
    // "INTERNAL", which is what hid the real cause the first time.
    try {
      const res = await fetch(url, {
        signal: AbortSignal.timeout(8000),
        headers: { "User-Agent": "shwoopnet-monitor/1.0 (read-only market data)", "Accept": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        return data.markets || [];
      }
      // A refusal from Kalshi's CDN says very little, so keep what it does say
      // in the logs. Without this a 403 reads as a bug in our code when it may
      // be the network path (some CDNs refuse cloud-provider address ranges),
      // and the two need different fixes. The thrown message names the host and
      // status only, never the response body, which is a whole HTML page.
      const body = (await res.text().catch(() => "")).slice(0, 200);
      const cdn = res.headers.get("x-cache") || res.headers.get("server") || "";
      console.error("Kalshi " + host + " " + series + " HTTP " + res.status + " cdn=" + cdn + " body=" + body);
      failures.push(host + " HTTP " + res.status + (cdn ? " (" + cdn + ")" : ""));
    } catch (e) {
      console.error("Kalshi " + host + " " + series + " failed:", e);
      failures.push(host + " " + ((e && e.name) || "error") + ": " + String((e && e.message) || e).slice(0, 80));
    }
  }
  throw new HttpsError("unavailable", "Kalshi " + series + ": " + failures.join(" | "));
}

exports.kalshiBooks = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  // Many tabs polling at once must not multiply into Kalshi rate limits.
  if (kalshiCache.body && Date.now() - kalshiCache.at < KALSHI_CACHE_MS) {
    return kalshiCache.body;
  }
  try {
    const markets = [];
    for (const series of kalshi.KALSHI_SERIES) {
      const raw = await kalshiFetchSeries(series, "open", 5);
      raw.forEach((m) => markets.push(kalshi.trimMarket(series, m)));
    }
    const body = { fetchedAt: Date.now(), markets };
    kalshiCache = { at: Date.now(), body };
    return body;
  } catch (e) {
    if (e instanceof HttpsError) throw e;
    console.error("kalshiBooks failed:", e);
    throw new HttpsError("unavailable", "Relay error: " + String((e && e.message) || e).slice(0, 120));
  }
});

// ---- Kalshi PAPER bot, on the server ----------------------------------------
// Runs once a minute on Google's servers, so nothing depends on a computer being
// awake. PAPER ONLY: it simulates trades from Kalshi's public prices and cannot place
// an order (the api object below has no order method, and a test asserts this file's
// bot section contains no order code). The logic lives in kalshiBotLib.js and the tick
// in kalshiBotRun.js, both tested without Firebase; this file only supplies Firestore
// and Kalshi to them.
//
// State is in Firestore, not on a disk. A position is created by a key derived from its
// market (h2-<ticker>) with create(), which fails if the document exists, so two runs at
// the same moment cannot enter one market twice. The collections have no client write
// rule except the admin's halt switch (see firestore.rules).
async function kalshiGetJson(pathAndQuery) {
  const failures = [];
  for (const base of KALSHI_HOSTS) {
    const host = base.replace("https://", "").split("/")[0];
    try {
      const res = await fetch(base + pathAndQuery, {
        signal: AbortSignal.timeout(8000),
        headers: { "User-Agent": "shwoopnet-bot/1.0 (paper)", "Accept": "application/json" },
      });
      if (res.ok) return await res.json();
      failures.push(host + " HTTP " + res.status);
    } catch (e) {
      failures.push(host + " " + String((e && e.message) || e).slice(0, 60));
    }
  }
  throw new Error(pathAndQuery.split("?")[0] + ": " + failures.join(" | "));
}

function kalshiBotApi() {
  return {
    exchangeStatus: () => kalshiGetJson("/exchange/status"),
    markets: (series) => kalshiFetchSeries(series, "open", 5),
    market: async (ticker) => (await kalshiGetJson("/markets/" + encodeURIComponent(ticker))).market || {},
  };
}

function firestoreBotStore(db) {
  const positions = db.collection("kalshiBotPositions");
  const events = db.collection("kalshiBotEvents");
  const meta = db.collection("kalshiBotMeta");
  const fromDocs = (snap) => snap.docs.map((d) => Object.assign({ id: d.id }, d.data()));
  return {
    async getStatus() { const s = await meta.doc("status").get(); return s.exists ? s.data() : null; },
    async getControl() { const s = await meta.doc("control").get(); return s.exists ? s.data() : {}; },
    async listOpen() { return fromDocs(await positions.where("status", "==", "open").get()); },
    // One range filter on one field, so no composite index is needed.
    async listClosedSince(ms) { return fromDocs(await positions.where("settledAt", ">=", ms).get()).filter((p) => p.status === "closed"); },
    async createPosition(id, data) {
      try {
        await positions.doc(id).create(data);
        return true;
      } catch (e) {
        if (e && (e.code === 6 || /ALREADY_EXISTS/.test(String(e.message)))) return false;
        throw e;
      }
    },
    async closePosition(id, patch) {
      return db.runTransaction(async (t) => {
        const ref = positions.doc(id);
        const snap = await t.get(ref);
        if (!snap.exists || snap.data().status !== "open") return false;
        t.update(ref, Object.assign({}, patch, { status: "closed" }));
        return true;
      });
    },
    async addEvent(e) { await events.add(e); },
    async setStatus(st) { await meta.doc("status").set(st); },
  };
}

// ---- Kalshi LIVE test order (ONE contract, real money, admin only) ----------------
// Step 1 of putting a small amount of real money behind this: it proves production signing, a real fill, the
// real fee and the real duplicate-order behaviour with one contract. All the logic and all the order code are in
// kalshiLiveLib.js (production host only, $2 cap, never retried, 2 a day and 5 ever). Takes nothing from the page.
function firestoreLiveStore(db) {
  const col = db.collection("kalshiLiveOrders");
  return {
    async halted() {
      const s = await db.collection("kalshiBotMeta").doc("control").get();
      return !s.exists || s.data().halt !== false;     // anything but an explicit "not halted" counts as halted
    },
    async countSince(ts) { return (await col.where("ts", ">=", ts).get()).size; },
    async countEver() { return (await col.get()).size; },
    async lastTestAt() {
      const s = await col.orderBy("ts", "desc").limit(1).get();
      return s.empty ? null : s.docs[0].data().ts;
    },
    async hasUnresolved() {
      const s = await col.where("status", "in", ["sending", "unknown"]).limit(1).get();
      return !s.empty;
    },
    async createTest(id, data) {
      try {
        await col.doc(id).create(data);
        return true;
      } catch (e) {
        if (e && (e.code === 6 || /ALREADY_EXISTS/.test(String(e.message)))) return false;
        throw e;
      }
    },
    async updateTest(id, patch) { await col.doc(id).update(patch); },
  };
}

exports.kalshiLiveTrade = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 60 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    ensureDefaultAdminApp();
    try {
      const { active, quotes } = await live.loadQuotes(kalshiBotApi());
      return await live.runLiveTest({
        quotes, active, enabled: KALSHI_LIVE_ENABLED.value() === "on", store: firestoreLiveStore(getFirestore()), now: Date.now(),
        keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), fetchFn: fetch,
      });
    } catch (e) {
      if (e instanceof HttpsError) throw e;
      throw new HttpsError("internal", "Live test failed: " + String((e && e.message) || e).slice(0, 120));
    }
  }
);

// ---- Kalshi account view (read only, admin only) -----------------------------------------------------------------
// Balance per shard, open positions and recent fills, read with the live key. GET requests only and no order code
// (kalshiAccountLib.js); it works whether or not the live test switch is on, and takes nothing from the page.
exports.kalshiLiveAccount = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 30 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    try {
      return await account.readAccount({ fetchFn: fetch, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), now: Date.now() });
    } catch (e) {
      if (e instanceof HttpsError) throw e;
      throw new HttpsError("internal", "Account read failed: " + String((e && e.message) || e).slice(0, 120));
    }
  }
);

// ---- Armed live test: click once, it scans every minute, sends ONE order, then switches itself off ------------
// kalshiLiveArm only flips a control document (no order code, no key). kalshiLiveArmed runs every minute, does
// nothing unless that document says armed and unexpired, and then makes one ordinary kalshiLiveTrade attempt with
// every one of its guards. One arming can place at most one order: it switches off as soon as an order is sent
// (or refused, or its answer is lost), on any error, and after 3 hours regardless. All logic is in kalshiLiveLib.js.
exports.kalshiLiveArm = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  ensureDefaultAdminApp();
  const on = request.data && request.data.on === true;
  const ref = getFirestore().collection("kalshiLiveControl").doc("arm");
  if (!on) {
    await ref.set({ armed: false, endedAt: Date.now(), endedBecause: "switched off by the owner" }, { merge: true });
    return { armed: false };
  }
  if (KALSHI_LIVE_ENABLED.value() !== "on") {
    throw new HttpsError("failed-precondition", "Live test trading is switched off on the server (KALSHI_LIVE_ENABLED), so there is nothing to arm.");
  }
  const now = Date.now();
  await ref.set({ armed: true, since: now, until: now + live.ARM_MS, endedAt: null, endedBecause: null });
  return { armed: true, until: now + live.ARM_MS };
});

exports.kalshiLiveArmed = onSchedule(
  { schedule: "every 1 minutes", secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 55, retryCount: 0, memory: "256MiB" },
  async () => {
    ensureDefaultAdminApp();
    const db = getFirestore();
    const armRef = db.collection("kalshiLiveControl").doc("arm");
    const snap = await armRef.get();
    const arm = snap.exists ? snap.data() : null;
    const now = Date.now();
    const args = {
      arm, now, setArm: (patch) => armRef.set(patch, { merge: true }),
      recordLast: (r) => db.collection("kalshiLiveControl").doc("last").set(r),
    };
    if (arm && arm.armed === true && arm.until > now) {
      const { active, quotes } = await live.loadQuotes(kalshiBotApi());
      Object.assign(args, {
        quotes, active, enabled: KALSHI_LIVE_ENABLED.value() === "on", store: firestoreLiveStore(db),
        keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), fetchFn: fetch,
      });
    }
    await live.runArmedTick(args);
  }
);

exports.kalshiBot = onSchedule(
  { schedule: "every 1 minutes", timeoutSeconds: 55, retryCount: 0, memory: "256MiB" },
  async () => {
    ensureDefaultAdminApp();
    const r = await botRun.runTick({ store: firestoreBotStore(getFirestore()), api: kalshiBotApi(), now: Date.now() });
    await alerts.sendAll(fetch, alerts.pingsFor({ base: KALSHI_WATCHDOG_URL.value(), ok: r.ok, tierMode: r.tier, prevTier: r.prevTier }));
    console.log("kalshiBot tick: entered=" + r.entered + " tier=" + r.tier + (r.block ? " blocked=" + r.block : ""));
  }
);
