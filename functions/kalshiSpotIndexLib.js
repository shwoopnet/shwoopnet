"use strict";
// The spot index reader for the CFRTIBTC probe (Nov 12, 2026, the Probe Engineering Desk; docs/probes/PROBE_SPEC_CFRTIBTC.md). INERT until a reviewed edit flips
// the probe's own switch in the second strategy's registry: nothing calls modelForMarket unless a registered strategy has a modelEdgeMin entry, and none does while the switch is off.
//
// What it does: rebuilds a three-venue Bitcoin spot index from PUBLIC trade lists (no key, no account, no auth header) and turns it into a model chance that a Kalshi
// 15 minute market settles YES, the research rule of kalshi-scalper/workers/CFRTI1_PROTOCOL.md (research branch). It decides nothing and sends nothing: the slot engine
// compares the chance with the quoted price and its one entry gate does the rest.
//
// What it will not do, by construction (each is a test in test/cfrtiProbeGates.test.js):
//   - reach any host but the three below, follow a redirect, send a header that could carry a credential, or read more than a fixed number of pages and bytes;
//   - guess: a venue that cannot be read back over the whole look-back span, a strike it does not understand, too few index changes, or a zero volatility is NO reading
//     (null), and no reading is no order;
//   - throw or hang: every failure is null and every request has its own abort timer (AbortSignal.timeout, as the book snapshot uses, so this file holds no timer of its own).
//
// UNVERIFIED AT THE TIME OF WRITING (the security review and a person must confirm before the switch is flipped): the three venues' response shapes below are written
// from their public documentation as remembered, not from a live read (this desk made no request to them), and their market data terms for commercial use have not been
// read by a person. A shape this code does not recognise is null, so a wrong assumption fails closed.

const SPOT_HOSTS = Object.freeze(["api.exchange.coinbase.com", "api.kraken.com", "www.bitstamp.net"]);
const SPOT_TIMEOUT_MS = 1500;                 // per request
const SPOT_TOTAL_MS = 5000;                   // all three venues together: past this every request still in flight is aborted and the reading is null
const SPOT_MAX_BYTES = 3 * 1024 * 1024;       // per response; a longer body is no reading
const SPOT_MAX_PAGES = Object.freeze({ coinbase: 6, kraken: 3, bitstamp: 1 });
const LOOKBACK_MS = 600 * 1000;               // the research rule: 60 ten-second index changes
const STEP_MS = 10 * 1000;
const FRESH_MS = 10 * 1000;                   // a venue counts at an instant only if it traded in the 10 s before it
const MIN_CHANGES = 30;                       // the research code needs at least 30 of the 60 changes
const AVG_SEC = 60;                           // the settlement value is a 60 s average
const VENUES_REQUIRED = 3;                    // the research held-out read refuses a run with fewer than three venues; so does this
const MODEL_SERIES = Object.freeze({ KXBTC15M: "BTC" });   // Bitcoin only: the pooled five-asset rule failed its bar and only the Bitcoin cell is a lead
const isNum = (x) => typeof x === "number" && Number.isFinite(x);

// One public GET. Returns { json, headers } or null. Never throws.
async function spotGet(fetchFn, url, overall) {
  try {
    const u = new URL(url);
    if (u.protocol !== "https:" || !SPOT_HOSTS.includes(u.hostname) || u.username || u.password) return null;
    const res = await fetchFn(u.toString(), { method: "GET", redirect: "error", headers: { accept: "application/json", "user-agent": "spot-index-reader" }, signal: overall ? AbortSignal.any([overall, AbortSignal.timeout(SPOT_TIMEOUT_MS)]) : AbortSignal.timeout(SPOT_TIMEOUT_MS) });
    if (!res || res.status !== 200) return null;
    const text = await res.text();
    if (typeof text !== "string" || text.length > SPOT_MAX_BYTES) return null;
    return { json: JSON.parse(text), headers: res.headers };
  } catch (e) { return null; }
}

