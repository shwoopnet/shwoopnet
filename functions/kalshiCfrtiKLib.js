"use strict";
// CFRTI-K, the decision (Nov 12, 2026, probation seat; spec: Idea Desk A's probation sheet, section A and C, kalshi-scalper/workers/DESK_A_PROBATION_SPECS_NOV12.md on claude/idea-desk-a).
//
// PURE: no network, no Firestore, no clock, no Math.random. Everything the rule needs is passed in, so the same inputs always give the same answer and a test can pin it against the desk's 20
// parity vectors. The slot engine reads the market quote and the Bitcoin perpetual's one minute candles; this file only decides.
//
// The rule, frozen, no number tuned (the constants below are the spec's):
//   - Market KXBTC15M, ONE look at 120 s before the close, using the perp candle that ends at that instant.
//   - The cheaper side: YES if its ask is 0.05 to 0.30 (a 1e-9 tolerance at both ends), else NO if 1 minus the YES bid is 0.05 to 0.30.
//   - The YES spread is at most 0.03 and not crossed.
//   - index = floor_strike x P(close-120 s) / P(close-900 s), P the mid of the perp candle's bid and ask close.
//   - sd = the sample standard deviation (n-1) of the log changes between neighbouring minute marks (at least 6 of the 10 possible), times sqrt(4/3).
//   - chance of YES = Phi(ln(index / floor_strike) / sd); the NO side is 1 minus it.
//   - buy when (chance of the side - its ask) is 0.05 or more.
// Any missing input is no order. The reasons are fixed strings so a skip log and the parity vectors agree.

const BAND_MIN = 0.05, BAND_MAX = 0.30, MAX_SPREAD = 0.03, MIN_EDGE = 0.05, MIN_CHANGES = 6, TOL = 1e-9;
const VOL_SCALE = Math.sqrt(4 / 3);
const isNum = (x) => typeof x === "number" && Number.isFinite(x);

// erfc to full double precision: the Taylor series of erf for small |z|, a continued fraction (modified Lentz) for large |z|.
function erfc(z) {
  if (z < 0) return 2 - erfc(-z);
  if (z < 2.5) {
    // erf(z) = 2/sqrt(pi) * sum_{n>=0} (-1)^n z^(2n+1) / (n! (2n+1))
    let term = z, sum = z;
    for (let n = 1; n < 200; n++) {
      term *= -z * z / n;
      const add = term / (2 * n + 1);
      sum += add;
      if (Math.abs(add) < 1e-18 * Math.abs(sum)) break;
    }
    return 1 - (2 / Math.sqrt(Math.PI)) * sum;
  }
  // erfc(z) = exp(-z^2)/sqrt(pi) * 1/(z + (1/2)/(z + 1/(z + (3/2)/(z + 2/(z + ...)))))
  const tiny = 1e-300;
  let f = z, C = z, D = 0;
  for (let k = 1; k < 500; k++) {
    const a = k / 2;
    D = z + a * D; if (D === 0) D = tiny;
    C = z + a / C; if (C === 0) C = tiny;
    D = 1 / D;
    const delta = C * D;
    f *= delta;
    if (Math.abs(delta - 1) < 1e-16) break;
  }
  return Math.exp(-z * z) / (Math.sqrt(Math.PI) * f);
}
function phi(x) { return 0.5 * erfc(-x / Math.SQRT2); }

// Log changes between neighbouring minute marks, only where BOTH marks exist (a gap drops its two changes, as the desk's scorer does). marks[0] is the decision minute, marks[1..10] the ten before it.
function logChanges(marks) {
  const out = [];
  for (let i = 0; i + 1 < marks.length; i++) {
    const a = marks[i], b = marks[i + 1];
    if (isNum(a) && isNum(b) && a > 0 && b > 0) out.push(Math.log(a / b));
  }
  return out;
}
function sampleSd(xs) {
  const n = xs.length;
  if (n < 2) return NaN;
  const mean = xs.reduce((s, x) => s + x, 0) / n;
  return Math.sqrt(xs.reduce((s, x) => s + (x - mean) * (x - mean), 0) / (n - 1));
}

