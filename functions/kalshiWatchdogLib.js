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

// The bot's own stop alert (opt-in, KALSHI_STOP_ALERT_URL): when a session ends BY ITSELF (the loss stop, an unresolved or lost order answer), say so, because
// otherwise it stays off until the owner happens to look. Not sent for stops the owner pressed. Written for ntfy.sh style URLs (a POST body is the message, the
// Title and Priority headers shape the push), which any plain webhook receiver also accepts.
function stopAlertPings({ base, detail }) {
  const url = String(base || "").trim().replace(/\/+$/, "");
  if (!url) return [];
  return [{ url, body: "The Kalshi bot stopped itself and stays off until you start it. " + String(detail || "").slice(0, 300),
            headers: { Title: "Kalshi bot stopped", Priority: "high", Tags: "warning" } }];
}

// A ping that fails must never break the run that already finished: log and move on.
async function sendAll(fetchFn, pings, log) {
  for (const p of pings) {
    try {
      const res = await fetchFn(p.url, { method: "POST", body: p.body, ...(p.headers ? { headers: p.headers } : {}), signal: AbortSignal.timeout(5000) });
      if (!res.ok) (log || console.warn)("watchdog ping HTTP " + res.status);
    } catch (e) {
      (log || console.warn)("watchdog ping failed: " + String((e && e.message) || e).slice(0, 80));
    }
  }
}

module.exports = { pingsFor, stopAlertPings, sendAll };
