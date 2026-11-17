"use strict";
// Margin cushion phone alert for the perpetuals account (Nov 17, 2026, the owner via the EA: "cushion alert FIRST"; the Risk Analyst confirms the lines).
// kalshiPerpsAccount already reads the perps account every 5 minutes. This turns the shaped result into at most one phone alert per spell, with no new function, no new request and no Kalshi write:
// cushion = (equity - maintenance margin) / equity. Under MEDIUM_PCT it is a warning (one alert, six hour cooldown); under HIGH_PCT it is critical (one alert, one hour cooldown). An escalation from
// medium to high alerts at once, because each level has its own cooldown. Its only write is a field on the session document that the existing phone alert trigger turns into an alert (same pattern as the
// low money on a shard alert, kalshiShardAlertLib).
//
// What it is NOT: it sends nothing to Kalshi, places no order, moves no money (the owner adds margin or closes by hand in Kalshi), holds no key of its own and is read by no trading code. Every error is
// swallowed: a failed alert costs an alert, never a trade. It warns on the CUSHION, not on a forced-close price: Kalshi's data carries none. It is only as fresh as the 5 minute read, so a fast move can
// pass a line between two reads. It does nothing at all on a read with no open perps position or a healthy cushion (no read, no write).
const MEDIUM_PCT = 20;
const HIGH_PCT = 10;
const COOLDOWN_MS = Object.freeze({ medium: 6 * 3600 * 1000, high: 1 * 3600 * 1000 });

const num = (v) => { const n = typeof v === "string" ? Number(v) : v; return typeof n === "number" && Number.isFinite(n) ? n : null; };

// Pure. The cushion of a shaped perps document ({equity, maintenance, count}), or null when it cannot be judged (no equity, no maintenance, or no open position).
function cushion(doc) {
  if (!doc || typeof doc !== "object") return null;
  const equity = num(doc.equity), maint = num(doc.maintenance), count = num(doc.count);
  if (equity === null || maint === null || equity <= 0 || maint <= 0 || !(count > 0)) return null;
  const dollars = Math.round((equity - maint) * 100) / 100;
  const pct = Math.round(((equity - maint) / equity) * 1000) / 10;
  return { pct, dollars, level: pct < HIGH_PCT ? "high" : (pct < MEDIUM_PCT ? "medium" : null) };
}

// Pure: may an alert of this level go out now? `last` is the time of the last alert of that level (ms or null); the claim applies this inside its transaction so two instances cannot both send one.
function claimable(level, now, last) {
  if (!COOLDOWN_MS[level]) return false;
  return !(Number.isFinite(last) && now - last < COOLDOWN_MS[level]);
}

// I/O is injected so this is testable without Firebase. `claim(now, level)` is a transaction that returns the PREVIOUS alert time of that level (or null) when it took the claim, or false when the cooldown holds.
// `release(level, prev)` puts it back if the write that raises the alert fails. Returns a short string; never throws.
async function runCushionAlert({ now, doc, claim, release, raise } = {}) {
  try {
    const c = cushion(doc);
    if (!c || !c.level) return "none";            // the normal read: nothing read, nothing written
    const prev = await claim(now, c.level);
    if (prev === false) return "already alerted";
    try { await raise({ at: now, level: c.level, pct: c.pct, dollars: c.dollars }); }
    catch (e) { try { await release(c.level, prev); } catch (e2) { /* the next read may try again or not */ } return "alert failed"; }
    return "alerted " + c.level;
  } catch (e) {
    return "error: " + String((e && e.message) || e).slice(0, 80);
  }
}

module.exports = { MEDIUM_PCT, HIGH_PCT, COOLDOWN_MS, cushion, claimable, runCushionAlert };