// Each venue reader returns { trades: [{ t (ms), p }], complete } or null. `complete` is true only when the pages read reach back to `fromMs` or earlier (or the venue's
// list simply ended), so the caller knows the whole span is covered. Trades after `toMs` are dropped: the model may not see the future of its own look.
function tidy(rows, fromMs, toMs) {
  const out = [];
  for (const r of rows) if (r && isNum(r.t) && isNum(r.p) && r.p > 0 && r.t <= toMs && r.t >= fromMs - FRESH_MS) out.push({ t: r.t, p: r.p });
  out.sort((a, b) => a.t - b.t);
  return out;
}
async function coinbaseTrades(fetchFn, fromMs, toMs, overall) {
  const rows = [];
  let after = "", oldest = Infinity;
  for (let page = 0; page < SPOT_MAX_PAGES.coinbase; page++) {
    const r = await spotGet(fetchFn, "https://api.exchange.coinbase.com/products/BTC-USD/trades?limit=1000" + (after ? "&after=" + encodeURIComponent(after) : ""), overall);
    if (!r || !Array.isArray(r.json)) return null;
    if (!r.json.length) return { trades: tidy(rows, fromMs, toMs), complete: true };
    let minId = Infinity;
    for (const x of r.json) {
      const t = Date.parse(x && x.time), p = Number(x && x.price), id = Number(x && x.trade_id);
      if (!Number.isFinite(t) || !Number.isFinite(p) || !Number.isInteger(id)) return null;
      rows.push({ t, p }); oldest = Math.min(oldest, t); minId = Math.min(minId, id);
    }
    if (oldest <= fromMs - FRESH_MS) return { trades: tidy(rows, fromMs, toMs), complete: true };
    after = String(minId);                    // the next page is the trades older than the oldest one read
  }
  return { trades: tidy(rows, fromMs, toMs), complete: false };
}
async function krakenTrades(fetchFn, fromMs, toMs, overall) {
  const rows = [];
  let since = String(Math.floor((fromMs - FRESH_MS) / 1000));
  for (let page = 0; page < SPOT_MAX_PAGES.kraken; page++) {
    const r = await spotGet(fetchFn, "https://api.kraken.com/0/public/Trades?pair=XBTUSD&since=" + encodeURIComponent(since));
    const res = r && r.json && Array.isArray(r.json.error) && r.json.error.length === 0 && r.json.result && typeof r.json.result === "object" ? r.json.result : null;
    if (!res) return null;
    const key = Object.keys(res).find((k) => k !== "last" && Array.isArray(res[k]));
    if (!key) return null;
    for (const x of res[key]) {
      const p = Number(Array.isArray(x) ? x[0] : NaN), t = Number(Array.isArray(x) ? x[2] : NaN) * 1000;
      if (!Number.isFinite(p) || !Number.isFinite(t)) return null;
      rows.push({ t, p });
    }
    if (res[key].length < 1000) return { trades: tidy(rows, fromMs, toMs), complete: true };   // the list ended: everything since `since` was read
    if (typeof res.last !== "string" && typeof res.last !== "number") return null;
    since = String(res.last);
  }
  return { trades: tidy(rows, fromMs, toMs), complete: false };
}
async function bitstampTrades(fetchFn, fromMs, toMs, overall) {
  const r = await spotGet(fetchFn, "https://www.bitstamp.net/api/v2/transactions/btcusd/?time=hour", overall);
  if (!r || !Array.isArray(r.json)) return null;
  const rows = [];
  for (const x of r.json) {
    const t = Number(x && x.date) * 1000, p = Number(x && x.price);
    if (!Number.isFinite(t) || !Number.isFinite(p)) return null;
    rows.push({ t, p });
  }
  return { trades: tidy(rows, fromMs, toMs), complete: true };   // the venue's last hour, which always covers the ten minute span
}
const VENUE_READERS = Object.freeze({ coinbase: coinbaseTrades, kraken: krakenTrades, bitstamp: bitstampTrades });

