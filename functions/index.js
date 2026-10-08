const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret, defineString } = require("firebase-functions/params");

// Optional outside watchdog for the live arm. Put KALSHI_WATCHDOG_URL=<ping url> in
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
const watchdog = require("./kalshiWatchdogLib");
const live = require("./kalshiLiveLib");
const book = require("./kalshiBookLib");
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

// ---- Kalshi market reads (public, keyless, GET only) ----
async function kalshiGetJson(pathAndQuery) {
  const failures = [];
  for (const base of KALSHI_HOSTS) {
    const host = base.replace("https://", "").split("/")[0];
    try {
      const res = await fetch(base + pathAndQuery, {
        signal: AbortSignal.timeout(8000),
        headers: { "User-Agent": "shwoopnet-bot/1.0", "Accept": "application/json" },
      });
      if (res.ok) return await res.json();
      failures.push(host + " HTTP " + res.status);
    } catch (e) {
      failures.push(host + " " + String((e && e.message) || e).slice(0, 60));
    }
  }
  throw new Error(pathAndQuery.split("?")[0] + ": " + failures.join(" | "));
}

function kalshiMarketApi() {
  return {
    exchangeStatus: () => kalshiGetJson("/exchange/status"),
    markets: (series) => kalshiFetchSeries(series, "open", 5),
    market: async (ticker) => (await kalshiGetJson("/markets/" + encodeURIComponent(ticker))).market || {},
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
    // Filled orders (a single-field query, so no index); the caller keeps the ones not yet settled.
    async openFilled() { return (await col.where("status", "==", "filled").get()).docs.map((d) => ({ id: d.id, ...d.data() })); },
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
    // Every order since a time, with its id. A single-field query, so it needs no composite index; the caller filters.
    async sessionTrades(since) { return (await col.where("ts", ">=", since).get()).docs.map((d) => ({ id: d.id, ...d.data() })); },
  };
}

exports.kalshiLiveTrade = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 60 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    ensureDefaultAdminApp();
    try {
      const { active, quotes } = await live.loadQuotes(kalshiMarketApi());
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
// Balance, positions, fills and the settled result of each fill's market. Shared by the page's callable and the
// once-a-minute snapshot, so both show the same thing. Reads only.
async function readAccountFull(db) {
  const snap = await db.collection("kalshiLiveControl").doc("baseline").get();
  const d = await account.readAccount({
    fetchFn: fetch, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), now: Date.now(),
    baseline: snap.exists ? snap.data() : null,
  });
  // How each market of the fills shown ended ("yes", "no", or null while it is still open), so the page can show a profit or loss on
  // every trade line. A public read of the market, one per ticker, never an order; a failed read just leaves that trade "open".
  const results = {};
  const tickers = [...new Set(((d.fills && d.fills.ok && d.fills.fills) || []).map((f) => f.ticker).filter(Boolean))].slice(0, 20);
  await Promise.all(tickers.map(async (t) => {
    try {
      const m = (await kalshiGetJson("/markets/" + encodeURIComponent(t))).market || {};
      results[t] = m.result === "yes" || m.result === "no" ? m.result : null;
    } catch (e) { results[t] = null; }
  }));
  // Whether the order switch is on, so the page can say so. It reveals nothing but "on" or "off".
  return { ...d, results, liveSwitch: KALSHI_LIVE_ENABLED.value() === "on" };
}

exports.kalshiLiveAccount = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 30 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    ensureDefaultAdminApp();
    try {
      return await readAccountFull(getFirestore());
    } catch (e) {
      if (e instanceof HttpsError) throw e;
      throw new HttpsError("internal", "Account read failed: " + String((e && e.message) || e).slice(0, 120));
    }
  }
);

