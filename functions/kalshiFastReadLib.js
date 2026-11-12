"use strict";
// Fast research reads through the owner's own Kalshi account (Nov 12, 2026, the owner). A JOB (inline JSON) lists PUBLIC market-data reads; this runs them as authenticated GETs through the live
// module's request function, with the same two secrets the hourly balance snapshot already uses, and returns the answers in the HTTP response. It exists because the shared research address is throttled
// to a trickle; the account's own key has a published read budget far above what this uses.
//
// What it is NOT: it sends no order and has no POST, PUT or DELETE. The job cannot contain a path at all: every URL is built here from a fixed template and typed values (ENDPOINTS), so there is nothing to
// smuggle a portfolio, order, fill, position, balance or account path through; a second check refuses those words anywhere in a built path anyway. Nothing is written anywhere (no Firestore, no file): the
// answers go back to the caller only. No key, signature, secret or token is ever put in a response or a log line; an error says a short fixed code, never the upstream text.
//
// THE MAIN RISK, and what bounds it: the trading key's request budget is shared with the exit watch (which sells at the 25c line and loops every 10 seconds) and the minute tick. So (1) it REFUSES to run, and
// stops mid-job, in the minutes of every quarter hour in which the bot buys and the exit watch is busiest (EXIT_BUY_MINUTES from kalshiLiveLib, plus one minute either side); (2) it never goes faster than
// 3 requests a second (MIN_GAP_MS), against a published Basic-tier read budget of 200 tokens a second (about 20 requests at the default 10 tokens); (3) it stops at the third 429 in a row and does not retry
// a refused read; (4) one call is at most 300 requests and one instance runs at a time. It cannot see an open position, so the quiet minutes are a rule of timing, not proof the exit watch is idle.
const crypto = require("crypto");
const live = require("./kalshiLiveLib");

const MAX_REQUESTS = 300;            // requests (pages included) one call may send
const MAX_JOB_ENTRIES = 300;
const MIN_GAP_MS = 340;              // under 3 a second; the code never goes above 5 a second (a gate pins MIN_GAP_MS >= 200)
const MAX_429_IN_A_ROW = 3;
const MAX_RESPONSE_BYTES = 8 * 1024 * 1024;   // the caller gets at most this much JSON; the rest is marked truncated
const MAX_PAGES = 50;
const CURSOR_MAX = 512;
const SLEEP_AFTER_FAIL_MS = 1500;
const WINDOW_PAD_MINUTES = 1;        // on top of EXIT_BUY_MINUTES

const SERIES_RE = /^[A-Z0-9]{2,32}$/;
const TICKER_RE = /^[A-Z0-9][A-Z0-9._-]{0,63}$/;
const FORBIDDEN_PATH = /portfolio|order|fill|position|balance|account|settlement|subaccount|api_keys|communications|transfer/i;
const STATUS = ["open", "closed", "settled", "unopened"];
const PERIODS = [1, 60, 1440];

const isInt = (v, lo, hi) => Number.isInteger(v) && v >= lo && v <= hi;
const isTs = (v) => isInt(v, 1500000000, 2100000000);

// One entry per allowed read: the fixed path, the typed fields it takes, and which fields are query parameters. Nothing else can be asked for.
const ENDPOINTS = Object.freeze({
  markets_list: { path: () => "/markets", paged: true, fields: { series: "series", status: "status", min_close_ts: "ts", max_close_ts: "ts", limit: "limit1000" }, query: { series: "series_ticker" } },
  market: { path: (r) => "/markets/" + encodeURIComponent(r.ticker), required: ["ticker"], fields: { ticker: "ticker" } },
  candles: { path: (r) => "/series/" + encodeURIComponent(r.series) + "/markets/" + encodeURIComponent(r.ticker) + "/candlesticks", required: ["series", "ticker", "start_ts", "end_ts", "period"], fields: { series: "series", ticker: "ticker", start_ts: "ts", end_ts: "ts", period: "period" }, query: { period: "period_interval" } },
  trades: { path: () => "/markets/trades", paged: true, required: ["ticker"], fields: { ticker: "ticker", min_ts: "ts", max_ts: "ts", limit: "limit1000" } },
  hist_markets_list: { path: () => "/historical/markets", paged: true, fields: { series: "series", status: "status", min_close_ts: "ts", max_close_ts: "ts", limit: "limit1000" }, query: { series: "series_ticker" } },
  hist_market: { path: (r) => "/historical/markets/" + encodeURIComponent(r.ticker), required: ["ticker"], fields: { ticker: "ticker" } },
  hist_candles: { path: (r) => "/historical/markets/" + encodeURIComponent(r.ticker) + "/candlesticks", required: ["ticker", "start_ts", "end_ts", "period"], fields: { ticker: "ticker", start_ts: "ts", end_ts: "ts", period: "period" }, query: { period: "period_interval" } },
  hist_trades: { path: () => "/historical/trades", paged: true, required: ["ticker"], fields: { ticker: "ticker", min_ts: "ts", max_ts: "ts", limit: "limit1000" } },
});

