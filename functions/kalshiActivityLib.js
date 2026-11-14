"use strict";
// Activity seats, built INERT (docs/ACTIVITY_SEATS.md). Live trial seats at 3 contracts on UNPROVEN candidates so the account is never idle, DATA ONLY: no edge is expected.
// Site label: ACTIVITY_LABEL. This module is PURE: it requires nothing, has no network, Firestore, clock or order code, and index.html never names it.
// ACTIVITY_SEATS is a frozen empty list, so with no seat registered the slot engine's gate path is byte for byte what it was (the check returns {applies:false} at once).
// Everything below is REPLAYED from settled slot orders on every call; nothing is stored, so two instances always agree. Nothing stored, sent by the page or typed into a callable
// can add, enlarge or re-arm a seat: every number is a constant in this file, and a return after the PF cut is a reviewed edit (reviewedAt moves).

const ACTIVITY_LABEL = "Activity seat: no edge expected, data only";
const ACTIVITY_SEATS = Object.freeze([]);                      // EMPTY. An entry is a reviewed edit with the owner's popup.
const ACTIVITY_MAX_SEATS = 3;
const ACTIVITY_CONTRACTS = 3, ACTIVITY_MAX_ORDER_COST = 3;     // dollars, fee included, at the seat's top price
const ACTIVITY_PRICE_CEILING = 0.88;                           // no entry price at 88c or above
const ACTIVITY_SEAT_DAILY_LOSS = 6, ACTIVITY_SEAT_WEEKLY_LOSS = 20, ACTIVITY_SHARED_WEEKLY_LOSS = 40;
const ACTIVITY_CUT_FILLS = 100, ACTIVITY_CUT_PF = 0.8;
const ACTIVITY_TZ = "America/Chicago";
// Families the owner declined or evidence closed (docs/STRATEGY_LIFECYCLE.md 7e). A seat naming one is refused. A reviewed edit may extend this list, never shrink it without the owner.
const ACTIVITY_DECLINED_FAMILIES = Object.freeze([
  "favourite-late", "taker-order-flow", "market-making", "weather-forecast-vs-market", "mapbreak", "lock-parity-scan", "approval-no-side", "gold-hold",
  // Added after the security review (Nov 14, 2026), from docs/STRATEGY_LIFECYCLE.md 7e. A free string matched exactly cannot catch a renamed idea: 7e rule 2 (a rename IS the declined idea) is a reviewer's check at admission, with the owner's popup.
  "ex-dividend-perp-short", "conditional-tie-premium", "second-of-minute-taker-clustering", "fractional-size-flow", "cheap-side-price-regime-grammar-sweep",
  "gold-maker-entry", "gold-price-floor", "gold-band-narrowed", "gold-ladder-cap", "l1-other-markets",
]);

const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const isObj = (x) => x && typeof x === "object" && !Array.isArray(x);
const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s + "T00:00:00Z"));
const exactKeys = (o, keys) => isObj(o) && Object.keys(o).sort().join() === keys.slice().sort().join();
const num = (x) => { if (x === null || x === undefined || x === "") return NaN; const n = Number(x); return Number.isFinite(n) ? n : NaN; };
// The slot's taker fee (7% of P x (1 - P) per contract, rounded up to the cent per order), copied so this file imports nothing; the test pins it to the slot's own function.
function fee(price, contracts) {
  if (!(price > 0 && price < 1) || !(contracts > 0)) return 0;
  return Math.ceil(Number((0.07 * contracts * price * (1 - price) * 100).toFixed(9))) / 100;
}

// ---- Central time (follows daylight saving) ----------------------------------------------------------------------------------------------
const dtf = new Intl.DateTimeFormat("en-US", { timeZone: ACTIVITY_TZ, hourCycle: "h23", year: "numeric", month: "numeric", day: "numeric", hour: "numeric", minute: "numeric", second: "numeric" });
function centralParts(ms) {
  const o = {};
  for (const p of dtf.formatToParts(new Date(ms))) if (p.type !== "literal") o[p.type] = Number(p.value);
  return o;
}
const offsetAt = (ms) => { const p = centralParts(ms); return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - Math.floor(ms / 1000) * 1000; };
// UTC ms of local midnight on the Central calendar date (y, m, d).
function centralMidnight(y, m, d) {
  const wall = Date.UTC(y, m - 1, d);
  let t = wall - offsetAt(wall + 6 * 3600e3);
  t = wall - offsetAt(t);
  return t;
}
// Start (UTC ms) of the Central day and of the Central week (Monday 00:00) that contain `ms`. Not finite in, not finite out.
function centralDayStart(ms) {
  if (!isNum(ms)) return NaN;
  try { const p = centralParts(ms); return centralMidnight(p.year, p.month, p.day); } catch (e) { return NaN; }   // an out of range clock refuses, never throws
}
function centralWeekStart(ms) {
  if (!isNum(ms)) return NaN;
  try { return centralWeekStartUnsafe(ms); } catch (e) { return NaN; }
}
function centralWeekStartUnsafe(ms) {
  const p = centralParts(ms);
  const dow = new Date(Date.UTC(p.year, p.month - 1, p.day)).getUTCDay();         // 0 Sunday .. 6 Saturday of the Central calendar date
  const back = (dow + 6) % 7;                                                       // days since Monday
  const mon = new Date(Date.UTC(p.year, p.month - 1, p.day - back));
  return centralMidnight(mon.getUTCFullYear(), mon.getUTCMonth() + 1, mon.getUTCDate());
}

