"use strict";
// Hard account stop (the owner, Nov 13, 2026, on the Risk Analyst's design: "Yes, add it in code"). Full definition, tradeoffs and deploy order: docs/HARD_ACCOUNT_STOP.md.
//
// One sentence: when the bot's cumulative CASH TRADING RESULT (every settled or sold order, L1 and the second strategy, booked on the cash basis the other stops use) falls 40% of the account's
// trading capital below its own peak, ALL new buys stop and stay stopped until the owner restarts them by a reviewed code edit. Exits are never gated.
//
// It is a CEILING on top of the 12% 24 hour stop, not a replacement. It is the same shape as the gold kill latch (kalshiGoldKillLib.js): a small scheduled function (kalshiHardStopCheck, its
// own process, no Kalshi key, no order) REPLAYS the orders since HARD_STOP.rearmAt and caches the verdict as a `hardStop` field on the sizing document, which runL1Tick already receives. The
// tick and the slot tick only LOOK at that value (hardStopBlocks); they make no new read or write. Nothing stored, requested or typed on the page can raise or lower the line or clear the
// latch: the fraction and rearmAt are code constants, and a stored latch from before the code's rearmAt is the only thing ignored (that is how a reviewed edit re-arms).
//
// The measure is TRADING RESULTS, never the raw balance: a deposit is not a gain and a withdrawal is not a loss, because the balance is never read here. The denominator is the sizing base at
// the moment the result last made a new peak (the same `base` the bot sizes on, which already excludes savings); see the doc for why that and not the other candidates.

const HARD_STOP_FRACTION = 0.40;
const HARD_STOP_MIN_FRACTION = 0.20, HARD_STOP_MAX_FRACTION = 0.40;
const HARD_STOP = Object.freeze({
  fraction: HARD_STOP_FRACTION,
  // The start of the measured period. Orders before it are history: they set no peak and count toward nothing. Moving this to a later time is the ONLY way to re-arm after a trip (a
  // reviewed edit, with the owner's approval); the stored latch of an older generation is then ignored and the equity peak starts again from zero.
  rearmAt: Date.parse("2026-11-13T00:00:00Z"),
  staleMs: 15 * 60 * 1000,       // a record whose heartbeat is older than this is treated as "the checker is silent": fail closed
  heartbeatMs: 4 * 60 * 1000,    // the checker runs every 5 minutes, so every run is past this and refreshes the heartbeat; the 15 minute stale rule above allows two missed runs
});

// A line outside [0.20, 0.40] is never used as written: above 0.40 it is clamped to 0.40, and below 0.20 or not a number it falls to 0.20 (the tightest), so a bad edit can only make the stop
// stricter than the owner's 40%, never looser. A gate fails the build if the shipped constant is out of range; this never throws, because the exit watch loads this module too.
function validFraction(f) { return Number.isFinite(f) && f >= HARD_STOP_MIN_FRACTION && f <= HARD_STOP_MAX_FRACTION; }
function effectiveFraction(cfg = HARD_STOP) {
  const f = Number(cfg && cfg.fraction);
  if (!Number.isFinite(f)) return HARD_STOP_MIN_FRACTION;
  return Math.max(HARD_STOP_MIN_FRACTION, Math.min(HARD_STOP_MAX_FRACTION, f));
}

// Is the stored latch in force? Pure; takes the sizing document the tick already read. Only a record of this generation (rearmAt at or after the code's) can block.
function hardStopTripped(sizingState, cfg = HARD_STOP) {
  const h = sizingState && sizingState.hardStop;
  if (!h || typeof h !== "object" || h.tripped !== true) return false;
  return Number(h.rearmAt) >= cfg.rearmAt;
}

