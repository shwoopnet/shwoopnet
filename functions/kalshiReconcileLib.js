"use strict";
// Nightly RECONCILIATION (Nov 17, 2026, the owner chose it by popup: "a deterministic check that does not depend on any model's judgment").
// It compares what the bot did with the rules it must follow and with what Kalshi last said, and reports a mismatch plainly. PURE: no I/O, no clock, no randomness; the caller reads the data and
// hands it in. READ ONLY and display and alerts only: nothing that decides an order, size, stop or risk reads any of it, it sends no order, and it adds no number of its own (every limit it uses
// is a constant already in the bot's code).
//
// What it checks TODAY (phase 1), and what it does NOT (said on every report, never guessed):
//   CHECKED  4. contracts against the cap: no order was bigger than the most its strategy may send (L1: the size lock `maxContractsAt` at the order's own time; the second slot: its ladder ceiling,
//               or the registry per-order size). It checks the HARD ceiling, not the base-scaled step of a ladder (that needs the base used at that moment).
//   CHECKED  3. perps position against Kalshi's last read: the latest perps account document is Kalshi's own positions read; the events log is built from consecutive reads. A position the document
//               shows must agree in size and direction with the last event of its market, and a market whose last event is a close must not still be in the document. A market with no event
//               (a position from before the log began) is "not checked", not a mismatch.
//   NOT CHECKED  1. fills and settlements against the bot's P&L, and 2. balance change against P&L plus transfers plus the perps price change: both need Kalshi's OWN fills, settlements and transfer
//               records (see the portfolio probe), and the only transfer signal we hold is a heuristic that already misfired once, so a check built on it could send a false alert. They are listed
//               as "not checked" until the real record shapes are known.
const live = require("./kalshiLiveLib");

const MAX_FINDINGS = 20;
// The same cutoff the nightly report's oversize section uses: Dogecoin left the bot on Nov 9, 2026, so its older orders are history, not oversize.
const REMOVED_SERIES_BEFORE = { KXDOGE15M: Date.parse("2026-11-09T00:00:00Z") };
const NOT_CHECKED_ALWAYS = Object.freeze([
  "fills and settlements against the bot's reported P&L (needs Kalshi's own fill and settlement records, shapes not yet known)",
  "balance change against P&L plus transfers plus the perps price change (needs Kalshi's transfer history; no heuristic is used)",
]);

const num = (v) => { if (v === null || v === undefined || v === "") return null; const n = Number(v); return Number.isFinite(n) ? n : null; };
const seriesOf = (o) => (typeof o.ticker === "string" && o.ticker ? o.ticker.split("-")[0] : "");
const iso = (ms) => new Date(ms).toISOString();

// The most one slot order of each strategy may hold: the ladder's ceiling for a laddered strategy, else its registry size (never above the slot-wide limit). A COPY of the slot library's numbers, because a gate
// keeps every other file from importing the slot library; test RC2b fails the moment it drifts from the registry (a strategy added, removed or resized without this table). An id not here is "not checked".
const SLOT_CEILINGS = Object.freeze({ OICORE: 30, EVENT830: 1, CFRTIK: 3, OIREL1: 3, XRPFAV10: 3 });
function slotCeiling(id) { return Object.prototype.hasOwnProperty.call(SLOT_CEILINGS, id) ? SLOT_CEILINGS[id] : null; }

// Check 4. Each order is judged by its own time (the gold trial seat's cap applies only while the trial runs).
function checkContracts(l1Orders, slotOrders) {
  const findings = []; let checked = 0, skipped = 0;
  for (const o of Array.isArray(l1Orders) ? l1Orders : []) {
    const ts = num(o && o.ts), series = o && seriesOf(o), n = o ? Math.max(num(o.count) || 0, num(o.fillCount) || 0) : 0;
    if (ts === null || !series) { skipped++; continue; }
    const max = live.maxContractsAt(series, ts);
    if (max === 0 && !(REMOVED_SERIES_BEFORE[series] && ts >= REMOVED_SERIES_BEFORE[series])) { skipped++; continue; }
    checked++;
    if (n > max) findings.push({ check: "contracts", who: "L1 " + series, at: iso(ts), count: n, max });
  }
  for (const o of Array.isArray(slotOrders) ? slotOrders : []) {
    const ts = num(o && o.ts), id = o && typeof o.slotId === "string" ? o.slotId : "", n = o ? Math.max(num(o.count) || 0, num(o.fillCount) || 0) : 0;
    const max = id ? slotCeiling(id) : null;
    if (ts === null || max === null) { skipped++; continue; }
    checked++;
    if (n > max) findings.push({ check: "contracts", who: id, at: iso(ts), count: n, max });
  }
  return { findings, checked, skipped };
}

