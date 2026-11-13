"use strict";
// ROTATION CONTROLLER, REPLAY-ONLY DRY RUN (Nov 13, 2026). STATUS: replay-only, not wired, not live.
// Piece D of docs/ROTATION_LANE.md (v1.3). Given shadow rows and rule definitions it REPLAYS the lane's written rules (section 4 block counting with the rulings (a) to (u),
// sections 5 and 5a seats, 6 leaving, 7 cooling and return, 8 the total at risk) and returns a decision log. It places no order, makes no network call, reads no Firestore,
// writes nothing, reads no clock (the caller always gives a stated nowMs) and has no randomness. It requires nothing at all. Nothing under functions/ or index.html imports it
// (test/rotationReplayGates.test.js RR-ISO). Making it live would be a separate reviewed change with the Chief of Staff's security review (lane section 13).
//
// ROW SHAPE (kalshiShadowRows plus the second look of lane section 4): { rule, ticker, series?, side: "yes"|"no", price (the ask touched, dollars), size, wouldFill, atMs (decision time on
// the clock of ruling (f)), secondsLeft, result, won, pnl (cash dollars at the wheel's size), fee (dollars), settled, void?, secondLookAtMs?, secondLookFill?, limitCents?, live? }.
//
// AMBIGUITIES left open by the lane text, and the reading chosen here (each is also listed in the builder's report):
//  A1. A row's `pnl` is taken as the cash dollars of the wheel's size already (fee included); the library does not rescale one contract to 10. Cents = floor(100*pnl + 1e-6), ruling (g).
//  A2. A void has no pnl: its cents are minus its fee rounded UP to the cent (toward the worse result). It is in n and the day count, in L, and neither a win nor a loss for the rarer count (n).
//  A3. "wouldFill: false" is a miss and a row with no secondLookAtMs is "not fill-checked"; both are skipped under (m). A row's second look must come strictly after the decision.
//  A4. The signal's limit in whole cents is limitCents if given, else round(100*price)+1 (the touch plus 1c, section 4 and ruling (i)).
//  A5. Both a rule without the favourites class and a favourites class rule use ONE minimum (60 or 150); `rule.minSignals` can only RAISE it, never lower it.
//  A6. The probation kill: section 5a.4 says a drawdown of $18 from the seat's own peak; 4a says the BUILT slot uses a net floor of minus $18. The replay now DEFAULTS to the built behaviour
//      (net floor, 4a) and says so in the log header; opts.probationKill = "drawdown" (5a.4) selects the rule text. An OWNER DECISION: which one the lane means.
//  A7. "Net under minus 1c a contract at the 50th fill" is read as: total cash cents at the 50th filled order < -(1 x contracts x 50), checked once, at that fill.
//  A8. "At every 60th fill, the last 60 under 1.0" is read as gross wins W < gross losses L over those 60 (so W=0 with L>0 is under, L=0 is not).
//  A9. The live-against-shadow check (6.4) runs when the 20th live ORDER (filled or not) is recorded: fewer than 60 percent filled, or the sum of (fill cents - shadow cents) over filled orders
//      greater than the number of filled orders (average more than 1c worse), is a KILL.
//  A10. A performance exit's new block (7.1) counts signals decided after the exit time; the 14 days only gate WHEN the seat may be retaken, not which signals count.
//  A11. A third exit means a third exit or kill in the place's history; at most 2 automatic returns, counted from the history given by the caller.
//  A12. Section 8 is exact arithmetic on stated caps. The sizing base is a parameter in cents; no account figure is stored here.
//  A13. A rule's seat conflict (4.7) is a string key (market|side|minute) that the caller puts in rule.collisionKey and ctx.liveKeys; the library only compares them.
//  A15. Ruling (s): rows are one signal per rule, ticker (the market instance) and side; later rows of the same key are repeats of the same signal and are dropped AFTER the other filters (the earliest counted row stays).
//  A16. The replay honours its stated nowMs: a row decided after it, a second look after it, or a result not settled by it (settledAtMs, else closeMs) is treated as not yet there / open.
//  A17. secondLookMaxMs is clamped to 4000 (fast logs) or 6000 (slow logs, 6000 or more); any other value is the stricter 4000.
//  A14. Full seats need ctx.premiseRead (9.5); probation seats do not (the lane's opening paragraph). Both need the owner's popup (rule.ownerAdmitted), the controller review and the caps check.

