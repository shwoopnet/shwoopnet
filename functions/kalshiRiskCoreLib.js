"use strict";
// RISK CORE SPEC v1 as pure functions (scalability rebuild, phase P1). INERT: nothing under functions/ and nothing in the page imports this file, it requires nothing
// (no order, slot, network, Firestore or signing code), and a gate (test/riskCoreGates.test.js RC11) keeps it that way. The few constants it needs are copied here and a
// test compares them with the slot library, as the rotation replay does. The 40 percent account floor (kalshiHardStopLib) and the 12 percent daily stop (RISK_PROFILES) already
// exist in code and are only named in docs/RISK_CORE.md, never re-implemented here.
// Fail closed everywhere: an unusable base, size or price can only make a limit smaller or a cost infinite, never larger.

const WINDOW_CEILING_FRACTION = 0.08;     // all seats together, one 15 minute window, share of the sizing base
const OPEN_MONEY_FRACTION = 0.12;         // money at risk in open orders, share of the base
const OPEN_MONEY_CEILING = 150;           // dollars, never above this whatever the base
const STOPS_BUDGET_FRACTION = 0.30;       // the sum of every live seat's maximum loss must be at or under this share of the base
const ORDER_CAP_FRACTION = 0.025, ORDER_CAP_CEILING = 20;   // Full and Proven per order cap (copy of SLOT_CAP_FRACTIONS.perOrder and its ceiling)
const DAILY_CAP_FRACTION = 0.025, DAILY_CAP_CEILING = 20;   // Full daily cap (copy of SLOT_CAP_FRACTIONS.daily and its ceiling)
const TRIAL = Object.freeze({ contracts: 3, orderCap: 3, dailyCap: 9, lossMargin: 18 });
const FULL = Object.freeze({ contracts: 10, maxLoss: 60 });
const PROVEN = Object.freeze({ dailyPerContract: 2.5, dailyBaseFraction: 0.06, dailyCeiling: 75, lossPerContract: 5, lossBaseFraction: 0.12, lossCeiling: 150 });
const PROBE_CONTRACTS = 1;
const TIER_ORDER = Object.freeze(["proven", "full", "trial", "probe"]);   // allocation priority, first served first

const nz = (x) => (typeof x === "number" && isFinite(x) && x > 0 ? x : 0);

function windowCeiling(base) { return WINDOW_CEILING_FRACTION * nz(base); }
function openMoneyCap(base) { return Math.min(OPEN_MONEY_FRACTION * nz(base), OPEN_MONEY_CEILING); }
function stopsBudget(base) { return STOPS_BUDGET_FRACTION * nz(base); }

// A seat: { id, tier: "trial"|"full"|"proven"|"probe", contracts, price (top price it may pay, 0 to 1), startedAtMs (start of its live record),
//           openContracts, netFloor (trial and probe: the net kill line, zero or negative dollars) }.
function seatCaps(seat, base) {
  const b = nz(base), s = seat || {};
  if (s.tier === "trial" || s.tier === "probe") {
    const max = s.tier === "probe" ? PROBE_CONTRACTS : TRIAL.contracts;
    return { contracts: Math.min(max, Math.floor(nz(s.contracts)) || max), orderCap: TRIAL.orderCap, dailyCap: TRIAL.dailyCap };
  }
  if (s.tier === "full") {
    return { contracts: Math.min(FULL.contracts, Math.floor(nz(s.contracts)) || FULL.contracts), orderCap: Math.min(ORDER_CAP_FRACTION * b, ORDER_CAP_CEILING), dailyCap: Math.min(DAILY_CAP_FRACTION * b, DAILY_CAP_CEILING) };
  }
  if (s.tier === "proven") {
    const c = Math.floor(nz(s.contracts));
    return { contracts: c, orderCap: Math.min(ORDER_CAP_FRACTION * b, ORDER_CAP_CEILING), dailyCap: Math.min(PROVEN.dailyPerContract * c, PROVEN.dailyBaseFraction * b, PROVEN.dailyCeiling) };
  }
  return { contracts: 0, orderCap: 0, dailyCap: 0 };   // unknown tier: nothing
}

// The most a seat can lose before its own stop ends it. Unknown tier is Infinity so it can never be admitted.
function seatMaxLoss(seat, base) {
  const s = seat || {}, b = nz(base);
  if (s.tier === "trial" || s.tier === "probe") {
    const f = typeof s.netFloor === "number" && isFinite(s.netFloor) && s.netFloor < 0 ? -s.netFloor : 0;   // a positive or missing floor counts as zero: the margin still applies
    return f + TRIAL.lossMargin;
  }
  if (s.tier === "full") return FULL.maxLoss;
  if (s.tier === "proven") return Math.min(PROVEN.lossPerContract * Math.floor(nz(s.contracts)), PROVEN.lossBaseFraction * b, PROVEN.lossCeiling);
  return Infinity;
}

