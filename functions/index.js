const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret, defineString } = require("firebase-functions/params");

// Optional outside watchdog for the live arm. Put KALSHI_WATCHDOG_URL=<ping url> in
// functions/.env (gitignored) before deploying. Empty means no alerts, nothing else changes.
const KALSHI_WATCHDOG_URL = defineString("KALSHI_WATCHDOG_URL", { default: "" });
// Optional push when the bot stops ITSELF (see kalshiWatchdogLib.stopAlertPings). Put KALSHI_STOP_ALERT_URL=https://ntfy.sh/<a-long-random-topic> in functions/.env.
// Empty means no alert, nothing else changes.
const KALSHI_STOP_ALERT_URL = defineString("KALSHI_STOP_ALERT_URL", { default: "" });

// The LIVE test order (real money). The switch is off until the owner sets KALSHI_LIVE_ENABLED=on in
// functions/.env and redeploys: deploying alone cannot place an order.
//   firebase functions:secrets:set KALSHI_LIVE_KEY_ID
//   firebase functions:secrets:set KALSHI_LIVE_PRIVATE_KEY   (--data-file, never paste the PEM into a chat)
const KALSHI_LIVE_KEY_ID = defineSecret("KALSHI_LIVE_KEY_ID");
const KALSHI_LIVE_PRIVATE_KEY = defineSecret("KALSHI_LIVE_PRIVATE_KEY");
const KALSHI_LIVE_ENABLED = defineString("KALSHI_LIVE_ENABLED", { default: "off" });
// Phone alerts (Web Push, kalshiPushLib.js): ONE secret, the VAPID private key; the public key is derived from it. Set it with functions/deploy-push.sh, never by pasting it anywhere.
const KALSHI_PUSH_VAPID_PRIVATE = defineSecret("KALSHI_PUSH_VAPID_PRIVATE");

// Any signed-in caller passes this first wall; the Kalshi functions then
// require the owner's email AND the isAdmin flag (assertKalshiAdmin below).
// There is no sign-up on the site: an account is created by hand, and
// firestore.rules refuses to create a users document from a browser.
function assertSignedIn(auth) {
  if (!auth) {
    throw new HttpsError("permission-denied", "Sign in required.");
  }
}

