"use strict";
// Perpetuals position changes, tracked like trades (Nov 17, 2026, the owner via the EA: perps phase 1, events log). The perps account is read every 5 minutes (kalshiPerpsAccountLib). This compares two
// reads and turns the difference into events: a position OPENED, CLOSED, or its size ADDED or REDUCED (a flip from up to down is a close and an open). It is display data only: the bot trades no perps,
// nothing that decides a trade reads it, and it writes only its own admin-read collection.
//
// What it can and cannot say. It sees the account every 5 minutes, so an event carries the time of the READ that saw it, not the fill time, and a position opened and closed between two reads is never seen.
// `lastPnl` on a close is the last unrealized profit it was SEEN at, not the realized result (the margin answers carry no fill price; whether a fills route exists is a separate, unprobed question). So the
// page must label it "last seen", never "result". An event is written only when BOTH reads had the positions answer (positionsOk) and the earlier read is recent enough to be the immediately preceding
// one; otherwise nothing is written, because a failed positions read looks like every position closing. The first read after a gap (or from an older document with no positionsOk) writes nothing.
const MAX_GAP_MS = 12 * 60000;          // the earlier read must be this recent, or the diff could hide several changes (a read is every 5 minutes)
const MAX_EVENTS = 40;
const COLLECTION = "kalshiPerpsEvents";
const TICKER_OK = /^[A-Z0-9_.-]{1,40}$/;

const num = (v) => { const n = typeof v === "string" ? Number(v) : v; return typeof n === "number" && Number.isFinite(n) ? n : null; };
const byMarket = (rows) => { const m = {}; for (const r of Array.isArray(rows) ? rows : []) { if (r && typeof r.market === "string" && TICKER_OK.test(r.market) && num(r.size) !== null && num(r.size) > 0) m[r.market] = r; } return m; };

// Pure. Events from the earlier and the later shaped perps document, or [] when they cannot be compared. Each event: { at, market, kind, up, size, prevSize, entry, mark, lastPnl }.
function diffPositions(prev, next) {
  if (!prev || !next || prev.positionsOk !== true || next.positionsOk !== true) return [];
  const t0 = num(prev.at), t1 = num(next.at);
  if (t0 === null || t1 === null || t1 <= t0 || t1 - t0 > MAX_GAP_MS) return [];
  const a = byMarket(prev.rows), b = byMarket(next.rows), out = [];
  const ev = (kind, cur, old) => ({
    at: t1, market: (cur || old).market, kind, up: (cur || old).up === true,
    size: cur ? num(cur.size) : 0, prevSize: old ? num(old.size) : 0,
    entry: num((cur || old).entry), mark: num((cur || old).mark),
    lastPnl: kind === "closed" ? num(old.pnl) : null,
  });
  for (const m of Object.keys(b)) {
    if (!a[m]) { out.push(ev("opened", b[m], null)); continue; }
    if ((a[m].up === true) !== (b[m].up === true)) { out.push(ev("closed", null, a[m])); out.push(ev("opened", b[m], null)); continue; }
    const ds = num(b[m].size) - num(a[m].size);
    if (Math.abs(ds) > 1e-9) out.push(ev(ds > 0 ? "added" : "reduced", b[m], a[m]));
  }
  for (const m of Object.keys(a)) if (!b[m]) out.push(ev("closed", null, a[m]));
  return out.slice(0, MAX_EVENTS);
}

// The document id is the same for the same change seen twice (two instances, a retry): read time, market and kind.
const eventId = (e) => e.at + "-" + e.market + "-" + e.kind;

// The I/O is injected: readPrev() gives the earlier shaped document (or null), write(id, event) stores one. Returns a short string; never throws.
async function recordEvents({ prev, next, write } = {}) {
  try {
    const events = diffPositions(prev, next);
    if (!events.length) return "none";
    for (const e of events) await write(eventId(e), e);
    return "events " + events.length;
  } catch (e) {
    return "error: " + String((e && e.message) || e).slice(0, 80);
  }
}

module.exports = { MAX_GAP_MS, MAX_EVENTS, COLLECTION, diffPositions, eventId, recordEvents };
