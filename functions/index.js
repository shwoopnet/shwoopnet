const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");

// Set once via: firebase functions:secrets:set FINNHUB_API_KEY
// Never committed -- this is the only place the real key lives now.
const FINNHUB_API_KEY = defineSecret("FINNHUB_API_KEY");

// Matches SHWOOP_OWNER_EMAIL in index.html -- this app is single-owner,
// so every callable rejects anyone else's token the same way the
// frontend's own auth gate does, rather than trusting the client to be
// the only thing enforcing that.
const OWNER_EMAIL = "heiszcam@gmail.com";

function assertOwner(auth) {
  if (!auth || auth.token.email !== OWNER_EMAIL) {
    throw new HttpsError("permission-denied", "This app is private.");
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
  assertOwner(request.auth);
  const symbol = request.data && request.data.symbol;
  if (!symbol || typeof symbol !== "string") {
    throw new HttpsError("invalid-argument", "symbol is required");
  }
  return finnhubGet("quote", { symbol });
});

exports.finnhubNews = onCall({ secrets: [FINNHUB_API_KEY] }, async (request) => {
  assertOwner(request.auth);
  return finnhubGet("news", { category: "general" });
});

exports.finnhubEarningsCalendar = onCall({ secrets: [FINNHUB_API_KEY] }, async (request) => {
  assertOwner(request.auth);
  const { from, to } = request.data || {};
  if (!from || !to) {
    throw new HttpsError("invalid-argument", "from and to (YYYY-MM-DD) are required");
  }
  return finnhubGet("calendar/earnings", { from, to });
});

exports.finnhubCompanyNews = onCall({ secrets: [FINNHUB_API_KEY] }, async (request) => {
  assertOwner(request.auth);
  const { symbol, from, to } = request.data || {};
  if (!symbol || !from || !to) {
    throw new HttpsError("invalid-argument", "symbol, from, and to are required");
  }
  return finnhubGet("company-news", { symbol, from, to });
});
