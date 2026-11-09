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
const RULE = (id, series, entry) => Object.freeze({ id, readme: "kalshi-scalper/README.md#SHADOW-WEEK1", series: Object.freeze([series]), entry: Object.freeze(entry), contracts: 1, registeredAt: "2026-11-09", forwardReadDate: "2026-12-14" });
const SHADOW_RULES = Object.freeze([
  RULE("ETHNO6", "KXETH15M", { sideRule: "no", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }),
  RULE("BTCHI6", "KXBTC15M", { sideRule: "favourite", priceMin: 0.92, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }),
  RULE("XRPYES10", "KXXRP15M", { sideRule: "yes", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }),
  RULE("ETHL1", "KXETH15M", { sideRule: "favourite", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }),
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
          wouldFill: Number.isFinite(depth) ? depth >= r.contracts : null, bid, ask, spread, secondsLeft: Math.round(left), closeTime: String(q.m.close_time), atMs: nowMs });
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

module.exports = { SHADOW_RULES, validateShadowRule, activeShadowRules, shadowSignals, shadowWriter, runShadowTick, COLLECTION };
