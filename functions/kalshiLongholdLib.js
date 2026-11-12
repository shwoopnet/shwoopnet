"use strict";
// LONG-HOLD PAPER LOG, PHASE 1 (Nov 12, 2026; docs/LONGHOLD_DESIGN.md). A general, log-only rule type for markets that are NOT 15 minute markets: look some hours before the close, pick one market per event
// and per arm, record what a held-to-settlement order WOULD have cost and made, and score it. It is the paper step in front of any future long-hold order path (phase 2, not built).
//
// INERT BY CONSTRUCTION:
//   - LONGHOLD_RULES is EMPTY. No real configuration ships here; the first one is added later in a reviewed edit with its registration in front of it. With no rule the deployed functions make no read and no write for this module.
//   - It sends no order, holds no key, signs nothing, and imports no order, slot, sizing or L1 code. Its only network use is two kinds of PUBLIC GET, injected by the caller: a series market list (to choose) and a
//     single-market read (to price). Its only writes are its own two documents: the rows (kalshiLongholdRows) and the latch (kalshiLongholdControl/latch).
//   - Nothing that decides an order reads either collection.
//   - Every error is swallowed; a failed or slow read leaves everything else in the minute exactly as it was.
//
// PRICING: a row is priced from the SINGLE-MARKET read (GET /markets/{ticker}), never from the list read. The list read is a copy that can be up to about 11 seconds old (the Forensics audit), so it is used only to
// CHOOSE which market to look at; the quote seen, the would-be price and the fill test all come from the fresh single read, and a market whose fresh quote has left the arm's band records nothing.

const COLLECTION = "kalshiLongholdRows";
const CONTROL_COLLECTION = "kalshiLongholdControl";
const LATCH_DOC = "latch";

// ---- The request bound: code constants, small, and they count against nothing L1 needs (L1 makes none of these reads). ----------------------------
const LIMITS = Object.freeze({
  maxListReadsPerMinute: 1,       // one series list per minute, round robin over every (rule, series) pair
  maxPriceReadsPerMinute: 3,      // single-market reads that price a candidate; the rest wait for the next minute (the look window is wider than a minute)
  maxSettleReadsPerSweep: 3,      // single-market reads per settle sweep (every 5th minute)
  maxSeriesPerRule: 8,
  maxRules: 4,
  freshHours: 0.25,               // the look is taken in the first 15 minutes at or under lookMinHours before the close (the hourly snapshot of the registrations, "the last one at least N hours before")
});

// The registry: a hard list IN CODE. EMPTY. A configuration is a reviewed edit of this array plus its registration; nothing stored, requested or typed on a page can add or change one.
const LONGHOLD_RULES = Object.freeze([]);

const RULE_KEYS = ["id", "readme", "series", "lookMinHours", "lookMaxHours", "sideRule", "arms", "contracts", "limitSlip", "hold", "registeredAt", "forwardReadDate", "rearmAt", "kill", "returnRule"];
const ARM_KEYS = ["arm", "priceMin", "priceMax"];
const KILL_KEYS = ["afterFills", "netBelow", "lossStreak"];
const RETURN_KEYS = ["coolOffDays", "pf", "fills"];
const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const isObj = (x) => x && typeof x === "object" && !Array.isArray(x);
const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s + "T00:00:00Z"));
const exactKeys = (o, keys) => isObj(o) && Object.keys(o).sort().join() === keys.slice().sort().join();
const num = (x) => { const n = Number(x); return Number.isFinite(n) ? n : NaN; };
const r4 = (x) => Math.round(x * 10000) / 10000;

