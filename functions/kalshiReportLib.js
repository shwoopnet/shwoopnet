// The nightly order report (the owner, Oct 28, 2026: "rather than me constantly uploading the full orders ... at midnight (00:00 UTC) reports").
// A READ-ONLY summary of the bot's own orders, behind one secret token, so a scheduled task can fetch it. It holds no Kalshi key, sends nothing to Kalshi,
// writes nothing, and never returns an order id, a client order id or any credential: only what the owner already pastes into the research chat.
const crypto = require("crypto");
const { maxContractsFor } = require("./kalshiLiveLib");
const deployStampLib = require("./deployStampLib");
const shadowLib = require("./kalshiShadowLib");   // read only: the shadow rules' score; this library still sends nothing to Kalshi and writes nothing

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

// Orders bigger than today's code could ever size them (Oct 29, 2026: one appeared where the code sends a smaller fixed size). Zero is the normal value. Series, count, the most that series may have and the
// time only, never an id. The limit comes from maxContractsFor, a code constant, so nothing stored can move it.
// Dogecoin left the bot on Nov 9, 2026, so maxContractsFor is 0 for it; its orders from before that (it was paused after Nov 3) are history, not oversize. An order of its placed AFTER the cutoff still shows.
const REMOVED_SERIES_BEFORE = { KXDOGE15M: Date.parse('2026-11-09T00:00:00Z') };
function oversizeRows(rows) {
  return rows.map((o) => {
    const series = seriesOf(o), n = Math.max(num(o.count) || 0, num(o.fillCount) || 0), max = maxContractsFor(series);
    if (REMOVED_SERIES_BEFORE[series] && Number(o.ts) < REMOVED_SERIES_BEFORE[series]) return null;
    return n > max ? { ts: new Date(Number(o.ts)).toISOString(), series, count: n, max } : null;
  }).filter(Boolean).sort((a, b) => a.ts < b.ts ? -1 : 1);
}

// Per-order market context for the tests that need it (the refinement chat's R2, the no-fill share, Oct 30, 2026): what was ordered against what rested at the touch, and the quote the bot saw. Numbers and short labels only, never an id. A field the order does not carry is null.
// Send timing (Oct 31, 2026, the owner: "log send time only"; the refinement chat's Dogecoin timing lead). The bot records when the minute function started, when the order left and when Kalshi answered; the three derived figures are
// how many milliseconds past the clock minute the function started (startLateMs), how long from the function start to the order leaving (startToSendMs) and how long Kalshi took to answer (answerMs). Numbers only, null when the order predates the log.
function timing(o) {
  const n = (x) => (x === null || x === undefined ? null : num(x));
  const t = n(o.tickStartMs), s = n(o.sentAtMs), a = n(o.answeredAtMs);
  const ok = (x) => x !== null && Number.isFinite(x);
  return {
    tickStartMs: t, sentAtMs: s, answeredAtMs: a,
    startLateMs: ok(t) ? ((t % 60000) + 60000) % 60000 : null,
    startToSendMs: ok(t) && ok(s) ? s - t : null,
    answerMs: ok(s) && ok(a) ? a - s : null,
  };
}
function bookPairs(v) {
  if (!Array.isArray(v)) return null;
  const out = [];
  for (const l of v.slice(0, 5)) {
    const p = l && typeof l === "object" ? num(l.p) : null, q = l && typeof l === "object" ? num(l.q) : null;
    if (p !== null && q !== null && Number.isFinite(p) && Number.isFinite(q)) out.push([p, q]);
  }
  return out.length ? out : null;
}
function context(o) {
  const seen = o && typeof o.seen === "object" && o.seen ? o.seen : {};
  return {
    orderedCount: num(o.count), price: num(o.price), limit: num(o.limit), seenBid: num(seen.bid), seenAsk: num(seen.ask), bidSize: num(seen.bidSize), askSize: num(seen.askSize),
    depthAtLimit: num(o.depthAtLimit), shareOfDepth: num(o.shareOfDepth), depthLevels: typeof o.depthLevels === "string" ? o.depthLevels.slice(0, 12) : null,
    // Decision-time book (Nov 11, 2026, "P2"): the best 5 YES and 5 NO bids as [price, size] pairs, numbers only, best first; null when the order carries none.
    bookYes5: bookPairs(o.bookYes5), bookNo5: bookPairs(o.bookNo5), bookReadMs: o.bookReadMs === undefined || o.bookReadMs === null ? null : num(o.bookReadMs),
    addon: num(o.addon), rise3: num(o.rise3), smooth: typeof o.smooth === "boolean" ? o.smooth : null,
    // Kalshi's own status for the order (Nov 4, 2026, the refinement chat's no-fill table; logged on the order since #712): a short word such as "canceled" or "executed", letters and underscores only, null when not logged.
    // The early sell the exit watch stored on the order (Nov 6, 2026, the refinement chat: it could not tell when a gold early sell happened or what it sold for): exitAt is when, exitAvg is the price it sold at (0 to 1, null for no fill), exitBid the bid that triggered it. Numbers only; no exit order id.
    exitAt: Number.isFinite(Number(o.exitAt)) && Number(o.exitAt) > 0 ? new Date(Number(o.exitAt)).toISOString() : null, exitAvg: num(o.exitAvg), exitBid: num(o.exitBid),
    kalshiStatus: typeof o.kalshiStatus === "string" && /^[a-z_]{1,24}$/i.test(o.kalshiStatus) ? o.kalshiStatus.toLowerCase() : null,
    ...timing(o),
  };
}