// The ONE question the ticks ask. blocked === true means: place no new order. Fails closed on everything, with one deliberate exception for time before the code's own start date:
//   - a stored latch of this generation blocks, whatever else it says (a latch never needs a fresh heartbeat);
//   - a record that is not an object, or says it could not read what it needs (status "unreadable"), blocks;
//   - a record of this generation whose heartbeat is missing or older than staleMs blocks (the checker went silent after it had run);
//   - an ABSENT field (never evaluated, the sizing document deleted, or the checker never deployed) blocks once now is at or after cfg.rearmAt, and an unreadable clock counts as after. Before rearmAt it does not,
//     which is what keeps the recorded replays (dated October 2026) byte identical. The deploy order in docs/HARD_ACCOUNT_STOP.md puts the checker first so this never blocks a healthy deploy.
// A record of an OLDER generation is ignored (a re-arm): the checker is about to write this generation's record, and an old latch is history.
function hardStopBlocks(sizingState, now, cfg = HARD_STOP) {
  const h = sizingState ? sizingState.hardStop : undefined;
  if (h === undefined || h === null) return !(now < cfg.rearmAt) ? { blocked: true, why: "not evaluated" } : { blocked: false, why: "before the start date" };
  if (typeof h !== "object") return { blocked: true, why: "the hard stop record is not readable" };
  if (!(Number(h.rearmAt) >= cfg.rearmAt)) return !(now < cfg.rearmAt) ? { blocked: true, why: "not evaluated for this generation" } : { blocked: false, why: "older generation" };
  if (h.tripped === true) return { blocked: true, why: "tripped" };
  if (h.status === "unreadable") return { blocked: true, why: "unreadable" };
  const at = Number(h.checkedAt);
  if (!Number.isFinite(at) || !Number.isFinite(now) || now - at > cfg.staleMs) return { blocked: true, why: "checker silent" };
  return { blocked: false, why: "ok" };
}

// One settled order as a cash result, or null when it is not a result (unfilled, still open, closed by hand). { unreadable: true } when it IS a result but cannot be priced: the
// caller then treats the whole evaluation as unreadable (fail closed), never as zero. L1 and second-strategy orders carry the same money fields and are read by one rule: the result stored when the
// order settled or was sold (the cash basis, since Nov 7, 2026), else derived the way the stops derive it (live.settledFields; an exit with no readable result books what was paid as lost).
function orderResult(t) {
  const live = require("./kalshiLiveLib");      // lazily: kalshiLiveLib requires this file
  if (!t || (t.strategy !== "L1" && !(t.strategy === "SLOT" && typeof t.slotId === "string"))) return null;
  const ts = Number(t.ts);
  if (!(Number(t.fillCount) > 0) || t.settled !== true || t.result === "hand") return null;
  const stored = t.settledPnl !== null && t.settledPnl !== undefined && t.settledPnl !== "" ? Number(t.settledPnl) : NaN;
  if (Number.isFinite(stored)) return { ts, pnl: stored };
  const want = Number(t.count) > 0 ? Number(t.count) : 1, got = Math.min(Number(t.fillCount), want);
  if (!Number.isFinite(Number(t.maxCost))) return { unreadable: true };
  if (t.result === "exit") return { ts, pnl: -(Number(t.maxCost) * (got / want)) };
  if (t.result !== "yes" && t.result !== "no") return null;
  const p = live.settledFields(t, t.result).settledPnl;
  return Number.isFinite(p) ? { ts, pnl: p } : { unreadable: true };
}

// Replay: the running cash result since rearmAt and its peak (the peak starts at zero, the result at the start). Orders are taken in the order they were placed (ts), which can differ from
// settlement order by a window or two; with a line of this size that cannot matter. Orders with an unreadable ts count as inside (fail closed).
function replay(orders, cfg = HARD_STOP) {
  const rows = [];
  let unreadable = 0;
  for (const t of orders || []) {
    const r = orderResult(t);
    if (r === null) continue;
    if (r.unreadable) { unreadable += 1; continue; }
    if (Number.isFinite(r.ts) && r.ts < cfg.rearmAt) continue;
    rows.push({ ts: Number.isFinite(r.ts) ? r.ts : cfg.rearmAt, pnl: r.pnl });
  }
  rows.sort((a, b) => a.ts - b.ts);
  let cum = 0, peak = 0;
  for (const r of rows) { cum += r.pnl; if (cum > peak) peak = cum; }
  return { unreadable, trades: rows.length, equity: cum, peak };
}