// input: { floorStrike, yesBid, yesAsk, marks: [11 numbers or null, newest first], openMark: number|null }
// Returns { trade, reason, side, sidePrice, edge, modelYes, sideChance, index, sd, nChanges }; reason "trade" when it fires. Never throws.
function cfrtiKDecide(input) {
  const i = input || {};
  const no = (reason, extra) => Object.assign({ trade: false, reason, side: null, sidePrice: null, edge: null, modelYes: null, sideChance: null, index: null, sd: null, nChanges: null }, extra || {});
  const bid = i.yesBid, ask = i.yesAsk;
  if (!isNum(bid) || !isNum(ask)) return no("no decision candle");
  // The cheaper side, then the spread (the order the desk's scorer reports them in is not pinned by a vector where both fail; both orders give the same no order).
  const yesCheap = ask >= BAND_MIN - TOL && ask <= BAND_MAX + TOL;
  const noPrice = 1 - bid;
  const noCheap = !yesCheap && noPrice >= BAND_MIN - TOL && noPrice <= BAND_MAX + TOL;
  const spread = ask - bid;
  if (!(spread > 0) || spread > MAX_SPREAD + TOL) return no("spread over 3c or crossed");
  if (!yesCheap && !noCheap) return no("not cheap");
  const side = yesCheap ? "yes" : "no";
  const sidePrice = yesCheap ? ask : noPrice;
  if (!isNum(i.floorStrike) || !(i.floorStrike > 0)) return no("no opening minute", { side, sidePrice });
  if (!isNum(i.openMark) || !(i.openMark > 0)) return no("no opening minute", { side, sidePrice });
  const marks = Array.isArray(i.marks) ? i.marks : [];
  const changes = logChanges(marks);
  if (changes.length < MIN_CHANGES) return no("under 6 changes", { side, sidePrice, nChanges: changes.length });
  const m0 = marks[0];
  const sd = sampleSd(changes) * VOL_SCALE;
  if (!isNum(m0) || !(m0 > 0) || !isNum(sd) || !(sd > 0)) return no("no volatility", { side, sidePrice, nChanges: changes.length, sd: isNum(sd) ? sd : null });
  const index = i.floorStrike * m0 / i.openMark;
  const modelYes = phi(Math.log(index / i.floorStrike) / sd);
  const sideChance = yesCheap ? modelYes : 1 - modelYes;
  const edge = sideChance - sidePrice;
  const base = { side, sidePrice, edge, modelYes, sideChance, index, sd, nChanges: changes.length };
  if (!(edge >= MIN_EDGE - TOL)) return Object.assign(no("no edge"), base);
  return Object.assign({ trade: true, reason: "trade" }, base);
}

// ---- Reading the perp candles (pure) ------------------------------------------------------------------------------------------------------------
// A candle is identified by end_period_ts, the END of its minute. Mark = (bid.close + ask.close) / 2; a missing side or a side at 0 is a missing mark. The marks the rule uses are the candle ending at
// close-120 s (mark 0), the ten ending at close-180 s ... close-720 s (marks 1 to 10), and the one ending at close-900 s (the opening mark). Nothing older or newer is ever substituted.
function candleMark(c) {
  if (!c || typeof c !== "object") return null;
  const side = (k) => { const v = c[k]; const x = v && typeof v === "object" ? Number(v.close) : NaN; return Number.isFinite(x) && x > 0 ? x : null; };
  const b = side("bid"), a = side("ask");
  return b !== null && a !== null ? (b + a) / 2 : null;
}
function perpMarks(candles, closeSec) {
  const list = Array.isArray(candles) ? candles : [];
  const at = (sec) => { const c = list.find((x) => x && Number(x.end_period_ts) === sec); return c ? candleMark(c) : null; };
  const marks = [];
  for (let k = 0; k <= 10; k++) marks.push(at(closeSec - 120 - 60 * k));
  let newest = null;
  for (const c of list) { const t = c ? Number(c.end_period_ts) : NaN; if (Number.isFinite(t) && (newest === null || t > newest)) newest = t; }
  return { marks, openMark: at(closeSec - 900), decisionPresent: marks[0] !== null, newestEndSec: newest };
}

module.exports = { cfrtiKDecide, perpMarks, candleMark, phi, erfc, logChanges, sampleSd, BAND_MIN, BAND_MAX, MAX_SPREAD, MIN_EDGE, MIN_CHANGES };
