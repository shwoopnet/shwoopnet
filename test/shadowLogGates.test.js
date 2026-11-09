// Shadow rules (Nov 9, 2026, lifecycle spec stage 1). Each gate states the consequence: a shadow rule can only LOG what it would have bought; it can never send an order, make a request, read a key or
// change behaviour while the registry is empty; one decision per window is logged; and nothing stored or typed on the page can add a rule.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sh = require('../functions/kalshiShadowLib.js');
const live = require('../functions/kalshiLiveLib.js');
const gates = {};
const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const NOW = Date.parse('2026-11-10T16:00:00Z');
const ALLOWED = ['KXGOLD15M', 'KXBTC15M'];
const GOOD = () => ({ id: 'SHTEST', readme: 'kalshi-scalper/README.md#SHADOW-SHTEST', series: ['KXGOLD15M'], entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.3, leftMaxSec: 400, leftMinSec: 330 }, contracts: 1, registeredAt: '2026-11-09', forwardReadDate: '2026-11-30' });
const q = (series, ticker, over) => ({ series, m: Object.assign({ ticker, status: 'open', close_time: new Date(NOW + 360000).toISOString(), yes_bid_dollars: '0.1100', yes_ask_dollars: '0.1200', yes_ask_size_fp: '50.00', yes_bid_size_fp: '40.00' }, over || {}) });