// ---- constants, each with its section ---------------------------------------------------------------------------------------------------------------------------------
const DAY_MS = 24 * 3600 * 1000;
const BLOCK_WINDOW_MS = 21 * DAY_MS;      // section 4 line 1 and rulings (b), (k): a block is complete within 21 x 24 hours of its first signal
const BLOCK_MIN_SIGNALS = 60;             // 4 line 1
const FAV_MIN_SIGNALS = 150;              // 4 line 3 and section 0.8: a rule that buys at 88c or above
const BLOCK_MIN_DAYS = 7;                 // 4 line 1: at least 7 different US Central days (ruling (d))
const RARER_MIN = 10;                     // 4 line 3
const FAV_LIMIT_CENTS = 88;               // 4 line 3, ruling (i)
const BAR_PF_NUM = 13, BAR_PF_DEN = 10;   // 4 line 2: 1.3 as 10W >= 13L, whole cents (ruling (g))
const CONFIRM_SIGNALS = 30;               // 4 line 5, ruling (j)
const SECOND_LOOK_FAST_MS = 4000;         // 4 "The record" and (o): R6 and the wheel book recorder
const SECOND_LOOK_SLOW_MS = 6000;         // 4 variant for slower logs (NC15), ruling (f)
const TOL_SEC = 1e-9;                     // (f) tolerance on the second-look gap
const NC15_START_ISO = "2026-11-13T02:40:00Z"; // WHEEL_ADMIT_LIST.md, start of the forward count for the 7 NC15 places (ruling (l))
const FULL_CONTRACTS = 10, FULL_ORDER_CENTS = 1000;     // 5.1 and 0.3
const PROBATION_CONTRACTS = 3, PROBATION_ORDER_CENTS = 300; // 5a.1
const PROBATION_SEATS_MAX = 5;            // 5a.1
const FULL_KILL_CENTS = 6000;             // 6.1: $60 drawdown from the rule's own peak
const PROBATION_KILL_CENTS = 1800;        // 5a.4: $18
const EXIT50_FILLS = 50, EXIT50_MIN_CENTS_PER_CONTRACT = -1; // 6.2
const EXIT60_EVERY = 60;                  // 6.3
const LIVE_CHECK_ORDERS = 20, LIVE_CHECK_MIN_FILL_NUM = 6, LIVE_CHECK_MIN_FILL_DEN = 10, LIVE_CHECK_SLIP_CENTS = 1; // 5.2 and 6.4
const COOL_MS = 14 * DAY_MS;              // 7.1
const MAX_AUTO_RETURNS = 2;               // 7.1 and 0.5
const EXITS_FOR_OWNER = 3;                // 7.3
const REARM_AFTER_KILL_MS = 30 * DAY_MS;  // 7.2
const ALERT_PF60 = 0.7, ALERT_EARLY_SELLS = 3, ALERT_EARLY_WINDOW = 40; // 6 alerts only
const LUCKY_RATE = 0.04, LUCKY_RATE_FAV = 0.05; // 9.2
// Slot caps today (5.1): fractions of the sizing base with fixed ceilings, in cents.
// COPIED from the slot library file (SLOT_CAP_FRACTIONS and SLOT_CAP_CEILINGS in dollars, here in cents). This module requires nothing, so a drift gate in the TEST compares them (RR_CAPS).
const SLOT_CAPS = Object.freeze({ order: [0.025, 2000], window: [0.04, 4000], open: [0.05, 6000], day: [0.025, 2000], lifetime: [0.075, 6000] });
const ACCOUNT_STOP_FRACTION = 0.12;       // 8.2 the shared 12 percent account stop