// The Finnhub proxy (finnhubQuote, finnhubCompanyNews) and its FINNHUB_API_KEY secret were removed on 2026-10-12 with the rest of the site's
// market-data integrations: the page no longer calls a vendor, and the Brief reads shared/marketSnapshot, which shwoop-server writes.
// Deleting them from this file does not undeploy them: `firebase deploy` asks whether to delete them (answer yes), and the secret goes with
// `firebase functions:secrets:destroy FINNHUB_API_KEY`.

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
// The owner asked for everything to be shut off (Oct 10, 2026) and turned it back on (Oct 12, 2026, with $500 in the account). While this is true NO live order is sent by the bot, whatever the
// session or the server switch say, and the bot cannot be started. It is a code change on purpose: it holds even if a session document says "on". Setting it back to true, in review and
// deploy, stops all buying and Start with one token. The exit watch is untouched either way (it only closes positions the bot already opened).
const CODE_KILL_SWITCH = false;
const book = require("./kalshiBookLib");
const marketTape = require("./marketTapeLib");
const account = require("./kalshiAccountLib");
const kalshi = require("./kalshiLib");
const paper = require("./kalshiPaperLib");
const push = require("./kalshiPushLib");
const webpush = require("web-push");
const { onDocumentWritten } = require("firebase-functions/v2/firestore");

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
    // The extra display series must never take the page's Bitcoin and gold cards down with them: a failure here is skipped, not thrown.
    for (const series of kalshi.KALSHI_EXTRA_SERIES) {
      try {
        const raw = await kalshiFetchSeries(series, "open", 5);
        raw.forEach((m) => markets.push(kalshi.trimMarket(series, m)));
      } catch (e) {
        console.error("kalshiBooks: " + series + " skipped: " + String((e && e.message) || e).slice(0, 120));
      }
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
// One reader per function instance, so the older part of the 24 hour list is read once every 15 minutes instead of every minute.
const l1OrderReader = live.makeRecentOrderReader(async (ts) => (await getFirestore().collection("kalshiLiveOrders").where("ts", ">=", ts).get()).docs.map((d) => ({ id: d.id, ...d.data() })));
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
    // Orders are created with settled: false, so "filled and not settled" is a handful of documents, not every order ever filled (this runs every minute and reads are billed). Orders
    // created before that field existed have no such field and would be missed, so the last few hours are read as well; the caller keeps the ones not yet settled.
    async openFilled() {
      const [open, recent] = await Promise.all([
        col.where("status", "==", "filled").where("settled", "==", false).get(),
        col.where("ts", ">=", Date.now() - 3 * 3600 * 1000).get(),
      ]);
      const byId = new Map();
      for (const d of [...open.docs, ...recent.docs]) { const x = d.data(); if (x.status === "filled") byId.set(d.id, { id: d.id, ...x }); }
      return [...byId.values()];
    },
    // Orders marked "hand" (a single-field query, so no index). A handful: the repair pass in settleOpenOrders asks each of them once more with the fixed check and marks it checked.
    async handOrders() {
      const s = await col.where("result", "==", "hand").get();
      return s.docs.map((d) => ({ id: d.id, ...d.data() }));
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
    // Every order since a time, with its id. A single-field query, so it needs no composite index; the caller filters.
    async sessionTrades(since) { return (await col.where("ts", ">=", since).get()).docs.map((d) => ({ id: d.id, ...d.data() })); },
    // The tick's 24 hour read, with the older part kept in memory (see makeRecentOrderReader).
    sessionTradesCached(since, now) { return l1OrderReader(since, now); },
    // The exit watch's few recent filled orders (a single-field query again), not every filled order ever: it looks several times a minute.
    // Cost (Oct 21, 2026): asks for filled AND unsettled orders only (two equalities, so no index) instead of every order of the last 25 minutes, because it runs several times a minute. Every order is written with settled: false,
    // and the exit watch only ever acts on an unsettled one, so nothing it would sell is left out. The time filter is applied here.
    async recentFilled(since) { return (await col.where("status", "==", "filled").where("settled", "==", false).get()).docs.map((d) => ({ id: d.id, ...d.data() })).filter((o) => Number(o.ts) >= since); },
    // One closer per market at a time (the exit watch or Flatten, see kalshiLiveLib.claimClose). False when the OTHER closer took it less than ttl ago; the same closer may take it again.
    async claimClose(ticker, who, now, ttl) {
      const ref = db.collection("kalshiLiveClosing").doc(String(ticker));
      return db.runTransaction(async (tx) => {
        const snap = await tx.get(ref);
        const d = snap.exists ? snap.data() : null;
        if (d && d.by !== who && now - Number(d.at) < ttl) return false;
        tx.set(ref, { by: who, at: now });
        return true;
      });
    },
    // Atomic: only one instance gets to send each exit sell. False when another has it, when it has already been tried this many times, or when the order has settled.
    async claimExit(id, tries) {
      const ref = col.doc(id);
      return db.runTransaction(async (tx) => {
        const snap = await tx.get(ref);
        const d = snap.exists ? snap.data() : null;
        if (!d || d.exitStatus === "sending" || (Number(d.exitTries) || 0) !== tries || d.settled === true) return false;
        tx.update(ref, { exitStatus: "sending", exitTries: tries + 1 });
        return true;
      });
    },
  };
}


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

// The single test order and its arming switch (kalshiLiveTrade, kalshiLiveArm) were removed on Oct 8, 2026: nothing could arm them any more and they were
// the only callables that could place an order outside the L1 session. kalshiLiveArmed below still reads the old arm document and runs its tick, which is
// inert unless that document says armed; deleting that path and its library code is a separate, larger change.

