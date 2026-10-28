// The nightly order report (the owner, Oct 28, 2026: "rather than me constantly uploading the full orders ... at midnight (00:00 UTC) reports").
// A READ-ONLY summary of the bot's own orders, behind one secret token, so a scheduled task can fetch it. It holds no Kalshi key, sends nothing to Kalshi,
// writes nothing, and never returns an order id, a client order id or any credential: only what the owner already pastes into the research chat.
const crypto = require("crypto");

const MAX_HOURS = 24 * 90;
const MAX_ORDER_ROWS = 2000;

function num(v) { const n = Number(v); return Number.isFinite(n) ? n : null; }
function round(v, d) { return Number.isFinite(v) ? Number(v.toFixed(d)) : null; }
function seriesOf(o) { return typeof o.ticker === "string" && o.ticker ? o.ticker.split("-")[0] : "unknown"; }

// Same definition the page uses (kalshiOrderPnl): a filled, settled order with a saved settledPnl. Anything else has no result yet.
function settledPnl(o) {
  if (!o || o.settled !== true || !(Number(o.fillCount) > 0)) return null;
  if (o.settledPnl === null || o.settledPnl === undefined) return null;
  return num(o.settledPnl);
}

function emptyTally() { return { filled: 0, settled: 0, won: 0, lost: 0, exits: 0, open: 0, noFill: 0, net: 0, grossWin: 0, grossLoss: 0, worstLoss: 0 }; }
function addTo(t, o) {
  if (o.status === "no fill") { t.noFill++; return; }
  if (!(Number(o.fillCount) > 0)) return;
  t.filled++;
  const p = settledPnl(o);
  if (p === null) { if (o.settled !== true) t.open++; return; }
  t.settled++; t.net += p;
  if (o.result === "exit") t.exits++;
  if (p > 0) { t.won++; t.grossWin += p; } else if (p < 0) { t.lost++; t.grossLoss += -p; if (-p > t.worstLoss) t.worstLoss = -p; }
}
function finish(t) {
  return {
    filled: t.filled, settled: t.settled, won: t.won, lost: t.lost, exits: t.exits, open: t.open, noFill: t.noFill,
    net: round(t.net, 2), grossWin: round(t.grossWin, 2), grossLoss: round(t.grossLoss, 2), worstLoss: round(t.worstLoss, 2),
    // null (not infinity) while there is no loss to divide by
    profitFactor: t.grossLoss > 0 ? round(t.grossWin / t.grossLoss, 2) : null,
    winRate: t.settled > 0 ? round(t.won / t.settled, 4) : null,
  };
}

function buildReport(orders, nowMs, hours, withOrders) {
  const since = nowMs - hours * 3600000;
  const rows = (Array.isArray(orders) ? orders : []).filter((o) => o && Number(o.ts) >= since);
  const all = emptyTally(), byMarket = {}, byLead = {};
  rows.forEach((o) => {
    addTo(all, o);
    const m = seriesOf(o); byMarket[m] = byMarket[m] || emptyTally(); addTo(byMarket[m], o);
    const l = typeof o.entryLead === "string" ? o.entryLead : "unknown"; byLead[l] = byLead[l] || emptyTally(); addTo(byLead[l], o);
  });
  const out = {
    generatedAt: new Date(nowMs).toISOString(), sinceUtc: new Date(since).toISOString(), hours,
    note: "Settled results only count orders with a saved settledPnl. Open orders have no result yet. Dollars after fees.",
    total: finish(all),
    byMarket: Object.fromEntries(Object.keys(byMarket).sort().map((k) => [k, finish(byMarket[k])])),
    byEntryLead: Object.fromEntries(Object.keys(byLead).sort().map((k) => [k, finish(byLead[k])])),
  };
  if (withOrders) {
    // One compact row per order. No order id, no client order id, nothing that identifies the account.
    out.orders = rows.slice().sort((a, b) => a.ts - b.ts).slice(-MAX_ORDER_ROWS).map((o) => ({
      ts: new Date(Number(o.ts)).toISOString(), ticker: o.ticker || null, side: o.side || null, count: num(o.fillCount), avgFill: num(o.avgFill),
      entryLead: o.entryLead || null, status: o.status || null, result: o.result || null, settledPnl: settledPnl(o),
    }));
    out.ordersTruncated = rows.length > MAX_ORDER_ROWS;
  }
  return out;
}

// Constant-time compare of two secrets of any length (hash both first so the lengths match).
function sameToken(a, b) {
  const x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}

// The whole request handler, with the secret and the order read passed in so it can be tested without Firebase.
function makeReportHandler(deps) {
  return async function handle(req, res) {
    res.set("Cache-Control", "no-store");
    if (req.method !== "GET") { res.status(405).json({ error: "GET only" }); return; }
    const token = deps.getToken();
    const header = String((req.headers && (req.headers.authorization || req.headers.Authorization)) || "");
    const given = header.startsWith("Bearer ") ? header.slice(7) : "";
    // No configured token means closed, never open.
    if (!token || String(token).length < 24 || !given || !sameToken(given, token)) { res.status(401).json({ error: "unauthorized" }); return; }
    let hours = Number(req.query && req.query.hours);
    if (!Number.isFinite(hours) || hours <= 0) hours = 24;
    hours = Math.min(hours, MAX_HOURS);
    try {
      const now = deps.now();
      const orders = await deps.readOrders(now - hours * 3600000);
      res.status(200).json(buildReport(orders, now, hours, String((req.query && req.query.orders) || "") === "1"));
    } catch (e) {
      res.status(500).json({ error: "could not read orders" });   // never echo the error text
    }
  };
}

module.exports = { buildReport, makeReportHandler, sameToken, MAX_HOURS, MAX_ORDER_ROWS };