// Check 3. `doc` is the perps account document (Kalshi's own read, with `rows` of market, up, size, and `positionsOk`), `events` the perps events log rows (market, kind, size, up, at).
function checkPerps(doc, events, now) {
  const findings = [], notChecked = [];
  if (!doc || typeof doc !== "object" || !Array.isArray(doc.rows) || doc.positionsOk !== true || num(doc.at) === null) {
    notChecked.push("perps positions against the events log (the perps account read is missing or had no positions answer)");
    return { findings, checked: 0, notChecked };
  }
  if (now - Number(doc.at) > 30 * 60000) { notChecked.push("perps positions against the events log (the perps account read is older than 30 minutes)"); return { findings, checked: 0, notChecked }; }
  const last = new Map();      // market -> its newest event at or before the document's read time
  for (const e of Array.isArray(events) ? events : []) {
    const at = num(e && e.at), m = e && typeof e.market === "string" ? e.market : "";
    if (!m || at === null || at > Number(doc.at)) continue;
    if (!last.has(m) || at > last.get(m).at) last.set(m, { at, kind: e.kind, size: num(e.size), up: e.up });
  }
  let checked = 0, noEvent = 0;
  const open = new Set();
  for (const r of doc.rows) {
    const m = r && typeof r.market === "string" ? r.market : "";
    if (!m || !(num(r.size) > 0)) continue;
    open.add(m);
    const ev = last.get(m);
    if (!ev) { noEvent++; continue; }
    checked++;
    if (ev.kind === "closed") findings.push({ check: "perps", who: m, at: iso(Number(doc.at)), detail: "the account shows an open position but the last event for it is a close" });
    else if (ev.size !== null && Math.abs(ev.size - Number(r.size)) > 1e-9) findings.push({ check: "perps", who: m, at: iso(Number(doc.at)), detail: "size " + Number(r.size) + " in the account read, " + ev.size + " in the last event" });
    else if (typeof ev.up === "boolean" && typeof r.up === "boolean" && ev.up !== r.up) findings.push({ check: "perps", who: m, at: iso(Number(doc.at)), detail: "direction differs between the account read and the last event" });
  }
  for (const [m, ev] of last) {    // an event that says a position is open, with no such position in the account read
    if (!open.has(m) && ev.kind !== "closed" && ev.size > 0) { checked++; findings.push({ check: "perps", who: m, at: iso(Number(doc.at)), detail: "the last event says " + ev.size + " open but the account read has no such position" }); }
  }
  if (noEvent) notChecked.push(noEvent + " perps position(s) older than the events log (no event to compare with)");
  return { findings, checked, notChecked };
}

function reconcile({ now, l1Orders, slotOrders, perpsDoc, events }) {
  const c4 = checkContracts(l1Orders, slotOrders), c3 = checkPerps(perpsDoc, events, now);
  const findings = c4.findings.concat(c3.findings);
  const notChecked = NOT_CHECKED_ALWAYS.concat(c3.notChecked);
  const rec = {
    at: now, ok: findings.length === 0,
    checks: { contracts: { checked: c4.checked, skipped: c4.skipped, findings: c4.findings.length }, perps: { checked: c3.checked, findings: c3.findings.length } },
    findings: findings.slice(0, MAX_FINDINGS), findingCount: findings.length, notChecked,
  };
  rec.line = lineOf(rec);
  return rec;
}

function lineOf(rec) {
  const ran = "checked: contracts against the cap (" + rec.checks.contracts.checked + " orders), perps against Kalshi's read (" + rec.checks.perps.checked + " positions); NOT checked: P&L and balance against Kalshi's records";
  if (rec.ok) return "RECONCILE OK, " + ran;
  return "RECONCILE MISMATCH: " + rec.findingCount + " finding(s), first: " + rec.findings[0].who + " " + (rec.findings[0].detail || (rec.findings[0].count + " contracts, cap " + rec.findings[0].max)) + "; " + ran;
}

// One phone alert per day at most. The claim and the stamp are injected (the caller does a transaction and writes the stamp on the session document); a failed raise puts the old time back. Never throws.
const ALERT_COOLDOWN_MS = 20 * 3600000;
async function runReconcileAlert({ now, rec, claim, release, raise }) {
  try {
    if (!rec || rec.ok !== false || !(rec.findingCount > 0)) return "none";
    const prev = await claim(now, ALERT_COOLDOWN_MS);          // resolves the previous time (a number or null) when the claim is taken, false when a recent alert exists
    if (prev === false) return "already alerted";
    try { await raise({ at: now, count: rec.findingCount, first: String(rec.findings[0].who).slice(0, 40), check: String(rec.findings[0].check) }); }
    catch (e) { try { await release(prev); } catch (e2) { /* nothing more to do */ } return "alert failed"; }
    return "alerted";
  } catch (e) { return "error: " + String((e && e.message) || e).slice(0, 80); }
}

const RECONCILE_HOUR_UTC = 5;      // the hourly balance snapshot function runs the check once a day in this UTC hour, before the 06:04 UTC nightly report read

module.exports = { RECONCILE_HOUR_UTC, SLOT_CEILINGS, MAX_FINDINGS, NOT_CHECKED_ALWAYS, ALERT_COOLDOWN_MS, REMOVED_SERIES_BEFORE, slotCeiling, checkContracts, checkPerps, reconcile, lineOf, runReconcileAlert, DOC: { collection: "kalshiLiveControl", id: "reconcile" } };