const CHECKS = {
  series: (v) => typeof v === "string" && SERIES_RE.test(v),
  ticker: (v) => typeof v === "string" && TICKER_RE.test(v),
  status: (v) => STATUS.includes(v),
  ts: isTs,
  period: (v) => PERIODS.includes(v),
  limit1000: (v) => isInt(v, 1, 1000),
};

// Pure. Checks one job entry and returns { ok, ep, base: {path, params}, pages } or { ok:false, reason } with a short fixed reason (never the caller's text).
function planEntry(r) {
  if (!r || typeof r !== "object" || Array.isArray(r)) return { ok: false, reason: "entry_not_object" };
  const def = Object.prototype.hasOwnProperty.call(ENDPOINTS, r.ep) ? ENDPOINTS[r.ep] : null;
  if (!def) return { ok: false, reason: "unknown_endpoint" };
  const allowedKeys = new Set(["ep", ...Object.keys(def.fields), ...(def.paged ? ["max_pages"] : [])]);
  for (const k of Object.keys(r)) if (!allowedKeys.has(k)) return { ok: false, reason: "unknown_field" };
  for (const k of def.required || []) if (r[k] === undefined) return { ok: false, reason: "missing_field" };
  const params = {};
  for (const [k, kind] of Object.entries(def.fields)) {
    if (r[k] === undefined) continue;
    if (!CHECKS[kind](r[k])) return { ok: false, reason: "bad_value" };
    const inPath = (r.ep === "candles" && (k === "series" || k === "ticker")) || ((r.ep === "market" || r.ep === "hist_market" || r.ep === "hist_candles") && k === "ticker");
    if (!inPath) params[(def.query && def.query[k]) || k] = String(r[k]);
  }
  if (r.start_ts !== undefined && r.end_ts !== undefined && !(r.end_ts > r.start_ts)) return { ok: false, reason: "bad_range" };
  let pages = 1;
  if (def.paged && r.max_pages !== undefined) { if (!isInt(r.max_pages, 1, MAX_PAGES)) return { ok: false, reason: "bad_value" }; pages = r.max_pages; }
  const path = def.path(r);
  if (!/^\/[A-Za-z0-9/_.%-]*$/.test(path) || path.includes("..") || FORBIDDEN_PATH.test(path)) return { ok: false, reason: "path_refused" };
  for (const k of Object.keys(params)) if (FORBIDDEN_PATH.test(k) || FORBIDDEN_PATH.test(params[k])) return { ok: false, reason: "path_refused" };
  return { ok: true, ep: r.ep, path, params, pages };
}

// Pure. The whole job: { ok, plan:[...], maxRequests } or { ok:false, reason }.
function planJob(job) {
  if (!job || typeof job !== "object" || Array.isArray(job)) return { ok: false, reason: "job_not_object" };
  for (const k of Object.keys(job)) if (!["id", "requests", "max_requests"].includes(k)) return { ok: false, reason: "unknown_job_field" };
  if (!Array.isArray(job.requests) || job.requests.length < 1 || job.requests.length > MAX_JOB_ENTRIES) return { ok: false, reason: "bad_request_list" };
  let cap = MAX_REQUESTS;
  if (job.max_requests !== undefined) { if (!isInt(job.max_requests, 1, MAX_REQUESTS)) return { ok: false, reason: "bad_max_requests" }; cap = job.max_requests; }
  const plan = [];
  for (const r of job.requests) { const p = planEntry(r); if (!p.ok) return p; plan.push(p); }
  return { ok: true, plan, maxRequests: cap };
}

// The minutes (of each quarter hour, UTC and Central both align) in which a read is refused: the bot's buying minutes and the exit watch's busiest minutes, plus a minute either side.
function blockedMinutes() {
  const s = new Set();
  for (const m of live.EXIT_BUY_MINUTES) for (let d = -WINDOW_PAD_MINUTES; d <= WINDOW_PAD_MINUTES; d++) s.add(((m + d) % 15 + 15) % 15);
  return s;
}
const BLOCKED = blockedMinutes();
function inBlockedWindow(nowMs) { return BLOCKED.has(Math.floor(nowMs / 60000) % 15); }