// "Start fresh from now": the account is shared with the owner's own earlier trades, so this draws a permanent line.
// It records the time and the current total balance ONCE (Firestore create(): it cannot be overwritten, and a second
// press only reports the existing line). Nothing on Kalshi is changed or erased. To move the line, delete the
// kalshiLiveControl/baseline document in the Firebase console. Reads only, takes nothing from the page.
exports.kalshiLiveBaseline = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 30 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    ensureDefaultAdminApp();
    const ref = getFirestore().collection("kalshiLiveControl").doc("baseline");
    const existing = await ref.get();
    if (existing.exists) return { set: false, alreadySet: true, baseline: existing.data() };
    const now = Date.now();
    const d = await account.readAccount({ fetchFn: fetch, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), now });
    const total = d.balance.ok ? d.balance.totalDollars : null;
    if (total === null) throw new HttpsError("failed-precondition", "The balance could not be read, so no baseline was set.");
    const doc = { since: now, startingDollars: Math.round(total * 100) / 100, setAt: now };
    try {
      await ref.create(doc);
    } catch (e) {
      if (e && (e.code === 6 || /ALREADY_EXISTS/.test(String(e.message)))) return { set: false, alreadySet: true, baseline: (await ref.get()).data() };
      throw e;
    }
    return { set: true, baseline: doc };
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
  const events = getFirestore().collection("kalshiLiveEvents");
  if (!on) {
    await ref.set({ armed: false, endedAt: Date.now(), endedBecause: "switched off by the owner" }, { merge: true });
    await events.add({ ts: Date.now(), kind: "disarmed", detail: "switched off by you" });
    return { armed: false };
  }
  if (KALSHI_LIVE_ENABLED.value() !== "on") {
    throw new HttpsError("failed-precondition", "Live test trading is switched off on the server (KALSHI_LIVE_ENABLED), so there is nothing to arm.");
  }
  const sess = await getFirestore().collection("kalshiLiveControl").doc("session").get();
  if (sess.exists && sess.data().active === true && sess.data().until > Date.now()) {
    throw new HttpsError("failed-precondition", "The 24 hour L1 session is running. Stop it before arming a single test order.");
  }
  const now = Date.now();
  await ref.set({ armed: true, since: now, until: now + live.ARM_MS, endedAt: null, endedBecause: null });
  await events.add({ ts: now, kind: "armed", detail: "scanning every minute for up to 3 hours, one order at most" });
  return { armed: true, until: now + live.ARM_MS };
});

// The owner's 24 hour L1 session (README: "Live waiver: L1 for 24 hours"). This only switches the session document
// on or off, with a server-set expiry; the scheduled function below does the work, and every limit is in kalshiLiveLib.js.
exports.kalshiL1Session = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  ensureDefaultAdminApp();
  const on = request.data && request.data.on === true;
  // Size scaling is off unless this is literally true. It is a choice made when starting, kept on the session, and cannot be changed mid-run.
  const sizing = on && request.data.sizing === true;
  const db = getFirestore();
  const ref = db.collection("kalshiLiveControl").doc("session");
  const events = db.collection("kalshiLiveEvents");
  if (!on) {
    await ref.set({ active: false, endedAt: Date.now(), endedBecause: "switched off by the owner" }, { merge: true });
    await events.add({ ts: Date.now(), kind: "session ended", detail: "switched off by you" });
    return { active: false };
  }
  if (KALSHI_LIVE_ENABLED.value() !== "on") {
    throw new HttpsError("failed-precondition", "Live trading is switched off on the server (KALSHI_LIVE_ENABLED), so there is nothing to start.");
  }
  const arm = await db.collection("kalshiLiveControl").doc("arm").get();
  if (arm.exists && arm.data().armed === true && arm.data().until > Date.now()) {
    throw new HttpsError("failed-precondition", "A single test order is armed. Disarm it before starting the 24 hour session.");
  }
  const now = Date.now();
  await ref.set({ active: true, since: now, until: now + live.L1_SESSION_MS, ordersSent: 0, startCash: null, sizing, endedAt: null, endedBecause: null, lastTickAt: null, lastNote: "Started. Waiting for a market about 6 minutes from its close." });
  await events.add({ ts: now, kind: "session started", detail: "L1 for 24 hours at 88c to 97c about 6 minutes before the close, " + (sizing ? "size scales with the account (" + (live.L1_SIZE_FRACTION * 100) + "% of cash per order, up to " + live.L1_SIZE_MAX + " contracts), stops when the bot is down " + (live.L1_SIZED_STOP_FRACTION * 100) + "% of the starting cash" : "one contract, stops when the bot is down $" + live.L1_LOSS_STOP.toFixed(2)) });
  return { active: true, until: now + live.L1_SESSION_MS };
});

