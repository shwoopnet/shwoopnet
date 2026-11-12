'use strict';
// GOLDOFF (Nov 12, 2026, the owner: "Make sure gold keeps a shadow record after the latch trips"). Each gate states the consequence: while gold is latched off, or the bot session is off, gold's would-be entry is
// still recorded (the return rule needs it); the record is one log row per window and nothing else; and every live decision, order and request the minute function makes is exactly what it was without the rule.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const harness = require('./fixtures/indexHarness');
const sh = require('../functions/kalshiShadowLib.js');
const live = require('../functions/kalshiLiveLib.js');
const gk = require('../functions/kalshiGoldKillLib.js');

const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const indexPath = path.join(root, 'functions', 'index.js');
const GOLD = 'KXGOLD15M';
const DUE = Date.parse('2026-11-12T14:09:00Z');      // 6 minutes (360 s) before the 14:15 close
const T = 'KXGOLD15M-26NOV121415-00';
const gold = (over) => Object.assign({ ticker: T, status: 'open', close_time: new Date(DUE + 360000).toISOString(), yes_bid_dollars: '0.9300', yes_ask_dollars: '0.9400', yes_ask_size_fp: '40.00', yes_bid_size_fp: '40.00', exchange_index: 0 }, over || {});
const ONLY = (r) => r.id === 'GOLDOFF';
const rule = () => sh.SHADOW_RULES.find(ONLY);
const gates = {};

// Runs kalshiLiveArmed once at `clock` against the in-memory database and a scripted exchange; returns the whole record. `rules` replaces the registry for the run only and is always restored.
async function runArmed({ seed, markets, rules, clock = DUE, over }) {
  const real = sh.SHADOW_RULES;
  if (rules) sh.SHADOW_RULES = rules;
  const h = harness.load(indexPath, seed);
  const realFetch = global.fetch, realNow = Date.now, realTimeout = global.setTimeout;
  global.fetch = harness.exchange(h.log, Object.assign({ '/markets': { markets: markets || [] } }, over || {}));
  Date.now = () => clock;
  global.setTimeout = (f) => realTimeout(f, 0);
  let threw = null;
  try { await h.mod.kalshiLiveArmed(); } catch (e) { threw = String(e && e.message); }
  finally { global.fetch = realFetch; Date.now = realNow; global.setTimeout = realTimeout; h.restore(); sh.SHADOW_RULES = real; }
  return { log: JSON.parse(JSON.stringify(h.log)), threw, rows: [...(await h.db.collection('kalshiShadowRows').get()).docs].map((d) => d.data()) };
}
const SESSION_ON = { 'kalshiLiveControl/session': { active: true, since: DUE - 600000 }, 'kalshiLiveControl/sizing': { cap: 2, base: 100, saved: 0, pool: 0, cum: 0, hwm: 0, reviewedAt: DUE - 1000, appliedTs: DUE - 5000 }, 'kalshiBotMeta/control': { halt: false } };
const LATCHED = (seed) => Object.assign({}, seed, { 'kalshiLiveControl/sizing': Object.assign({}, seed['kalshiLiveControl/sizing'], { goldKill: { tripped: true, rearmAt: gk.GOLD_KILL.rearmAt, rule: 'drawdown' } }) });
const touchesShadow = (e) => /kalshiShadowRows/.test(JSON.stringify(e));
const isShadowMarketRead = (e) => e[0] === 'fetch' && /\/markets/.test(e[2]) && /series_ticker=KXGOLD15M/.test(e[2]);
const isShadowSettleRead = (e) => e[0] === 'fetch' && /\/markets\/KXGOLD15M-26NOV121345-00$/.test(e[2]);
const live_ = (log) => log.filter((e) => !touchesShadow(e) && !isShadowSettleRead(e));