function buildReport(orders, nowMs, hours, withOrders, slotOrders) {
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
    oversize: (() => { const r = oversizeRows(rows); return { count: r.length, orders: r.slice(0, 50) }; })(),
  };
  // The second slot (OICORE and any later strategy; the owner, Oct 30, 2026: "the report should include oicore since it's part of our strategies"). Kept SEPARATE from the L1 figures above, which are unchanged, so a
  // comparison with earlier reports still holds; allStrategies is the two added together, the figure the Bot page's Account result line shows. Slot orders are not size-checked here (maxContractsFor is L1's lock).
  const slotRows = (Array.isArray(slotOrders) ? slotOrders : []).filter((o) => o && Number(o.ts) >= since);
  const slotAll = emptyTally(), both = emptyTally(), bySlot = {}, slotMarket = {};
  slotRows.forEach((o) => {
    addTo(slotAll, o); addTo(both, o);
    const id = typeof o.slotId === "string" && o.slotId ? o.slotId.slice(0, 40) : "unknown"; bySlot[id] = bySlot[id] || emptyTally(); addTo(bySlot[id], o);
    const m = seriesOf(o); slotMarket[m] = slotMarket[m] || emptyTally(); addTo(slotMarket[m], o);
  });
  rows.forEach((o) => addTo(both, o));
  out.secondSlot = {
    total: finish(slotAll),
    byStrategy: Object.fromEntries(Object.keys(bySlot).sort().map((k) => [k, finish(bySlot[k])])),
    byMarket: Object.fromEntries(Object.keys(slotMarket).sort().map((k) => [k, finish(slotMarket[k])])),
  };
  out.allStrategies = finish(both);
  if (withOrders) {
    // One compact row per order. No order id, no client order id, nothing that identifies the account.
    out.orders = rows.slice().sort((a, b) => a.ts - b.ts).slice(-MAX_ORDER_ROWS).map((o) => ({
      ts: new Date(Number(o.ts)).toISOString(), ticker: o.ticker || null, side: o.side || null, count: num(o.fillCount), avgFill: num(o.averageFillPrice != null ? o.averageFillPrice : o.avgFill), avgFee: num(o.averageFeePaid != null ? o.averageFeePaid : o.avgFee),
      entryLead: o.entryLead || null, status: o.status || null, result: o.result || null, settledPnl: settledPnl(o), ...context(o),
    }));
    out.ordersTruncated = rows.length > MAX_ORDER_ROWS;
    // Slot rows are listed apart from L1's so the L1 row shape does not change; the strategy id replaces any order id.
    out.slotOrders = slotRows.slice().sort((a, b) => a.ts - b.ts).slice(-MAX_ORDER_ROWS).map((o) => ({
      ts: new Date(Number(o.ts)).toISOString(), strategy: typeof o.slotId === "string" ? o.slotId.slice(0, 40) : null, ticker: o.ticker || null, side: o.side || null, count: num(o.fillCount), avgFill: num(o.averageFillPrice != null ? o.averageFillPrice : o.avgFill), avgFee: num(o.averageFeePaid != null ? o.averageFeePaid : o.avgFee),
      // The open interest rise the signal fired on (Nov 12, 2026, "oiRise" log): a number, or null on an order that carries none. Slot rows only; the L1 row shape is unchanged.
      status: o.status || null, result: o.result || null, settledPnl: settledPnl(o), oiRise: num(o.oiRise), ...context(o),
    }));
  }
  return out;
}