// ---- small pure helpers -----------------------------------------------------------------------------------------------------------------------------------------------
const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const centsOf = (dollars) => Math.floor(100 * dollars + 1e-6);              // ruling (g), the one expression every build uses
const feeCentsUp = (fee) => Math.ceil(100 * (isNum(fee) ? fee : 0) - 1e-6);  // A2
const sideRank = (s) => (s === "yes" ? 0 : 1);
let _fmt = null;
function centralDay(ms) { // ruling (d): America/Chicago calendar day, daylight saving followed
  if (!_fmt) _fmt = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Chicago", year: "numeric", month: "2-digit", day: "2-digit" });
  return _fmt.format(new Date(ms));
}
const placeKey = (rule) => rule.id + "|" + rule.market;
const rowMarket = (r) => (r.series ? String(r.series) : String(r.ticker || "").split("-")[0]);
const limitCentsOf = (r) => (isNum(r.limitCents) ? r.limitCents : Math.round(100 * r.price) + 1);

// A rule's class comes from its REGISTERED band, never from fills (ruling (i)). Band is the range of limits it allows, in whole cents.
function classOf(rule) {
  const lo = rule.bandLoCents, hi = rule.bandHiCents;
  const favourites = !!rule.favourites;
  const needWins = hi <= 50 || (lo <= 50 && hi > 50);
  const needLosses = lo > 50 || (lo <= 50 && hi > 50);
  const base = favourites ? FAV_MIN_SIGNALS : BLOCK_MIN_SIGNALS;
  return { favourites, needWins, needLosses, minSignals: Math.max(base, isNum(rule.minSignals) ? rule.minSignals : 0) };
}

// Is the row fill-checked? A3, ruling (o) and the variant for slower logs. `live` rows (a seat's own fills) are fill-checked by nature.
function fillChecked(rule, r) {
  if (r.live === true) return true;
  if (r.wouldFill === false) return false;
  if (!isNum(r.secondLookAtMs) || r.secondLookFill !== true) return false;
  const maxMs = isNum(rule.secondLookMaxMs) && rule.secondLookMaxMs >= SECOND_LOOK_SLOW_MS ? SECOND_LOOK_SLOW_MS : SECOND_LOOK_FAST_MS; // A17
  const gap = r.secondLookAtMs - r.atMs;
  return gap > 0 && gap / 1000 <= maxMs / 1000 + TOL_SEC;
}

// Counted signals of one place, ordered by (p): decision time, ticker ascending, side yes before no.
function countedSignals(rule, rows, opts) {
  const cls = classOf(rule);
  const startMs = Math.max(isNum(rule.startMs) ? rule.startMs : 0, opts && isNum(opts.afterMs) ? opts.afterMs + 1 : 0); // (l); A10 for a return block
  const out = [];
  const hasNow = !!opts && isNum(opts.nowMs);
  for (const r of rows || []) {
    if (r.rule !== rule.id || rowMarket(r) !== rule.market) continue;
    if (!isNum(r.atMs) || r.atMs < startMs) continue;                                  // (l)
    if (hasNow && r.atMs > opts.nowMs) continue;                                       // A16: not decided yet at the stated now
    if (!fillChecked(rule, r)) continue;                                               // (m)
    if (hasNow && r.live !== true && isNum(r.secondLookAtMs) && r.secondLookAtMs > opts.nowMs) continue; // A16
    if (!cls.favourites && limitCentsOf(r) >= FAV_LIMIT_CENTS) continue;               // (i) skipped, not counted
    const isVoid = r.void === true;
    const settledBy = isNum(r.settledAtMs) ? r.settledAtMs : isNum(r.closeMs) ? r.closeMs : null;
    const knownByNow = !hasNow || settledBy === null || settledBy <= opts.nowMs;                // A16
    const final = knownByNow && (isVoid || (r.settled === true && isNum(r.pnl)));
    out.push({ atMs: r.atMs, ticker: String(r.ticker || ""), side: r.side, void: isVoid, final,
      cents: !final ? 0 : isVoid ? -feeCentsUp(r.fee) : centsOf(r.pnl), day: centralDay(r.atMs) });
  }
  out.sort((a, b) => a.atMs - b.atMs || (a.ticker < b.ticker ? -1 : a.ticker > b.ticker ? 1 : 0) || sideRank(a.side) - sideRank(b.side));
  const seen = new Set(), uniq = [];                                                   // ruling (s), A15
  for (const s of out) { const k = rule.id + "|" + s.ticker + "|" + s.side; if (seen.has(k)) continue; seen.add(k); uniq.push(s); }
  return uniq;
}