// Worst case cost of one order: contracts x top price + the fee. feeFn(contracts, price) is the order's total fee in dollars (a parameter, never imported).
function seatOrderCost(contracts, price, feeFn) {
  const c = Math.floor(nz(contracts)), p = nz(price);
  if (c < 1 || p <= 0 || p > 1) return Infinity;
  const fee = typeof feeFn === "function" ? feeFn(c, p) : NaN;
  if (typeof fee !== "number" || !isFinite(fee) || fee < 0) return Infinity;
  return c * p + fee;
}

function sumMaxLoss(seats, base) { let t = 0; for (const s of seats || []) t += seatMaxLoss(s, base); return t; }
function allSeatsWorstCase(seats, base) {
  const total = sumMaxLoss(seats, base), budget = stopsBudget(base);
  return { total, budget, ok: total <= budget };
}

// The seat admission gate: a new live seat is admitted only if every live seat's maximum loss, with the candidate's, is at or under the stops budget.
function admitSeat(liveSeats, candidate, base) {
  const used = sumMaxLoss(liveSeats, base) + seatMaxLoss(candidate, base), budget = stopsBudget(base);
  const admit = used <= budget;
  return { admit, used, budget, reason: admit ? "fits" : "stops_budget" };
}

// Deterministic allocation of one window's money (R3: a seat waiting on a feed, waitingOnFeed true, is evaluated last of all). Depends only on its arguments. Priority: tier (proven, full, trial, probe), then the longest live record first
// (earliest startedAtMs; a missing start is last), then id. Each seat in turn gets its full order if it fits the window ceiling, the open money cap and its own caps,
// else the largest smaller size that fits; under 1 contract it sends nothing: reason "window_ceiling" when the shared ceilings are what stopped it, "seat_cap" when its own caps did.
function allocateWindow(seats, base, windowSpent, openMoney, feeFn) {
  const list = (Array.isArray(seats) ? seats : []).map((s, i) => ({ s: s || {}, i }));
  const rank = (t) => { const k = TIER_ORDER.indexOf(t); return k < 0 ? TIER_ORDER.length : k; };
  const start = (s) => (typeof s.startedAtMs === "number" && isFinite(s.startedAtMs) ? s.startedAtMs : Infinity);
  list.sort((a, b) => (a.s.waitingOnFeed ? 1 : 0) - (b.s.waitingOnFeed ? 1 : 0) || rank(a.s.tier) - rank(b.s.tier) || (start(a.s) < start(b.s) ? -1 : start(a.s) > start(b.s) ? 1 : 0) || (String(a.s.id) < String(b.s.id) ? -1 : String(a.s.id) > String(b.s.id) ? 1 : 0) || a.i - b.i);
  let winLeft = Math.max(0, windowCeiling(base) - nz(windowSpent)), openLeft = Math.max(0, openMoneyCap(base) - nz(openMoney));
  const out = [];
  for (const { s } of list) {
    const id = s.id;
    if (TIER_ORDER.indexOf(s.tier) < 0) { out.push({ id, contracts: 0, skip: "unknown_tier", cost: 0 }); continue; }
    const caps = seatCaps(s, base);
    let c = Math.min(Math.floor(nz(s.contracts)), caps.contracts - Math.floor(nz(s.openContracts)));
    while (c >= 1 && seatOrderCost(c, s.price, feeFn) > caps.orderCap) c--;
    if (c < 1) { out.push({ id, contracts: 0, skip: "seat_cap", cost: 0 }); continue; }
    while (c >= 1 && seatOrderCost(c, s.price, feeFn) > Math.min(winLeft, openLeft)) c--;
    if (c < 1) { out.push({ id, contracts: 0, skip: "window_ceiling", cost: 0 }); continue; }
    const cost = seatOrderCost(c, s.price, feeFn);
    winLeft -= cost; openLeft -= cost;
    out.push({ id, contracts: c, skip: null, cost });
  }
  return out;
}