// Runs the job. I/O injected: fetchFn, keyId, pem, now(), sleep(ms). Returns { status, results, ... } and never throws. A status other than "done" means the job stopped early; what was read is still returned.
async function runFastRead({ job, fetchFn, keyId, pem, now, sleep } = {}) {
  const clock = typeof now === "function" ? now : () => Date.now();
  const wait = typeof sleep === "function" ? sleep : (ms) => new Promise((r) => setTimeout(r, ms));
  const planned = planJob(job);
  if (!planned.ok) return { status: "refused", reason: planned.reason, requests: 0, results: [] };
  if (inBlockedWindow(clock())) return { status: "refused", reason: "exit_watch_window", requests: 0, results: [] };
  const out = { status: "done", requests: 0, results: [], truncated: false };
  let in429 = 0, bytes = 0, lastStart = 0;
  try {
    for (let i = 0; i < planned.plan.length; i++) {
      const p = planned.plan[i];
      let cursor;
      for (let page = 0; page < p.pages; page++) {
        if (out.requests >= planned.maxRequests) { out.status = "stopped_at_cap"; return out; }
        if (inBlockedWindow(clock())) { out.status = "stopped_exit_watch_window"; return out; }
        const gap = lastStart + MIN_GAP_MS - clock();
        if (gap > 0) await wait(gap);
        lastStart = clock();
        const params = cursor ? { ...p.params, cursor } : p.params;
        let r;
        try {
          // noRetry: a refused read is never asked twice here, so the rate cannot double behind this loop's back. GET is the only method this module can send.
          r = await live.liveRequest({ fetchFn, keyId, pem, method: "GET", path: p.path, params: Object.keys(params).length ? params : undefined, nowMs: clock(), noRetry: true, timeoutMs: 15000 });
        } catch (e) { out.status = "stopped_error"; return out; }
        out.requests++;
        if (r.status === 429) { in429++; if (in429 >= MAX_429_IN_A_ROW) { out.status = "stopped_429"; out.results.push({ i, ep: p.ep, page, status: 429 }); return out; } await wait(SLEEP_AFTER_FAIL_MS); page--; continue; }
        in429 = 0;
        const row = { i, ep: p.ep, page, status: r.status, body: r.status === 200 ? r.body : null };
        const size = JSON.stringify(row).length;
        if (bytes + size > MAX_RESPONSE_BYTES) { out.truncated = true; out.status = "stopped_response_size"; return out; }
        bytes += size; out.results.push(row);
        cursor = r.status === 200 && r.body && typeof r.body === "object" && typeof r.body.cursor === "string" && r.body.cursor.length > 0 && r.body.cursor.length <= CURSOR_MAX ? r.body.cursor : undefined;
        if (r.status !== 200 || !cursor) break;
      }
    }
  } catch (e) { out.status = "stopped_error"; }
  return out;
}

function sameToken(a, b) {
  const x = crypto.createHash("sha256").update(String(a)).digest(), y = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}

// POST with a JSON body {job} (a job is too long for a query string); the body is the only input. 405 for any other method. No token configured, or under 24 characters, means closed.
function makeFastReadHandler(deps) {
  return async function handle(req, res) {
    res.set("Cache-Control", "no-store");
    if (req.method !== "POST") { res.status(405).json({ error: "POST only" }); return; }   // POST to this endpoint only carries the job; it sends nothing but GETs to Kalshi
    const token = deps.getToken();
    const header = String((req.headers && (req.headers.authorization || req.headers.Authorization)) || "");
    const given = header.startsWith("Bearer ") ? header.slice(7) : "";
    if (!token || String(token).length < 24 || !given || !sameToken(given, token)) { res.status(401).json({ error: "unauthorized" }); return; }
    try {
      const out = await runFastRead({ job: req.body && req.body.job !== undefined ? req.body.job : req.body, fetchFn: deps.fetchFn, keyId: deps.getKeyId(), pem: deps.getPem(), now: deps.now, sleep: deps.sleep });
      res.status(out.status === "refused" ? 400 : 200).json(out);
    } catch (e) {
      if (typeof deps.logError === "function") deps.logError(e);
      res.status(500).json({ error: "could not run" });
    }
  };
}

module.exports = { ENDPOINTS, MAX_REQUESTS, MIN_GAP_MS, MAX_429_IN_A_ROW, MAX_RESPONSE_BYTES, MAX_PAGES, FORBIDDEN_PATH, planEntry, planJob, inBlockedWindow, runFastRead, makeFastReadHandler, sameToken };
