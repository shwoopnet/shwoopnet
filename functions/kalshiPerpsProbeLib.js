"use strict";
// One-shot, READ ONLY probe of the perpetuals (margin) account (Nov 16, 2026, the owner's popup answer: "Yes, run the probe").
// Question it answers: can the existing trading key read the margin account? It makes three GETs through the same signer the bot uses
// (liveRequest signs "/trade-api/v2" + path) and keeps ONLY the HTTP status and the NAMES of the fields in each answer.
// No value is ever stored: no balance, size, price or P&L, so nothing about the account lands in Firestore or the report.
// No POST, no order, nothing written to Kalshi. Delete this file and its function once the answer is known.

const PATHS = ["/margin/enabled", "/margin/balance", "/margin/positions"];
const MAX_NAMES = 60;
const NAME_OK = /^[A-Za-z0-9_]{1,40}$/;

// The key names of a parsed answer, to depth 2 (a name inside an array's first element counts, written "list[].name"). Names only.
function fieldNames(body) {
  const out = [];
  const add = (n) => { if (out.length < MAX_NAMES && NAME_OK.test(n.split(/[.\[\]]+/).filter(Boolean).pop() || "") && !out.includes(n)) out.push(n); };
  const walk = (v, prefix, depth) => {
    if (depth > 2 || v === null || typeof v !== "object") return;
    if (Array.isArray(v)) { if (v.length) walk(v[0], prefix + "[]", depth + 1); return; }
    for (const k of Object.keys(v)) {
      add(prefix ? prefix + "." + k : k);
      walk(v[k], prefix ? prefix + "." + k : k, depth + 1);
    }
  };
  walk(body, "", 0);
  return out;
}

// Calls only the three fixed GET paths. liveRequest is injected (index.js passes the bot's own).
async function runPerpsProbe({ liveRequest, fetchFn, keyId, pem, now }) {
  const results = {};
  for (const path of PATHS) {
    const r = await liveRequest({ fetchFn, keyId, pem, method: "GET", path, nowMs: now, timeoutMs: 8000, noRetry: true });
    const status = Number(r && r.status) || 0;
    results[path] = { status, fields: status === 200 && r && typeof r.body === "object" ? fieldNames(r.body) : [] };
  }
  return { at: now, results };
}

// PORTFOLIO PROBE (Nov 17, 2026, the Head of Engineering under the owner's reconciliation job): which of Kalshi's own record routes answer, and what FIELD NAMES they carry, so the nightly reconciliation can
// later compare the bot's books with Kalshi's own fills, settlements and any transfer or deposit history. Same rules as above: GET only, no retry, only the HTTP status and the NAMES of the fields,
// never a value (no amount, price, count, id or time is stored), nothing written to Kalshi. A 404 or 403 is a result. Candidate routes that do not exist simply answer 404. Delete with the function.
const PORTFOLIO_PROBES = Object.freeze([
  { path: "/portfolio/settlements", params: { limit: "3" } },
  { path: "/portfolio/fills", params: { limit: "3" } },
  { path: "/portfolio/subaccounts/transfers", params: { limit: "3" } },
  { path: "/portfolio/deposits", params: { limit: "3" } },
  { path: "/portfolio/withdrawals", params: { limit: "3" } },
  { path: "/portfolio/transfers", params: { limit: "3" } },
  { path: "/margin/fills", params: { limit: "3" } },
  { path: "/margin/settlements", params: { limit: "3" } },
  { path: "/margin/transfers", params: { limit: "3" } },
]);
async function runPortfolioProbe({ liveRequest, fetchFn, keyId, pem, now }) {
  const results = {};
  for (const p of PORTFOLIO_PROBES) {
    let status = 0, fields = [];
    try {
      const r = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: p.path, params: p.params, nowMs: now, timeoutMs: 8000, noRetry: true });
      status = Number(r && r.status) || 0;
      fields = status === 200 && r && typeof r.body === "object" ? fieldNames(r.body) : [];
    } catch (e) { status = 0; }
    results[p.path] = { status, fields };
  }
  return { at: now, results };
}

module.exports = { PATHS, PORTFOLIO_PROBES, fieldNames, runPerpsProbe, runPortfolioProbe, DOC: { collection: "kalshiLiveControl", id: "perpsProbe" }, PORTFOLIO_DOC: { collection: "kalshiLiveControl", id: "portfolioProbe" } };