const tally = (list) => { let W = 0, L = 0, w = 0, l = 0; for (const s of list) { if (s.cents > 0) { W += s.cents; if (!s.void) w++; } else if (s.cents < 0) { L -= s.cents; if (!s.void) l++; } } return { W, L, wins: w, losses: l, n: list.length }; };
const passesPF = (t) => t.W > 0 && BAR_PF_DEN * t.W >= BAR_PF_NUM * t.L;   // 4 line 2 and (g): no float
const passesOne = (t) => t.W > 0 && t.W >= t.L;                             // 1.0 or better, W = 0 fails

// The three counts of ruling (a) hold together.
function countsHold(cls, list, daySet) {
  const t = tally(list);
  return list.length >= cls.minSignals && daySet.size >= BLOCK_MIN_DAYS && (!cls.needWins || t.wins >= RARER_MIN) && (!cls.needLosses || t.losses >= RARER_MIN);
}

// Section 4, one place. Returns { status, blocks, events, nextStartIndex }. `nowMs` is always stated by the caller (k).
// status: COLLECTING | WAITING_RESULTS | CONFIRMING | QUALIFIED.
function readPlace(rule, rows, nowMs, opts) {
  const cls = classOf(rule);
  const sigs = countedSignals(rule, rows, Object.assign({}, opts, { nowMs }));
  const events = [], blocks = [];
  let status = "COLLECTING";
  let i = 0;
  while (i < sigs.length) {
    const first = sigs[i], limit = first.atMs + BLOCK_WINDOW_MS;
    const list = [], days = new Set();
    let complete = -1, blocked = false, k = i;
    for (; k < sigs.length; k++) {
      const s = sigs[k];
      if (s.atMs > limit) break;
      if (!s.final) { blocked = true; break; }       // (r) an open result stops the search
      list.push(s); days.add(s.day);
      if (countsHold(cls, list, days)) { complete = k; break; }
    }
    if (complete < 0) {
      if (blocked) { status = "WAITING_RESULTS"; events.push({ atMs: nowMs, kind: "BLOCK_WAITING_RESULTS", startAtMs: first.atMs }); break; } // (q)
      if (k < sigs.length || nowMs > limit) {        // (k) EXPIRED by the clock, all signals up to the limit are final
        blocks.push({ result: "EXPIRED", firstAtMs: first.atMs, n: list.length });
        events.push({ atMs: limit, kind: "BLOCK_EXPIRED", startAtMs: first.atMs, n: list.length });
        let j = i; while (j < sigs.length && sigs[j].atMs <= limit) j++; // (t): next block starts at the first counted signal after the expiry time
        i = j; continue;
      }
      status = "COLLECTING"; break;
    }
    const n = list.length, h = Math.floor(n / 2);   // (e)
    const t = tally(list), t1 = tally(list.slice(0, h)), t2 = tally(list.slice(h));
    const pass = passesPF(t) && passesOne(t1) && passesOne(t2);
    const last = sigs[complete];
    const rec = { result: pass ? "CLEARED" : "FAILED", firstAtMs: first.atMs, lastAtMs: last.atMs, n, W: t.W, L: t.L, days: days.size };
    blocks.push(rec);
    events.push({ atMs: last.atMs, kind: pass ? "BLOCK_CLEARED" : "BLOCK_FAILED", startAtMs: first.atMs, n, W: t.W, L: t.L, days: days.size });
    if (!pass) { i = complete + 1; continue; }       // 4 line 4: blocks never overlap
    // Confirmation (j): the next 30 counted signals, complete within 21 x 24 hours of the block's last signal.
    const c0 = complete + 1, climit = last.atMs + BLOCK_WINDOW_MS;
    const conf = []; let cblocked = false, ck = c0;
    for (; ck < sigs.length && conf.length < CONFIRM_SIGNALS; ck++) {
      const s = sigs[ck];
      if (s.atMs > climit) break;
      if (!s.final) { cblocked = true; break; }
      conf.push(s);
    }
    if (conf.length === CONFIRM_SIGNALS) {
      const ct = tally(conf), ok = passesOne(ct);
      blocks.push({ result: ok ? "CONFIRMED" : "CONFIRMATION_FAILED", n: CONFIRM_SIGNALS, W: ct.W, L: ct.L });
      events.push({ atMs: conf[conf.length - 1].atMs, kind: ok ? "CONFIRMED_QUALIFIED" : "CONFIRMATION_FAILED", W: ct.W, L: ct.L });
      if (ok) { status = "QUALIFIED"; break; }       // (t) no further block is read for that place
      i = c0 + CONFIRM_SIGNALS; continue;            // (j) its signals never count toward any block
    }
    if (cblocked) { status = "WAITING_RESULTS"; events.push({ atMs: nowMs, kind: "CONFIRMATION_WAITING_RESULTS" }); break; }
    if (ck < sigs.length || nowMs > climit) {
      blocks.push({ result: "CONFIRMATION_EXPIRED", n: conf.length });
      events.push({ atMs: climit, kind: "CONFIRMATION_EXPIRED", n: conf.length });
      let j = c0; while (j < sigs.length && sigs[j].atMs <= climit) j++;
      i = j; continue;
    }
    status = "CONFIRMING"; break;
  }
  return { status, blocks, events, signalsCounted: sigs.length };
}