// ---- The model (pure). `venues` is { name: [{ t, p }] sorted by t }. ---------------------------------------------------------------------------------
// The index at an instant: the mean, over the venues that traded in the 10 s before it, of each venue's last price. No such venue: null.
function indexAt(venues, t) {
  let sum = 0, n = 0;
  for (const name of Object.keys(venues || {})) {
    const L = venues[name];
    if (!Array.isArray(L)) continue;
    let lo = 0, hi = L.length - 1, at = -1;
    while (lo <= hi) { const mid = (lo + hi) >> 1; if (L[mid].t <= t) { at = mid; lo = mid + 1; } else hi = mid - 1; }
    if (at >= 0 && t - L[at].t <= FRESH_MS) { sum += L[at].p; n += 1; }
  }
  return n > 0 ? sum / n : null;
}
// Sample standard deviation of the ten-second log changes of the index over the ten minutes before `t`. Fewer than MIN_CHANGES usable changes, or no movement: null.
function sigma10(venues, t) {
  const xs = [];
  for (let j = 0; j <= LOOKBACK_MS / STEP_MS; j++) xs.push(indexAt(venues, t - STEP_MS * j));
  const lr = [];
  for (let j = 0; j < xs.length - 1; j++) if (xs[j] && xs[j + 1]) lr.push(Math.log(xs[j] / xs[j + 1]));
  if (lr.length < MIN_CHANGES) return null;
  const m = lr.reduce((a, v) => a + v, 0) / lr.length;
  const sd = Math.sqrt(lr.reduce((a, v) => a + (v - m) * (v - m), 0) / (lr.length - 1));
  return sd > 0 && Number.isFinite(sd) ? sd : null;
}
// The variance the settlement average still has to live through, in ten-second steps: the time until the 60 s average starts plus a third of the average itself.
// At the research look (120 s left) this is 8, the research code's sqrt(8). The bot looks about a minute earlier (the slot cannot enter under 120 s), so it is larger.
function horizonSteps(secondsLeft) {
  if (!isNum(secondsLeft) || secondsLeft < AVG_SEC) return null;
  return (secondsLeft - AVG_SEC + AVG_SEC / 3) / (STEP_MS / 1000);
}
// Standard normal distribution function (Abramowitz and Stegun 7.1.26 on erf; absolute error under 1.5e-7, far below a cent).
function phi(z) {
  if (!isNum(z)) return NaN;
  const x = Math.abs(z) / Math.SQRT2, t = 1 / (1 + 0.3275911 * x);
  const erf = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return z >= 0 ? 0.5 * (1 + erf) : 0.5 * (1 - erf);
}
// The model chance of YES for a market that settles YES when the average is at or above `strike`. Anything unusable is null.
function modelYes({ venues, t, strike, secondsLeft }) {
  if (!isNum(strike) || !(strike > 0) || !isNum(t)) return null;
  const p0 = indexAt(venues, t), sd = sigma10(venues, t), h = horizonSteps(secondsLeft);
  if (!p0 || sd === null || h === null) return null;
  const pYes = phi(Math.log(p0 / strike) / (sd * Math.sqrt(h)));
  return Number.isFinite(pYes) ? { pYes, index: p0, sigma: sd, steps: h } : null;
}

// ---- The one entry point the slot engine is handed. Returns { pSide, pYes, index, sigma, venues } or null. Never throws. ---------------------------------
// args: { fetchFn, series, market (Kalshi's market object, already read by the engine), side ("yes" | "no"), now (ms, the look) }
async function modelForMarket(args) {
  try {
    const a = args || {};
    if (!Object.prototype.hasOwnProperty.call(MODEL_SERIES, a.series) || (a.side !== "yes" && a.side !== "no") || !isNum(a.now) || typeof a.fetchFn !== "function") return null;
    const m = a.market || {};
    // Only the plain "at or above the strike" market is understood. Any other strike type, or a missing strike, is no reading.
    const strike = Number(m.floor_strike);
    if (!["greater", "greater_or_equal"].includes(String(m.strike_type)) || !(strike > 0) || !Number.isFinite(strike)) return null;
    const closeMs = Date.parse(m.close_time), secondsLeft = (closeMs - a.now) / 1000;
    if (!Number.isFinite(secondsLeft)) return null;
    const fromMs = a.now - LOOKBACK_MS;
    const names = Object.keys(VENUE_READERS);
    const overall = AbortSignal.timeout(SPOT_TOTAL_MS);
    const got = await Promise.all(names.map((n) => VENUE_READERS[n](a.fetchFn, fromMs, a.now, overall).catch(() => null)));
    const venues = {};
    let ok = 0;
    names.forEach((n, i) => { const g = got[i]; if (g && g.complete === true && Array.isArray(g.trades) && g.trades.length) { venues[n] = g.trades; ok += 1; } });
    if (ok < VENUES_REQUIRED) return null;
    const r = modelYes({ venues, t: a.now, strike, secondsLeft });
    if (!r) return null;
    return { pSide: a.side === "yes" ? r.pYes : 1 - r.pYes, pYes: r.pYes, index: r.index, sigma: r.sigma, steps: r.steps, venues: ok, strike };
  } catch (e) { return null; }
}

module.exports = {
  modelForMarket, modelYes, indexAt, sigma10, horizonSteps, phi, spotGet,
  SPOT_HOSTS, SPOT_TIMEOUT_MS, SPOT_TOTAL_MS, SPOT_MAX_BYTES, SPOT_MAX_PAGES, LOOKBACK_MS, STEP_MS, FRESH_MS, MIN_CHANGES, VENUES_REQUIRED, MODEL_SERIES,
  _testOnly: Object.freeze({ coinbaseTrades, krakenTrades, bitstampTrades }),
};
