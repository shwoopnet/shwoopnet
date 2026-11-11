"use strict";
// The market tape: the few market figures this site is PERMITTED to read by machine, written to the one document shared/marketTape for the ticker strip and the Brief.
//
// KEYLESS. It holds no secret and no account credential, and it places no order.
//
// Why so little (Nov 11, 2026, the owner): this used to read Yahoo's chart endpoint and the public RSS feeds of CNBC, MarketWatch, WSJ, CoinDesk and Cointelegraph, plus CNN's fear and greed
// page. Yahoo's terms forbid automated access, and nobody had read the others' terms, so all of it was removed. What is left is what docs/MARKET_TAPE_SOURCES.md found permitted:
//   - Treasury daily par yield curve (10 and 30 year), the close of each trading day, no key.
//   - alternative.me crypto fear and greed (commercial use allowed with the attribution shown next to the data), no key.
// Everything else is written as `noPrice: true`, and the page says "No price". An honest gap is better than a number from a source we may not use.
//
// HOW TO ADD A PERMITTED SOURCE LATER (for example Bitcoin and Ethereum once the owner has read the exchange's market data terms): add a reader to READERS below (one pinned https host,
// added to ALLOWED_HOSTS), then set that symbol's `source` in SYMBOLS to the reader's name. A symbol whose `source` is null is never read and renders "No price". Nothing else changes, and
// test/noYahooMarketTapeGates.test.js fails until the host is added to its exact allowlist on purpose.

// `tape: true` shows in the strip. `source` is the ONE permitted reader for the symbol, or null when we have none.
const SYMBOLS = [
  { sym: "^GSPC", name: "S&P 500", kind: "index", tape: true, source: null },
  { sym: "^NDX", name: "Nasdaq 100", kind: "index", tape: true, source: null },
  { sym: "^DJI", name: "Dow", kind: "index", tape: true, source: null },
  { sym: "^RUT", name: "Russell 2000", kind: "index", tape: true, source: null },
  { sym: "UST10Y", name: "10Y yield", kind: "yield", tape: true, source: "treasury" },
  { sym: "UST30Y", name: "30Y yield", kind: "yield", tape: true, source: "treasury" },
  { sym: "^VIX", name: "VIX", kind: "index", tape: true, source: null },
  { sym: "GC=F", name: "Gold", kind: "future", tape: true, source: null },
  { sym: "BTC-USD", name: "Bitcoin", kind: "crypto", tape: true, source: null },
  { sym: "ETH-USD", name: "Ethereum", kind: "crypto", tape: false, source: null },
  { sym: "CL=F", name: "Crude oil", kind: "future", tape: false, source: null },
  { sym: "SPY", name: "S&P 500 (SPY)", kind: "etf", tape: false, source: null },
  { sym: "QQQ", name: "Nasdaq 100 (QQQ)", kind: "etf", tape: false, source: null },
  { sym: "DIA", name: "Dow (DIA)", kind: "etf", tape: false, source: null },
];

// The exact hosts this file may contact. A test pins this list; adding a source means adding its host here and there on purpose.
const TREASURY_HOST = "home.treasury.gov";
const FG_HOST = "api.alternative.me";
const ALLOWED_HOSTS = [TREASURY_HOST, FG_HOST];

// Treasury's daily par yield curve as an XML (OData) feed, one month per read. Confirmed to answer on Nov 11, 2026 (docs/MARKET_TAPE_SOURCES.md, "Nov 11 confirmation"); the elements are NEW_DATE,
// BC_10YEAR and BC_30YEAR. The terms page read states no ban on automated reads and no explicit grant either (see that doc), so this is the one source to re-check first if anything changes.
const treasuryUrl = (yyyymm) => "https://" + TREASURY_HOST + "/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=" + yyyymm;
const FG_CRYPTO_URL = "https://" + FG_HOST + "/fng/?limit=2";
const FETCH_TIMEOUT_MS = 8000;
// A generic client name: no personal contact detail in a request header.
const UA = "shwoopnet-market-tape";

