"use strict";
// Gold L1 kill latch (the owner, Nov 10, 2026: "give gold L1 a coded KILL and RETURN"). Design and costs of the options considered: docs/GOLD_KILL_LATCH.md.
//
// Shape in one paragraph: the kill is REPLAYED from gold's own settled orders since GOLD_KILL.rearmAt (cash basis), the way OICORE's ladder is replayed, so there is no
// hidden state to drift between instances. A small scheduled function (kalshiGoldKillCheck, its own process) runs runGoldKillCheck every minute and CACHES the result in a
// `goldKill` field on the sizing document, which the minute tick already reads. runL1Tick never reads or writes anything new: it only looks at the value it already receives
// (goldKillActive). A latch is sticky: once tripped, nothing a later trade does clears it. Only a reviewed edit that moves GOLD_KILL.rearmAt past the latch re-arms it.
//
// It can only REMOVE gold orders. The exit watch is untouched and still sells an open gold position. No size, band, stop or other strategy is changed by this file, except the
// optional half-size period after a re-arm (it can only lower a count). Nothing stored, requested or typed on the page can disable or loosen it: a stored latch from before the
// code's rearmAt is ignored, a stored latch at or after it blocks, and the checker never clears one.

const GOLD_SERIES = "KXGOLD15M";
const GOLD_KILL = Object.freeze({
  series: GOLD_SERIES,
  // Moving this to a later time is the ONLY way to re-arm (a reviewed edit, with the bar in docs/GOLD_KILL_LATCH.md met and the owner's approval). Trades before it are history:
  // they set no peak and count toward no rule.
  rearmAt: Date.parse("2026-11-10T00:00:00Z"),
  // Set true in the same edit that re-arms after a KILL (not for the first arming): the first halfSizeFills gold trades after the re-arm go out at half size.
  rearmIsReturn: false,
  halfSizeFills: 30,
  // A FIXED dollar line, not a fraction of the moving sizing base: 6% of the $979.25 base when it was written. A line that depends on sizing.base could be loosened by a base that rises
  // (or is missing) between a trip and a re-derivation, and the tick's full write of the sizing document can erase a fresh latch; with a constant, the next replay re-derives the same trip
  // on every instance. When the base grows, re-set it by a reviewed code edit. Measured from gold's own cash peak since rearmAt (the peak starts at 0).
  drawdownDollars: 58.75,
  netFloor: -20,                 // dollars, cash net since rearmAt ...
  netAfterTrades: 40,            // ... once at least this many trades have settled since rearmAt
  alertPf60: 0.7, alertPf100: 1.0, alertEarlySells: 3, alertEarlyWindow: 40,   // ALERT ONLY: they never latch and never change an order
});

// Is the stored latch in force for this series? Pure; takes the sizing document the tick already read. A latch recorded for an older generation (rearmAt before the code's) is
// ignored, which is how a reviewed edit re-arms. Any other shape fails toward "not tripped" only when it says nothing: a stored object with tripped === true blocks.
function goldKillActive(sizingState, series, cfg = GOLD_KILL) {
  if (series !== cfg.series) return false;
  const g = sizingState && sizingState.goldKill;
  if (!g || g.tripped !== true) return false;
  return Number(g.rearmAt) >= cfg.rearmAt;
}
// True while a re-arm after a kill is inside its half size period (only ever lowers a count).
function goldHalfSize(sizingState, series, cfg = GOLD_KILL) {
  if (series !== cfg.series || cfg.rearmIsReturn !== true) return false;
  const g = sizingState && sizingState.goldKill;
  if (!g || Number(g.rearmAt) !== cfg.rearmAt) return true;   // no record for this generation yet: the safe side is half size
  return g.half !== false;
}

// One settled gold order as a cash result, or null when it is not a result (unfilled, still open, closed by hand). A result at the close is re-derived on the cash basis with the
// real fill and fee (fillCost, through settledFields); an early sell keeps its stored settledPnl, as the account result does.
function goldResult(t) {
  const live = require("./kalshiLiveLib");   // lazily: kalshiLiveLib requires this file for goldKillActive
  if (!t || t.series !== GOLD_SERIES || t.strategy !== "L1") return null;
  if (!(Number(t.fillCount) > 0) || t.settled !== true || t.result === "hand") return null;
  if (t.result === "exit") { const p = Number(t.settledPnl); return Number.isFinite(p) ? { ts: Number(t.ts), pnl: p, exit: true } : null; }
  if (t.result !== "yes" && t.result !== "no") return null;
  if (!Number.isFinite(Number(t.maxCost))) return null;
  const p = live.settledFields(t, t.result).settledPnl;
  return Number.isFinite(p) && Number.isFinite(Number(t.ts)) ? { ts: Number(t.ts), pnl: p, exit: false } : null;
}
function profitFactor(rows) {
  let w = 0, l = 0;
  for (const r of rows) { if (r.pnl > 0) w += r.pnl; else l -= r.pnl; }
  return l > 0 ? w / l : Infinity;   // no losses: not a failing figure
}

