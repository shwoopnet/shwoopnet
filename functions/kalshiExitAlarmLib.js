"use strict";
// Exit watch alarm (Oct 29, 2026). The exit watch (kalshiLiveExit) is the only thing that sells a losing position before settlement, and a function that has stopped cannot say that it stopped. The page already
// shows "no check for several minutes", but only to someone looking at it. This is the phone side: if the bot is on, a position is open and the exit watch has not completed a pass for EXIT_WATCH_STALE_MS, the owner's
// phone gets a stop-or-issue alert.
//
// What it is NOT: it holds no Kalshi key, signs nothing, sends no order and sells nothing. It reads two small things the bot already keeps (the exit watch's own heartbeat document, the open order list), and its only
// write is one field on the session document, which the existing push trigger (kalshiPushSession, kalshiPushLib.sessionKinds) turns into the alert. No new secret, endpoint or scheduled function: index.js calls
// runExitAlarm from the minute function that already runs, which is a different process from the exit watch, so it can notice the exit watch's silence. The limit is a code constant: nothing stored, requested or typed
// on the page feeds it. Every error is swallowed here: an alarm that fails costs an alarm, never a trade.
const EXIT_WATCH_STALE_MS = 4 * 60 * 1000;

// An order the exit watch still has a duty to watch: bought by L1, filled, not settled, not already sold out.
function needsWatching(t) {
  return !!t && t.strategy === "L1" && t.settled !== true && Number(t.fillCount) > 0 && t.exitStatus !== "sold";
}

// Pure. `beatAt` is the exit watch's last completed pass (ms, or null), `alarmedFor` the spell already alerted.
// A spell is identified by `reference`: the later of the last pass and the OLDEST open position's time, because the watch owed that position nothing before it existed (and this keeps a fresh deploy, with no heartbeat
// yet, from alarming at once). A new pass moves the reference, so a second, separate silence is a new spell and alerts again; the same silence never does.
function judge({ now, beatAt, orders, alarmedFor }) {
  const open = (Array.isArray(orders) ? orders : []).filter(needsWatching);
  if (!open.length) return { fire: false, why: "nothing open" };
  const oldest = Math.min(...open.map((t) => Number(t.ts)).filter(Number.isFinite));
  const reference = Math.max(Number.isFinite(beatAt) ? beatAt : 0, Number.isFinite(oldest) ? oldest : 0);
  if (!(reference > 0)) return { fire: false, why: "no usable time" };
  const silentMs = now - reference;
  if (!(silentMs > EXIT_WATCH_STALE_MS)) return { fire: false, why: "fresh", reference };
  if (alarmedFor === reference) return { fire: false, why: "already alerted", reference };
  return { fire: true, reference, silentMs, open: open.length };
}

// The I/O is injected so this is testable without Firebase. Returns a short string for the log; never throws.
async function runExitAlarm({ now, session, readBeat, readOrders, claim, release, raise } = {}) {
  try {
    if (!session || session.active !== true) return "bot off";
    const beat = await readBeat();                         // { at, alarmedFor } or null
    const beatAt = beat && Number.isFinite(Number(beat.at)) ? Number(beat.at) : null;
    // A fresh heartbeat is the normal case: stop before reading any orders.
    if (beatAt !== null && now - beatAt <= EXIT_WATCH_STALE_MS) return "fresh";
    const orders = await readOrders();
    const j = judge({ now, beatAt, orders, alarmedFor: beat && Number.isFinite(Number(beat.alarmedFor)) ? Number(beat.alarmedFor) : null });
    if (!j.fire) return j.why;
    // Claim the spell BEFORE alerting (a transaction in index.js), so two instances during a deploy cannot both send it.
    if (!(await claim(j.reference))) return "already alerted";
    try { await raise({ at: now, silentMin: Math.floor(j.silentMs / 60000), open: j.open }); }
    catch (e) { try { await release(j.reference); } catch (e2) { /* the next minute may try again or not; nothing else depends on it */ } return "alert failed"; }
    return "alerted";
  } catch (e) {
    return "error: " + String((e && e.message) || e).slice(0, 80);
  }
}

module.exports = { EXIT_WATCH_STALE_MS, needsWatching, judge, runExitAlarm };