// The owner's 24 hour L1 session (README: "Live waiver: L1 for 24 hours"). This only switches the session document
// on or off, with a server-set expiry; the scheduled function below does the work, and every limit is in kalshiLiveLib.js.
// kalshiExitMode and kalshiPoolRule (the page's two switches) were removed on Oct 12, 2026 at the owner's request: the exit is fixed at 25c and always sells, and the
// reinvest pool always rebuilds after every win. There is deliberately no callable that can change either, and nothing stored on the session document is read for them
// (the scheduled exit and runL1Tick ignore any old exitMode or poolRule). Do not add one back as a convenience: a risk setting that can be toggled from the page can be toggled in a bad hour.
exports.kalshiL1Session = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  ensureDefaultAdminApp();
  const on = request.data && request.data.on === true;
  // Size scaling is decided HERE, never by the page (the owner, Oct 23, 2026): a risk setting that can be chosen from the page can be chosen in a bad hour. Starting always means the
  // gold size ladder (every other market is capped at one contract in code), which is what the old box did while it was ticked. Nothing in request.data can change it.
  const sizing = on;
  // The high-point stop is likewise off unless this is literally true, chosen at the start and kept on the session.
  const trailing = on && request.data.trailing === true;
  const db = getFirestore();
  const ref = db.collection("kalshiLiveControl").doc("session");
  const events = db.collection("kalshiLiveEvents");
  if (!on) {
    await ref.set({ active: false, endedAt: Date.now(), endedBecause: "switched off by the owner" }, { merge: true });
    await events.add({ accountId: live.DEFAULT_ACCOUNT_ID, ts: Date.now(), kind: "session ended", detail: "switched off by you" });
    return { active: false };
  }
  if (CODE_KILL_SWITCH) {
    throw new HttpsError("failed-precondition", "Live trading is switched off in the code (CODE_KILL_SWITCH in functions/index.js), so the bot cannot be started.");
  }
  if (KALSHI_LIVE_ENABLED.value() !== "on") {
    throw new HttpsError("failed-precondition", "Live trading is switched off on the server (KALSHI_LIVE_ENABLED), so there is nothing to start.");
  }
  const arm = await db.collection("kalshiLiveControl").doc("arm").get();
  if (arm.exists && arm.data().armed === true && arm.data().until > Date.now()) {
    throw new HttpsError("failed-precondition", "A single test order is armed. Disarm it before starting the bot.");
  }
  // Starting replaces the session document, and the loss stop is measured from its `since`. A second Start (a stale tab, a double tap) on a bot that is already running would hand it a
  // fresh stop budget mid-loss, so a running bot refuses it. Stop it first if you mean to start again.
  const running = await ref.get();
  if (running.exists && running.data().active === true) {
    throw new HttpsError("failed-precondition", "The bot is already running. Switch it off first if you want to start it again.");
  }
  const now = Date.now();
  // Starting replaces the session document. There are no owner switches to carry across any more: the exit (25c, always selling) and the pool rule (after every win) are fixed in the code.
  await ref.set({ active: true, since: now, until: null, ordersSent: 0, startCash: null, sizing, trailing, endedAt: null, endedBecause: null, lastTickAt: null, lastNote: "Started. Waiting for a market about 6 minutes from its close." });
  // Flag the saved sizing state so the next review raises a collapsed cap to what a fresh start gives (see reviewSizing). Pool, savings and the loss-stop clock are kept.
  if (sizing) await db.collection("kalshiLiveControl").doc("sizing").set({ reseed: true }, { merge: true });
  await events.add({ accountId: live.DEFAULT_ACCOUNT_ID, ts: now, kind: "session started", detail: "L1 until you stop it, at 88c to 97c about 6 minutes before the close, " + (sizing ? "size scales with the account (one contract per $" + live.SCALE_DOLLARS_PER_CONTRACT + ", reviewed every 3 days, up to " + live.L1_SIZE_CEILING + "), stops when the bot is down " + (live.L1_SIZED_STOP_FRACTION * 100) + "% of the balance at the last review" : "one contract, stops when the bot is down $" + live.L1_LOSS_STOP.toFixed(2)) + (trailing ? ", measured from its best result so far" : "") });
  return { active: true };
});