// Second-slot skip reasons (Nov 5, 2026, the owner: "Save skip reasons"): the last SKIP_DAYS of the slot's skip documents, as a count per reason code and one row per document. The document holds
// strategy, ticker, a short fixed code, a few numbers and the minute; the row keeps those (numbers only in detail, a code that is not a short plain word is dropped) and never the document id.
const SKIP_DAYS = 7;
const SHADOW_DAYS = 90;
const MAX_SKIP_ROWS = 500;
// NEAR_MISS_CONTRACTS: an oi_below skip whose rise was within this many contracts under the strategy's line is a near miss (Nov 12, 2026; reporting only, it is not a rule and nothing reads it back).
const NEAR_MISS_CONTRACTS = 10000;
// `results` (optional) maps a market ticker to "yes" or "no", read from rows this report already has (settled shadow rows). The report makes no Kalshi call, so a market with no such row has result null.
function skipSection(docs, nowMs, results) {
  const since = nowMs - SKIP_DAYS * 86400000;
  const word = (v, n) => (typeof v === "string" && /^[A-Za-z0-9_]{1,40}$/.test(v) ? v.slice(0, n) : null);
  const rows = (Array.isArray(docs) ? docs : []).filter((d) => d && Number(d.atMs) >= since).map((d) => {
    const detail = {};
    if (d.detail && typeof d.detail === "object") for (const [k, v] of Object.entries(d.detail)) if (/^[A-Za-z]{1,20}$/.test(k) && typeof v === "number" && Number.isFinite(v)) detail[k] = v;
    return { at: new Date(Number(d.atMs)).toISOString(), atMs: Number(d.atMs), strategy: word(d.strategy, 40), ticker: typeof d.ticker === "string" && /^[A-Z0-9-]{1,60}$/.test(d.ticker) ? d.ticker : null,
      reason: word(d.reason, 40) || "unknown", secondsLeft: num(d.secondsLeft), detail: Object.keys(detail).length ? detail : null,
      side: d.side === "yes" || d.side === "no" ? d.side : (d.note === "yes" || d.note === "no" ? d.note : null),
      // A skip that happened after the strategy's trigger had passed (Nov 11, 2026, "P3"): qualified, the open interest rise and the price it would have bought, numbers and a flag only. Null on a skip that never triggered.
      qualified: d.qualified === true ? true : null, oiRise: d.qualified === true ? num(d.oiRise) : null, price: d.qualified === true ? num(d.price) : null };   // the side a skipped signal would have bought (the skip's note holds it for price skips); only "yes" or "no", never free text
  }).sort((a, b) => a.atMs - b.atMs);
  // The open interest join (Nov 12, 2026): per skip, the rise it was judged on (oiSeen: from the oi_below detail, or from the qualified fields), the line, how far under it (shortBy, only for oi_below)
  // and the market's result when a settled row for that ticker is on hand. All numbers or null; a missing rise stays null.
  const known = results && typeof results === "object" ? results : {};
  rows.forEach((r) => {
    const det = r.detail || {};
    const below = r.reason === "oi_below";
    r.oiSeen = below ? num(det.oiRise) : r.oiRise;
    r.oiMin = below ? num(det.min) : null;
    r.shortBy = below && r.oiSeen !== null && r.oiMin !== null ? Math.max(0, r.oiMin - r.oiSeen) : null;
    const res = r.ticker !== null && Object.prototype.hasOwnProperty.call(known, r.ticker) ? known[r.ticker] : null;
    r.result = res === "yes" || res === "no" ? res : null;
  });
  const oi = { belowLine: 0, nearMissLimit: NEAR_MISS_CONTRACTS, nearMisses: 0, nearMissByResult: { yes: 0, no: 0, unknown: 0 }, belowByResult: { yes: 0, no: 0, unknown: 0 } };
  rows.forEach((r) => {
    if (r.reason !== "oi_below") return;
    const k = r.result === null ? "unknown" : r.result;
    oi.belowLine += 1; oi.belowByResult[k] += 1;
    if (r.shortBy !== null && r.shortBy > 0 && r.shortBy <= NEAR_MISS_CONTRACTS) { oi.nearMisses += 1; oi.nearMissByResult[k] += 1; }
  });
  const byReason = {};
  rows.forEach((r) => { byReason[r.reason] = (byReason[r.reason] || 0) + 1; });
  return { days: SKIP_DAYS, count: rows.length, byReason: Object.fromEntries(Object.keys(byReason).sort().map((k) => [k, byReason[k]])), openInterest: oi, rows: rows.slice(-MAX_SKIP_ROWS) };
}

