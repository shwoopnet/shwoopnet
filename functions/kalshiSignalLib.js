"use strict";
// The strategy's entry signal and its cost model. No Firebase, no network, so the repo's plain-node tests can run it.
// This is H2's entry rule (about 40c or 50c, YES tried before NO), used by the live test and the armed scan to pick
// what to buy. It holds no order code and no position keeping: there is no simulated trading anywhere in this repo.

const BANDS = { "40c": [0.38, 0.42], "50c": [0.48, 0.52] };
const MIN_LEFT_S = 300;
const FEE_RATE = 0.07;
// One copy of the series list and the dollar-string parsing, shared with the relay.
const { KALSHI_SERIES: SERIES, kalshiNum: num } = require("./kalshiLib");

// The NO side of a YES quote is 1 - x, and in floating point 1 - 0.58 is
// 0.42000000000000004, which is above the 0.42 band edge. Compared raw, a NO entry at
// exactly 42c was skipped while the same price on the YES side was taken. Every derived
// price is snapped to 4 places (sub-cent safe) before it meets a band or the target.
const round4 = (x) => Math.round(x * 10000) / 10000;
const noSide = (yesPrice) => round4(1 - yesPrice);

// Rounded UP to a cent per order, as Kalshi does.
function takerFee(price, contracts) {
  if (!(price > 0 && price < 1) || !(contracts > 0)) return 0;
  return Math.ceil(Number((FEE_RATE * contracts * price * (1 - price) * 100).toFixed(9))) / 100;
}

// A real two sided book. A just opened market shows bid 0.1c and ask $1.00 (empty).
function validQuote(bid, ask) {
  return bid != null && ask != null && bid >= 0.001 && ask <= 0.999 && ask >= bid && ask - bid <= 0.10;
}

// Most contracts whose cost INCLUDING the fee fits the cap and that the touch can fill.
function sizeFor(price, cap, displayed) {
  if (!(price > 0 && price < 1) || !(cap > 0)) return 0;
  let n = Math.floor(cap / price);
  while (n >= 1 && price * n + takerFee(price, n) > cap + 1e-9) n--;
  if (displayed != null) n = Math.min(n, Math.floor(displayed));
  return Math.max(n, 0);
}

function parseMarket(m) {
  return {
    ticker: m.ticker, status: m.status, closeMs: Date.parse(m.close_time),
    bid: num(m.yes_bid_dollars), ask: num(m.yes_ask_dollars),
    bidSz: num(m.yes_bid_size_fp), askSz: num(m.yes_ask_size_fp),
  };
}

// Entries the strategy wants now (H2: about 40c or 50c, YES tried before NO), at most one
// per market. The caller turns each into a position; whether it already exists is decided
// atomically by the store, not here.
function planEntries(quotes, nowMs, cap) {
  const out = [];
  for (const { series, m } of quotes) {
    const q = parseMarket(m);
    if (q.status !== "active" && q.status !== "open") continue;
    if (!Number.isFinite(q.closeMs) || q.closeMs - nowMs < MIN_LEFT_S * 1000) continue;
    if (!validQuote(q.bid, q.ask)) continue;
    for (const side of ["yes", "no"]) {
      const price = side === "yes" ? q.ask : noSide(q.bid);
      const band = Object.keys(BANDS).find((b) => price >= BANDS[b][0] && price <= BANDS[b][1]);
      if (!band) continue;
      const n = sizeFor(price, cap, side === "yes" ? q.askSz : q.bidSz);
      if (n >= 1) {
        out.push({ ticker: q.ticker, series, side, band, contracts: n, price, fee: takerFee(price, n), closeTs: q.closeMs });
      }
      break;
    }
  }
  return out;
}

module.exports = { SERIES, BANDS, takerFee, validQuote, sizeFor, planEntries };
