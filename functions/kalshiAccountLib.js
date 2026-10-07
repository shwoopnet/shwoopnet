"use strict";
// Read-only view of the live Kalshi account for the owner's page: balance per shard, open positions, recent fills.
// GET requests only, through the live module's production-host-checked request function. No order code lives here
// (a test asserts it): it cannot place, change or cancel anything. Each part reports its own HTTP status, so one
// failing endpoint does not hide the others, and the unknown shapes Kalshi returns are shown as key lists so the
// page can be adapted without guessing.

const live = require("./kalshiLiveLib");

const num = (v) => (v === undefined || v === null || v === "" ? NaN : Number(v));
const short = (b) => (typeof b === "string" ? b : JSON.stringify(b)).slice(0, 160);
const keysOf = (b) => (b && typeof b === "object" && !Array.isArray(b) ? Object.keys(b).slice(0, 30) : []);
const failed = (r) => ({ ok: false, status: r.status, error: short(r.body) });

function shapeBalance(r) {
  if (r.status !== 200 || !r.body || typeof r.body !== "object") return failed(r);
  const b = r.body;
  const shards = Array.isArray(b.balance_breakdown)
    ? b.balance_breakdown.map((x) => ({ shard: x.exchange_index, dollars: num(x.balance) })).filter((x) => Number.isFinite(x.dollars))
    : [];
  // The top-level balance is documented in cents; the per-shard figures are dollar strings. Say which was used.
  let totalDollars = NaN, totalFrom = null;
  if (shards.length) { totalDollars = shards.reduce((s, x) => s + x.dollars, 0); totalFrom = "sum of the shards"; }
  else if (Number.isFinite(num(b.balance))) { totalDollars = num(b.balance) / 100; totalFrom = "top-level balance, read as cents"; }
  return {
    ok: true, status: 200, shards, totalDollars: Number.isFinite(totalDollars) ? totalDollars : null, totalFrom,
    portfolioValue: b.portfolio_value !== undefined ? String(b.portfolio_value) : null, keys: keysOf(b),
  };
}

function shapePositions(r) {
  if (r.status !== 200 || !r.body || typeof r.body !== "object") return failed(r);
  const list = Array.isArray(r.body.market_positions) ? r.body.market_positions : [];
  const positions = list.slice(0, 50).map((p) => ({
    ticker: p.ticker, position: num(p.position_fp !== undefined ? p.position_fp : p.position),
    realizedPnl: p.realized_pnl_dollars !== undefined ? String(p.realized_pnl_dollars) : (p.realized_pnl !== undefined ? String(p.realized_pnl) : null),
    feesPaid: p.fees_paid_dollars !== undefined ? String(p.fees_paid_dollars) : (p.fees_paid !== undefined ? String(p.fees_paid) : null),
  })).filter((p) => p.ticker && p.position !== 0);
  return { ok: true, status: 200, positions, keys: keysOf(r.body), sampleKeys: list.length ? keysOf(list[0]) : [] };
}

function shapeFills(r) {
  if (r.status !== 200 || !r.body || typeof r.body !== "object") return failed(r);
  const list = Array.isArray(r.body.fills) ? r.body.fills : [];
  const fills = list.slice(0, 20).map((f) => ({
    ticker: f.ticker || f.market_ticker, side: f.side, action: f.action || null,
    count: num(f.count_fp !== undefined ? f.count_fp : f.count),
    price: f.yes_price_dollars !== undefined ? String(f.yes_price_dollars) : (f.yes_price !== undefined ? String(f.yes_price) : null),
    taker: f.is_taker === undefined ? null : f.is_taker === true, time: f.created_time || null,
  }));
  return { ok: true, status: 200, fills, keys: keysOf(r.body), sampleKeys: list.length ? keysOf(list[0]) : [] };
}

async function readAccount({ fetchFn, keyId, pem, now }) {
  const get = (path, params) => live.liveRequest({ fetchFn, keyId, pem, method: "GET", path, params, nowMs: now });
  const [bal, pos, fills] = await Promise.all([
    get("/portfolio/balance"),
    get("/portfolio/positions", { limit: "50" }),
    get("/portfolio/fills", { limit: "20" }),
  ]);
  return { at: now, balance: shapeBalance(bal), positions: shapePositions(pos), fills: shapeFills(fills) };
}

module.exports = { readAccount, shapeBalance, shapePositions, shapeFills };