// ---- Risk Analyst answers R1 to R7 (constants and pure functions; still inert) ----
const MINUTE_MS = 60 * 1000, HOUR_MS = 60 * MINUTE_MS, DAY_MS = 24 * HOUR_MS;
const CACHE_MAX_AGE_MS = 3 * MINUTE_MS;                 // R1
const UNCLEAR_SESSION_COUNT = 2, UNCLEAR_SESSION_WINDOW_MS = 60 * MINUTE_MS;   // R2
const MARKET_CONTRACT_CAP = 30, DEPTH_SHARE_CAP = 0.25; // R3
const SEAT_ORDERS_PER_DAY = 40, ACCOUNT_ORDERS_PER_DAY = 300;   // R4
const SEAT_ORDERS_PER_DAY_OVERRIDES = Object.freeze({ L1: 60 }); // R4: gold's own listed value (it is the L1 seat)
const GOLD_RESERVE_CONTRACTS = 1;                       // R5: only while gold is armed
const GENERIC_LADDER = Object.freeze([{ contracts: 10, minBase: 0 }, { contracts: 15, minBase: 1000 }, { contracts: 20, minBase: 1350 }, { contracts: 30, minBase: 2000 }]);   // R6
const OICORE_LADDER = Object.freeze([20, 25, 30]);      // R6: the written exception, until OICORE meets the proven bar
const LADDER_STEP_TESTS = Object.freeze({ fills: 15, days: 5, pf: 1.3, netPerContract: 1, drawdownPerContract: 3 });
const UP_MOVES_PER_DAY = 2, SEAT_COOL_MS = DAY_MS, ACCOUNT_COOL_MS = 6 * HOUR_MS;   // R7

// R1: a cached seat peak or drawdown may only REFUSE. A cache older than 3 minutes, unreadable or in the future sends nothing for that seat; a fresh cache at or past the seat's limit refuses.
// cache: { atMs, drawdown }, limit: the seat's maximum loss. It never returns more room than a replay would.
function cachedSeatGate(cache, nowMs, limit) {
  const c = cache || {};
  const age = nowMs - c.atMs;
  if (typeof c.atMs !== "number" || typeof nowMs !== "number" || !isFinite(age) || age < 0 || age > CACHE_MAX_AGE_MS || typeof c.drawdown !== "number" || !isFinite(c.drawdown)) return { allow: false, reason: "cache_stale" };
  if (!(typeof limit === "number" && isFinite(limit) && limit > 0)) return { allow: false, reason: "no_limit" };
  if (c.drawdown >= limit) return { allow: false, reason: "seat_stopped" };
  return { allow: true, reason: "ok" };
}
// R1: the full re-replay runs at least daily; if the replay is worse than the cache the seat latches until they agree and a critical item is logged.
function replayDue(lastReplayAtMs, nowMs) { return !(typeof lastReplayAtMs === "number" && isFinite(lastReplayAtMs)) || !(nowMs - lastReplayAtMs < DAY_MS); }
function auditCache(cache, replay) {
  const c = cache && typeof cache.drawdown === "number" && isFinite(cache.drawdown) ? cache.drawdown : NaN;
  const r = replay && typeof replay.drawdown === "number" && isFinite(replay.drawdown) ? replay.drawdown : NaN;
  if (!isFinite(r)) return { latch: true, critical: true, reason: "replay_unreadable" };
  if (!isFinite(c)) return { latch: true, critical: true, reason: "cache_unreadable" };
  if (r > c) return { latch: true, critical: true, reason: "replay_worse" };
  return { latch: false, critical: false, reason: r < c ? "cache_more_cautious" : "agree" };
}

// R2: unclear = [{ seatId, market, kind: "buy"|"sell"|"exit", atMs, maxCost, resolved }]. Only the unresolved ones count.
function unclearAnswerDecision(unclear, nowMs) {
  const open = (Array.isArray(unclear) ? unclear : []).filter((u) => u && !u.resolved);
  const quarantined = [], blocked = [], lost = {};
  let lostTotal = 0;
  for (const u of open) {
    if (!quarantined.includes(u.seatId)) quarantined.push(u.seatId);
    if (!blocked.includes(u.market)) blocked.push(u.market);
    const m = nz(u.maxCost); lost[u.seatId] = (lost[u.seatId] || 0) + m; lostTotal += m;   // counted as lost in every stop until resolved
  }
  quarantined.sort(); blocked.sort();
  const recent = new Set(open.filter((u) => typeof u.atMs === "number" && nowMs - u.atMs >= 0 && nowMs - u.atMs <= UNCLEAR_SESSION_WINDOW_MS).map((u) => u.seatId));
  let endSession = false, reason = open.length ? "quarantine" : "none";
  if (open.some((u) => u.kind === "sell" || u.kind === "exit")) { endSession = true; reason = "unclear_exit"; }
  else if (recent.size >= UNCLEAR_SESSION_COUNT) { endSession = true; reason = "two_seats_unclear"; }
  return { endSession, reason, quarantinedSeats: quarantined, blockedMarkets: blocked, lostBySeat: lost, lostTotal };
}

// R3: contracts a seat may send into one market: the market's sum across seats stays at or under 30 and the order is at most 25 percent of the touch size (unknown touch: zero).
function marketOrderContracts(wanted, marketOpenContracts, touchSize) {
  const room = Math.max(0, MARKET_CONTRACT_CAP - Math.floor(nz(marketOpenContracts)));
  const depth = Math.floor(DEPTH_SHARE_CAP * nz(touchSize));
  return Math.max(0, Math.min(Math.floor(nz(wanted)), room, depth));
}
// R3: opposite sides of one market are never allowed; the first seat in holds the direction for the window. heldSide null means nobody is in.
function directionAllowed(heldSide, side) {
  if (side !== "yes" && side !== "no") return false;
  return heldSide == null || heldSide === side;
}

