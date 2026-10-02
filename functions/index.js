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

// ---- Kalshi read-only relay ------------------------------------------------
// Kalshi's API answers 403 to any request carrying a browser Origin header and
// sends no CORS headers, so the page cannot call it directly. This relays the
// public order-book fields the Kalshi page needs.
//
// Deliberately narrow: two fixed series, GET only, no caller-supplied path or
// query, and no Kalshi credentials anywhere. It cannot place or cancel an order
// and must not be widened into something that can without a separate review.
const KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2";
const KALSHI_SERIES = ["KXBTC15M", "KXGOLD15M"];
const KALSHI_CACHE_MS = 2000;
let kalshiCache = { at: 0, body: null };

function kalshiNum(x) {
  const n = parseFloat(x);
  return Number.isFinite(n) ? n : null;
}

exports.kalshiBooks = onCall(async (request) => {
  assertSignedIn(request.auth);
  // Many tabs polling at once must not multiply into Kalshi rate limits.
  if (kalshiCache.body && Date.now() - kalshiCache.at < KALSHI_CACHE_MS) {
    return kalshiCache.body;
  }
  const markets = [];
  for (const series of KALSHI_SERIES) {
    const url = KALSHI_BASE + "/markets?series_ticker=" + series + "&status=open&limit=5";
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) {
      throw new HttpsError("unavailable", "Kalshi " + series + " HTTP " + res.status);
    }
    const data = await res.json();
    (data.markets || []).forEach((m) => {
      markets.push({
        series,
        ticker: m.ticker,
        closeTime: m.close_time,
        strike: m.floor_strike == null ? null : m.floor_strike,
        yesBid: kalshiNum(m.yes_bid_dollars),
        yesBidSz: kalshiNum(m.yes_bid_size_fp),
        yesAsk: kalshiNum(m.yes_ask_dollars),
        yesAskSz: kalshiNum(m.yes_ask_size_fp),
        last: kalshiNum(m.last_price_dollars),
      });
    });
  }
  const body = { fetchedAt: Date.now(), markets };
  kalshiCache = { at: Date.now(), body };
  return body;
});