// ---- Flatten all + halt (admin only, the owner's emergency button) ---------------------------------------------------------------
// Order matters: the bot is stopped FIRST (halt switch on, session ended, any armed single order disarmed) with nothing but database writes, so
// it cannot add to the account while the sells go out, and a failure of the exchange calls cannot leave it running. Then every open position is
// sold (kalshiLiveLib.flattenAll). Takes nothing from the page.
// The automatic shard split (see applyShardSplit in kalshiLiveLib.js). Admin only. "read" shows the target Kalshi has now; "apply" sets the fixed 20 / 80 split. Nothing in the request chooses a percentage.
exports.kalshiShardSplit = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 30 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    const apply = !!(request.data && request.data.action === "apply");
    // Anything that throws (a signing problem, an unreadable secret) is reported as its own message instead of the page's blank "internal", so the owner can see WHY it did not work. No secret value is in these messages.
    let out;
    try {
      ensureDefaultAdminApp();
      const args = { fetchFn: fetch, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), nowMs: Date.now() };
      out = apply ? await live.applyShardSplit(args) : await live.readShardSplit(args);
    } catch (e) {
      out = { ok: false, status: 0, reason: "The split call failed before Kalshi answered: " + String((e && e.name) || "Error") + ": " + String((e && e.message) || e).slice(0, 140) };
    }
    if (apply) {
      try { await getFirestore().collection("kalshiLiveEvents").add({ accountId: live.DEFAULT_ACCOUNT_ID, ts: Date.now(), kind: "shard split", detail: out.ok ? "target set: " + out.allocations.map((x) => "shard " + x.exchange_index + " " + x.percent + "%").join(", ") : String(out.reason || "failed").slice(0, 120) }); } catch (e) { /* the event is a note, never a reason to fail */ }
    }
    return { applied: apply, target: live.SHARD_SPLIT, ...out };
  }
);

exports.kalshiFlattenAll = onCall(
  { secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 60 },
  async (request) => {
    await assertKalshiAdmin(request.auth);
    ensureDefaultAdminApp();
    const db = getFirestore();
    const now = Date.now();
    await db.collection("kalshiBotMeta").doc("control").set({ halt: true, at: new Date(now) });
    await db.collection("kalshiLiveControl").doc("session").set({ active: false, endedAt: now, endedBecause: "flattened by the owner" }, { merge: true });
    await db.collection("kalshiLiveControl").doc("arm").set({ armed: false, endedAt: now, endedBecause: "flattened by the owner" }, { merge: true });
    const events = db.collection("kalshiLiveEvents");
    await events.add({ accountId: live.DEFAULT_ACCOUNT_ID, ts: now, kind: "session ended", detail: "flatten all and halt pressed by you" });
    let out;
    try {
      out = await live.flattenAll({ fetchFn: fetch, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), now, store: firestoreLiveStore(db) });
    } catch (e) {
      out = { ok: false, reason: "The sells failed: " + String((e && e.message) || e).slice(0, 120), results: [] };
    }
    try { await events.add({ accountId: live.DEFAULT_ACCOUNT_ID, ts: Date.now(), kind: "flatten", detail: out.ok ? out.results.map((r) => r.ticker + " " + r.status).join(", ") || "no open positions" : out.reason }); } catch (e) { /* the log is optional */ }
    return { halted: true, ...out };
  }
);