// ---- seats (sections 5, 5a) --------------------------------------------------------------------------------------------------------------------------------------------
// ctx: { premiseRead, controllerReviewed, capsChecked, liveKeys: [], probationSeatsTaken, coolingUntilMs?, killed? }
function seatDecision(rule, place, ctx) {
  const c = ctx || {};
  const no = (reason) => ({ seat: "none", contracts: 0, maxOrderCents: 0, reason });
  if (rule.declined || rule.closed) return no("declined or closed rule (1.2, 5a.2)");
  if (c.killed) return no("killed: only a reviewed re-arm returns it (7.2)");
  if (isNum(c.coolingUntilMs) && c.coolingUntilMs > (c.nowMs || 0)) return no("cooling (7.1)");
  if (!rule.ownerAdmitted) return no("no owner popup for this exact spec (1.4)");
  if (!c.controllerReviewed || !c.capsChecked) return no("controller not reviewed or slot caps not checked (opening paragraph)");
  if (rule.collisionKey && Array.isArray(c.liveKeys) && c.liveKeys.includes(rule.collisionKey)) return no("same market, side and minute as a live strategy (4.7)");
  if (place && place.status === "QUALIFIED") {
    if (!c.premiseRead) return no("premise test WHEEL0 not read (9.5)");
    return { seat: "full", contracts: FULL_CONTRACTS, maxOrderCents: FULL_ORDER_CENTS, reason: "qualified record (4.5, 5.1)" };
  }
  // Probation (5a): no forward record needed.
  if (classOf(rule).favourites) return no("favourites at 88c or above take no probation seat (5a.2)");
  if (!rule.registered) return no("no written registration (5a.2)");
  if (isNum(rule.researchRead) && rule.researchRead < 1.0) return no("registered research read under 1.0 (5a.2)");
  if ((c.probationSeatsTaken || 0) >= PROBATION_SEATS_MAX) return no("five probation seats are taken (5a.1)");
  return { seat: "probation", contracts: PROBATION_CONTRACTS, maxOrderCents: PROBATION_ORDER_CENTS, reason: "probation, no record (5a)" };
}

// Probation steps up only on the full record counted on its OWN live fills (5a.5): a live-mode readPlace.
function stepUpDecision(rule, liveRows, nowMs) {
  const r = readPlace(rule, (liveRows || []).map((x) => Object.assign({}, x, { live: true })), nowMs, {});
  return { stepUp: r.status === "QUALIFIED", status: r.status };
}

// ---- leaving a seat (section 6), replayed from the seat's own orders on the cash basis -----------------------------------------------------------------------------------
// orders: [{ atMs, filled (bool), pnl (cash dollars, for a filled order that settled), fillCents?, shadowCents?, earlySell? }]
function replaySeat(seatKind, orders, opts) {
  const o = opts || {};
  const full = seatKind === "full";
  const killCents = full ? FULL_KILL_CENTS : PROBATION_KILL_CENTS;
  const contracts = full ? FULL_CONTRACTS : PROBATION_CONTRACTS;
  const sorted = (orders || []).slice().sort((a, b) => a.atMs - b.atMs);
  const events = [];
  let cum = 0, peak = 0, fills = 0, seen = 0, filledSeen = 0, slip = 0, missing = false;
  const cents = [];
  for (const ord of sorted) {
    seen++;
    if (ord.filled) { filledSeen++; if (isNum(ord.fillCents) && isNum(ord.shadowCents)) slip += ord.fillCents - ord.shadowCents; else missing = true; }
    if (seen === LIVE_CHECK_ORDERS) {              // 5.2, 6.4, A9
      const slow = LIVE_CHECK_MIN_FILL_DEN * filledSeen < LIVE_CHECK_MIN_FILL_NUM * LIVE_CHECK_ORDERS;
      const bad = missing || slip > LIVE_CHECK_SLIP_CENTS * filledSeen; // A9: a missing fill or shadow price fails closed
      if (slow || bad) { events.push({ atMs: ord.atMs, kind: "KILL", reason: missing ? "live against shadow (6.4): fill or shadow price missing, failed closed" : "live against shadow (6.4)", latched: true }); return { events, ended: true }; }
    }
    if (!ord.filled || !isNum(ord.pnl)) continue;
    const c = centsOf(ord.pnl); fills++; cents.push(c); cum += c; if (cum > peak) peak = cum;
    const dd = (full || o.probationKill === "drawdown") ? peak - cum : -cum; // A6: probation defaults to the built net floor
    if (dd >= killCents) { events.push({ atMs: ord.atMs, kind: "KILL", reason: (full ? "$60" : "$18") + " drawdown (6.1, 5a.4)", latched: true, fills }); return { events, ended: true }; }
    if (fills === EXIT50_FILLS && cum < EXIT50_MIN_CENTS_PER_CONTRACT * contracts * EXIT50_FILLS) { events.push({ atMs: ord.atMs, kind: "EXIT", reason: "net under minus 1c a contract at 50 fills (6.2)", fills }); return { events, ended: true }; }
    if (fills % EXIT60_EVERY === 0) {
      const t = tally(cents.slice(-EXIT60_EVERY).map((x) => ({ cents: x })));
      if (t.W < t.L) { events.push({ atMs: ord.atMs, kind: "EXIT", reason: "last 60 fills under 1.0 (6.3)", fills }); return { events, ended: true }; }
    }
  }
  return { events, ended: false };
}

