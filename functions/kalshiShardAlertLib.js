"use strict";
// Low money on an exchange shard (Oct 31, 2026, the owner picked "low-balance alert per exchange shard" from the 50 directions; the page warning for it was removed on Oct 24).
// Kalshi keeps each market group's money on its own exchange shard and an order needs money on ITS shard. When the minute function skips a market because its shard holds too little ("only $X on its shard"), that market has silently stopped trading.
// The tick already notices this; this file turns it into a phone alert (an "issue" through the existing session push trigger) once per spell, and never more than once in SHARD_ALERT_COOLDOWN_MS, however many minutes the shortage lasts.
//
// What it is NOT: no Kalshi key, no order, no transfer (the bot cannot move money between shards and this does not try), no new secret or endpoint. Its one write is a field on the session document, like the exit watch alarm. Every error is swallowed:
// an alert that fails costs an alert, never a trade. It does nothing at all on a minute with no shortage (no read, no write).
const SHARD_ALERT_COOLDOWN_MS = 6 * 3600 * 1000;

// The worst shortage this minute (lowest money on its shard), or null. `short` is what runL1Tick reports: [{ shard, avail, need, ticker }].
function worst(short) {
  const rows = (Array.isArray(short) ? short : []).filter((x) => x && Number.isFinite(Number(x.avail)) && Number.isFinite(Number(x.need)));
  if (!rows.length) return null;
  return rows.reduce((a, b) => (Number(b.avail) < Number(a.avail) ? b : a));
}

// Pure: may an alert go out now? `lastAt` is the time of the last alert (ms or null); the claim in index.js applies this inside its transaction so two instances during a deploy cannot both send one.
function claimable(now, lastAt) { return !(Number.isFinite(lastAt) && now - lastAt < SHARD_ALERT_COOLDOWN_MS); }

// The I/O is injected so this is testable without Firebase. `claim(now)` is a transaction that returns the PREVIOUS alert time (or null) when it took the claim, so a release can put it back, or false when the cooldown holds. Returns a short string; never throws.
async function runShardAlert({ now, short, claim, release, raise } = {}) {
  try {
    const w = worst(short);
    if (!w) return "none";                      // the normal minute: nothing read, nothing written
    const prev = await claim(now);
    if (prev === false) return "already alerted";
    try { await raise({ at: now, shard: String(w.shard), avail: Number(w.avail), need: Number(w.need), market: String(w.ticker || "").split("-")[0].slice(0, 20) }); }
    catch (e) { try { await release(prev); } catch (e2) { /* the next minute may try again or not */ } return "alert failed"; }
    return "alerted";
  } catch (e) {
    return "error: " + String((e && e.message) || e).slice(0, 80);
  }
}

module.exports = { SHARD_ALERT_COOLDOWN_MS, worst, claimable, runShardAlert };
