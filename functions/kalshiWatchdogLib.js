"use strict";
// The outside watchdog for the live arm. A function that has stopped cannot report that it stopped, so the alarm
// must live somewhere else: a dead-man's switch. Every healthy run pings a URL, and the service behind it raises
// the alert when the pings STOP. Silence is the signal, which is why a run that threw sends no success ping.
//
// "Healthy" means the scheduled arm check completed, armed or not: it runs every minute either way, so an
// idle but alive function keeps the switch alive and a dead one does not.
//
// Opt-in: with no URL configured nothing is sent. Written for Healthchecks.io style URLs (`<url>` is the success
// ping, `<url>/fail` a failure), which most dead-man's-switch services also accept.

function pingsFor({ base, ok, reason }) {
  const url = String(base || "").trim().replace(/\/+$/, "");
  if (!url) return [];
  return ok
    ? [{ url, body: "ok" }]
    : [{ url: url + "/fail", body: String(reason || "arm check failed").slice(0, 200) }];
}

// A ping that fails must never break the run that already finished: log and move on.
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
