"use strict";
// SHADOW RULES (Nov 9, 2026, lifecycle spec docs/STRATEGY_LIFECYCLE.md, stage 1). A shadow rule is a registered entry rule that only LOGS what it would have bought, with no money at risk:
// it sends no order, makes no Kalshi request, reads no key and writes only its own log collection. It exists so a candidate can collect 150 forward signals (cash PF 1.3 or better, 7 days)
// before it is allowed an incubator slot, and so the research and refinement chats can feed a constant queue of candidates into the bot without risking money.
//
// The registry is a hard list IN CODE (SHADOW_RULES). Nothing stored, requested or typed on the page can add or change a rule; adding one is a reviewed edit and a deploy, like the slot registry.
// It starts EMPTY: with no rule registered the deployed functions make exactly the reads, writes and orders they made before (the off-equivalence fixtures prove it).
//
// Quote source: the market list the bot's minute function already holds (the L1 markets: gold, Bitcoin, Ethereum, XRP), so a shadow rule costs zero extra requests. Another market needs its quote read added
// in a reviewed edit (as EVENT830's markets were), not here.
// WEEK 1 (Nov 9, 2026; the weekly candidate list from the refinement chat, pre-registration kalshi-scalper/README.md#SHADOW-WEEK1). Four rules, each on a market the bot already quotes, 1 contract, log only.
// Every one is a SHADOW candidate, never a pass (N about 670 on top of about 540; no counterparty named for any). Shadow rows assume a fill at the touch (an upper bound): read `wouldFill`.
const RULE = (id, series, entry, anchor = "SHADOW-WEEK1") => Object.freeze({ id, readme: "kalshi-scalper/README.md#" + anchor, series: Object.freeze([series]), entry: Object.freeze(entry), contracts: 1, registeredAt: "2026-11-09", forwardReadDate: "2026-12-14" });
const SHADOW_RULES = Object.freeze([
  // ETHNO6 was retired before its first row (Nov 10, 2026): on 4.3 weeks of Ethereum candles (2,609 windows) it fails, PF 1.04 / 0.72 at +0c; its live PF 2.59 (n 53) was its only support. See kalshi-scalper/README.md#SHADOW-WEEK2.
  // BTCHI6 was retired before its first row (Nov 10, 2026): on an independent window (Jun to Sep, 1,206 windows) it is PF 1.13 at +0c and 0.91 at +1c, under the 1.3 bar. See kalshi-scalper/README.md#SHADOW-WEEK2.
  RULE("XRPYES10", "KXXRP15M", { sideRule: "yes", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }),
  // ETHL1 was retired before its first row (Nov 10, 2026): the refinement chat's candle recheck found it under 1.0 in both halves at +1c (0.92 / 1.10 at +0c); see kalshi-scalper/README.md#SHADOW-WEEK2.
  // GOLDALL (Nov 9, 2026, the refinement chat's forward test of the gold momentum lead, kalshi-scalper/README.md#SHADOW-GOLDALL): L1's own entry on gold, logged for EVERY signal ordered or not, so the 3 minute move (rise3) can be read from public candles at read time and the pre-registered split (|rise3| at least 0.05, "moving") scored against the unfiltered baseline on the same rows.
  RULE("GOLDALL", "KXGOLD15M", { sideRule: "favourite", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, "SHADOW-GOLDALL"),
  // WEEK 2 (Nov 10, 2026; the refinement chat's batch 2 after the fee fix, kalshi-scalper/README.md#SHADOW-WEEK2). Best of 120 cells, so selection bias is likely: SHADOW candidates only, prior low on both. BTCHI10 and XRPFAV10 were dropped before merge (BTCHI10 fails an earlier out of sample period, PF 0.90 on Jun to Aug against 1.62 on Sep to Nov; XRPFAV10 is the same low prior XRP selection). XRPFAV6 and GOLDHI6S use the optional maxSpread (YES spread at most 2c).
  RULE("XRPFAV6", "KXXRP15M", { sideRule: "favourite", priceMin: 0.88, priceMax: 0.92, leftMaxSec: 400, leftMinSec: 330, maxSpread: 0.02 }, "SHADOW-WEEK2"),
  RULE("GOLDHI6S", "KXGOLD15M", { sideRule: "favourite", priceMin: 0.92, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330, maxSpread: 0.02 }, "SHADOW-WEEK2"),
  // LANTERN (Nov 10, 2026, kalshi-scalper/README.md#SHADOW-LANTERN): the owner's decision Nov 10 on Ethereum (live cash PF 1.18, n 113): it comes back through shadow first and returns live only at cash PF 1.3+ over the shadow sample, 150 forward signals, held out second half 1.2, at least 14 days. L1's own rule on Ethereum at the 6 minute look with NO smooth gate: the smooth climb split can be computed by the reader from public candles at read time (not built here). ETHL1 was registered then retired Nov 10 after the refinement chat's candle recheck found it under 1.0 in both halves at +1c, so this is re-registered against that recheck and a pass is not expected (prior low). Forward read about 2026-12-22.
  Object.freeze({ ...RULE("LANTERN", "KXETH15M", { sideRule: "favourite", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, "SHADOW-LANTERN"), forwardReadDate: "2026-12-22" }),
]);

const OPEN = ["open", "active"];
const RULE_KEYS = ["id", "readme", "series", "entry", "contracts", "registeredAt", "forwardReadDate"];
const ENTRY_KEYS = ["sideRule", "priceMin", "priceMax", "leftMaxSec", "leftMinSec"];
const ENTRY_KEYS_SPREAD = ENTRY_KEYS.concat(["maxSpread"]);
const SIDE_RULES = ["yes", "no", "favourite", "cheap"];
const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const isObj = (x) => x && typeof x === "object" && !Array.isArray(x);
const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s + "T00:00:00Z"));
const exactKeys = (o, keys) => isObj(o) && Object.keys(o).sort().join() === keys.slice().sort().join();
const num = (x) => { const n = Number(x); return Number.isFinite(n) ? n : NaN; };
const r4 = (x) => Math.round(x * 10000) / 10000;