// The verdict. base: the sizing document's current base (what the bot sizes on). stored: the record from the sizing document (any generation). Pure.
// peakBase is the base in force when the result last made a new peak: it is kept while the peak stands and refreshed only when a higher peak is seen, so a later deposit cannot loosen the line and
// a later withdrawal or loss cannot tighten it (the line is "40% of the account when it was at its best"). A peak can only rise, even if the stored record is lost.
function judge({ ev, base, stored, cfg = HARD_STOP }) {
  if (ev.unreadable > 0) return { status: "unreadable", why: ev.unreadable + " settled order(s) could not be priced" };
  if (!Number.isFinite(base) || !(base > 0)) return { status: "unreadable", why: "the sizing base could not be read" };
  const sameGen = Boolean(stored && typeof stored === "object" && Number(stored.rearmAt) === cfg.rearmAt);
  const sPeakE = sameGen && Number.isFinite(Number(stored.peakEquity)) ? Number(stored.peakEquity) : null;
  const sPeakB = sameGen && Number.isFinite(Number(stored.peakBase)) && Number(stored.peakBase) > 0 ? Number(stored.peakBase) : null;
  const sMinB = sameGen && Number.isFinite(Number(stored.minBase)) && Number(stored.minBase) > 0 ? Number(stored.minBase) : null;
  // The smallest sizing base seen since rearmAt: the fail-closed fallback when the base at the peak is not on record (a tighter line, never a looser one).
  const minBase = sMinB === null ? base : Math.min(sMinB, base);
  const peakEquity = Math.max(ev.peak, sPeakE === null ? 0 : sPeakE);
  const newHigh = sPeakE === null || ev.peak > sPeakE + 1e-9;
  // A new high takes the base now. Otherwise the stored base at the peak stands; if it cannot be read, the smallest base seen is used instead.
  const peakBase = newHigh ? base : (sPeakB !== null ? sPeakB : minBase);
  const drawdown = peakEquity - ev.equity;
  const line = effectiveFraction(cfg) * peakBase;
  const trip = drawdown >= line - 1e-9;
  return { status: "ok", peakEquity, peakBase, minBase, equity: ev.equity, drawdown, line, trip, trades: ev.trades };
}

const money = (x) => "$" + Math.abs(x).toFixed(2);
function tripDetail(j, cfg = HARD_STOP) {
  return "the bot's cash trading result is " + money(j.drawdown) + " below its own peak, which reaches the " + Math.round(effectiveFraction(cfg) * 100) + "% line (" + money(j.line) + " of the " + money(j.peakBase) + " the account could size on at that peak)";
}