gates.SH1 = () => {
  assert.ok(Object.isFrozen(sh.SHADOW_RULES) && sh.SHADOW_RULES.length === 0, 'the registry is a frozen list in code and starts empty: nothing changes until a reviewed edit adds a rule');
  assert.strictEqual(sh.validateShadowRule(GOOD(), ALLOWED).ok, true);
  for (const [why, mut] of [['a market the bot does not quote', (r) => { r.series = ['KXSOL15M']; }], ['an exit field (a shadow rule has none)', (r) => { r.exit = {}; }], ['price outside 0.01 to 0.99', (r) => { r.entry.priceMax = 1; }],
    ['a window under 60 s', (r) => { r.entry.leftMinSec = 30; }], ['more than 10 contracts', (r) => { r.contracts = 11; }], ['a bad id', (r) => { r.id = 'bad id'; }], ['no readme', (r) => { r.readme = 'x'; }]]) {
    const r = GOOD(); mut(r);
    assert.strictEqual(sh.validateShadowRule(r, ALLOWED).ok, false, why + ' is refused');
  }
  assert.deepStrictEqual(sh.activeShadowRules([GOOD(), Object.assign(GOOD(), { id: 'BAD ID' })], ALLOWED), [], 'one bad entry refuses the whole registry');
  assert.deepStrictEqual(sh.activeShadowRules([GOOD(), GOOD()], ALLOWED), [], 'a repeated id refuses the whole registry');
  assert.strictEqual(sh.activeShadowRules([GOOD()], ALLOWED).length, 1);
};
gates.SH2 = () => {
  const rule = GOOD();
  const rows = sh.shadowSignals([rule], [q('KXGOLD15M', 'KXGOLD15M-26NOV101115-00')], NOW);
  assert.strictEqual(rows.length, 1, 'a cheap side inside the band and the look is one signal');
  const r = rows[0];
  assert.deepStrictEqual([r.rule, r.side, r.price, r.size, r.depth, r.wouldFill, r.secondsLeft], ['SHTEST', 'yes', 0.12, 1, 50, true, 360], JSON.stringify(r));
  const none = (over, label) => assert.strictEqual(sh.shadowSignals([rule], [q('KXGOLD15M', 'KXGOLD15M-26NOV101115-00', over)], NOW).length, 0, label);
  none({ yes_bid_dollars: '0.4800', yes_ask_dollars: '0.4900' }, 'the cheap side at 0.49 is outside the band');
  none({ close_time: new Date(NOW + 500000).toISOString() }, 'too early');
  none({ close_time: new Date(NOW + 300000).toISOString() }, 'too late');
  none({ status: 'closed' }, 'a closed market');
  none({ yes_bid_dollars: '0.0000', yes_ask_dollars: '0.1200' }, 'no two sided quote');
  assert.strictEqual(sh.shadowSignals([rule], [q('KXBTC15M', 'KXBTC15M-26NOV101115-00')], NOW).length, 0, 'a series not on the rule is never looked at');
  const thin = sh.shadowSignals([rule], [q('KXGOLD15M', 'KXGOLD15M-26NOV101115-00', { yes_ask_size_fp: '0.00' })], NOW);
  assert.ok(thin.length === 1 && thin[0].wouldFill === false, 'no size at the touch is logged as wouldFill false');
  assert.deepStrictEqual(sh.shadowSignals([], [q('KXGOLD15M', 'T')], NOW), [], 'no rules, no signals');
  assert.deepStrictEqual(sh.shadowSignals([rule], null, NOW), [], 'no quotes, no signals');
};
gates.SH3 = async () => {
  const rule = GOOD(), writes = [], seen = new Set();
  const record = async (d) => { writes.push(d); };
  const quotes = [q('KXGOLD15M', 'KXGOLD15M-26NOV101115-00')];
  const a = await sh.runShadowTick({ now: NOW, quotes, rules: [rule], allowedSeries: ALLOWED, record, seen });
  assert.deepStrictEqual([a.signals, a.written, writes.length], [1, 1, 1]);
  const b = await sh.runShadowTick({ now: NOW + 60000, quotes, rules: [rule], allowedSeries: ALLOWED, record, seen });
  assert.strictEqual(writes.length, 1, 'the same rule and market is logged once a window: the first look wins');
  const c = await sh.runShadowTick({ now: NOW, quotes, rules: [rule], allowedSeries: ALLOWED, record: async () => { throw new Error('boom'); }, seen: new Set() });
  assert.ok(c && c.written === 0, 'a failing write is swallowed and never throws');
  const d = await sh.runShadowTick({ now: NOW, quotes, rules: [], allowedSeries: ALLOWED, record: async () => { throw new Error('never called'); } });
  assert.deepStrictEqual(d, { skipped: 'no shadow rule' }, 'an empty registry does nothing and calls nothing');
  const e = await sh.runShadowTick({ now: NOW, quotes: 'garbage', rules: [rule], allowedSeries: ALLOWED, record });
  assert.ok(e, 'garbage input never throws');
  const writer = sh.shadowWriter({ collection: (c) => ({ doc: (id) => ({ create: (x) => ({ c, id, x }) }) }) });
  const w = writer({ rule: 'SHTEST', ticker: 'T1' });
  assert.deepStrictEqual([w.c, w.id], ['kalshiShadowRows', 'SHTEST_T1'], 'one document per rule and market, written with create so a second write cannot overwrite the first look');
};
gates.SH4 = () => {
  const lib = code(read('functions', 'kalshiShadowLib.js'));
  assert.ok(!/fetch|liveRequest|submitOrder|\/orders|keyId|pem|process\.env|secret|runTransaction|\.update\(|\.delete\(|\.set\(/.test(lib), 'the shadow library places no order, makes no request, reads no key or secret and only creates log rows');
  const idx = code(read('functions', 'index.js'));
  assert.ok(/if \(shadowLib\.SHADOW_RULES\.length\)/.test(idx) && /rules: shadowLib\.SHADOW_RULES/.test(idx), 'index.js passes only the constant registry, and only when it is not empty');
  assert.ok(!/args\.rules|request\.data[^;]*shadow|shadowRules\s*=/i.test(idx), 'nothing from a request or storage can supply a rule');
  const tickPos = idx.indexOf('slotRun.runSlotTick'), shadowPos = idx.indexOf('shadowLib.runShadowTick');
  assert.ok(tickPos > 0 && shadowPos > tickPos, 'the shadow run comes AFTER everything that can trade has run');
  const rules = read('firestore.rules');
  const m = rules.match(/match \/kalshiShadowRows\/\{id\} \{([\s\S]*?)\}/);
  assert.ok(m && /allow read: if isAdmin\(\)/.test(m[1]) && /allow write: if false/.test(m[1]), 'the log is admin read and no client write');
  assert.ok(!/kalshiShadowRows/.test(read('index.html')), 'the page does not read the shadow log (the scorer will, in a later pull request)');
  for (const f of ['kalshiLiveLib.js', 'kalshiSlotLib.js', 'kalshiSlotRunLib.js', 'kalshiReportLib.js']) assert.ok(!/kalshiShadowRows|kalshiShadowLib/.test(read('functions', f)), f + ' knows nothing of the shadow log: nothing that decides an order can read it');
};
(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });
