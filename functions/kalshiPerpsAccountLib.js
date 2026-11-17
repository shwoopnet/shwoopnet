"use strict";
// The owner's perpetuals (margin) account, READ ONLY (Nov 16, 2026, the owner: the Account card shows one total, predictions plus perps, and the Open positions card lists each perp).
// The probe (kalshiPerpsProbeLib) proved the trading key can read /margin/balance and /margin/positions. This shapes those two answers, plus the PUBLIC perps list (mark price and leverage
// estimate by ticker), into one small document the Bot page reads. GET only: no order, no POST, nothing written to Kalshi, nothing that decides a trade reads it (display only; the stops,
// limits and sizing stay on the bot's own trade results).
//
// What the margin answers give (field names confirmed by the probe): positions[] market_ticker, position, entry_price, unrealized_pnl, margin_used, fees, subaccount;
// subaccount_balances[] account_equity, position_value, maintenance_margin, available_balance, initial_margin. They do NOT give a mark price, a forced-close price, a multiplier or any
// take-profit or stop-loss level. So: mark and multiplier come from the public list (the multiplier is the list's leverage estimate, labelled an estimate), and the forced-close price, the
// buffer, and the auto close levels are NOT derived here: the exact margin formula is not documented in this repo and a guess would be shown as a fact, so they stay null and the page says
// "n/a" or "not readable". A later change may fill them once a real answer proves the math.
//
// Units are UNVERIFIED: the probe stored names only. Every figure is read through PERPS_SCALE (1 = the answer is in dollars). The nightly report carries the first rows raw, so one real read can
// confirm or correct the scale before the page trusts it.

const PERPS_SCALE = 1;
const MAX_ROWS = 40;
const PATHS = Object.freeze(["/margin/balance", "/margin/positions"]);
const DOC = Object.freeze({ collection: "kalshiLiveControl", id: "perpsAccount" });
const LIST_URL = "https://external-api.kalshi.com/trade-api/v2/margin/markets";
const TICKER_OK = /^[A-Z0-9_.-]{1,40}$/;

const num = (v) => { const n = typeof v === "string" ? Number(v) : v; return typeof n === "number" && Number.isFinite(n) ? n : null; };
const scaled = (v) => { const n = num(v); return n === null ? null : Math.round(n * PERPS_SCALE * 1e6) / 1e6; };

// Pure. One document from the two margin answers and the public list answer (any may be missing). Never throws.
function shapePerps(balanceBody, positionsBody, listBody, now) {
  const subs = balanceBody && Array.isArray(balanceBody.subaccount_balances) ? balanceBody.subaccount_balances : [];
  let equity = null, positionValue = null, maintenance = null, available = null;
  for (const s of subs) {
    if (!s || typeof s !== "object") continue;
    const add = (cur, v) => { const n = scaled(v); return n === null ? cur : (cur === null ? n : cur + n); };
    equity = add(equity, s.account_equity); positionValue = add(positionValue, s.position_value);
    maintenance = add(maintenance, s.maintenance_margin); available = add(available, s.available_balance);
  }
  const byTicker = {};
  for (const m of (listBody && Array.isArray(listBody.markets) ? listBody.markets : [])) {
    if (m && typeof m.ticker === "string" && TICKER_OK.test(m.ticker)) byTicker[m.ticker] = m;
  }
  const rows = [];
  for (const p of (positionsBody && Array.isArray(positionsBody.positions) ? positionsBody.positions : []).slice(0, MAX_ROWS)) {
    if (!p || typeof p.market_ticker !== "string" || !TICKER_OK.test(p.market_ticker)) continue;
    const size = num(p.position);
    if (size === null || size === 0) continue;                       // a closed or empty row is not an open position
    const m = byTicker[p.market_ticker] || {};
    rows.push({
      market: p.market_ticker,
      up: size > 0,                                                  // the sign of the position is its direction (UNVERIFIED until a real row is read)
      size: Math.abs(size),
      entry: num(p.entry_price),
      pnl: scaled(p.unrealized_pnl),
      margin: scaled(p.margin_used),
      fees: scaled(p.fees),
      mark: num(m.price),                                            // the list's last price; the page labels it "now", not an index
      multiplierEstimate: num(m.leverage_estimate),                  // an ESTIMATE, labelled so on the page
      closeAt: null, bufferPct: null,                                // not derived: see the header
      takeProfit: null, stopLoss: null,                              // not readable from the key
    });
  }
  const pnlTotal = rows.reduce((a, r) => a + (r.pnl || 0), 0);
  return { at: now, scale: PERPS_SCALE, equity, positionValue, maintenance, available, pnlTotal: Math.round(pnlTotal * 100) / 100, count: rows.length, rows, listRead: Object.keys(byTicker).length > 0 };
}

// liveRequest is injected (the bot's own signer); publicGet is a keyless GET of the public list. A failed balance read gives null (the page then shows no perps total, never a made up one).
async function runPerpsAccount({ liveRequest, fetchFn, keyId, pem, now, publicGet }) {
  const out = {};
  for (const path of PATHS) {
    const r = await liveRequest({ fetchFn, keyId, pem, method: "GET", path, nowMs: now, timeoutMs: 8000, noRetry: true });
    out[path] = r && Number(r.status) === 200 && r.body && typeof r.body === "object" ? r.body : null;
  }
  if (!out["/margin/balance"] && !out["/margin/positions"]) return null;
  let list = null;
  try { list = typeof publicGet === "function" ? await publicGet(LIST_URL) : null; } catch (e) { list = null; }
  return shapePerps(out["/margin/balance"], out["/margin/positions"], list, now);
}

module.exports = { PERPS_SCALE, PATHS, DOC, LIST_URL, shapePerps, runPerpsAccount };