// The checker. All I/O is injected; every failure either leaves the stored record as it was or marks it unreadable (which BLOCKS), and a failed read never trips and never clears a latch.
// TWO records, one truth: the AUTHORITATIVE record (peak, peak base, the latch, whether the alert went out) lives in its own document (readState / writeState), which only this function writes, so the tick's
// full write of the sizing document can never erase the latch or reset the peak base. The sizing document carries a CACHE of it (`hardStop`, what the tick reads), rewritten whenever it is missing, differs or its
// heartbeat is due, so a cache the tick erased is back within a minute.
// Order of effects: the authoritative record first, then the cache, then the alert (retried on later minutes while the record says it has not gone out).
// io: { now, readL1Orders(since), readSlotOrders(since), readSizing() -> doc|null, readState() -> doc|null, writeState(obj) (merge), writeHardStop(obj) (merge into the sizing doc's hardStop),
//       claimAlert(rearmAt) -> true when this call took the once-per-generation claim, raiseAlert({at, rearmAt, ...}), releaseAlert(rearmAt) (puts the claim back when the alert write failed), endSession(why) -> true when it ended a running session, logEvent(e) }
async function runHardStopCheck(io, cfg = HARD_STOP) {
  const { now } = io;
  let l1, slot, sizing, state;
  const unreadable = async (why) => {
    // Fail closed: say so on the record the ticks already read. If even that write fails, the missing heartbeat blocks within staleMs.
    try { await io.writeHardStop({ rearmAt: cfg.rearmAt, status: "unreadable", checkedAt: now, why }); } catch (e2) { /* the stale heartbeat covers it */ }
    return { skipped: "unreadable" };
  };
  try { l1 = await io.readL1Orders(cfg.rearmAt); slot = await io.readSlotOrders(cfg.rearmAt); sizing = await io.readSizing(); state = await io.readState(); }
  catch (e) { return unreadable("orders or the stored records could not be read"); }
  if (!Array.isArray(l1) || !Array.isArray(slot)) return unreadable("an order list was not a list");
  const st = state && typeof state === "object" && Number(state.rearmAt) === cfg.rearmAt ? state : null;     // this generation's authoritative record, or none
  const cache = sizing && sizing.hardStop && typeof sizing.hardStop === "object" ? sizing.hardStop : null;
  const active = Boolean(st && st.tripped === true) || hardStopTripped(sizing, cfg);                         // a latch in either place holds (the cache can only have been written by this function)
  const ev = replay(l1.concat(slot), cfg);
  const j = judge({ ev, base: Number(sizing && sizing.base), stored: st, cfg });
  const rec = { rearmAt: cfg.rearmAt, checkedAt: now, tripped: active };
  let kill = null;
  if (j.status === "unreadable") Object.assign(rec, { status: "unreadable", why: j.why });
  else {
    Object.assign(rec, { status: "ok", why: null, peakEquity: Number(j.peakEquity.toFixed(4)), peakBase: Number(j.peakBase.toFixed(2)), minBase: Number(j.minBase.toFixed(2)), equity: Number(j.equity.toFixed(4)), drawdown: Number(j.drawdown.toFixed(4)), line: Number(j.line.toFixed(2)) });
    if (!active && j.trip) {
      kill = tripDetail(j, cfg);
      Object.assign(rec, { tripped: true, trippedAt: now, rule: "drawdown", detail: kill, alerted: false });
    }
  }
  if (active) {   // carry the details of the trip forward, never rewrite them
    const src = st && st.tripped === true ? st : cache;
    const pick = (k) => (src && src[k] !== undefined ? src[k] : null);   // Firestore refuses undefined
    Object.assign(rec, { trippedAt: pick("trippedAt"), rule: pick("rule"), detail: pick("detail"), alerted: st && st.alerted === true });
  } else if (!kill) Object.assign(rec, { tripped: false, trippedAt: null, rule: null, detail: null, alerted: false });
  const beatDue = (r) => !r || !Number.isFinite(Number(r.checkedAt)) || now - Number(r.checkedAt) >= cfg.heartbeatMs;
  const differs = (r) => !r || Number(r.rearmAt) !== cfg.rearmAt || r.status !== rec.status || (r.tripped === true) !== rec.tripped
    || (rec.status === "ok" && (Number(r.peakEquity) !== rec.peakEquity || Number(r.peakBase) !== rec.peakBase || Number(r.minBase) !== rec.minBase));
  const stateDue = differs(st) || beatDue(st), cacheDue = differs(cache) || beatDue(cache);
  if (stateDue) { try { await io.writeState(rec); } catch (e) { return { skipped: "unwritten" }; } }
  if (cacheDue) { try { await io.writeHardStop(rec); } catch (e) { return { skipped: "unwritten" }; } }
  // A trip ENDS THE SESSION, the way the 12% loss stop does (active false, endedAt, endedBecause, a "session ended" event), so no tick runs after it whatever the sizing cache says (the tick's full write of the sizing
  // document can overwrite the cache). Done on every run while the latch holds, so a session started by hand again is ended again within one run (the Start callable also refuses while the latch holds). The exit
  // watch does not depend on the session being active, so exits keep running. Every error is swallowed; the ticks still block on the latch.
  if (rec.tripped && typeof io.endSession === "function") {
    try {
      const ended = await io.endSession("hard account stop: the account is down " + Math.round(effectiveFraction(cfg) * 100) + "% from its best on trading results");
      if (ended === true) { try { await io.logEvent({ ts: now, kind: "session ended", detail: "the hard account stop (" + Math.round(effectiveFraction(cfg) * 100) + "% below the account's best on trading results) ended the session. It stays off until a reviewed edit re-arms it" }); } catch (e) { /* informational */ } }
    } catch (e) { /* the ticks still block on the latch */ }
  }
  // The alert (a critical bell item and a phone alert): once per generation, claimed in a transaction by the caller, and retried on later minutes until the authoritative record says it went out.
  if (rec.tripped && rec.alerted !== true) {
    let first = true;
    try { first = await io.claimAlert(cfg.rearmAt); } catch (e) { first = true; }   // a claim that cannot be made still shows the bell item (a duplicate beats silence)
    if (first) {
      try { await io.logEvent({ ts: now, kind: "hard stop", detail: "Hard account stop: " + (rec.detail || "the account fell to the hard stop line") + ". No new buy of any strategy will be placed; open positions are still managed and sold. It stays off until a reviewed edit re-arms it." }); } catch (e) { /* the latch is already set */ }
      try { await io.raiseAlert({ at: now, rearmAt: cfg.rearmAt, drawdown: Number((j.drawdown || rec.drawdown || 0).toFixed(2)), line: Number((j.line || rec.line || 0).toFixed(2)) }); }
      catch (e) { try { if (typeof io.releaseAlert === "function") await io.releaseAlert(cfg.rearmAt); } catch (e2) { /* nothing more to do */ } return { ok: true, killed: true, tripped: kill ? "drawdown" : null, j }; }
    }
    try { await io.writeState({ rearmAt: cfg.rearmAt, alerted: true }); await io.writeHardStop({ rearmAt: cfg.rearmAt, alerted: true }); } catch (e) { /* retried next minute; the claim makes a repeat silent */ }
  }
  return { ok: true, killed: rec.tripped, tripped: kill ? "drawdown" : null, j };
}

module.exports = { HARD_STOP, HARD_STOP_FRACTION, HARD_STOP_MIN_FRACTION, HARD_STOP_MAX_FRACTION, validFraction, effectiveFraction, hardStopTripped, hardStopBlocks, orderResult, replay, judge, runHardStopCheck };