// A shadow rule can only look at markets the bot already quotes. The caller passes the allowed series (the live L1 list); a rule naming anything else is refused.
function validateShadowRule(r, allowedSeries) {
  const e = [];
  if (!exactKeys(r, RULE_KEYS)) return { ok: false, errors: ["a shadow rule must have exactly these fields: " + RULE_KEYS.join(", ")] };
  if (!/^[A-Z0-9]{2,12}$/.test(r.id)) e.push("id must be 2 to 12 capitals or digits");
  if (typeof r.readme !== "string" || !/^[\w./-]+\.md(#[\w-]+)?$/.test(r.readme)) e.push("readme must point at a pre-registration file");
  const allowed = Array.isArray(allowedSeries) ? allowedSeries : [];
  if (!Array.isArray(r.series) || !r.series.length || new Set(r.series).size !== r.series.length || r.series.some((x) => !allowed.includes(x))) e.push("series must be a non-empty subset of the markets the bot already quotes: " + allowed.join(", "));
  if (!exactKeys(r.entry, ENTRY_KEYS) && !exactKeys(r.entry, ENTRY_KEYS_SPREAD)) e.push("entry has the wrong fields");
  else {
    const x = r.entry;
    if (!SIDE_RULES.includes(x.sideRule)) e.push("entry.sideRule must be yes, no, favourite or cheap");
    if (!isNum(x.priceMin) || !isNum(x.priceMax) || x.priceMin < 0.01 || x.priceMax > 0.99 || !(x.priceMin < x.priceMax)) e.push("entry price bounds must sit inside 0.01 to 0.99 with priceMin below priceMax");
    if (!isNum(x.leftMaxSec) || !isNum(x.leftMinSec) || x.leftMinSec < 60 || x.leftMaxSec > 840 || !(x.leftMinSec < x.leftMaxSec)) e.push("entry time left must sit inside 60 to 840 seconds");
    if (Object.prototype.hasOwnProperty.call(x, "maxSpread") && !(isNum(x.maxSpread) && x.maxSpread >= 0.01 && x.maxSpread <= 0.2)) e.push("entry.maxSpread must be 0.01 to 0.20");
  }
  if (!Number.isInteger(r.contracts) || r.contracts < 1 || r.contracts > 10) e.push("contracts must be a whole number from 1 to 10");
  if (!isDate(r.registeredAt) || !isDate(r.forwardReadDate)) e.push("registeredAt and forwardReadDate must be YYYY-MM-DD");
  return { ok: e.length === 0, errors: e };
}

// The rules that may act: the registry is refused whole if any entry is invalid or an id repeats (a typo cannot quietly drop one guard and keep the rest).
function activeShadowRules(rules, allowedSeries) {
  const reg = rules === undefined ? SHADOW_RULES : rules;
  if (!Array.isArray(reg) || !reg.length) return [];
  const ids = new Set();
  for (const r of reg) { if (!validateShadowRule(r, allowedSeries).ok || ids.has(r.id)) return []; ids.add(r.id); }
  return reg.slice();
}

// PURE. From the quotes in hand, the shadow signals of this minute: for every rule and every open market of its series inside its entry window, with a two-sided quote, the side the rule would take
// and the price at the touch; only a price inside the rule's band is a signal. No order, no request, no write. A row is a plain object of numbers and short labels.
function shadowSignals(rules, quotes, nowMs) {
  const out = [];
  if (!Array.isArray(rules) || !rules.length || !Array.isArray(quotes)) return out;
  for (const r of rules) {
    for (const q of quotes) {
      try {
        if (!q || !q.m || !r.series.includes(q.series) || !OPEN.includes(q.m.status)) continue;
        const closeMs = Date.parse(q.m.close_time);
        const left = (closeMs - nowMs) / 1000;
        if (!(left >= r.entry.leftMinSec && left <= r.entry.leftMaxSec)) continue;
        const bid = num(q.m.yes_bid_dollars), ask = num(q.m.yes_ask_dollars);
        if (!(bid > 0 && ask > 0 && ask > bid && ask <= 1 && bid < 1)) continue;
        const spread = r4(ask - bid);
        if (Object.prototype.hasOwnProperty.call(r.entry, "maxSpread") && !(spread <= r.entry.maxSpread + 1e-9)) continue;
        const yesPrice = Math.ceil(r4(ask) * 100 - 1e-9) / 100, noPrice = Math.round((1 - Math.floor(r4(bid) * 100 + 1e-9) / 100) * 100) / 100;
        const side = r.entry.sideRule === "favourite" ? (yesPrice >= noPrice ? "yes" : "no") : r.entry.sideRule === "cheap" ? (yesPrice < noPrice ? "yes" : "no") : r.entry.sideRule;
        const price = side === "yes" ? yesPrice : noPrice;
        if (price < r.entry.priceMin - 1e-9 || price > r.entry.priceMax + 1e-9) continue;
        // The size resting at the touch we would hit (buying YES meets the YES ask size, buying NO meets the YES bid size); the book carries only the top level.
        const depth = num(side === "yes" ? q.m.yes_ask_size_fp : q.m.yes_bid_size_fp);
        out.push({ rule: r.id, ticker: String(q.m.ticker), series: String(q.series), side, price, size: r.contracts, depth: Number.isFinite(depth) ? depth : null,
          wouldFill: Number.isFinite(depth) ? depth >= r.contracts : null, bid, ask, spread, secondsLeft: Math.round(left), closeTime: String(q.m.close_time), closeMs, settled: false, atMs: nowMs });
      } catch (e) { /* one bad market never stops the rest */ }
    }
  }
  return out;
}

const COLLECTION = "kalshiShadowRows";
// The first in-band look of each rule and market wins (create fails if the row exists, which is swallowed), so one decision per window is logged and the later minutes of the same window change nothing.
function shadowWriter(db) {
  return (d) => db.collection(COLLECTION).doc(String(d.rule) + "_" + String(d.ticker)).create(d);
}

// One minute's shadow run: signals from the quotes in hand, written after everything that can trade has run. Returns a count only. Every error is swallowed: a shadow rule must never fail a tick.
// `seen` is a per instance memory so a repeat look in the same window does not even try the write.
async function runShadowTick(args) {
  try {
    const rules = activeShadowRules(args.rules, args.allowedSeries);
    if (!rules.length) return { skipped: "no shadow rule" };
    const rows = shadowSignals(rules, args.quotes, args.now);
    const seen = args.seen instanceof Set ? args.seen : new Set();
    const fresh = [];
    for (const d of rows) { const key = d.rule + "|" + d.ticker; if (seen.has(key)) continue; seen.add(key); fresh.push(d); }
    // In parallel, so a slow write never delays the rest of the minute by more than one round trip; each one is swallowed on its own.
    const results = await Promise.all(fresh.map(async (d) => { try { await args.record(d); return 1; } catch (e) { return 0; } }));   // already logged this window, or a failed write: log only
    const written = results.reduce((a, b) => a + b, 0);
    if (seen.size > 5000) seen.clear();
    return { signals: rows.length, written };
  } catch (e) { return { skipped: "shadow failed" }; }
}

// ---- Settlement and scoring (lifecycle spec (c)) ---------------------------------------------------------------------------------------------------------------
// A shadow row is settled from the PUBLIC market answer (no key, no order): once the market has a result, the row gets result, won and pnl, the dollars one contract of it would have made on the CASH
// basis (the side's price plus the fee; the fee is the 10 contract fee the research uses, 7% of P x (1 - P) per contract rounded up to the cent on 10 contracts, so every number is comparable with the
// research record and with a real 10 contract order). It assumes a fill at the touch, which is an upper bound; `wouldFill` says whether the touch could cover the size.
function shadowFee(price) {
  const p = Number(price);
  if (!(p > 0 && p < 1)) return NaN;
  return Math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 100 / 10;
}
function shadowOutcome(row, result) {
  if (!row || (result !== "yes" && result !== "no")) return null;
  const fee = shadowFee(row.price);
  if (!Number.isFinite(fee) || (row.side !== "yes" && row.side !== "no")) return null;
  const won = row.side === result;
  return { result, won, fee, pnl: Math.round((won ? 1 - row.price - fee : -(row.price + fee)) * 10000) / 10000 };
}
// Settle at most `max` unsettled rows whose market closed at least 2 minutes ago. Public reads only, every error swallowed, one row at a time so a slow answer costs one round trip.
async function settleShadowRows(args) {
  const out = { checked: 0, settled: 0 };
  try {
    const max = Number.isInteger(args.max) && args.max > 0 ? Math.min(args.max, 20) : 12;
    const rows = (await args.readOpen()).filter((r) => r && r.settled === false && Number.isFinite(Number(r.closeMs)) && Number(r.closeMs) + 120000 <= args.now).sort((a, b) => Number(a.closeMs) - Number(b.closeMs)).slice(0, max);
    const started = typeof args.clock === "function" ? args.clock() : Date.now(), budgetMs = Number.isFinite(args.budgetMs) ? args.budgetMs : 15000;
    for (const r of rows) {
      // A time guard (security review note): the reads are one after another at the end of a minute function with a hard timeout, so stop after the budget and leave the rest for the next run.
      if ((typeof args.clock === "function" ? args.clock() : Date.now()) - started > budgetMs) break;
      out.checked += 1;
      try {
        const m = await args.market(String(r.ticker));
        const result = m && typeof m.result === "string" ? m.result.toLowerCase() : "";
        const o = shadowOutcome(r, result);
        if (!o) continue;
        await args.update(String(r.rule) + "_" + String(r.ticker), { settled: true, result: o.result, won: o.won, fee: o.fee, pnl: o.pnl, settledAtMs: args.now });
        out.settled += 1;
      } catch (e) { /* the next run tries again */ }
    }
  } catch (e) { /* log only */ }
  return out;
}

// The nightly scorer's read of the shadow log: per rule, signals, settled, wins, cash PF per contract (all signals, and only those the touch could fill), net cents per contract, days, signals in the
// last 30 days, and the lifecycle verdict against the written rules (docs/STRATEGY_LIFECYCLE.md section 3 and 4). Numbers and short labels only: no ticker, no document id.
const DAY = 86400000;
function pfOf(rows) {
  let w = 0, l = 0;
  for (const r of rows) { if (r.pnl > 0) w += r.pnl; else if (r.pnl < 0) l += -r.pnl; }
  return { gw: Math.round(w * 10000) / 10000, gl: Math.round(l * 10000) / 10000, pf: l > 0 ? Math.round((w / l) * 100) / 100 : null, n: rows.length, net: Math.round((w - l) * 10000) / 10000 };
}
function shadowReport(rules, docs, nowMs) {
  const all = (Array.isArray(docs) ? docs : []).filter((d) => d && typeof d.rule === "string" && Number.isFinite(Number(d.atMs)));
  return (Array.isArray(rules) ? rules : []).map((rule) => {
    const mine = all.filter((d) => d.rule === rule.id).sort((a, b) => Number(a.atMs) - Number(b.atMs));
    const settled = mine.filter((d) => d.settled === true && Number.isFinite(Number(d.pnl))).map((d) => ({ pnl: Number(d.pnl), wouldFill: d.wouldFill === true, atMs: Number(d.atMs) }));
    const fill = settled.filter((d) => d.wouldFill);
    const a = pfOf(settled), f = pfOf(fill);
    const first = mine.length ? Number(mine[0].atMs) : null, last = mine.length ? Number(mine[mine.length - 1].atMs) : null;
    const days = first === null ? 0 : Math.round(((nowMs - first) / DAY) * 10) / 10;
    const half = fill.length >= 2 ? pfOf(fill.slice(Math.floor(fill.length / 2))) : null;
    const byDay = {};
    for (const d of fill) { const k = new Date(d.atMs).toISOString().slice(0, 10); byDay[k] = (byDay[k] || 0) + d.pnl; }
    const topDay = f.net > 0 ? Math.max(...Object.values(byDay)) / f.net : null;
    const netCents = fill.length ? Math.round((f.net / fill.length) * 1000) / 10 : null;
    const last30 = mine.filter((d) => Number(d.atMs) >= nowMs - 30 * DAY).length;
    // Verdict, in the order the written rules apply: a kill first, then a retire for too few signals, then the pass to incubator, else collecting.
    let status = "collecting";
    if (fill.length >= 50 && netCents !== null && netCents < -1) status = "kill: net under -1c per contract after 50 signals";
    else if (days >= 30 && last30 < 40) status = "retire: under 40 signals in 30 days";
    else if (fill.length >= 150 && days >= 14 && f.pf !== null && f.pf >= 1.3 && half && half.pf !== null && half.pf >= 1.2 && topDay !== null && topDay <= 0.3) status = "ready: meets the shadow pass rule, owner packet next";
    return { rule: rule.id, signals: mine.length, settled: settled.length, fillable: fill.length, wins: settled.filter((d) => d.pnl > 0).length, pf: a.pf, pfFillable: f.pf, netFillableDollars: f.net, netCentsPerContract: netCents,
      secondHalfPf: half ? half.pf : null, topDayShareOfNet: topDay === null ? null : Math.round(topDay * 100) / 100, days, signalsLast30d: last30, status };
  });
}

module.exports = { SHADOW_RULES, validateShadowRule, activeShadowRules, shadowSignals, shadowWriter, runShadowTick, shadowFee, shadowOutcome, settleShadowRows, shadowReport, COLLECTION };