const num = (v) => { const x = Number(v); return v !== null && v !== undefined && v !== "" && Number.isFinite(x) ? x : null; };

// Treasury XML to the rows it holds, oldest first: [{ date: "YYYY-MM-DD", y10, y30 }]. A row with no date or no 10 year yield is dropped, a missing 30 year is null.
// Nothing in the feed is kept except these three numbers and a date string of a fixed shape.
function parseTreasuryXml(xml) {
  const out = [];
  const re = /<m:properties>([\s\S]*?)<\/m:properties>/gi;
  const field = (b, tag) => { const m = new RegExp("<d:" + tag + "[^>]*>([^<]*)</d:" + tag + ">", "i").exec(b); return m ? m[1].trim() : ""; };
  let m;
  while ((m = re.exec(String(xml || "")))) {
    const d = /^(\d{4}-\d{2}-\d{2})T/.exec(field(m[1], "NEW_DATE"));
    const y10 = num(field(m[1], "BC_10YEAR")), y30 = num(field(m[1], "BC_30YEAR"));
    if (!d || y10 === null || y10 <= 0 || y10 > 25) continue;
    out.push({ date: d[1], y10, y30: y30 !== null && y30 > 0 && y30 <= 25 ? y30 : null });
  }
  return out.sort((a, b) => (a.date < b.date ? -1 : 1));
}

// Rows to the two yield quotes. A quote needs a latest AND a previous close (the move is the whole point of showing it), so one row is no quote. `daily` and `closeDate` let the page say
// "close of <date>" instead of passing a once a day figure off as live.
function treasuryQuotes(rows, nowMs) {
  const make = (key) => {
    const r = rows.filter((x) => x[key] !== null);
    if (r.length < 2) return null;
    const last = r[r.length - 1], prev = r[r.length - 2];
    return { price: last[key], prevClose: prev[key], asOf: Date.parse(last.date + "T00:00:00Z") || nowMs, source: "treasury", daily: true, closeDate: last.date };
  };
  const q = {}, a = make("y10"), b = make("y30");
  if (a) q.UST10Y = a;
  if (b) q.UST30Y = b;
  return q;
}

// A fear and greed reading to {score 0 to 100, rating, prev}. Only a finite score inside 0 to 100 counts; the rating is cut to a short plain string. null when the answer has no usable score.
const fgNum = (v) => { const x = num(v); return x !== null && x >= 0 && x <= 100 ? Math.round(x * 10) / 10 : null; };
const fgText = (v) => String(v || "").replace(/[^A-Za-z ]/g, "").trim().toLowerCase().slice(0, 24);
function parseFearGreedCrypto(json) {
  const d = json && typeof json === "object" && Array.isArray(json.data) ? json.data : [];
  const score = fgNum(d[0] && d[0].value);
  if (score === null) return null;
  return { score, rating: fgText(d[0].value_classification), prev: fgNum(d[1] && d[1].value) };
}

// https only, no redirect followed (a redirect would send the read to a host this file has not pinned), a timeout, and a host that must be on the allowlist.
async function getText(fetchFn, url) {
  const u = new URL(url);
  if (u.protocol !== "https:" || !ALLOWED_HOSTS.includes(u.hostname)) throw new Error("host not allowed");
  const ctl = typeof AbortController === "function" ? new AbortController() : null;
  const timer = ctl ? setTimeout(() => ctl.abort(), FETCH_TIMEOUT_MS) : null;
  try {
    const res = await fetchFn(url, { headers: { "user-agent": UA, accept: "*/*" }, redirect: "manual", signal: ctl ? ctl.signal : undefined });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.text();
  } finally {
    if (timer) clearTimeout(timer);
  }
}

const ym = (d) => d.getUTCFullYear() + String(d.getUTCMonth() + 1).padStart(2, "0");