// Alerts only, never an exit (section 6, last paragraph).
function alertsFor(cashCentsList, earlySellFlags) {
  const out = [];
  if (cashCentsList.length >= 60) { const t = tally(cashCentsList.slice(-60).map((x) => ({ cents: x }))); if (t.L > 0 && t.W < ALERT_PF60 * t.L) out.push("rolling 60 fill profit factor under 0.7"); }
  if (earlySellFlags && earlySellFlags.length >= ALERT_EARLY_WINDOW && earlySellFlags.slice(-ALERT_EARLY_WINDOW).filter(Boolean).length >= ALERT_EARLY_SELLS) out.push("3 early sells in the last 40");
  return out;
}

// ---- cooling and return (section 7) --------------------------------------------------------------------------------------------------------------------------------------
// history: [{ type: "exit"|"kill", atMs, returned?: bool }] oldest first. Rows are the place's shadow rows (fill-checked by readPlace).
function returnDecision(rule, history, rows, nowMs, opts) {
  const h = history || [], o = opts || {};
  if (!h.length) return { allowed: false, reason: "no exit to return from" };
  const lastEv = h[h.length - 1];
  if (h.some((x) => x.type === "kill")) {            // 7.2 never automatic after a kill
    const ready = nowMs >= lastEv.atMs + REARM_AFTER_KILL_MS;
    const rec = readPlace(rule, rows, nowMs, { afterMs: lastEv.atMs });
    return { allowed: false, needsOwner: true, reason: "after a kill only a reviewed re-arm: 30 days, a fresh block and confirmation, the owner's popup (7.2)", rearmWindowPassed: ready, freshRecord: rec.status === "QUALIFIED" };
  }
  const returns = h.filter((x) => x.returned).length;
  if (h.length >= EXITS_FOR_OWNER || returns >= MAX_AUTO_RETURNS) return { allowed: false, needsOwner: true, reason: "a third exit, or two automatic returns used: the owner's popup (7.1, 7.3)" };
  const coolEnd = lastEv.atMs + COOL_MS;
  if (nowMs < coolEnd) return { allowed: false, reason: "cooling until " + coolEnd + " (7.1)", coolEndMs: coolEnd };
  const rec = readPlace(rule, rows, nowMs, { afterMs: lastEv.atMs });  // A10
  if (rec.status !== "QUALIFIED") return { allowed: false, reason: "no fresh block and confirmation yet (7.1)", status: rec.status };
  return { allowed: true, reason: "14 days out and a fresh qualified record (7.1)", returnNumber: returns + 1 };
}

// ---- the total at risk (section 8), exact arithmetic ----------------------------------------------------------------------------------------------------------------------------
function slotCaps(baseCents) {
  const b = isNum(baseCents) && baseCents > 0 ? baseCents : 0;
  const out = {};
  for (const k of Object.keys(SLOT_CAPS)) out[k] = Math.min(Math.floor(SLOT_CAPS[k][0] * b), SLOT_CAPS[k][1]);
  return out;
}
const orderAllowed = (orderCostCents, baseCents) => orderCostCents <= slotCaps(baseCents).order && orderCostCents > 0;   // 5.1: a $10 order needs a base of $1,000
function totalAtRisk(seats, baseCents) {
  const caps = slotCaps(baseCents);
  const list = (seats || []).map((s) => (s === "full" ? "full" : "probation"));
  let killSum = 0, dayBound = 0, openBound = 0;
  for (const s of list) {
    const kill = s === "full" ? FULL_KILL_CENTS : PROBATION_KILL_CENTS;
    killSum += Math.min(kill, caps.lifetime > 0 ? caps.lifetime : 0);       // 5.1: the lifetime cap stops a rule before a kill line it exceeds
    dayBound += Math.min(caps.day, kill);
    openBound += Math.min(caps.open, s === "full" ? FULL_ORDER_CENTS : PROBATION_ORDER_CENTS);
  }
  const accountStop = Math.floor(ACCOUNT_STOP_FRACTION * (isNum(baseCents) && baseCents > 0 ? baseCents : 0));
  return { seats: list.length, caps, lifetimeKillSum: killSum, dailyBoundBySlotCaps: dayBound, dailyBound: Math.min(dayBound, accountStop), openBound, accountStop,
    stopBinds: dayBound > accountStop }; // 8.3: the shared stop is the only hard daily bound across seats
}
const luckyClears = (blocksRead, favourite) => blocksRead * (favourite ? LUCKY_RATE_FAV : LUCKY_RATE);   // 9.2