// Replay. orders: any order documents (other series are ignored). Nothing here reads the sizing base: the drawdown line is the fixed GOLD_KILL.drawdownDollars.
function evaluateGold({ orders, cfg = GOLD_KILL }) {
  const rows = (orders || []).map(goldResult).filter(Boolean).sort((a, b) => a.ts - b.ts);
  const since = rows.filter((r) => r.ts >= cfg.rearmAt);
  const limit = cfg.drawdownDollars;
  let cum = 0, peak = 0, trip = null;
  since.forEach((r, i) => {
    cum += r.pnl; peak = Math.max(peak, cum);
    if (trip) return;   // sticky within the replay: a later win never un-trips
    if (peak - cum >= limit - 1e-9) trip = { rule: "drawdown", at: r.ts, detail: "gold is $" + (peak - cum).toFixed(2) + " below its own peak since the last re-arm, which reaches the fixed $" + limit.toFixed(2) + " line" };
    else if (i + 1 >= cfg.netAfterTrades && cum < cfg.netFloor - 1e-9) trip = { rule: "net", at: r.ts, detail: "gold is $" + (-cum).toFixed(2) + " down after " + (i + 1) + " trades since the last re-arm, under the -$" + Math.abs(cfg.netFloor) + " line" };
  });
  // Alerts look at the same bounded set (gold's settled trades since the re-arm; they inform, they never act), so the read is never wider than the kill's own.
  const last = (n) => since.slice(-n);
  const alerts = {
    pf60: last(60).length >= 60 && profitFactor(last(60)) < cfg.alertPf60,
    pf100: last(100).length >= 100 && profitFactor(last(100)) < cfg.alertPf100,
    early: last(cfg.alertEarlyWindow).filter((r) => r.exit).length >= cfg.alertEarlySells,
  };
  return { trip, tradesSince: since.length, net: Number(cum.toFixed(4)), peak: Number(peak.toFixed(4)), drawdown: Number((peak - cum).toFixed(4)), alerts,
    pf60: last(60).length >= 60 ? profitFactor(last(60)) : null, pf100: last(100).length >= 100 ? profitFactor(last(100)) : null };
}

const ALERT_TEXT = {
  pf60: (e) => "Gold alert: the last 60 gold trades have a cash profit factor of " + (e.pf60 === null ? "?" : e.pf60.toFixed(2)) + ", under 0.7. Nothing was changed; this only tells you.",
  pf100: (e) => "Gold alert: the last 100 gold trades have a cash profit factor of " + (e.pf100 === null ? "?" : e.pf100.toFixed(2)) + ", under 1.0. Nothing was changed; this only tells you.",
  early: () => "Gold alert: 3 or more early sells in gold's last 40 trades. Nothing was changed; this only tells you.",
};

// The checker. All I/O is injected, every failure leaves the stored record as it was (a failed read never trips and never clears). Order of effects: the record is written FIRST, then the
// event, so a failed event write can never leave the latch unset. A latch erased by the tick's full sizing write is re-derived by the next replay (the line is a constant).
// io: { now, readOrders(since) -> orders, readSizing() -> doc|null, writeGoldKill(obj) (merge into the sizing doc's goldKill), logEvent(e) }
async function runGoldKillCheck(io, cfg = GOLD_KILL) {
  const { now } = io;
  let orders, sizing;
  // bounded: only orders since the re-arm date are read
  try { orders = await io.readOrders(cfg.rearmAt); sizing = await io.readSizing(); }
  catch (e) { return { skipped: "unreadable" }; }
  if (!Array.isArray(orders)) return { skipped: "unreadable" };
  const ev = evaluateGold({ orders, cfg });
  const stored = sizing && sizing.goldKill && typeof sizing.goldKill === "object" ? sizing.goldKill : null;
  const sameGen = Boolean(stored && Number(stored.rearmAt) === cfg.rearmAt);
  const active = goldKillActive(sizing, cfg.series, cfg);
  const patch = {};
  let kill = null;
  if (!active && ev.trip) {
    kill = ev.trip;
    Object.assign(patch, { tripped: true, rearmAt: cfg.rearmAt, rule: ev.trip.rule, trippedAt: now, firstBreachTs: ev.trip.at, detail: ev.trip.detail });
  } else if (!active && !sameGen) {
    Object.assign(patch, { tripped: false, rearmAt: cfg.rearmAt });   // a fresh generation: record it so the half size period and the alert flags have a place to live
  }
  const prevAlerts = sameGen && stored.alerts && typeof stored.alerts === "object" ? stored.alerts : {};
  const newAlerts = [];
  for (const k of Object.keys(ev.alerts)) if (ev.alerts[k] && prevAlerts[k] !== true) newAlerts.push(k);
  if (newAlerts.length || Object.keys(ev.alerts).some((k) => Boolean(prevAlerts[k]) !== ev.alerts[k])) patch.alerts = { pf60: ev.alerts.pf60, pf100: ev.alerts.pf100, early: ev.alerts.early };
  const half = cfg.rearmIsReturn === true && ev.tradesSince < cfg.halfSizeFills;
  if (cfg.rearmIsReturn === true && (!sameGen || stored.half !== half)) patch.half = half;
  if (!Object.keys(patch).length) return { ok: true, killed: active, ev };
  patch.rearmAt = cfg.rearmAt;
  try { await io.writeGoldKill(patch); } catch (e) { return { skipped: "unwritten" }; }
  if (kill) { try { await io.logEvent({ ts: now, kind: "gold kill", detail: "Gold L1 is switched off by its own kill latch: " + kill.detail + ". No new gold order will be placed (an open position is still sold at the 25c line). Only a reviewed edit re-arms it." }); } catch (e) { /* the latch is already set */ } }
  for (const k of newAlerts) { try { await io.logEvent({ ts: now, kind: "gold alert", detail: ALERT_TEXT[k](ev) }); } catch (e) { /* informational */ } }
  return { ok: true, killed: active || Boolean(kill), tripped: kill ? kill.rule : null, alerts: newAlerts, ev };
}

module.exports = { GOLD_KILL, GOLD_SERIES, goldKillActive, goldHalfSize, goldResult, evaluateGold, runGoldKillCheck, profitFactor };