// A rule is refused whole unless every field is in range. Notably: a 15 minute series is refused (this is the NON-15-minute path), at most 3 contracts, hold to settlement only, kill rules required.
function validateLongholdRule(r) {
  const e = [];
  if (!exactKeys(r, RULE_KEYS)) return { ok: false, errors: ["a long-hold rule must have exactly these fields: " + RULE_KEYS.join(", ")] };
  if (!/^[A-Z0-9_]{2,16}$/.test(r.id)) e.push("id must be 2 to 16 capitals, digits or underscores");
  if (typeof r.readme !== "string" || !/^[\w./-]+\.md(#[\w-]+)?$/.test(r.readme)) e.push("readme must point at a pre-registration file");
  if (!Array.isArray(r.series) || !r.series.length || r.series.length > LIMITS.maxSeriesPerRule || new Set(r.series).size !== r.series.length || r.series.some((x) => typeof x !== "string" || !/^KX[A-Z0-9]{1,40}$/.test(x) || /15M$/.test(x))) e.push("series must be 1 to " + LIMITS.maxSeriesPerRule + " distinct KX tickers and none a 15 minute series");
  if (!isNum(r.lookMinHours) || !isNum(r.lookMaxHours) || r.lookMinHours < 2 || r.lookMaxHours > 72 || !(r.lookMinHours < r.lookMaxHours)) e.push("the look window must sit inside 2 to 72 hours before the close with min below max");
  if (r.sideRule !== "yes" && r.sideRule !== "no") e.push("sideRule must be yes or no");
  if (!Array.isArray(r.arms) || !r.arms.length || r.arms.length > 3) e.push("1 to 3 arms");
  else {
    const names = new Set();
    for (const a of r.arms) {
      if (!exactKeys(a, ARM_KEYS) || !/^[A-Z]$/.test(a.arm) || names.has(a.arm) || !isNum(a.priceMin) || !isNum(a.priceMax) || a.priceMin < 0.01 || a.priceMax > 0.99 || !(a.priceMin < a.priceMax)) { e.push("each arm needs a unique letter and a price band inside 0.01 to 0.99"); break; }
      names.add(a.arm);
    }
  }
  if (!Number.isInteger(r.contracts) || r.contracts < 1 || r.contracts > 3) e.push("contracts must be a whole number from 1 to 3");
  if (!isNum(r.limitSlip) || r.limitSlip < 0 || r.limitSlip > 0.05) e.push("limitSlip must be 0 to 0.05");
  if (r.hold !== "settlement") e.push("hold must be settlement");
  if (!isDate(r.registeredAt) || !isDate(r.forwardReadDate) || !isDate(r.rearmAt)) e.push("registeredAt, forwardReadDate and rearmAt must be YYYY-MM-DD");
  if (!exactKeys(r.kill, KILL_KEYS) || !Number.isInteger(r.kill.afterFills) || r.kill.afterFills < 1 || !isNum(r.kill.netBelow) || r.kill.netBelow >= 0 || !Number.isInteger(r.kill.lossStreak) || r.kill.lossStreak < 1) e.push("kill needs afterFills, a negative netBelow and lossStreak");
  if (!exactKeys(r.returnRule, RETURN_KEYS) || !Number.isInteger(r.returnRule.coolOffDays) || r.returnRule.coolOffDays < 1 || !isNum(r.returnRule.pf) || r.returnRule.pf < 1 || !Number.isInteger(r.returnRule.fills) || r.returnRule.fills < 1) e.push("returnRule needs coolOffDays, pf (1 or more) and fills");
  return { ok: e.length === 0, errors: e };
}

// The registry is refused whole if any entry is invalid or an id repeats, so a typo cannot quietly drop one guard and keep the rest.
function activeLongholdRules(rules) {
  const reg = rules === undefined ? LONGHOLD_RULES : rules;
  if (!Array.isArray(reg) || !reg.length || reg.length > LIMITS.maxRules) return [];
  const ids = new Set();
  for (const r of reg) { if (!validateLongholdRule(r).ok || ids.has(r.id)) return []; ids.add(r.id); }
  return reg.slice();
}

// ---- Which series to list this minute: one, round robin, so the whole registry costs one list read a minute at most. -----------------------------
function longholdSeriesDue(rules, nowMs) {
  const pairs = [];
  for (const r of Array.isArray(rules) ? rules : []) for (const s of r.series) pairs.push({ rule: r, series: s });
  if (!pairs.length) return [];
  return [pairs[Math.floor(nowMs / 60000) % pairs.length]].slice(0, LIMITS.maxListReadsPerMinute);
}

const eventOf = (m) => (typeof m.event_ticker === "string" && m.event_ticker ? m.event_ticker : String(m.ticker).replace(/-[^-]*$/, ""));
// The touch price of the side the rule buys (before slip): a NO buy meets the YES bid, a YES buy meets the YES ask. Whole cents, the way the shadow rules read them.
function sidePrice(side, bid, ask) { return side === "yes" ? Math.ceil(r4(ask) * 100 - 1e-9) / 100 : Math.round((1 - Math.floor(r4(bid) * 100 + 1e-9) / 100) * 100) / 100; }
const twoSided = (bid, ask) => bid > 0 && ask > 0 && ask > bid && ask <= 1 && bid < 1;

// PURE. From a (possibly stale) series list, the CHOICES to go and price: per event and per arm, among the event's open markets inside the look window whose side price lands in the arm's band, the one whose
// YES mid is nearest 0.5 (ties by ticker). Not chosen by result. Nothing here is a price to record; the fresh single read decides that.
function longholdCandidates(rule, series, markets, nowMs) {
  const out = [];
  if (!Array.isArray(markets)) return out;
  const byEvent = new Map();
  for (const m of markets) {
    try {
      if (!m || m.status === undefined || !["open", "active"].includes(m.status) || !/^[A-Z0-9-]+$/.test(String(m.ticker))) continue;
      const left = (Date.parse(m.close_time) - nowMs) / 1000;
      if (!(left >= rule.lookMinHours * 3600 && left <= (rule.lookMinHours + LIMITS.freshHours) * 3600 && left <= rule.lookMaxHours * 3600)) continue;
      const bid = num(m.yes_bid_dollars), ask = num(m.yes_ask_dollars);
      if (!twoSided(bid, ask)) continue;
      const k = eventOf(m);
      if (!byEvent.has(k)) byEvent.set(k, []);
      byEvent.get(k).push({ m, bid, ask, mid: (bid + ask) / 2, price: sidePrice(rule.sideRule, bid, ask), left });
    } catch (e) { /* one bad market never stops the rest */ }
  }
  for (const [event, list] of byEvent) {
    for (const arm of rule.arms) {
      const inBand = list.filter((x) => x.price >= arm.priceMin - 1e-9 && x.price <= arm.priceMax + 1e-9)
        .sort((a, b) => Math.abs(a.mid - 0.5) - Math.abs(b.mid - 0.5) || (String(a.m.ticker) < String(b.m.ticker) ? -1 : 1));
      if (inBand.length) out.push({ rule: rule.id, arm: arm.arm, event, series, ticker: String(inBand[0].m.ticker) });
    }
  }
  return out;
}

// PURE. The row, priced from the single-market read `m`. Null (nothing recorded) unless that fresh quote is two-sided, the market is open and the same one, still inside the look window, and the side price is still in
// the arm's band. The would-be price is the touch plus the limit slip. wouldFill: the size resting at the touch we would hit covers the contracts.
function longholdRow(rule, cand, m, nowMs) {
  try {
    if (!m || String(m.ticker) !== cand.ticker || !["open", "active"].includes(m.status)) return null;
    const arm = rule.arms.find((a) => a.arm === cand.arm);
    if (!arm) return null;
    const closeMs = Date.parse(m.close_time), left = (closeMs - nowMs) / 1000;
    if (!(left >= rule.lookMinHours * 3600 && left <= rule.lookMaxHours * 3600)) return null;
    const bid = num(m.yes_bid_dollars), ask = num(m.yes_ask_dollars);
    if (!twoSided(bid, ask)) return null;
    const touch = sidePrice(rule.sideRule, bid, ask);
    if (touch < arm.priceMin - 1e-9 || touch > arm.priceMax + 1e-9) return null;
    const price = Math.min(0.99, Math.round((touch + rule.limitSlip) * 100) / 100);
    const depth = num(rule.sideRule === "yes" ? m.yes_ask_size_fp : m.yes_bid_size_fp);
    return { rule: rule.id, arm: cand.arm, event: cand.event, ticker: cand.ticker, series: cand.series, side: rule.sideRule, contracts: rule.contracts,
      yesBid: bid, yesAsk: ask, touch, price, depth: Number.isFinite(depth) ? depth : null, wouldFill: Number.isFinite(depth) ? depth >= rule.contracts : null,
      secondsLeft: Math.round(left), closeMs, closeTime: String(m.close_time), source: "single-market", settled: false, atMs: nowMs };
  } catch (e) { return null; }
}

// Cash basis, the fee unrounded at 0.07 x p x (1 - p) per contract (the registrations' fee), times the contracts.
function longholdFee(price) { const p = Number(price); return p > 0 && p < 1 ? 0.07 * p * (1 - p) : NaN; }
function longholdOutcome(row, result) {
  if (!row || (result !== "yes" && result !== "no") || (row.side !== "yes" && row.side !== "no")) return null;
  const fee = longholdFee(row.price), n = Number(row.contracts);
  if (!Number.isFinite(fee) || !(n >= 1)) return null;
  const won = row.side === result;
  return { result, won, pnl: r4(n * (won ? 1 - row.price - fee : -(row.price + fee))) };
}

// ---- The latch: the registered kill rules, replayed from SETTLED rows that could have filled, per arm, counting only rows from the rule's rearmAt on. --------
// STICKY: it is tripped if the rule was met at ANY point of the replay (a later recovery does not lift it), and the tripped state is also stored (latchDoc) with the rearmAt it was tripped under. A stored latch
// binds only while its rearmAt equals the code's: bumping rearmAt is the reviewed edit that re-arms. Nothing stored can un-trip an arm.
function armVerdict(rule, rows, armName) {
  const since = Date.parse(rule.rearmAt + "T00:00:00Z");
  const fills = rows.filter((d) => d && d.rule === rule.id && d.arm === armName && d.settled === true && d.wouldFill === true && Number(d.atMs) >= since && Number.isFinite(Number(d.pnl))).sort((a, b) => Number(a.closeMs) - Number(b.closeMs) || Number(a.atMs) - Number(b.atMs));
  let net = 0, streak = 0, reason = null;
  fills.forEach((d, i) => {
    net += Number(d.pnl); streak = Number(d.pnl) < 0 ? streak + 1 : 0;
    if (!reason && i + 1 >= rule.kill.afterFills && net < rule.kill.netBelow) reason = "net under " + rule.kill.netBelow + " after " + rule.kill.afterFills + " fills";
    if (!reason && streak >= rule.kill.lossStreak) reason = rule.kill.lossStreak + " losses in a row";
  });
  return { arm: armName, tripped: reason !== null, reason, fills: fills.length, net: r4(net) };
}
function latchVerdict(rule, rows, latchDoc) {
  return rule.arms.map((a) => {
    const v = armVerdict(rule, rows, a.arm);
    const stored = latchDoc && latchDoc[rule.id] && latchDoc[rule.id][a.arm];
    if (!v.tripped && stored && stored.tripped === true && stored.rearmAt === rule.rearmAt) return Object.assign(v, { tripped: true, reason: String(stored.reason || "stored latch"), stored: true });
    return v;
  });
}
const armLatched = (rule, arm, latchDoc) => { const s = latchDoc && latchDoc[rule.id] && latchDoc[rule.id][arm]; return Boolean(s && s.tripped === true && s.rearmAt === rule.rearmAt); };

// ---- One minute ------------------------------------------------------------------------------------------------------------------------------------
// args: now, rules, listMarkets(series) (public list), market(ticker) (public single read), readLatch() -> doc or null, record(row) (create-if-absent), seen (Set).
// Order of cheapness and caution: at most one list read; choices; drop what this instance already did; at most maxPriceReadsPerMinute single reads; the latch is read ONLY when a row is about to be written, and
// an unreadable latch writes nothing (fail closed). Returns counts only. Every error is swallowed.
async function runLongholdTick(args) {
  const out = { listReads: 0, priceReads: 0, written: 0 };
  try {
    const rules = activeLongholdRules(args.rules);
    if (!rules.length) return { skipped: "no long-hold rule", listReads: 0, priceReads: 0, written: 0 };
    const seen = args.seen instanceof Set ? args.seen : new Set();
    const due = longholdSeriesDue(rules, args.now);
    let markets;
    for (const d of due) {
      try { out.listReads += 1; markets = await args.listMarkets(d.series); } catch (e) { return out; }
      const cands = longholdCandidates(d.rule, d.series, markets, args.now).filter((c) => !seen.has(c.rule + "|" + c.arm + "|" + c.event));
      let latch;
      for (const c of cands) {
        if (out.priceReads >= LIMITS.maxPriceReadsPerMinute) break;
        try {
          out.priceReads += 1;
          const row = longholdRow(d.rule, c, await args.market(c.ticker), args.now);
          if (!row) continue;
          if (latch === undefined) latch = (await args.readLatch()) || {};      // a throw lands in the catch below: nothing is written
          if (armLatched(d.rule, c.arm, latch)) continue;
          seen.add(c.rule + "|" + c.arm + "|" + c.event);
          try { await args.record(row); out.written += 1; } catch (e) { /* already logged by the other process, or a failed write: log only */ }
        } catch (e) { /* one candidate never stops the rest */ }
      }
    }
    if (seen.size > 5000) seen.clear();
  } catch (e) { /* log only */ }
  return out;
}

// ---- Settlement and the latch write ----------------------------------------------------------------------------------------------------------------
// args: now, rules, readOpen() (unsettled rows), market(ticker), update(id, patch), readSettled(ruleId), readLatch(), writeLatch(patch). At most maxSettleReadsPerSweep reads, an 8 s guard, then the latch is
// re-evaluated from the settled rows and written only if an arm is newly tripped.
function rowId(d) { return String(d.rule) + "_" + String(d.arm) + "_" + String(d.event); }
async function settleLongholdRows(args) {
  const out = { checked: 0, settled: 0, latched: [] };
  try {
    const rules = activeLongholdRules(args.rules);
    if (!rules.length) return out;
    const open = (await args.readOpen()).filter((r) => r && r.settled === false && Number.isFinite(Number(r.closeMs)) && Number(r.closeMs) + 120000 <= args.now && rules.some((x) => x.id === r.rule)).sort((a, b) => Number(a.closeMs) - Number(b.closeMs)).slice(0, LIMITS.maxSettleReadsPerSweep);
    const started = typeof args.clock === "function" ? args.clock() : Date.now(), budgetMs = Number.isFinite(args.budgetMs) ? args.budgetMs : 8000;
    for (const r of open) {
      if ((typeof args.clock === "function" ? args.clock() : Date.now()) - started > budgetMs) break;
      out.checked += 1;
      try {
        const m = await args.market(String(r.ticker));
        const o = longholdOutcome(r, m && typeof m.result === "string" ? m.result.toLowerCase() : "");
        if (!o) continue;
        await args.update(rowId(r), { settled: true, result: o.result, won: o.won, pnl: o.pnl, settledAtMs: args.now });
        out.settled += 1;
      } catch (e) { /* the next sweep tries again */ }
    }
    if (out.settled) {
      for (const rule of rules) {
        try {
          const latch = (await args.readLatch()) || {};
          const patch = {};
          for (const v of latchVerdict(rule, await args.readSettled(rule.id), latch)) {
            if (v.tripped && !v.stored) { patch[rule.id] = Object.assign(patch[rule.id] || {}, { [v.arm]: { tripped: true, reason: v.reason, rearmAt: rule.rearmAt, atMs: args.now } }); out.latched.push(rule.id + "/" + v.arm); }
          }
          if (Object.keys(patch).length) await args.writeLatch(patch);
        } catch (e) { /* the replay still holds the verdict */ }
      }
    }
  } catch (e) { /* log only */ }
  return out;
}

// ---- The nightly report: compact rows, numbers and short labels only. No ticker, no event, no document id. ---------------------------------------------
const DAY = 86400000;
function pfOf(list) { let w = 0, l = 0; for (const d of list) { if (d.pnl > 0) w += d.pnl; else if (d.pnl < 0) l += -d.pnl; } return { pf: l > 0 ? Math.round((w / l) * 100) / 100 : null, net: r4(w - l) }; }
function longholdReport(rules, docs, nowMs) {
  const all = (Array.isArray(docs) ? docs : []).filter((d) => d && typeof d.rule === "string" && Number.isFinite(Number(d.atMs)));
  return (Array.isArray(rules) ? rules : []).map((rule) => ({
    rule: rule.id,
    arms: rule.arms.map((a) => {
      const mine = all.filter((d) => d.rule === rule.id && d.arm === a.arm);
      const settled = mine.filter((d) => d.settled === true && Number.isFinite(Number(d.pnl))).map((d) => ({ pnl: Number(d.pnl), wouldFill: d.wouldFill === true, atMs: Number(d.atMs) }));
      const fill = settled.filter((d) => d.wouldFill);
      const f = pfOf(fill), v = armVerdict(rule, all, a.arm);
      const since = Date.parse(rule.rearmAt + "T00:00:00Z");
      const sinceFill = fill.filter((d) => d.atMs >= since);
      const days = mine.length ? Math.round(((nowMs - Math.min(...mine.map((d) => Number(d.atMs)))) / DAY) * 10) / 10 : 0;
      const ret = pfOf(sinceFill);
      return { arm: a.arm, rows: mine.length, settled: settled.length, fillable: fill.length, wins: settled.filter((d) => d.pnl > 0).length, pfFillable: f.pf, netFillableDollars: f.net, days,
        latched: v.tripped, latchReason: v.reason,
        returnRule: { needFills: rule.returnRule.fills, needPf: rule.returnRule.pf, coolOffDays: rule.returnRule.coolOffDays, fillsSinceRearm: sinceFill.length, pfSinceRearm: ret.pf,
          statsMet: sinceFill.length >= rule.returnRule.fills && ret.pf !== null && ret.pf >= rule.returnRule.pf, ownerApprovalNeeded: true } };
    }),
  }));
}

module.exports = { COLLECTION, CONTROL_COLLECTION, LATCH_DOC, LIMITS, LONGHOLD_RULES, validateLongholdRule, activeLongholdRules, longholdSeriesDue, longholdCandidates, longholdRow, longholdFee, longholdOutcome,
  armVerdict, latchVerdict, runLongholdTick, settleLongholdRows, longholdReport, rowId };