// ---- the replay -----------------------------------------------------------------------------------------------------------------------------------------------------------------
// input: { rules: [...], rows: [...], liveOrders?: { "<place key>": [...] }, nowMs, ctx? }. Returns { log, places }. Same input, same output.
function replay(input) {
  const inp = input || {};
  if (!isNum(inp.nowMs)) throw new Error("replay needs a stated nowMs");
  const nowMs = inp.nowMs, ctxIn = inp.ctx || {};
  const rules = (inp.rules || []).slice().sort((a, b) => (placeKey(a) < placeKey(b) ? -1 : placeKey(a) > placeKey(b) ? 1 : 0));
  const probationKill = inp.probationKill === "drawdown" ? "drawdown" : "net_floor"; // A6
  const log = [], places = {};
  let probation = ctxIn.probationSeatsTaken || 0;
  for (const rule of rules) {
    const key = placeKey(rule);
    const rec = readPlace(rule, inp.rows, nowMs, {});
    for (const e of rec.events) log.push(Object.assign({ place: key }, e));
    const live = (inp.liveOrders && inp.liveOrders[key]) || [];
    const ctx = Object.assign({}, ctxIn, { nowMs, probationSeatsTaken: probation });
    let seat = seatDecision(rule, rec, ctx);
    let seatEvents = [], ended = false;
    if (live.length && seat.seat !== "none") {
      const rs = replaySeat(seat.seat, live, { probationKill });
      ended = rs.ended;
      seatEvents = rs.events;
      for (const e of rs.events) log.push(Object.assign({ place: key }, e));
      if (ended) log.push({ atMs: rs.events[rs.events.length - 1].atMs, place: key, kind: "SEAT_ENDED", seatState: "ended", by: rs.events[rs.events.length - 1].kind });
    }
    if (seat.seat === "probation" && !ended) probation++;
    log.push({ atMs: nowMs, place: key, kind: "SEAT_DECISION", seat: seat.seat, contracts: seat.contracts, reason: seat.reason, status: rec.status });
    places[key] = { status: rec.status, blocks: rec.blocks, seat: ended ? "ended" : seat.seat, seatState: ended ? "ended" : seat.seat === "none" ? "none" : "open", seatEvents };
  }
  log.sort((a, b) => a.atMs - b.atMs || (a.place < b.place ? -1 : a.place > b.place ? 1 : 0));
  log.unshift({ atMs: nowMs, kind: "HEADER", lane: "ROTATION_LANE v1.3", probationKill, nowMs, scope: "sections 4 to 6 plus the seat decision; sections 7 and 8 are exported pure functions only" });
  return { log, places };
}

module.exports = {
  NC15_START_ISO, BLOCK_WINDOW_MS, DAY_MS, SLOT_CAPS, FULL_KILL_CENTS, PROBATION_KILL_CENTS, ACCOUNT_STOP_FRACTION,
  centsOf, centralDay, classOf, fillChecked, countedSignals, readPlace, seatDecision, stepUpDecision, replaySeat, alertsFor, returnDecision,
  slotCaps, orderAllowed, totalAtRisk, luckyClears, replay, placeKey,
};
