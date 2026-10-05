const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");

// Set once via: firebase functions:secrets:set FINNHUB_API_KEY
// Never committed -- this is the only place the real key lives now.
const FINNHUB_API_KEY = defineSecret("FINNHUB_API_KEY");

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
const { onSchedule } = require("firebase-functions/v2/scheduler");
const { initializeApp, getApps } = require("firebase-admin/app");
const { getFirestore, Timestamp } = require("firebase-admin/firestore");
const kalshi = require("./kalshiLib");

const KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2";
const KALSHI_CACHE_MS = 2000;
let kalshiCache = { at: 0, body: null };

// The Kalshi page is for the owner only. Two independent checks, both required:
// the token's email, and the isAdmin flag on the user document that
// firestore.rules already treats as the single source of truth for admin. The
// email alone would not follow a change of admin account; the flag alone would
// let a second admin in by accident. The page hides itself for anyone else, but
// hiding is not the control, this is.
const KALSHI_OWNER_EMAIL = "heiszcam@gmail.com";
async function assertKalshiAdmin(auth) {
  assertSignedIn(auth);
  if (!auth.token || auth.token.email !== KALSHI_OWNER_EMAIL) {
    throw new HttpsError("permission-denied", "Not available for this account.");
  }
  if (!getApps().length) initializeApp();
  const snap = await getFirestore().collection("users").doc(auth.uid).get();
  if (!snap.exists || snap.data().isAdmin !== true) {
    throw new HttpsError("permission-denied", "Not available for this account.");
  }
}

async function kalshiFetchSeries(series, status, limit) {
  const url = KALSHI_BASE + "/markets?series_ticker=" + series + "&status=" + status + "&limit=" + limit;
  const res = await fetch(url, {
    signal: AbortSignal.timeout(8000),
    headers: { "User-Agent": "shwoopnet-monitor/1.0 (read-only market data)", "Accept": "application/json" },
  });
  if (!res.ok) {
    // A refusal from Kalshi's CDN says very little, so keep what it does say.
    // Without this a 403 reads as a bug in our code when it may be the network
    // path (some CDNs refuse cloud-provider address ranges), and the two need
    // different fixes.
    const body = (await res.text().catch(() => "")).slice(0, 200);
    const cdn = res.headers.get("x-cache") || res.headers.get("server") || "";
    console.error("Kalshi " + series + " HTTP " + res.status + " cdn=" + cdn + " body=" + body);
    throw new HttpsError("unavailable", "Kalshi " + series + " HTTP " + res.status +
      (cdn ? " (" + cdn + ")" : "") + (body ? ": " + body : ""));
  }
  const data = await res.json();
  return data.markets || [];
}

exports.kalshiBooks = onCall(async (request) => {
  await assertKalshiAdmin(request.auth);
  // Many tabs polling at once must not multiply into Kalshi rate limits.
  if (kalshiCache.body && Date.now() - kalshiCache.at < KALSHI_CACHE_MS) {
    return kalshiCache.body;
  }
  const markets = [];
  for (const series of kalshi.KALSHI_SERIES) {
    const raw = await kalshiFetchSeries(series, "open", 5);
    raw.forEach((m) => markets.push(kalshi.trimMarket(series, m)));
  }
  const body = { fetchedAt: Date.now(), markets };
  kalshiCache = { at: Date.now(), body };
  return body;
});

// Background recorder: one top-of-book snapshot per open market per minute,
// plus settled results, into Firestore. The collections have no rule that
// allows a client, so only the Admin SDK (this function) can touch them.
// Cloud Scheduler's floor is one minute, so this is market-level data, not the
// second-by-second book a real scalp study needs.
//
// Retention: docs carry expireAt; enable a TTL policy on it once, see DEPLOY.md.
exports.kalshiRecorder = onSchedule(
  { schedule: "every 1 minutes", timeoutSeconds: 55, retryCount: 0 },
  async () => {
    if (!getApps().length) initializeApp();
    const db = getFirestore();
    const now = Date.now();
    const failures = [];
    const batch = db.batch();
    let writes = 0;

    for (const series of kalshi.KALSHI_SERIES) {
      try {
        const raw = await kalshiFetchSeries(series, "open", 5);
        raw.forEach((m) => {
          const doc = kalshi.snapshotDoc(kalshi.trimMarket(series, m), now);
          const ref = db.collection("kalshiSnapshots").doc(kalshi.snapshotId(doc.ticker, now));
          // set() on a deterministic id, never add(): a second invocation for
          // the same minute overwrites the same document instead of doubling it.
          batch.set(ref, Object.assign({}, doc, { expireAt: Timestamp.fromMillis(doc.expireAtMs) }));
          writes++;
        });
      } catch (e) {
        failures.push(series + ": " + e.message);
      }
    }

    // Settled results are checked every 5th minute and written only when new,
    // which keeps the write count (and the free-tier headroom) down.
    if (new Date(now).getUTCMinutes() % 5 === 0) {
      for (const series of kalshi.KALSHI_SERIES) {
        try {
          const settled = (await kalshiFetchSeries(series, "settled", 3)).filter((m) => m.result);
          if (!settled.length) continue;
          const refs = settled.map((m) => db.collection("kalshiResults").doc(m.ticker));
          const have = await db.getAll(...refs);
          settled.forEach((m, i) => {
            if (have[i].exists) return;
            batch.set(refs[i], { series, ticker: m.ticker, result: m.result, closeTime: m.close_time, strike: m.floor_strike == null ? null : m.floor_strike, recordedAt: now });
            writes++;
          });
        } catch (e) {
          failures.push(series + " results: " + e.message);
        }
      }
    }

    if (writes) await batch.commit();
    console.log("kalshiRecorder wrote " + writes + " docs" + (failures.length ? "; failures: " + failures.join(" | ") : ""));
    // A partial failure still committed what it could; throw so the run is
    // visible as failed rather than silently thinner than it should be.
    if (failures.length) throw new Error(failures.join(" | "));
  }
);