// ---- The market tape: prices for the ticker strip and the Brief, and a few headlines -------------------------------------------------------
// Every 5 minutes, around the clock, with NO secrets: public Yahoo chart prices and the public CNBC and MarketWatch RSS feeds (marketTapeLib.js), written to the one document
// shared/marketTape that every signed-in account reads. It places no order and holds no key. It replaces the Brief's dependence on shwoop-server (prices only between 08:00 and 17:00
// Eastern, news behind a paid key). Quotes are merged into the stored document one symbol at a time, so a symbol or feed that fails keeps its older value with its own asOf
// and the page says how old it is; `errors` names what failed on the last run.
exports.marketTapeTick = onSchedule(
  { schedule: "every 5 minutes", timeoutSeconds: 60, retryCount: 0, memory: "256MiB" },
  async () => {
    ensureDefaultAdminApp();
    const db = getFirestore();
    const r = await marketTape.readTape({ fetchFn: fetch, now: Date.now() });
    const patch = { updatedAt: Date.now(), errors: r.errors };
    if (Object.keys(r.quotes).length) patch.quotes = r.quotes;
    if (r.news) patch.news = r.news;
    if (r.mood) patch.mood = r.mood;
    await db.collection("shared").doc("marketTape").set(patch, { merge: true });
    console.log("marketTapeTick: quotes=" + Object.keys(r.quotes).length + " news=" + (r.news ? r.news.length : 0) + " errors=" + r.errors.length);
  }
);

