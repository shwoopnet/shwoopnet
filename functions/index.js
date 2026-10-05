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
const { initializeApp, getApps } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");
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
    if (!getApps().length) initializeApp();
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
