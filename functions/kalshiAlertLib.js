"use strict";
// The outside watchdog for the Kalshi paper bot. A bot that has stopped cannot report that
// it stopped, so the alarm must live somewhere else: a dead-man's switch. Every healthy
// tick pings a URL; the service behind that URL raises the alert when the pings STOP.
// Silence is the signal, which is why an unreadable feed sends no ping at all.
//
// Opt-in: with no URL configured nothing is sent and the bot behaves exactly as before.
// Written for Healthchecks.io style URLs (`<url>` is the success ping, `<url>/fail` a
// failure), which most dead-man's-switch services also accept.

function pingsFor({ base, ok, tierMode, prevTier }) {
  const url = String(base || "").trim().replace(/\/+$/, "");
  if (!url) return [];
  const out = [];
  if (ok) out.push({ url, body: "ok tier=" + tierMode });
  // One alert when the day's hard stop is hit, not one a minute for the rest of the day.
  if (tierMode === "done" && prevTier !== "done") out.push({ url: url + "/fail", body: "done for the day: loss limit reached" });
  return out;
}

// A ping that fails must never break the tick that already finished: log and move on.
async function sendAll(fetchFn, pings, log) {
  for (const p of pings) {
    try {
      const res = await fetchFn(p.url, { method: "POST", body: p.body, signal: AbortSignal.timeout(5000) });
      if (!res.ok) (log || console.warn)("watchdog ping HTTP " + res.status);
    } catch (e) {
      (log || console.warn)("watchdog ping failed: " + String((e && e.message) || e).slice(0, 80));
    }
  }
}

module.exports = { pingsFor, sendAll };