// The exit watch: looks at the bot's own open positions about every 10 seconds for most of each minute (a scheduled function cannot run more often than once a minute, so it
// loops inside its run). It is the only function besides the armed bot that holds the live key, and it can only close a long the bot opened (kalshiLiveLib.runExitWatch).
// There is no mode: it always sells (at 25c) while the server's live switch is on, and only records what it would have sold when that switch is off. Nothing on the session document can turn it off.
exports.kalshiLiveExit = onSchedule(
  { schedule: "every 1 minutes", secrets: [KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY], timeoutSeconds: 58, retryCount: 0, memory: "256MiB" },
  async () => {
    ensureDefaultAdminApp();
    const db = getFirestore();
    const sessRef = db.collection("kalshiLiveControl").doc("session");
    const store = firestoreLiveStore(db);
    // Nothing open and not a minute L1 can buy in: skip the whole minute rather than sit in the loop below (compute time is the bill). Fails open (see exitWatchIdle).
    if (await live.exitWatchIdle({ store, now: Date.now() })) return;
    const stopAt = Date.now() + 47000;
    for (;;) {
      try {
        const snap = await sessRef.get();
        const session = snap.exists ? snap.data() : null;
        if (session) {
          await live.runExitWatch({
            store, fetchFn: fetch, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), now: Date.now(),
            enabled: KALSHI_LIVE_ENABLED.value() === "on", setSession: (patch) => sessRef.set(patch, { merge: true }),
            logEvent: async (e) => {
              await db.collection("kalshiLiveEvents").add({ accountId: live.DEFAULT_ACCOUNT_ID, ...e });
              if (e && e.kind === "session ended") await watchdog.sendAll(fetch, watchdog.stopAlertPings({ base: KALSHI_STOP_ALERT_URL.value(), detail: e.detail }));
            },
          });
        }
      } catch (e) {
        console.error("kalshiLiveExit: " + String((e && e.message) || e).slice(0, 200));
      }
      if (Date.now() + 11000 > stopAt) break;
      await new Promise((r) => setTimeout(r, 10000));
    }
  }
);

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
        // A session that ends by itself (the loss stop, a lost order answer) pushes an alert, if one is configured. The owner's own stops never come through here.
        logEvent: async (e) => {
          await db.collection("kalshiLiveEvents").add({ accountId: live.DEFAULT_ACCOUNT_ID, ...e });
          if (e && e.kind === "session ended") await watchdog.sendAll(fetch, watchdog.stopAlertPings({ base: KALSHI_STOP_ALERT_URL.value(), detail: e.detail }));
        },
      };
      const armedOn = Boolean(arm && arm.armed === true && arm.until > now);
      const sizingRef = db.collection("kalshiLiveControl").doc("sizing");
      const sessRef = db.collection("kalshiLiveControl").doc("session");
      const sessSnap = await sessRef.get();
      const session = sessSnap.exists ? sessSnap.data() : null;
      const sessionOn = Boolean(session && session.active === true);
      let market = null;
      if (armedOn || sessionOn) market = await live.loadQuotes(kalshiMarketApi());
      // Ethereum's markets are added to the list the tick reads (Bitcoin and gold come from loadQuotes). A failure here is skipped, never allowed to stop Bitcoin and gold.
      if (sessionOn && market) {
        for (const series of live.L1_SERIES.filter((x) => !live.LIVE_SERIES.includes(x))) {
          try { for (const m of await kalshiMarketApi().markets(series)) market.quotes.push({ series, m }); }
          catch (e) { console.error("kalshiLiveArmed: " + series + " quotes skipped: " + String((e && e.message) || e).slice(0, 120)); }
        }
      }
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
        const sizingSnap = await sizingRef.get();
        await live.runL1Tick({
          sizingState: sizingSnap.exists ? sizingSnap.data() : null, setSizingState: (st) => sizingRef.set(st),
          // The probe drop record (kalshiLiveControl/probeRecord): applied to the FRESH document inside a transaction, so two instances during a deploy cannot overwrite each other's entries. Admin read only and no client write (the kalshiLiveControl rule): only this function writes it.
          updateProbeRecord: (apply) => db.runTransaction(async (tx) => {
            const ref = db.collection("kalshiLiveControl").doc("probeRecord");
            const snap = await tx.get(ref);
            const r = apply(snap.exists ? snap.data() : {});
            if (r.changed) tx.set(ref, r.record);
            return r.record;
          }),
          session, now, setSession: (patch) => sessRef.set(patch, { merge: true }), logEvent: args.logEvent,
          quotes: market.quotes, active: market.active, enabled: !CODE_KILL_SWITCH && KALSHI_LIVE_ENABLED.value() === "on", store: firestoreLiveStore(db),
          keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), fetchFn: fetch,
        });
      }
      // Settle finished trades whether or not a session is running (see settleOpenOrders). After the tick and after its own guard, so it can never fail or
      // delay the tick: a bad read is logged and the next minute tries again.
      // The hand-sold repair pass re-reads every order marked hand, which is no longer needed every minute: once every 10 minutes is enough for something that only ever looks back.
      try {
        await live.settleOpenOrders({ store: firestoreLiveStore(db), fetchFn: fetch, nowMs: now, keyId: KALSHI_LIVE_KEY_ID.value(), pem: KALSHI_LIVE_PRIVATE_KEY.value(), repair: Math.floor(now / 60000) % 10 === 0 });
      } catch (e) {
        console.error("kalshiLiveArmed: settle sweep failed: " + String((e && e.message) || e).slice(0, 160));
      }
      // Keep the account page current while nobody has it open: the latest read is stored for the page to show the
      // moment it loads, at the minutes where the account can change (see snapshotDue). This runs after the tick and can never fail it: a bad read is logged and the minute still counts.
      try {
        const accRef = db.collection("kalshiLiveControl").doc("account");
        const prev = await accRef.get();
        if (account.snapshotDue(now, prev.exists ? prev.data().at : NaN)) {
          // At the quarter-hour minute, give the close a few seconds to settle before reading (the next minute's read is the backstop).
          const settleWait = account.snapshotWaitMs(Date.now());
          if (settleWait > 0) await new Promise((r) => setTimeout(r, settleWait));
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

// ---- The paper tracker (PAPER1), keyless ---------------------------------------------------------------------------------------------------
// Records what L1's rule WOULD have bought on three candidate markets (kalshiPaperLib.js), one contract, no money, and settles each from the public result. It holds NO secret, signs nothing, calls no
// /portfolio endpoint and sends no order: public market reads and its own Firestore records only. Each entry document is created once (its id is the ticker), so two processes during a deploy cannot
// record a market twice. It is not imported by, and shares nothing with, the trading code; a failure here is logged and costs a paper row at most.
async function kalshiFetchMarket(ticker) {
  for (const base of KALSHI_HOSTS) {
    try {
      const res = await fetch(base + "/markets/" + encodeURIComponent(ticker), { signal: AbortSignal.timeout(8000), headers: { "User-Agent": "shwoopnet-monitor/1.0 (read-only market data)", "Accept": "application/json" } });
      if (res.ok) { const data = await res.json(); return data.market || null; }
    } catch (e) { /* try the next host */ }
  }
  return null;
}
// Switched off on Oct 21, 2026 at the owner's request to cut the Firebase bill: its page card is gone and live one-contract probes replaced it, so it recorded for nobody. The function stays exported
// (the tests and the deploy scripts name it) and returns at once, which costs almost nothing; set this to true to record again. Its collection and its pass bar in the research README are untouched.
const PAPER_TRACKER_ON = false;
exports.kalshiPaperTick = onSchedule(
  { schedule: "every 1 minutes", timeoutSeconds: 50, retryCount: 0, memory: "256MiB" },
  async () => {
    if (!PAPER_TRACKER_ON) return;
    try {
      ensureDefaultAdminApp();
      const col = getFirestore().collection("kalshiPaperOrders");
      const r = await paper.runPaperTick({
        now: Date.now(),
        store: {
          async openDocs() { return (await col.where("settled", "==", false).limit(60).get()).docs.map((d) => ({ id: d.id, data: d.data() })); },
          async create(id, doc) { try { await col.doc(id).create(doc); return true; } catch (e) { if (e && (e.code === 6 || /ALREADY_EXISTS/.test(String(e.message)))) return false; throw e; } },
          async update(id, patch) { await col.doc(id).update(patch); },
        },
        fetchSeries: (series) => kalshiFetchSeries(series, "open", 6),
        fetchMarket: kalshiFetchMarket,
        log: (m) => console.error("kalshiPaperTick: " + m),
      });
      if (r.entries || r.settled) console.log("kalshiPaperTick: entries=" + r.entries + " settled=" + r.settled);
    } catch (e) { console.error("kalshiPaperTick: " + String((e && e.message) || e).slice(0, 200)); }
  }
);

// ---- Phone alerts (Web Push), admin only ---------------------------------------------------------------------------------------------
// The Kalshi page subscribes this phone or browser (a service worker and the owner's tap); the two triggers below read what the bot already wrote and push a short text to every stored
// subscription. Nothing here places or changes an order, holds a Kalshi key, or is called by the trading code, and each trigger catches every error: an alert that fails costs an alert, never a trade.
const PUSH_SUBJECT = "https://shwoopnet.github.io";
async function pushSend(db, kinds, doc, tagBase) {
  if (!kinds.length) return;
  const subsSnap = await db.collection("kalshiPushSubs").get();
  const subs = subsSnap.docs.map((d) => ({ id: d.id, subscription: d.data().subscription })).filter((x) => x.subscription);
  if (!subs.length) return;
  // The last 24 hours of the bot's own trades go into a settled or sold alert, so the lock screen says how the day is going. One read of the recent orders, only when such an alert is sent.
  let ctx = {};
  if (kinds.includes("settled") || kinds.includes("sell")) {
    try { const now = Date.now(); ctx = { day: push.dayNet((await db.collection("kalshiLiveOrders").where("ts", ">=", now - 24 * 3600 * 1000).get()).docs.map((d) => d.data()), now) }; } catch (e) { ctx = {}; }
  }
  const priv = KALSHI_PUSH_VAPID_PRIVATE.value();
  const details = { subject: PUSH_SUBJECT, publicKey: push.publicKeyFromPrivate(priv), privateKey: priv };
  for (const kind of kinds) {
    const m = push.message(kind, doc, ctx);
    await push.sendAll({
      subs, payload: { title: m.title, body: m.body, tag: m.tag || tagBase },
      send: (subscription, body) => webpush.sendNotification(subscription, body, { vapidDetails: details, TTL: 3600, urgency: "high" }),
      remove: (id) => db.collection("kalshiPushSubs").doc(id).delete(),
    });
  }
}
exports.kalshiPushKey = onCall({ secrets: [KALSHI_PUSH_VAPID_PRIVATE] }, async (request) => {
  await assertKalshiAdmin(request.auth);
  return { key: push.publicKeyFromPrivate(KALSHI_PUSH_VAPID_PRIVATE.value()) };
});
exports.kalshiPushSubscribe = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  const sub = push.cleanSubscription(request.data && request.data.subscription);
  if (!sub) throw new HttpsError("invalid-argument", "That is not a push subscription.");
  const db = getFirestore();
  const have = await db.collection("kalshiPushSubs").get();
  if (have.size >= 10 && !have.docs.some((d) => d.id === push.subId(sub.endpoint))) throw new HttpsError("resource-exhausted", "Ten phones or browsers are already subscribed.");
  await db.collection("kalshiPushSubs").doc(push.subId(sub.endpoint)).set({ subscription: sub, at: Date.now() });
  return { ok: true, count: have.size + 1 };
});
exports.kalshiPushUnsubscribe = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  const endpoint = request.data && request.data.endpoint;
  if (typeof endpoint !== "string" || !endpoint) throw new HttpsError("invalid-argument", "No endpoint.");
  await getFirestore().collection("kalshiPushSubs").doc(push.subId(endpoint)).delete();
  return { ok: true };
});
exports.kalshiPushOrder = onDocumentWritten({ document: "kalshiLiveOrders/{id}", secrets: [KALSHI_PUSH_VAPID_PRIVATE], retry: false, memory: "256MiB" }, async (event) => {
  try {
    ensureDefaultAdminApp();
    const before = event.data && event.data.before && event.data.before.exists ? event.data.before.data() : null;
    const after = event.data && event.data.after && event.data.after.exists ? event.data.after.data() : null;
    if (!after) return;
    await pushSend(getFirestore(), push.orderKinds(before, after), after, event.params.id);
  } catch (e) { console.error("kalshiPushOrder: " + String((e && e.message) || e).slice(0, 200)); }
});
exports.kalshiPushSession = onDocumentWritten({ document: "kalshiLiveControl/session", secrets: [KALSHI_PUSH_VAPID_PRIVATE], retry: false, memory: "256MiB" }, async (event) => {
  try {
    ensureDefaultAdminApp();
    const before = event.data && event.data.before && event.data.before.exists ? event.data.before.data() : null;
    const after = event.data && event.data.after && event.data.after.exists ? event.data.after.data() : null;
    await pushSend(getFirestore(), push.sessionKinds(before, after), after, "session");
  } catch (e) { console.error("kalshiPushSession: " + String((e && e.message) || e).slice(0, 200)); }
});

// Records the real order book of the open Bitcoin and gold 15 minute markets about every 10 seconds
// (see kalshiBookLib.js). READ ONLY and keyless. It is the LAST export on purpose: the tests slice the file from
// here to prove nothing after this point can see the live key or place an order.
const BOOK_RECORDER_ON = false;
exports.kalshiBookRecorder = onSchedule(
  { schedule: "every 1 minutes", timeoutSeconds: 70, retryCount: 0, memory: "256MiB" },
  async () => {
    // Switched off on Oct 12, 2026 at the owner's request to cut the Firebase bill: it trades nothing and only fed research that has concluded. Remove this line to record again.
    if (!BOOK_RECORDER_ON) {
      // Switched off, it still tidies up (Oct 21, 2026 cost review): the only thing that ever deleted old snapshots was the recorder itself, so the ones written before Oct 12 were never removed and kept
      // billing as stored data. One small delete-only query a minute until they are gone (an empty result costs one read); it reads no market and places nothing.
      try {
        ensureDefaultAdminApp();
        const old = await getFirestore().collection("kalshiBookSnaps").where("ts", "<", Date.now() - 86400000).limit(200).get();
        if (!old.empty) await Promise.all(old.docs.map((d) => d.ref.delete()));
      } catch (e) { console.error("kalshiBookRecorder prune: " + String((e && e.message) || e).slice(0, 160)); }
      return;
    }
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