exports.kalshiLiveArmed = onSchedule(
  { schedule: "every 1 minutes", secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 55, retryCount: 0, memory: "256MiB" },
  async () => {
    // The dead-man's switch pings after EVERY completed run, armed or not, so an idle but alive function keeps it
    // alive and a dead one does not. A run that throws sends the failure ping instead of the success one.
    let failure = null;
    try {
      ensureDefaultAdminApp();
      const db = getFirestore();
      const armRef = db.collection("kalshiLiveControl").doc("arm");
      const snap = await armRef.get();
      const arm = snap.exists ? snap.data() : null;
      const now = Date.now();
      const args = {
        arm, now, setArm: (patch) => armRef.set(patch, { merge: true }),
        recordLast: (r) => db.collection("kalshiLiveControl").doc("last").set(r),
        logEvent: (e) => db.collection("kalshiLiveEvents").add(e),
      };
      const armedOn = Boolean(arm && arm.armed === true && arm.until > now);
      const sessRef = db.collection("kalshiLiveControl").doc("session");
      const sessSnap = await sessRef.get();
      const session = sessSnap.exists ? sessSnap.data() : null;
      const sessionOn = Boolean(session && session.active === true);
      let market = null;
      if (armedOn || sessionOn) market = await live.loadQuotes(kalshiMarketApi());
      if (armedOn) {
        Object.assign(args, {
          quotes: market.quotes, active: market.active, enabled: KALSHI_LIVE_ENABLED.value() === "on", store: firestoreLiveStore(db),
          keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), fetchFn: fetch,
        });
      }
      await live.runArmedTick(args);
      // A single armed test order and the session never run together; the callables refuse to start one while the
      // other is on, and if both documents say "on" anyway, the session does nothing this minute.
      if (sessionOn && !armedOn) {
        await live.runL1Tick({
          session, now, setSession: (patch) => sessRef.set(patch, { merge: true }), logEvent: args.logEvent,
          quotes: market.quotes, active: market.active, enabled: KALSHI_LIVE_ENABLED.value() === "on", store: firestoreLiveStore(db),
          keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), fetchFn: fetch,
        });
      }
      // Settle finished trades whether or not a session is running (see settleOpenOrders). After the tick and after its own guard, so it can never fail or
      // delay the tick: a bad read is logged and the next minute tries again.
      try {
        await live.settleOpenOrders({ store: firestoreLiveStore(db), fetchFn: fetch, nowMs: now });
      } catch (e) {
        console.error("kalshiLiveArmed: settle sweep failed: " + String((e && e.message) || e).slice(0, 160));
      }
      // Keep the account page current while nobody has it open: the latest read is stored for the page to show the
      // moment it loads, at the minutes where the account can change (see snapshotDue). This runs after the tick and can never fail it: a bad read is logged and the minute still counts.
      try {
        const accRef = db.collection("kalshiLiveControl").doc("account");
        const prev = await accRef.get();
        if (account.snapshotDue(now, prev.exists ? prev.data().at : NaN)) {
          const full = await readAccountFull(db);
          await accRef.set(JSON.parse(JSON.stringify(full)));
        }
      } catch (e) {
        console.error("kalshiLiveArmed: account snapshot failed: " + String((e && e.message) || e).slice(0, 160));
      }
    } catch (e) {
      failure = e;
    }
    await watchdog.sendAll(fetch, watchdog.pingsFor({ base: KALSHI_WATCHDOG_URL.value(), ok: !failure, reason: failure && failure.message }));
    if (failure) throw failure;
  }
);

// Records the real order book of the open Bitcoin and gold 15 minute markets about every 10 seconds
// (see kalshiBookLib.js). READ ONLY and keyless. It is the LAST export on purpose: the tests slice the file from
// here to prove nothing after this point can see the live key or place an order.
exports.kalshiBookRecorder = onSchedule(
  { schedule: "every 1 minutes", timeoutSeconds: 70, retryCount: 0, memory: "256MiB" },
  async () => {
    ensureDefaultAdminApp();
    const db = getFirestore();
    const snaps = db.collection("kalshiBookSnaps");
    const r = await book.recordMinute({
      get: kalshiGetJson, now: Date.now, sleep: (ms) => new Promise((res) => setTimeout(res, ms)),
      store: {
        writeMinute: (id, doc) => snaps.doc(id).set(doc),
        async pruneBefore(ts) {
          const old = await snaps.where("ts", "<", ts).limit(50).get();
          await Promise.all(old.docs.map((d) => d.ref.delete()));
        },
        setStatus: (st) => db.collection("kalshiBookMeta").doc("status").set(st),
      },
    });
    console.log("kalshiBookRecorder: snaps=" + r.snaps + " errs=" + r.errs);
  }
);