gates.GO1 = async () => {
  // The rule is the return evidence for gold L1 itself: one frozen, valid rule on gold's own entry window, dated today, with a README entry.
  const r = rule();
  assert.ok(r && Object.isFrozen(r) && Object.isFrozen(r.entry), 'GOLDOFF is registered, frozen');
  assert.deepStrictEqual([sh.SHADOW_RULES.length, r.series, r.contracts, r.registeredAt], [1, [GOLD], 1, '2026-11-12']);
  assert.deepStrictEqual(r.entry, { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 });
  assert.strictEqual(sh.validateShadowRule(r, live.L1_SERIES).ok, true);
  assert.strictEqual(sh.activeShadowRules(undefined, live.L1_SERIES).length, 1, 'the production registry accepts it');
  assert.ok(Date.parse(r.forwardReadDate) - Date.parse(r.registeredAt) >= 7 * 86400000, 'the return review is at least 7 days after the first row');
  const readme = read('kalshi-scalper', 'README.md');
  assert.ok(/## SHADOW-GOLDOFF/.test(readme) && /counterparty/i.test(readme.split('## SHADOW-GOLDOFF')[1].slice(0, 6000)), 'pre-registered in the README before its first row, with a counterparty');
};

gates.GO2 = async () => {
  // Consequence: with gold LATCHED OFF and the bot session ON, the minute still records gold's entry (one row), and sends no order for it.
  const seed = LATCHED(SESSION_ON);
  assert.strictEqual(gk.goldKillActive(seed['kalshiLiveControl/sizing'], GOLD), true, 'the fixture really is latched');
  const r = await runArmed({ seed, markets: [gold()] });
  assert.strictEqual(r.threw, null);
  const rows = r.rows.filter((x) => x.rule === 'GOLDOFF');
  assert.strictEqual(rows.length, 1, 'one shadow row for the window');
  assert.deepStrictEqual([rows[0].ticker, rows[0].side, rows[0].price, rows[0].size, rows[0].settled], [T, 'yes', 0.94, 1, false]);
  assert.ok(!r.log.some((e) => e[0] === 'fetch' && e[1] === 'POST'), 'no order, no POST of any kind');
  assert.ok(!r.log.some((e) => e[0] === 'create' && /kalshiLiveOrders/.test(e[1])), 'no order document');
};

gates.GO3 = async () => {
  // Consequence: with the SESSION OFF (a loss stop, a stop by hand) rows are still written: the function reads gold's public quotes itself, in the entry window only.
  const r = await runArmed({ seed: {}, markets: [gold()] });
  assert.strictEqual(r.threw, null);
  assert.strictEqual(r.rows.filter((x) => x.rule === 'GOLDOFF').length, 1, 'a row is written with no session on');
  const reads = r.log.filter(isShadowMarketRead);
  assert.strictEqual(reads.length, 1, 'exactly one public market read, for gold');
  assert.ok(!r.log.some((e) => e[0] === 'fetch' && e[1] === 'POST'), 'no order (the minute\'s own account snapshot is unchanged: GO6 compares it with the rule removed)');
  // Outside the entry window the session-off minute makes NO extra request at all.
  for (const clock of [Date.parse('2026-11-12T14:03:00Z'), Date.parse('2026-11-12T14:12:00Z'), Date.parse('2026-11-12T14:14:00Z')]) {
    const q = await runArmed({ seed: {}, markets: [gold({ close_time: new Date(clock + 360000).toISOString() })], clock });
    assert.strictEqual(q.log.filter(isShadowMarketRead).length, 0, 'no market read at ' + new Date(clock).toISOString());
    assert.strictEqual(q.rows.length, 0);
  }
};

gates.GO4 = async () => {
  // Consequence: nothing is logged for a market outside the band or the time window, and a missing or one sided quote fails closed (no row, no throw).
  const none = async (over, label, seed) => { const r = await runArmed({ seed: seed || {}, markets: [gold(over)] }); assert.strictEqual(r.threw, null, label); assert.strictEqual(r.rows.length, 0, label); };
  await none({ yes_bid_dollars: '0.5000', yes_ask_dollars: '0.5200' }, 'a coin flip is below the band');
  await none({ yes_bid_dollars: '0.9800', yes_ask_dollars: '0.9900' }, 'above 97c is outside the band');
  await none({ close_time: new Date(DUE + 500000).toISOString() }, 'too early in the window');
  await none({ close_time: new Date(DUE + 300000).toISOString() }, 'too late in the window');
  await none({ yes_bid_dollars: '0.0000' }, 'no bid');
  await none({ yes_ask_dollars: undefined }, 'no ask');
  await none({ status: 'closed' }, 'a closed market');
  const cut = await runArmed({ seed: {}, markets: [] });
  assert.strictEqual(cut.threw, null); assert.strictEqual(cut.rows.length, 0, 'no market list at all: nothing logged');
  // the NO side: a favourite NO priced inside the band is the signal
  const no = await runArmed({ seed: {}, markets: [gold({ yes_bid_dollars: '0.0500', yes_ask_dollars: '0.0600' })] });
  assert.deepStrictEqual([no.rows.length, no.rows[0] && no.rows[0].side, no.rows[0] && no.rows[0].price], [1, 'no', 0.95]);
  // a failing market read is swallowed
  assert.deepStrictEqual(await sh.runShadowTick({ now: DUE, quotes: undefined, rules: sh.SHADOW_RULES, allowedSeries: live.L1_SERIES, record: async () => { throw new Error('x'); } }), { signals: 0, written: 0 });
};

gates.GO5 = async () => {
  // Consequence: two instances (a deploy overlap) write ONE row: the id is rule + ticker, written with create, and the second create is refused and swallowed.
  const a = await runArmed({ seed: {}, markets: [gold()] });
  const create = a.log.find((e) => e[0] === 'create' && /kalshiShadowRows/.test(e[1]));
  assert.strictEqual(create[1], 'kalshiShadowRows/GOLDOFF_' + T, 'a key both processes compute identically');
  const seed = { ['kalshiShadowRows/GOLDOFF_' + T]: a.rows[0] };
  const b = await runArmed({ seed, markets: [gold({ yes_bid_dollars: '0.9200', yes_ask_dollars: '0.9300' })] });   // a second instance sees a later, different quote
  assert.strictEqual(b.threw, null, 'the refused second create is swallowed');
  assert.strictEqual(b.rows.length, 1);
  assert.strictEqual(b.rows[0].price, a.rows[0].price, 'the first look wins; the later write cannot overwrite it');
};

gates.GO6 = async () => {
  // THE CONSEQUENCE THAT MATTERS: the rule changes no live decision. For each state of the bot (session on, session on and gold latched, session off), everything the minute function does other than
  // the shadow log (every read, write, request and console line) is identical with and without the rule, in the entry window and with a tradable gold quote.
  const SWEEP = Date.parse('2026-11-12T14:10:00Z');      // floor(now/60000) % 5 === 0: the settle sweep also runs; 5 minutes before a 14:15 close is outside the entry window, so a stale open row is what it reads
  assert.strictEqual(Math.floor(SWEEP / 60000) % 5, 0);
  const OLD = { rule: 'GOLDOFF', ticker: 'KXGOLD15M-26NOV121345-00', side: 'yes', price: 0.94, settled: false, closeMs: SWEEP - 1500000, atMs: SWEEP - 2400000 };
  for (const [clock, tag] of [[DUE, ''], [SWEEP, ' (sweep minute)']]) for (const [name0, seed0] of [['session on', SESSION_ON], ['session on, gold latched', LATCHED(SESSION_ON)], ['session off', {}]]) {
    const name = name0 + tag, seed = tag ? Object.assign({}, seed0, { ['kalshiShadowRows/GOLDOFF_' + OLD.ticker]: OLD }) : seed0;
    const mk = tag ? [gold({ close_time: new Date(clock + 360000).toISOString() })] : [gold()];
    const over = { ['/markets/' + OLD.ticker]: { market: { ticker: OLD.ticker, status: 'finalized', result: 'yes' } } };
    const withRule = await runArmed({ seed, markets: mk, clock, over });
    const without = await runArmed({ seed, markets: mk, rules: [], clock, over });
    assert.strictEqual(withRule.threw, null); assert.strictEqual(without.threw, null);
    const a = live_(withRule.log).filter((e) => !isShadowMarketRead(e) || name0 !== 'session off');
    const b = live_(without.log);
    assert.deepStrictEqual(a, b, name + ': a decision, order, read or write other than the shadow log differs with the rule registered');
    assert.strictEqual(without.rows.filter((x) => x.settled === true || x.atMs > SWEEP - 1000).length, 0, name + ': an empty registry writes and settles no shadow row');
    if (tag) assert.ok(withRule.rows.some((x) => x.ticker === OLD.ticker && x.settled === true), name + ': the sweep really ran and settled the old row');
    if (name0 === 'session off') assert.strictEqual(without.log.filter(isShadowMarketRead).length, 0, 'an empty registry makes no extra market read');
    else assert.deepStrictEqual(withRule.log.filter(isShadowMarketRead).length, without.log.filter(isShadowMarketRead).length, name + ': with the session on the rule makes no market request of its own');
  }
};

gates.GO7 = () => {
  // No order path: the library stays free of requests, keys and order code (SH4 also pins this); index.js runs the shadow tick only AFTER the slot tick, only when no armed test order is on, and passes only the constant registry.
  const idx = code(read('functions', 'index.js'));
  const blockStart = idx.indexOf('if (shadowLib.SHADOW_RULES.length && !armedOn)');
  assert.ok(blockStart > idx.indexOf('slotRun.runSlotTick'), 'after everything that can trade');
  for (const step of ['live.settleOpenOrders', 'exitAlarm.runExitAlarm', 'accRef']) assert.ok(blockStart > idx.indexOf(step), 'after ' + step + ': nothing shadow related may delay a settle, a snapshot or an alarm');
  assert.ok(/budgetMs: 8000/.test(idx.slice(blockStart)), 'the settle sweep budget is 8 s');
  const block = idx.slice(blockStart, idx.indexOf('failure = e', blockStart));
  assert.ok(block.length > 200 && block.length < 3000, 'the block was found');
  assert.ok(!/submit|liveRequest|keyId|pem|KALSHI_LIVE_KEY|KALSHI_LIVE_PRIVATE|\.runTransaction|POST/.test(block), 'the shadow block touches no key and sends no order');
  assert.ok(/shadowSeriesDue\(shadowLib\.SHADOW_RULES, now\)/.test(block) && /rules: shadowLib\.SHADOW_RULES/.test(block), 'only the constant registry is ever passed');
  assert.strictEqual(sh.shadowSeriesDue([rule()], Date.parse('2026-11-12T14:09:00Z')).join(), GOLD);
  assert.strictEqual(sh.shadowSeriesDue([rule()], Date.parse('2026-11-12T14:03:00Z')).length, 0);
  assert.strictEqual(sh.shadowSeriesDue(null, DUE).length, 0, 'garbage in, nothing due');
};

gates.GO8 = () => {
  // The return rule is readable from the report without changing the lifecycle thresholds: 60 fillable settled rows, 7 days, PF 1.3, second half 1.3.
  const mk = (n, days, pnl) => Array.from({ length: n }, (_, i) => ({ rule: 'GOLDOFF', atMs: DUE - days * 86400000 + (i * days * 86400000) / n, settled: true, wouldFill: true, pnl: pnl(i) }));
  const NOW2 = DUE;
  const good = sh.shadowReport([rule()], mk(70, 8, (i) => (i % 10 === 9 ? -0.5 : 0.12)), NOW2)[0];
  assert.strictEqual(sh.returnRule(good).met, true, JSON.stringify(sh.returnRule(good)));
  assert.strictEqual(good.status, 'collecting', 'the existing lifecycle verdict is unchanged: 70 signals is still collecting');
  const few = sh.shadowReport([rule()], mk(40, 8, () => 0.12), NOW2)[0];
  assert.strictEqual(sh.returnRule(few).met, false, 'under 60 rows');
  const young = sh.shadowReport([rule()], mk(70, 3, (i) => (i % 10 === 9 ? -0.5 : 0.12)), NOW2)[0];
  assert.strictEqual(sh.returnRule(young).met, false, 'under 7 days');
  const weak = sh.shadowReport([rule()], mk(70, 8, (i) => (i % 3 === 2 ? -0.9 : 0.12)), NOW2)[0];
  assert.strictEqual(sh.returnRule(weak).met, false, 'PF under 1.3');
  assert.strictEqual(sh.returnRule(null).met, false);
  const rep = read('functions', 'kalshiReportLib.js');
  assert.ok(/returnRule: shadowLib\.returnRule\(x\)/.test(rep), 'the nightly report carries the return rule for GOLDOFF');
  assert.ok(/fill\.length >= 150 && days >= 14/.test(read('functions', 'kalshiShadowLib.js')), 'the existing ready threshold is untouched');
};

gates.GO9 = async () => {
  // Gold's live decision does not read the shadow log or the rule: the live library knows nothing of either, and the latch still removes gold from the tradable list.
  for (const f of ['kalshiLiveLib.js', 'kalshiGoldKillLib.js']) assert.ok(!/kalshiShadow|GOLDOFF/.test(read('functions', f)), f + ' knows nothing of the shadow rule');
  assert.strictEqual(gk.goldKillActive({ goldKill: { tripped: true, rearmAt: gk.GOLD_KILL.rearmAt } }, GOLD), true, 'the latch still removes gold from the live list; the shadow rule does not change that');
};

(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });
