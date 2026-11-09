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
  assert.ok(Object.isFrozen(sh.SHADOW_RULES), 'the registry is a frozen list in code: nothing changes until a reviewed edit adds a rule');
  assert.ok(sh.SHADOW_RULES.every((r) => Object.isFrozen(r) && Object.isFrozen(r.entry) && Object.isFrozen(r.series)), 'every level of every rule is frozen');
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
  const own = lib.replace(/args\.(update|record|market|readOpen)\(/g, 'inject(');   // the library only calls what the minute function injects
  assert.ok(!/fetch|liveRequest|submitOrder|\/orders|keyId|pem|process\.env|secret|runTransaction|\.update\(|\.delete\(|\.set\(/.test(own), 'the shadow library places no order, makes no request of its own, reads no key or secret and only creates log rows (settlement uses injected public readers)');
  const idx = code(read('functions', 'index.js'));
  assert.ok(/if \(shadowLib\.SHADOW_RULES\.length\)/.test(idx) && /rules: shadowLib\.SHADOW_RULES/.test(idx), 'index.js passes only the constant registry, and only when it is not empty');
  assert.ok(!/args\.rules|request\.data[^;]*shadow|shadowRules\s*=/i.test(idx), 'nothing from a request or storage can supply a rule');
  const tickPos = idx.indexOf('slotRun.runSlotTick'), shadowPos = idx.indexOf('shadowLib.runShadowTick');
  assert.ok(tickPos > 0 && shadowPos > tickPos, 'the shadow run comes AFTER everything that can trade has run');
  const rules = read('firestore.rules');
  const m = rules.match(/match \/kalshiShadowRows\/\{id\} \{([\s\S]*?)\}/);
  assert.ok(m && /allow read: if isAdmin\(\)/.test(m[1]) && /allow write: if false/.test(m[1]), 'the log is admin read and no client write');
  assert.ok(!/kalshiShadowRows/.test(read('index.html')), 'the page does not read the shadow log (the scorer will, in a later pull request)');
  for (const f of ['kalshiLiveLib.js', 'kalshiSlotLib.js', 'kalshiSlotRunLib.js']) assert.ok(!/kalshiShadowRows|kalshiShadowLib/.test(read('functions', f)), f + ' knows nothing of the shadow log: nothing that decides an order can read it');
  const rep = code(read('functions', 'kalshiReportLib.js'));
  assert.ok(/require\("\.\/kalshiShadowLib"\)/.test(rep) && !/fetch|liveRequest|collection\(|\.create\(|runTransaction|firebase|getFirestore/.test(rep), 'the report may SCORE the log (rows are handed in by index.js) but still sends nothing and writes nothing itself');
};
gates.SH5 = async () => {
  // Week 1 (Nov 9, 2026): exactly four registered shadow rules, each valid against the markets the bot quotes, 1 contract, and pointing at a pre-registration that exists.
  const rules = sh.SHADOW_RULES;
  assert.deepStrictEqual(rules.map((r) => r.id), ['ETHNO6', 'BTCHI6', 'XRPYES10', 'ETHL1']);
  for (const r of rules) { assert.strictEqual(sh.validateShadowRule(r, live.L1_SERIES).ok, true, r.id); assert.strictEqual(r.contracts, 1, r.id + ' is one contract'); }
  assert.strictEqual(sh.activeShadowRules(undefined, live.L1_SERIES).length, 4, 'the production registry passes the same validation');
  const by = (id) => rules.find((r) => r.id === id);
  assert.deepStrictEqual({ ...by('ETHNO6').entry }, { sideRule: 'no', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 });
  assert.deepStrictEqual({ ...by('BTCHI6').entry }, { sideRule: 'favourite', priceMin: 0.92, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 });
  assert.deepStrictEqual({ ...by('XRPYES10').entry }, { sideRule: 'yes', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }, 'the 10 minute look');
  assert.deepStrictEqual({ ...by('ETHL1').entry }, { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, "L1's own entry on Ethereum");
  const readme = read('kalshi-scalper', 'README.md');
  assert.ok(readme.includes('## SHADOW-WEEK1') && rules.every((r) => readme.includes(r.id) && r.readme === 'kalshi-scalper/README.md#SHADOW-WEEK1'), 'the pre-registration is in the README before the first row');
  // A signal only inside its own window and band: an Ethereum favourite at 0.93 with 6 minutes left is a signal for ETHL1 (and ETHNO6 only if its NO side is the one in band).
  const quote = (series, over) => ({ series, m: Object.assign({ ticker: series + '-26NOV101115-00', status: 'open', close_time: new Date(NOW + 360000).toISOString(), yes_bid_dollars: '0.9200', yes_ask_dollars: '0.9300', yes_ask_size_fp: '100.00', yes_bid_size_fp: '100.00' }, over || {}) });
  const rows = sh.shadowSignals(rules, [quote('KXETH15M'), quote('KXBTC15M'), quote('KXXRP15M')], NOW);
  const ids = rows.map((r) => r.rule).sort();
  assert.deepStrictEqual(ids, ['BTCHI6', 'ETHL1'], 'at 6 minutes left: Bitcoin 0.93 and the Ethereum favourite qualify; XRP needs the 10 minute look; the Ethereum NO side is 0.08 (outside 0.88 to 0.97): ' + ids);
  const ten = sh.shadowSignals(rules, [quote('KXXRP15M', { close_time: new Date(NOW + 600000).toISOString() })], NOW);
  assert.deepStrictEqual(ten.map((r) => r.rule), ['XRPYES10'], 'XRP at 10 minutes left');
  assert.deepStrictEqual(sh.shadowSignals(rules, [quote('KXGOLD15M')], NOW), [], 'a market no rule names (gold) is never logged');
};
gates.SC1 = async () => {
  // Settlement and scoring (lifecycle spec (c)): a shadow row is settled from the public market result; PF is per contract on the cash basis with the 10 contract fee; the verdict follows the written rules.
  assert.strictEqual(sh.shadowFee(0.93), 0.005, 'a 0.93 contract: 7% x 10 x 0.93 x 0.07 = 4.56c on ten, rounded up to 5c, so 0.5c a contract');
  assert.strictEqual(sh.shadowFee(0.5), 0.018, 'a 0.50 contract: 7% x 10 x 0.25 = 17.5c on ten, rounded up to 18c, so 1.8c a contract');
  const win = sh.shadowOutcome({ side: 'yes', price: 0.9 }, 'yes'), loss = sh.shadowOutcome({ side: 'yes', price: 0.9 }, 'no'), noWin = sh.shadowOutcome({ side: 'no', price: 0.12 }, 'no');
  assert.ok(win.won && win.pnl > 0.09 && win.pnl < 0.1, 'a win at 0.90 makes about 9.4c a contract: ' + win.pnl);
  assert.ok(!loss.won && loss.pnl < -0.9 && loss.pnl > -0.92, 'a loss at 0.90 costs about 90.6c: ' + loss.pnl);
  assert.ok(noWin.won && noWin.pnl > 0.8, 'a NO win at 0.12 is about 88c');
  assert.strictEqual(sh.shadowOutcome({ side: 'yes', price: 0.9 }, ''), null, 'no result yet is no outcome');
  assert.strictEqual(sh.shadowOutcome({ side: 'maybe', price: 0.9 }, 'yes'), null);
  // The sweep: only rows whose market closed 2+ minutes ago, at most `max` reads, each error swallowed.
  const rows = [{ rule: 'R1', ticker: 'A', side: 'yes', price: 0.9, settled: false, closeMs: NOW - 600000 }, { rule: 'R1', ticker: 'B', side: 'yes', price: 0.9, settled: false, closeMs: NOW - 60000 }, { rule: 'R1', ticker: 'C', side: 'yes', price: 0.9, settled: false, closeMs: NOW - 900000 }];
  const updates = [], asked = [];
  const r = await sh.settleShadowRows({ now: NOW, max: 12, readOpen: async () => rows, update: async (id, p) => { updates.push([id, p]); },
    market: async (t) => { asked.push(t); if (t === 'C') throw new Error('boom'); return { result: 'yes' }; } });
  assert.deepStrictEqual(asked.sort(), ['A', 'C'], 'B closed under 2 minutes ago and is not asked');
  assert.deepStrictEqual([r.checked, r.settled, updates.length, updates[0][0]], [2, 1, 1, 'R1_A'], 'a failing read is skipped and the next run tries again');
  assert.ok(updates[0][1].settled === true && updates[0][1].won === true && Number.isFinite(updates[0][1].pnl));
  let tclock = 0;
  const slow = await sh.settleShadowRows({ now: NOW, max: 12, budgetMs: 1000, clock: () => (tclock += 600), readOpen: async () => rows.map((x, i) => Object.assign({}, x, { ticker: 'S' + i, closeMs: NOW - 900000 })).concat(rows.map((x, i) => Object.assign({}, x, { ticker: 'T' + i, closeMs: NOW - 900000 }))), update: async () => {}, market: async () => ({ result: 'yes' }) });
  assert.ok(slow.checked < 6, 'the time guard stops the sweep and leaves the rest for the next run: ' + JSON.stringify(slow));
  const bad = await sh.settleShadowRows({ now: NOW, readOpen: async () => { throw new Error('x'); }, update: async () => {}, market: async () => ({}) });
  assert.deepStrictEqual(bad, { checked: 0, settled: 0 }, 'an unreadable list never throws');
};
gates.SC2 = () => {
  const rule = { id: 'R1' };
  const mk = (n, over) => Array.from({ length: n }, (_, i) => Object.assign({ rule: 'R1', atMs: NOW - (n - i) * 3600000, settled: true, wouldFill: true, pnl: i % 10 === 9 ? -0.9 : 0.09 }, over && over(i)));
  // 150 signals over 6.25 days: 90% wins of 9c and 10% losses of 90c is PF 1.0, so it is not ready.
  const flat = sh.shadowReport([rule], mk(150), NOW)[0];
  assert.deepStrictEqual([flat.signals, flat.fillable, flat.pfFillable], [150, 150, 0.9], JSON.stringify(flat));
  assert.strictEqual(flat.status, 'collecting', 'under 14 days and under PF 1.3: still collecting');
  // A clean 150 signals over 20 days at PF 1.5 and a steady second half passes.
  const good = sh.shadowReport([rule], Array.from({ length: 160 }, (_, i) => ({ rule: 'R1', atMs: NOW - (160 - i) * 3 * 3600000, settled: true, wouldFill: true, pnl: i % 8 === 7 ? -0.9 : 0.2 })), NOW)[0];
  assert.ok(good.pfFillable >= 1.3 && good.days >= 14, JSON.stringify(good));
  assert.ok(/^ready/.test(good.status), 'the written pass rule: ' + JSON.stringify(good));
  // A kill: net under -1c per contract after 50 fillable signals.
  const dead = sh.shadowReport([rule], mk(60, () => ({ pnl: i => -0.5 })).map((d) => Object.assign(d, { pnl: d.pnl === -0.9 ? -0.9 : -0.1 })), NOW)[0];
  assert.ok(/^kill/.test(dead.status), 'a net under -1c per contract after 50 signals is a kill: ' + JSON.stringify(dead));
  // Retire: 30+ days old with under 40 signals in the last 30.
  const old = sh.shadowReport([rule], [{ rule: 'R1', atMs: NOW - 40 * 86400000, settled: true, wouldFill: true, pnl: 0.1 }, { rule: 'R1', atMs: NOW - 10 * 86400000, settled: true, wouldFill: true, pnl: 0.1 }], NOW)[0];
  assert.ok(/^retire/.test(old.status), JSON.stringify(old));
  assert.deepStrictEqual(sh.shadowReport([rule], [], NOW)[0].signals, 0, 'no rows: a row of zeros, never a crash');
  assert.deepStrictEqual(sh.shadowReport(null, null, NOW), [], 'garbage in, empty out');
  assert.ok(!/ticker|rule_/.test(JSON.stringify(good).replace('"rule"', '')) , 'no ticker or document id in the score');
};
gates.SC3 = async () => {
  const rep = require('../functions/kalshiReportLib.js');
  const calls = [];
  const req = { method: 'GET', headers: { authorization: 'Bearer ' + 'x'.repeat(30) }, query: {} };
  const res = { headers: {}, set(k, v) { this.headers[k] = v; }, status(c) { this.code = c; return this; }, json(b) { this.body = b; } };
  const deps = (extra) => Object.assign({ getToken: () => 'x'.repeat(30), now: () => NOW, readOrders: async () => [], logError: (e) => calls.push(String(e && e.message)) }, extra || {});
  await rep.makeReportHandler(deps({ readShadowRows: async () => [{ rule: 'ETHNO6', atMs: NOW - 3600000, settled: true, wouldFill: true, pnl: 0.09 }], shadowRules: () => [{ id: 'ETHNO6' }] }))(req, res);
  assert.ok(res.code === 200 && res.body.shadow && res.body.shadow.rules[0].rule === 'ETHNO6' && res.body.shadow.rules[0].signals === 1, JSON.stringify(res.body.shadow));
  const res2 = Object.assign({}, res, { code: null, body: null });
  await rep.makeReportHandler(deps({ readShadowRows: async () => { throw new Error('boom'); }, shadowRules: () => [] }))(req, res2);
  assert.ok(res2.code === 200 && res2.body.shadow === undefined, 'a failing shadow read leaves the field out and never blanks the report');
  const res3 = Object.assign({}, res, { code: null, body: null });
  await rep.makeReportHandler(deps())(req, res3);
  assert.ok(res3.code === 200 && res3.body.shadow === undefined, 'without the optional reader the report is exactly what it was');
};
(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });
