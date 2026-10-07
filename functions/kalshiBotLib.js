"use strict";
// Pure logic for the server-side Kalshi paper bot. No Firebase, no network, so the
// repo's plain-node tests can run it. A port of kalshi-scalper/src/scalper/
// (limits.py, bot.py, scalps.py, since retired); the tests use the same cases.
//
// PAPER ONLY. There is no order code anywhere in the bot. Real orders will be
// written only after a strategy passes its pre-registered test in paper trading.

const BANDS = { "40c": [0.38, 0.42], "50c": [0.48, 0.52] };
const TARGET = 0.80;
const MIN_LEFT_S = 300;
const FEE_RATE = 0.07;
const SETTLE_GRACE_MS = 15000;
const BANKROLL = 100; // the owner starts at $100
// One copy of the series list and the dollar-string parsing, shared with the relay.
const { KALSHI_SERIES: SERIES, kalshiNum: num } = require("./kalshiLib");
const LIMITS = { perTradePct: 0.01, softPct: 0.03, hardPct: 0.05, breakMs: 2 * 60 * 60 * 1000 };
const TZ = "America/Chicago"; // the owner's day; the server clock is UTC

const round2 = (x) => Math.round(x * 100) / 100;
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

function localDayStart(nowMs, tz) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: tz || TZ, hourCycle: "h23", hour: "2-digit", minute: "2-digit", second: "2-digit",
  }).formatToParts(new Date(nowMs));
  const g = (t) => Number(parts.find((p) => p.type === t).value);
  return nowMs - ((g("hour") * 60 + g("minute")) * 60 + g("second")) * 1000 - (nowMs % 1000);
}

// Daily loss tiers: the same rules as the web page. closed: [{settledAt, pnl}].
//   per trade 1% of bankroll; down 3%: a 2 hour break then half size; down 5%: done.
// Realised only, in the owner's local day, in settlement order. The break is measured
// from the trade that crossed the soft line and later wins do not shorten it. The hard
// stop is sticky. No bankroll means no trading (fail closed).
function tierState(closed, bankroll, nowMs) {
  const out = { mode: "ok", cap: 0, perTradeCap: 0, softLimit: 0, hardLimit: 0, pnlToday: 0, counted: 0, softAt: null, breakUntil: null };
  const bank = Number(bankroll);
  if (!(bank > 0)) { out.mode = "done"; return out; }
  out.perTradeCap = bank * LIMITS.perTradePct;
  out.softLimit = bank * LIMITS.softPct;
  out.hardLimit = bank * LIMITS.hardPct;
  const start = localDayStart(nowMs);
  const today = (closed || []).filter((c) => c && typeof c.pnl === "number" && c.settledAt >= start && c.settledAt <= nowMs)
    .sort((a, b) => a.settledAt - b.settledAt);
  let cum = 0, hard = false;
  today.forEach((c) => {
    cum += c.pnl;
    if (out.softAt === null && cum <= -out.softLimit) out.softAt = c.settledAt;
    if (cum <= -out.hardLimit) hard = true;
  });
  out.pnlToday = round2(cum);
  out.counted = today.length;
  if (hard) {
    out.mode = "done";
  } else if (out.softAt !== null) {
    out.breakUntil = out.softAt + LIMITS.breakMs;
    if (nowMs < out.breakUntil) out.mode = "break";
    else { out.mode = "half"; out.cap = out.perTradeCap / 2; }
  } else {
    out.cap = out.perTradeCap;
  }
  return out;
}

// Most contracts whose cost INCLUDING the fee fits the cap and that the touch can fill.
function sizeFor(price, cap, displayed) {
  if (!(price > 0 && price < 1) || !(cap > 0)) return 0;
  let n = Math.floor(cap / price);
  while (n >= 1 && price * n + takerFee(price, n) > cap + 1e-9) n--;
  if (displayed != null) n = Math.min(n, Math.floor(displayed));
  return Math.max(n, 0);
}

// The same string in every process: this is what makes entry idempotent.
const positionId = (ticker) => "h2-" + ticker;

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

// Sell at the target when that side's bid reaches it, never on the entry tick itself.
function exitDue(pos, m, nowMs) {
  if (nowMs <= pos.entryAt) return false;
  const q = parseMarket(m);
  const sideBid = pos.side === "yes" ? q.bid : (q.ask == null ? null : noSide(q.ask));
  return sideBid != null && sideBid >= TARGET;
}

const exitPnl = (pos) => round2(TARGET * pos.contracts - takerFee(TARGET, pos.contracts) - pos.entry * pos.contracts - pos.entryFee);
const settlePnl = (pos, result) => round2((result === pos.side ? pos.contracts : 0) - pos.entry * pos.contracts - pos.entryFee);

module.exports = {
  TARGET, SETTLE_GRACE_MS, BANKROLL, SERIES, BANDS,
  takerFee, validQuote, localDayStart, tierState, sizeFor, positionId,
  planEntries, exitDue, exitPnl, settlePnl, round2,
};
