"use strict";
// Wheel seats, LIVE WIRING, built INERT (docs/WHEEL_SEAT_WIRING.md, docs/ROTATION_LANE.md sections 5, 5a, 6, 8).
//
// A seat is a registered second-slot strategy taken from the wheel. This module only says what a seat IS and what it may be: a validator, the caps a seat
// runs under, its kill, its shard check and the live-against-shadow check. It is PURE (no network, no Firestore, no clock, no order or signing code),
// NOTHING imports it (a gate fails if anything under functions/ or index.html does), and WHEEL_SEATS is a frozen empty list, so no seat exists and no
// deployed function behaves differently. A seat becomes real only by a later reviewed edit that adds one entry here AND maps it into the slot registry,
// after the owner's popup with the exact spec, the Chief of Staff's security review, the shard check and the caps.
// Nothing stored in Firestore, sent by the page or typed into a callable can add, enlarge or re-arm a seat: every number below is a constant in this file.

const slot = require("./kalshiSlotLib");
const bot = require("./kalshiSignalLib");

const WHEEL_SEATS = Object.freeze([]);                          // EMPTY. An entry is a reviewed edit (ROTATION_LANE section 1.4).
const WHEEL_RULE_IDS = Object.freeze([]);                       // the fixed code-side list of rule ids a seat may name; empty until an admission adds one
const WHEEL_FULL_SEATS_ENABLED = false;                         // full 10 contract seats wait for the premise test (section 9.5) and a bigger account; a constant, never a stored value
const WHEEL_MAX_PROBATION_SEATS = 5;
const WHEEL_PROBATION_CONTRACTS = 3, WHEEL_PROBATION_MAX_ORDER_COST = 3, WHEEL_PROBATION_NET_FLOOR = -18;
const WHEEL_FULL_CONTRACTS = 10, WHEEL_FULL_MAX_ORDER_COST = 10;
const WHEEL_PROBATION_FAVOURITE_FROM = 0.88;                   // a probation seat may not reach a price of 88c or above (section 5a.2)
const WHEEL_CHECK_MIN_ORDERS = 20, WHEEL_CHECK_MIN_FILL_SHARE = 0.6, WHEEL_CHECK_MAX_WORSE = 0.01;

const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const isObj = (x) => x && typeof x === "object" && !Array.isArray(x);
const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s + "T00:00:00Z"));
const exactKeys = (o, keys) => isObj(o) && Object.keys(o).sort().join() === keys.slice().sort().join();

// A seat has NO scaleIn field and no way to carry one: the mapping below fixes it, so a seat can never scale in or loosen it.
const SEAT_KEYS = ["id", "ruleId", "readme", "series", "entry", "exit", "contractsPerOrder", "killRules", "probation", "forwardReadDate", "reviewedAt", "popupDate"];
const SEAT_SCALE_IN = Object.freeze({ maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true });

// The second-slot strategy a seat becomes. The slot's own validator then judges it, so every slot bound (series list, bands, times, hold list, kill ranges) applies unchanged.
function seatToSlotStrategy(seat) {
  const s = seat || {};
  return {
    id: s.id, readme: s.readme, series: s.series, entry: s.entry, exit: s.exit, contractsPerOrder: s.contractsPerOrder,
    scaleIn: SEAT_SCALE_IN, killRules: s.killRules, forwardReadDate: s.forwardReadDate, reviewedAt: s.reviewedAt,
  };
}

// Returns { ok, errors }. Never throws. `flags` exists only for tests (ruleIds, fullSeatsEnabled); production calls validateWheelSeat(seat).
function validateWheelSeatWith(flags, seat) {
  const f = flags || {};
  const ruleIds = f.ruleIds === undefined ? WHEEL_RULE_IDS : f.ruleIds;
  const fullOn = f.fullSeatsEnabled === undefined ? WHEEL_FULL_SEATS_ENABLED : f.fullSeatsEnabled;
  if (!exactKeys(seat, SEAT_KEYS)) return { ok: false, errors: ["a seat must have exactly these fields: " + SEAT_KEYS.join(", ")] };
  const e = [];
  if (!Array.isArray(ruleIds) || !ruleIds.includes(seat.ruleId)) e.push("ruleId is not on the fixed list of wheel rules in code");
  if (typeof seat.probation !== "boolean") e.push("probation must be true or false");
  if (!isDate(seat.popupDate)) e.push("popupDate (the owner's popup) must be YYYY-MM-DD");
  else if (isDate(seat.reviewedAt) && seat.popupDate > seat.reviewedAt) e.push("the owner's popup must not be later than reviewedAt");
  const sv = slot.validateSlotStrategy(seatToSlotStrategy(seat));
  for (const x of sv.errors) e.push(x);
  const contracts = seat.contractsPerOrder;
  const entry = isObj(seat.entry) ? seat.entry : {};
  const worstCost = isNum(entry.priceMax) && Number.isInteger(contracts) && contracts >= 1 ? entry.priceMax * contracts + bot.takerFee(entry.priceMax, contracts) : NaN;
  if (seat.probation === true) {
    if (contracts !== WHEEL_PROBATION_CONTRACTS) e.push("a probation seat is exactly " + WHEEL_PROBATION_CONTRACTS + " contracts");
    if (!(worstCost <= WHEEL_PROBATION_MAX_ORDER_COST + 1e-9)) e.push("a probation order may cost at most $" + WHEEL_PROBATION_MAX_ORDER_COST + " at its top price");
    if (isNum(entry.priceMax) && entry.priceMax >= WHEEL_PROBATION_FAVOURITE_FROM - 1e-9) e.push("a probation seat may not buy at 88c or above (favourites need the 150 signal, 10 loss record)");
    const k = isObj(seat.killRules) && isObj(seat.killRules.minNet) ? seat.killRules.minNet : null;
    if (!k || !isNum(k.net) || k.net < WHEEL_PROBATION_NET_FLOOR) e.push("a probation seat's net floor must be no looser than $" + WHEEL_PROBATION_NET_FLOOR);
  } else if (seat.probation === false) {
    if (fullOn !== true) e.push("full seats are not enabled (WHEEL_FULL_SEATS_ENABLED is false until the premise test is read)");
    if (!Number.isInteger(contracts) || contracts > WHEEL_FULL_CONTRACTS) e.push("a full seat is at most " + WHEEL_FULL_CONTRACTS + " contracts");
    if (!(worstCost <= WHEEL_FULL_MAX_ORDER_COST + 1e-9)) e.push("a full order may cost at most $" + WHEEL_FULL_MAX_ORDER_COST + " at its top price");
    if (isNum(entry.priceMax) && entry.priceMax >= WHEEL_PROBATION_FAVOURITE_FROM - 1e-9) e.push("a seat at 88c or above needs a 150 signal record with 10 losses, which this code cannot see, so it is refused");
  }
  return { ok: e.length === 0, errors: e };
}
const validateWheelSeat = (seat) => validateWheelSeatWith({}, seat);