// ---- Validator ------------------------------------------------------------------------------------------------------------------------------
const SEAT_KEYS = ["id", "familyId", "readme", "series", "entry", "contractsPerOrder", "ioc", "reviewedAt"];
// Returns { ok, errors }. Never throws. A seat maps to a second-slot strategy later (docs/ACTIVITY_SEATS.md); the slot's own validator then judges that too.
function validateActivitySeat(seat) {
  if (!exactKeys(seat, SEAT_KEYS)) return { ok: false, errors: ["a seat must have exactly these fields: " + SEAT_KEYS.join(", ")] };
  const e = [];
  if (typeof seat.id !== "string" || !/^[A-Z][A-Z0-9]{2,15}$/.test(seat.id)) e.push("id must be 3 to 16 capitals or digits");
  if (typeof seat.familyId !== "string" || !seat.familyId) e.push("familyId is required");
  else if (ACTIVITY_DECLINED_FAMILIES.includes(seat.familyId)) e.push("the family '" + seat.familyId + "' is declined or closed by evidence");
  if (typeof seat.readme !== "string" || !seat.readme) e.push("readme (the pre-registration pointer) is required");
  if (!Array.isArray(seat.series) || seat.series.length < 1 || seat.series.some((s) => typeof s !== "string" || !/^KX[A-Z0-9]+$/.test(s))) e.push("series must be a list of Kalshi series names");
  if (!isDate(seat.reviewedAt)) e.push("reviewedAt must be YYYY-MM-DD");
  if (seat.contractsPerOrder !== ACTIVITY_CONTRACTS) e.push("an activity seat is exactly " + ACTIVITY_CONTRACTS + " contracts");
  if (seat.ioc !== true) e.push("an activity seat's order must be immediate-or-cancel (ioc: true)");
  const en = isObj(seat.entry) ? seat.entry : null;
  if (!en || !isNum(en.priceMin) || !isNum(en.priceMax) || en.priceMin <= 0 || en.priceMax < en.priceMin) e.push("entry needs a price band (priceMin, priceMax)");
  else {
    if (en.priceMax >= ACTIVITY_PRICE_CEILING - 1e-9) e.push("an activity seat may not buy at 88c or above");
    if (!(en.priceMax * ACTIVITY_CONTRACTS + fee(en.priceMax, ACTIVITY_CONTRACTS) <= ACTIVITY_MAX_ORDER_COST + 1e-9)) e.push("an order may cost at most $" + ACTIVITY_MAX_ORDER_COST + " at its top price");
  }
  return { ok: e.length === 0, errors: e };
}
// The whole list or nothing: one bad seat, a repeated id or a fourth seat refuses every seat.
function activeActivitySeats(list) {
  const seats = list === undefined ? ACTIVITY_SEATS : list;
  if (!Array.isArray(seats) || seats.length > ACTIVITY_MAX_SEATS) return [];
  const ids = new Set();
  for (const s of seats) { if (!validateActivitySeat(s).ok || ids.has(s.id)) return []; ids.add(s.id); }
  return seats.slice();
}

// ---- Replayed figures -----------------------------------------------------------------------------------------------------------------
// `read` is the slot's accountOrder (cash basis: realised result, plus dollars still open counted as lost). Without it nothing can be judged, so the check refuses.
const orderTime = (t) => { const s = num(t && t.settledAt); if (Number.isFinite(s)) return s; return num(t && t.ts); };
const entryTime = (t) => num(t && t.ts);
// Dollars to the bottom of a window: realised net plus open cost counted as lost, of orders entered at or after `from`. An order with no readable time counts in every window (fail closed).
function windowNet(orders, read, from) {
  let sum = 0;
  for (const t of orders) {
    const a = read(t);
    if (!a || !a.counted) continue;
    const ts = entryTime(t);
    if (Number.isFinite(ts) && ts < from) continue;
    sum += (a.net || 0) - (a.openCost || 0);
  }
  return sum;
}
const mineOf = (orders, id) => orders.filter((t) => t && t.strategy === "SLOT" && t.slotId === id);
// The PF cut: of the seat's own final cash results since its reviewedAt, the last 100 have profit factor under 0.8. Needs all 100.
function activityCut(seat, orders, read) {
  const re = Date.parse(seat.reviewedAt + "T00:00:00Z");
  const fin = mineOf(orders, seat.id).map((t) => ({ t, a: read(t), at: orderTime(t) }))
    .filter((x) => x.a && x.a.counted && x.a.final && !(x.t.settled === true && x.t.result === "hand") && (!Number.isFinite(re) || !(x.at < re)))
    .sort((x, y) => (x.at || 0) - (y.at || 0)).slice(-ACTIVITY_CUT_FILLS);
  if (fin.length < ACTIVITY_CUT_FILLS) return { cut: false, fills: fin.length, pf: null };
  let w = 0, l = 0;
  for (const x of fin) { if (x.a.net > 0) w += x.a.net; else l += -x.a.net; }
  const pf = l > 0 ? w / l : (w > 0 ? Infinity : 1);
  return { cut: pf < ACTIVITY_CUT_PF - 1e-12, fills: fin.length, pf };
}
// How many of the seat's orders were entered today (Central): the minimum-activity check ("fired today").
function activityFiredToday(seatId, orders, now) {
  const from = centralDayStart(now);
  if (!isNum(from)) return 0;
  return mineOf(Array.isArray(orders) ? orders : [], seatId).filter((t) => { const a = num(t.fillCount); const ts = entryTime(t); return Number.isFinite(ts) && ts >= from && (a > 0 || t.status === "filled"); }).length;
}