// R4: orders in the rolling 24 hours (times in ms, now inclusive).
function ordersInDay(times, nowMs) { let n = 0; for (const t of Array.isArray(times) ? times : []) if (typeof t === "number" && isFinite(t) && nowMs - t >= 0 && nowMs - t < DAY_MS) n++; return n; }
function seatOrderBudget(seatId, times, nowMs) {
  const limit = SEAT_ORDERS_PER_DAY_OVERRIDES[seatId] || SEAT_ORDERS_PER_DAY, used = ordersInDay(times, nowMs);
  return { allowed: used < limit, used, limit };
}
function accountOrderCheck(times, nowMs) {   // a runaway check: at the limit the session ends
  const used = ordersInDay(times, nowMs);
  return { endSession: used >= ACCOUNT_ORDERS_PER_DAY, used, limit: ACCOUNT_ORDERS_PER_DAY };
}

// R5: the one contract gold reserve inside the window ceiling exists only while gold is armed.
function goldReserveContracts(goldArmed) { return goldArmed === true ? GOLD_RESERVE_CONTRACTS : 0; }

// R6: the generic ladder's size for a base (the top step whose base is reached; an unusable base is the bottom step), and its step test.
function genericLadderStep(base) {
  const b = nz(base); let c = GENERIC_LADDER[0].contracts;
  for (const s of GENERIC_LADDER) if (b >= s.minBase) c = s.contracts;
  return c;
}
function ladderStepTestsPass(st) {
  const t = LADDER_STEP_TESTS, s = st || {}, c = nz(s.contracts);
  return nz(s.fills) >= t.fills && nz(s.days) >= t.days && nz(s.pf) >= t.pf && c > 0 && typeof s.net === "number" && s.net >= t.netPerContract * c && typeof s.drawdown === "number" && s.drawdown >= 0 && s.drawdown < t.drawdownPerContract * c;
}

// R7: moves = [{ seatId, kind: "up"|"down", atMs }]. A new Trial admission is an up-move. stopsFitAfter: whether the 30 percent stops budget still fits after the move.
// Down-moves, stops and kills are never limited and not asked here.
function upMoveAllowed(moves, nowMs, seatId, stopsFitAfter) {
  if (stopsFitAfter !== true) return { allow: false, reason: "stops_budget" };
  const ups = (Array.isArray(moves) ? moves : []).filter((m) => m && m.kind === "up" && typeof m.atMs === "number" && isFinite(m.atMs) && nowMs - m.atMs >= 0);
  if (ups.filter((m) => nowMs - m.atMs < DAY_MS).length >= UP_MOVES_PER_DAY) return { allow: false, reason: "daily_limit" };
  if (ups.some((m) => m.seatId === seatId && nowMs - m.atMs < SEAT_COOL_MS)) return { allow: false, reason: "seat_cooling" };
  if (ups.some((m) => nowMs - m.atMs < ACCOUNT_COOL_MS)) return { allow: false, reason: "account_cooling" };
  return { allow: true, reason: "ok" };
}

module.exports = {
  CACHE_MAX_AGE_MS, UNCLEAR_SESSION_COUNT, UNCLEAR_SESSION_WINDOW_MS, MARKET_CONTRACT_CAP, DEPTH_SHARE_CAP, SEAT_ORDERS_PER_DAY, ACCOUNT_ORDERS_PER_DAY, SEAT_ORDERS_PER_DAY_OVERRIDES, GOLD_RESERVE_CONTRACTS,
  GENERIC_LADDER, OICORE_LADDER, LADDER_STEP_TESTS, UP_MOVES_PER_DAY, SEAT_COOL_MS, ACCOUNT_COOL_MS,
  cachedSeatGate, replayDue, auditCache, unclearAnswerDecision, marketOrderContracts, directionAllowed, ordersInDay, seatOrderBudget, accountOrderCheck, goldReserveContracts, genericLadderStep, ladderStepTestsPass, upMoveAllowed,
  WINDOW_CEILING_FRACTION, OPEN_MONEY_FRACTION, OPEN_MONEY_CEILING, STOPS_BUDGET_FRACTION, ORDER_CAP_FRACTION, ORDER_CAP_CEILING, DAILY_CAP_FRACTION, DAILY_CAP_CEILING,
  TRIAL, FULL, PROVEN, PROBE_CONTRACTS, TIER_ORDER,
  windowCeiling, openMoneyCap, stopsBudget, seatCaps, seatMaxLoss, seatOrderCost, admitSeat, allocateWindow, allSeatsWorstCase,
};