// ticker -> "yes" | "no" from settled shadow rows (the public market answer the shadow settler already stored). Nothing is asked of Kalshi here.
function resultsFromRows(rows) {
  const out = {};
  (Array.isArray(rows) ? rows : []).forEach((r) => { if (r && r.settled === true && typeof r.ticker === "string" && (r.result === "yes" || r.result === "no")) out[r.ticker] = r.result; });
  return out;
}

// Hourly balance snapshots (Nov 12, 2026): the whole asked window, at most one row an hour for 90 days. Only ts, total and per-shard cash survive; anything else on the document is dropped.
const MAX_BALANCE_ROWS = 2160;
function balanceSection(docs) {
  const rows = (Array.isArray(docs) ? docs : []).filter((d) => d && Number.isFinite(Number(d.ts)) && Number.isFinite(Number(d.total))).map((d) => ({
    ts: new Date(Number(d.ts)).toISOString(), total: Number(d.total),
    shards: (Array.isArray(d.shards) ? d.shards : []).slice(0, 10).filter((s) => s && Number.isFinite(Number(s.dollars))).map((s) => ({ shard: Number(s.shard), dollars: Number(s.dollars) })),
  })).sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0)).slice(-MAX_BALANCE_ROWS);
  return { count: rows.length, rows };
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
      // The slot read is optional and its failure never blanks the L1 report: the second slot section is then simply empty.
      let slotOrders = [];
      if (typeof deps.readSlotOrders === "function") { try { slotOrders = await deps.readSlotOrders(now - hours * 3600000); } catch (e) { if (typeof deps.logError === "function") deps.logError(e); } }
      // Which commit each function was deployed from (the deploy stamp). Optional, read only; a failure leaves the field out.
      let deploys;
      if (typeof deps.readDeploys === "function") { try { deploys = deployStampLib.summarize(await deps.readDeploys()); } catch (e) { if (typeof deps.logError === "function") deps.logError(e); } }
      // The second slot's skip reasons, last SKIP_DAYS whatever `hours` says. Optional, read only; a failure leaves the field out and never blanks the report.
      let shadowRows = null;
      if (typeof deps.readShadowRows === "function") { try { shadowRows = await deps.readShadowRows(now - SHADOW_DAYS * 86400000); } catch (e) { if (typeof deps.logError === "function") deps.logError(e); } }
      let skips;
      if (typeof deps.readSkips === "function") { try { skips = skipSection(await deps.readSkips(now - SKIP_DAYS * 86400000), now, resultsFromRows(shadowRows)); } catch (e) { if (typeof deps.logError === "function") deps.logError(e); } }
      // The shadow rules' score (lifecycle spec (c)): per rule, signals, cash PF per contract and the verdict against the written pass and kill rules. Optional, read only; a failure leaves the field out.
      let shadow;
      if (shadowRows !== null && typeof deps.shadowRules === "function") { try { shadow = { days: SHADOW_DAYS, rules: shadowLib.shadowReport(deps.shadowRules(), shadowRows, now).map((x) => (x.rule === "GOLDOFF" ? Object.assign({}, x, { returnRule: shadowLib.returnRule(x) }) : x)) }; } catch (e) { if (typeof deps.logError === "function") deps.logError(e); } }
      // The hourly balance history over the asked window. Optional, read only; a failure leaves the field out, an empty history is an empty list.
      let balanceHistory;
      if (typeof deps.readBalances === "function") { try { balanceHistory = balanceSection(await deps.readBalances(now - hours * 3600000)); } catch (e) { if (typeof deps.logError === "function") deps.logError(e); } }
      const report = buildReport(orders, now, hours, String((req.query && req.query.orders) || "") === "1", slotOrders);
      if (deploys !== undefined) report.deploys = deploys;
      if (skips !== undefined) report.skips = skips;
      if (shadow !== undefined) report.shadow = shadow;
      if (balanceHistory !== undefined) report.balanceHistory = balanceHistory;
      res.status(200).json(report);
    } catch (e) {
      // The caller learns nothing about why. The log gets the error's name and a short message (no token, no order data) so the owner can find the cause.
      if (typeof deps.logError === "function") deps.logError(e);
      res.status(500).json({ error: "could not read orders" });   // never echo the error text
    }
  };
}

module.exports = { buildReport, resultsFromRows, NEAR_MISS_CONTRACTS, makeReportHandler, sameToken, skipSection, balanceSection, MAX_BALANCE_ROWS, MAX_HOURS, MAX_ORDER_ROWS, SKIP_DAYS };
