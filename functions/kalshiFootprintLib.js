"use strict";
// Footprint (order flow) for the Bot page, from Kalshi's PUBLIC trade tape (the owner, Oct 26, 2026: "build the footprint view", read only).
// Every trade has a YES price, a size and the side the TAKER bought. In YES-price terms a taker buying YES lifts the ask (a buy) and a taker buying NO hits the bid (a sell).
// This file only reads and sums. It holds no key, signs nothing and places no order; the one callable that uses it (kalshiTape in index.js) is admin only and GET only.

const BAR_MS = 60000;
const WINDOW_MS = 45 * 60000;          // how far back one read goes; the page shows the last 20 or 40 minutes of it
const PAGE_LIMIT = 1000;
const MAX_PAGES = 6;                   // a 15 minute market trades a few thousand contracts at most; this bounds the cost of a busy one
const MAX_AGE_MS = 48 * 3600000;       // old enough to look at yesterday's windows, not the whole history

// A live bot market ticker, e.g. KXGOLD15M-26OCT261530-30. The series part must be one the bot trades; anything else is refused before a request is made.
function validTicker(ticker, allowedSeries) {
  const m = /^(KX[A-Z0-9]+)-\d{2}[A-Z]{3}\d{6}-[A-Z0-9.]+$/.exec(String(ticker || ""));
  return !!(m && Array.isArray(allowedSeries) && allowedSeries.includes(m[1]));
}

// The window to read, in milliseconds: it ends at `toMs` (the market's close, or now while it is open) and is clamped to the last 48 hours and not past a minute from now.
function readWindow(toMs, nowMs) {
  let to = Number(toMs);
  if (!Number.isFinite(to)) to = nowMs;
  to = Math.min(to, nowMs + 60000);
  to = Math.max(to, nowMs - MAX_AGE_MS);
  return { fromMs: to - WINDOW_MS, toMs: to };
}

// One trade of Kalshi's answer -> { ts (ms), price (YES cents), size, side (+1 buy, -1 sell) }, or null when it cannot be read. Both the dollar and the older cent fields are accepted.
function parseTrade(t) {
  if (!t) return null;
  const ts = Date.parse(t.created_time);
  const priceRaw = t.yes_price_dollars !== undefined && t.yes_price_dollars !== null ? Number(t.yes_price_dollars) * 100 : Number(t.yes_price);
  const size = Number(t.count_fp !== undefined && t.count_fp !== null ? t.count_fp : t.count);
  const taker = t.taker_outcome_side !== undefined ? t.taker_outcome_side : t.taker_side;
  const price = Math.round(priceRaw);
  if (!Number.isFinite(ts) || !Number.isFinite(price) || price < 1 || price > 99 || !Number.isFinite(size) || size <= 0) return null;
  if (taker !== "yes" && taker !== "no") return null;
  return { ts, price, size, side: taker === "yes" ? 1 : -1 };
}

// Trades -> one bar per minute, each with its price levels. A level is [price cents, sell volume, buy volume]. Bars carry their delta (buys minus sells), the running total of the delta from the
// first bar, and the point of control (the price with the most volume). Empty minutes inside the window are kept, so the page's columns line up with the clock.
function buildFootprint(trades, fromMs, toMs) {
  const start = Math.floor(fromMs / BAR_MS) * BAR_MS, end = Math.floor((toMs - 1) / BAR_MS) * BAR_MS;   // the minute that starts AT the end is not part of the window
  const byBar = new Map();
  (trades || []).forEach((raw) => {
    const t = raw && raw.price !== undefined && raw.side !== undefined ? raw : parseTrade(raw);
    if (!t || t.ts < start || t.ts >= end + BAR_MS) return;
    const k = Math.floor(t.ts / BAR_MS) * BAR_MS;
    const levels = byBar.get(k) || new Map();
    const lv = levels.get(t.price) || [0, 0];
    lv[t.side > 0 ? 1 : 0] += t.size;
    levels.set(t.price, lv);
    byBar.set(k, levels);
  });
  const bars = [];
  let cum = 0;
  for (let k = start; k <= end; k += BAR_MS) {
    const levels = byBar.get(k);
    let buy = 0, sell = 0, poc = null, pocVol = -1;
    const rows = [];
    if (levels) {
      [...levels.keys()].sort((a, b) => a - b).forEach((p) => {
        const [s, b] = levels.get(p);
        rows.push([p, s, b]);
        sell += s; buy += b;
        if (s + b > pocVol) { pocVol = s + b; poc = p; }
      });
    }
    cum += buy - sell;
    bars.push({ t: k / 1000, l: rows, buy, sell, delta: buy - sell, cum, poc });
  }
  return bars;
}

// The whole-series view (the owner, Oct 26, 2026: "30 minutes or 1 hour, since we work in 15 minute increments"): the last 30 or 60 minutes of ONE series, stitched across its consecutive 15 minute markets.
// Only a series the bot trades is accepted, and only those two spans; anything else becomes 30 minutes.
const SERIES_SPANS = [30, 60];
const MAX_SERIES_MARKETS = 6;          // one hour is four windows, plus the one that is open now and one of slack
const MAX_SERIES_TRADES = 8000;
function validSeries(series, allowedSeries) {
  return typeof series === "string" && /^KX[A-Z0-9]+$/.test(series) && Array.isArray(allowedSeries) && allowedSeries.includes(series);
}
function seriesWindow(spanMin, toMs, nowMs) {
  const span = SERIES_SPANS.includes(Number(spanMin)) ? Number(spanMin) : 30;
  const w = readWindow(toMs, nowMs);
  return { spanMin: span, fromMs: w.toMs - span * 60000, toMs: w.toMs };
}
// Kalshi's market list for the series -> the windows inside [fromMs, toMs]: [{ ticker, closeMs }] oldest first, only a market that closes after the window starts and was open before it ends (a market closes
// 15 minutes after it opens), only a valid ticker of this series, at most MAX_SERIES_MARKETS (the newest).
function windowsFromMarkets(markets, series, fromMs, toMs) {
  const out = [];
  (markets || []).forEach((m) => {
    const closeMs = Date.parse(m && m.close_time);
    const ticker = m && m.ticker;
    if (!Number.isFinite(closeMs) || typeof ticker !== "string" || !ticker.startsWith(series + "-") || !validTicker(ticker, [series])) return;
    if (closeMs <= fromMs || closeMs - 15 * 60000 >= toMs) return;
    out.push({ ticker, closeMs });
  });
  out.sort((a, b) => a.closeMs - b.closeMs);
  return out.slice(-MAX_SERIES_MARKETS);
}

module.exports = { BAR_MS, WINDOW_MS, PAGE_LIMIT, MAX_PAGES, MAX_AGE_MS, SERIES_SPANS, MAX_SERIES_MARKETS, MAX_SERIES_TRADES, validTicker, validSeries, readWindow, seriesWindow, windowsFromMarkets, parseTrade, buildFootprint };