// ---- The gate -------------------------------------------------------------------------------------------------------------------------
// input: { seatId, count, limit, slotOrders, now, read, seats }. `seats` exists for tests; production passes none.
// { applies:false } when seatId is not an active activity seat (the engine then does nothing extra). Otherwise { applies:true, allowed, reason }. Fails closed on any missing input.
function activityOrderCheck(input) {
  const i = input || {};
  const seats = activeActivitySeats(i.seats);
  const seat = seats.find((s) => s.id === i.seatId);
  if (!seat) return { applies: false, allowed: true, reason: "" };
  const no = (reason) => ({ applies: true, allowed: false, reason });
  if (typeof i.read !== "function" || !Array.isArray(i.slotOrders) || !isNum(i.now)) return no("activity seat caps cannot be checked: orders, clock or reader missing");
  if (!(Number.isInteger(i.count) && i.count >= 1 && i.count <= ACTIVITY_CONTRACTS)) return no("an activity seat order is 1 to " + ACTIVITY_CONTRACTS + " contracts");
  if (!isNum(i.limit) || i.limit >= ACTIVITY_PRICE_CEILING - 1e-9 || i.limit <= 0) return no("an activity seat may not buy at 88c or above");
  const cost = i.limit * i.count + fee(i.limit, i.count);
  if (cost > ACTIVITY_MAX_ORDER_COST + 1e-9) return no("an activity order may cost at most $" + ACTIVITY_MAX_ORDER_COST);
  const orders = i.slotOrders;
  const cut = activityCut(seat, orders, i.read);
  if (cut.cut) return no("cut: the last " + ACTIVITY_CUT_FILLS + " settled fills have profit factor under " + ACTIVITY_CUT_PF + "; only a reviewed edit returns it");
  const dayFrom = centralDayStart(i.now), weekFrom = centralWeekStart(i.now);
  if (!isNum(dayFrom) || !isNum(weekFrom)) return no("no usable Central time");
  const mine = mineOf(orders, seat.id);
  if (windowNet(mine, i.read, dayFrom) - cost < -ACTIVITY_SEAT_DAILY_LOSS - 1e-9) return no("the seat's daily loss cap ($" + ACTIVITY_SEAT_DAILY_LOSS + ") would be passed");
  if (windowNet(mine, i.read, weekFrom) - cost < -ACTIVITY_SEAT_WEEKLY_LOSS - 1e-9) return no("the seat's weekly loss cap ($" + ACTIVITY_SEAT_WEEKLY_LOSS + ") would be passed; it resumes Monday 00:00 Central");
  const ids = new Set(seats.map((s) => s.id));
  const all = orders.filter((t) => t && t.strategy === "SLOT" && ids.has(t.slotId));
  if (windowNet(all, i.read, weekFrom) - cost < -ACTIVITY_SHARED_WEEKLY_LOSS - 1e-9) return no("the shared weekly loss cap for all activity seats ($" + ACTIVITY_SHARED_WEEKLY_LOSS + ") would be passed; every activity seat resumes Monday 00:00 Central");
  return { applies: true, allowed: true, reason: "" };
}

module.exports = {
  ACTIVITY_LABEL, ACTIVITY_SEATS, ACTIVITY_MAX_SEATS, ACTIVITY_CONTRACTS, ACTIVITY_MAX_ORDER_COST, ACTIVITY_PRICE_CEILING, ACTIVITY_SEAT_DAILY_LOSS, ACTIVITY_SEAT_WEEKLY_LOSS,
  ACTIVITY_SHARED_WEEKLY_LOSS, ACTIVITY_CUT_FILLS, ACTIVITY_CUT_PF, ACTIVITY_DECLINED_FAMILIES,
  fee, centralDayStart, centralWeekStart, validateActivitySeat, activeActivitySeats, activityCut, activityFiredToday, activityOrderCheck,
};