// The whole list or nothing: one bad entry, a repeated id or a sixth probation seat refuses every seat (a typo can never quietly drop one guard and keep the rest).
function activeWheelSeatsWith(flags, list) {
  const seats = list === undefined ? WHEEL_SEATS : list;
  if (!Array.isArray(seats)) return [];
  const ids = new Set();
  let probation = 0;
  for (const s of seats) {
    if (!validateWheelSeatWith(flags, s).ok || ids.has(s.id)) return [];
    ids.add(s.id);
    if (s.probation === true) probation += 1;
  }
  if (probation > WHEEL_MAX_PROBATION_SEATS) return [];
  return seats.slice();
}
const activeWheelSeats = () => activeWheelSeatsWith({});

// The caps a seat runs under: the slot's own caps from the sizing base, and the seat's per order ceiling on top, the SMALLER always winning (section 5.1).
function wheelSeatCaps(seat, sizingBase) {
  const caps = slot.slotCaps(sizingBase);
  const own = seat && seat.probation === true ? WHEEL_PROBATION_MAX_ORDER_COST : WHEEL_FULL_MAX_ORDER_COST;
  caps.perOrder = Math.min(caps.perOrder, own);
  return caps;
}

// The net floor latch: the slot's own kill check on the seat's own orders (sticky, replayed, a latch at or after reviewedAt keeps it off until a reviewed edit moves reviewedAt).
// `latch` is what kalshiSlotControl/killed holds for this id, or null.
function wheelSeatKilled(seat, slotOrders, latch) {
  return slot.killCheck(seatToSlotStrategy(seat), slotOrders, latch === undefined ? null : latch);
}

// The shard check: an order needs money on ITS market's shard, with the same margin the slot uses. Unknown means refuse, with the skip code the slot logs.
function wheelShardCheck({ avail, cost, margin }) {
  const m = isNum(margin) ? margin : 0.5;
  if (!isNum(avail) || !isNum(cost) || !(cost >= 0)) return { ok: false, code: "shard_short", reason: "the shard balance or the cost is unknown" };
  if (avail < cost + m) return { ok: false, code: "shard_short", reason: "only $" + avail.toFixed(2) + " on its shard" };
  return { ok: true, code: null, reason: "" };
}

// Live against shadow, first 20 live orders (section 5.2). PURE and NOT WIRED to anything: it returns the verdict, nothing acts on it.
// rows: one per live order, { filled: boolean, fillPrice, shadowPrice } (prices in dollars; the prices matter only for filled orders). Returns 'wait', 'stay' or 'leave seat'.
function wheelLiveVsShadow(rows) {
  if (!Array.isArray(rows) || rows.length < WHEEL_CHECK_MIN_ORDERS) return "wait";
  const first = rows.slice(0, WHEEL_CHECK_MIN_ORDERS);
  const filled = first.filter((r) => r && r.filled === true);
  if (filled.length / first.length < WHEEL_CHECK_MIN_FILL_SHARE - 1e-12) return "leave seat";
  if (filled.some((r) => !isNum(r.fillPrice) || !isNum(r.shadowPrice))) return "leave seat";   // an unreadable price cannot show the shadow was honest: fail closed
  const worse = filled.reduce((a, r) => a + (r.fillPrice - r.shadowPrice), 0) / filled.length;
  return worse > WHEEL_CHECK_MAX_WORSE + 1e-9 ? "leave seat" : "stay";
}

module.exports = {
  WHEEL_SEATS, WHEEL_RULE_IDS, WHEEL_FULL_SEATS_ENABLED, WHEEL_MAX_PROBATION_SEATS, WHEEL_PROBATION_CONTRACTS, WHEEL_PROBATION_MAX_ORDER_COST, WHEEL_PROBATION_NET_FLOOR,
  WHEEL_FULL_CONTRACTS, WHEEL_FULL_MAX_ORDER_COST, WHEEL_PROBATION_FAVOURITE_FROM, WHEEL_CHECK_MIN_ORDERS, WHEEL_CHECK_MIN_FILL_SHARE, WHEEL_CHECK_MAX_WORSE,
  seatToSlotStrategy, validateWheelSeat, activeWheelSeats, wheelSeatCaps, wheelSeatKilled, wheelShardCheck, wheelLiveVsShadow,
  _testOnly: Object.freeze({ validateWheelSeatWith, activeWheelSeatsWith }),
};