// One reader per permitted source. Each returns { quotes } and throws on failure; readTape catches per reader, so one failing source never aborts the others.
const READERS = {
  treasury: async ({ fetchFn, nowMs }) => {
    const now = new Date(nowMs);
    let rows = parseTreasuryXml(await getText(fetchFn, treasuryUrl(ym(now))));
    // Early in a month there may be one row or none: add the month before so there is a previous close to measure the move from.
    if (rows.length < 2) {
      const prevMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1));
      rows = parseTreasuryXml(await getText(fetchFn, treasuryUrl(ym(prevMonth)))).concat(rows);
    }
    const quotes = treasuryQuotes(rows, nowMs);
    if (!Object.keys(quotes).length) throw new Error("no usable yield");
    return { quotes };
  },
};

// Returns only what was read. `quotes` holds the symbols that answered with a price, `noPrice` names the symbols that have no permitted source, `mood` is null when the crypto reading failed,
// `errors` names what failed. The caller merges, so a source that fails keeps its older quote with its own asOf.
async function readTape({ fetchFn, now }) {
  const nowMs = typeof now === "number" ? now : Date.now();
  const quotes = {}, errors = [];
  const names = Array.from(new Set(SYMBOLS.map((s) => s.source).filter(Boolean)));
  await Promise.all(names.map(async (name) => {
    try {
      const r = await READERS[name]({ fetchFn, nowMs });
      // Only symbols that are listed with this source may be written from it.
      Object.keys(r.quotes).forEach((sym) => { if (SYMBOLS.some((s) => s.sym === sym && s.source === name)) quotes[sym] = r.quotes[sym]; });
    } catch (e) { errors.push(name + ": " + String((e && e.message) || e).slice(0, 80)); }
  }));
  const noPrice = SYMBOLS.filter((s) => !s.source).map((s) => s.sym);
  const mood = {};
  try {
    const v = parseFearGreedCrypto(JSON.parse(await getText(fetchFn, FG_CRYPTO_URL)));
    if (v) mood.crypto = Object.assign(v, { asOf: nowMs, source: "alternative.me" }); else throw new Error("no usable score");
  } catch (e) { errors.push("fear and greed crypto: " + String((e && e.message) || e).slice(0, 80)); }
  return { quotes, noPrice, mood: Object.keys(mood).length ? mood : null, errors };
}

// The document to store: a whole replacement, not a merge, so nothing a removed source once wrote (Yahoo prices, headlines, CNN's reading) can linger beside the new fields. A symbol whose source
// answered is replaced; a symbol whose source FAILED keeps its older quote with its own asOf, but only if that quote came from the same permitted source (an old Yahoo quote has no `source` and is
// dropped); a symbol with no source is written as `noPrice` and never carries a number.
function buildTapeDoc(prev, r, nowMs) {
  const old = prev && typeof prev === "object" && prev.quotes && typeof prev.quotes === "object" ? prev.quotes : {};
  const quotes = {};
  SYMBOLS.forEach((s) => {
    if (!s.source) { quotes[s.sym] = { noPrice: true, source: null, asOf: nowMs }; return; }
    if (r.quotes[s.sym]) { quotes[s.sym] = r.quotes[s.sym]; return; }
    const o = old[s.sym];
    if (o && o.source === s.source && Number(o.price) > 0 && Number(o.prevClose) > 0) quotes[s.sym] = o;
  });
  const doc = { updatedAt: nowMs, errors: r.errors, quotes };
  const oldMood = prev && prev.mood && prev.mood.crypto && prev.mood.crypto.source === "alternative.me" ? prev.mood.crypto : null;
  const crypto = r.mood && r.mood.crypto ? r.mood.crypto : oldMood;
  if (crypto) doc.mood = { crypto };
  return doc;
}

module.exports = { buildTapeDoc, SYMBOLS, ALLOWED_HOSTS, READERS, parseTreasuryXml, treasuryQuotes, treasuryUrl, parseFearGreedCrypto, readTape, getText };
