'use strict';
// LONG-HOLD PAPER LOG, phase 1 (Nov 12, 2026; docs/LONGHOLD_DESIGN.md). Every gate states a consequence. The politics series below are TEST FIXTURES only: no real configuration is registered.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lh = require('../functions/kalshiLongholdLib.js');
const sh = require('../functions/kalshiShadowLib.js');
const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const gates = {};

const NOW = Date.parse('2026-11-12T12:00:00Z');
const CLOSE = new Date(NOW + 24 * 3600000 + 5 * 60000).toISOString();     // 24h05m left
const RULE = Object.freeze({ id: 'FIXTURE_LH', readme: 'docs/LONGHOLD_DESIGN.md#phase-1', series: Object.freeze(['KXTRUMPAPPROVE', 'KXVHGCB']), lookMinHours: 24, lookMaxHours: 27, sideRule: 'no',
  arms: Object.freeze([Object.freeze({ arm: 'A', priceMin: 0.75, priceMax: 0.90 }), Object.freeze({ arm: 'B', priceMin: 0.10, priceMax: 0.25 })]), contracts: 3, limitSlip: 0.01, hold: 'settlement',
  registeredAt: '2026-11-12', forwardReadDate: '2026-12-12', rearmAt: '2026-11-12', kill: Object.freeze({ afterFills: 20, netBelow: -15, lossStreak: 5 }), returnRule: Object.freeze({ coolOffDays: 14, pf: 1.3, fills: 30 }) });
const mk = (n, bid, ask, over) => Object.assign({ ticker: 'KXTRUMPAPPROVE-26NOV13-' + n, event_ticker: 'KXTRUMPAPPROVE-26NOV13', status: 'open', close_time: CLOSE, yes_bid_dollars: bid, yes_ask_dollars: ask, yes_bid_size_fp: '50.00', yes_ask_size_fp: '50.00' }, over || {});

gates.LH1 = () => {
  // Consequence: nothing ships configured. The registry is empty and frozen, so the deployed functions make no read and no write for this module, and the shadow registry (and the registry gate over it) is untouched.
  assert.deepStrictEqual([lh.LONGHOLD_RULES.length, Object.isFrozen(lh.LONGHOLD_RULES)], [0, true]);
  assert.deepStrictEqual(lh.activeLongholdRules(), []);
  assert.ok(!sh.SHADOW_RULES.some((r) => /LONGHOLD|APPR/.test(r.id)), 'no long-hold rule in SHADOW_RULES');
  assert.ok(!fs.existsSync(path.join(root, 'strategies-registry.json')) || !/APPR_NO_PAPER/.test(read('strategies-registry.json')), 'no registry row for a removed configuration');
};

gates.LH2 = () => {
  // Consequence: a malformed or dangerous rule is refused whole: a 15 minute series, more than 3 contracts, a hold other than settlement, no kill rule, a bad window.
  assert.strictEqual(lh.validateLongholdRule(RULE).ok, true);
  const bad = (o) => lh.validateLongholdRule(Object.assign({}, RULE, o)).ok;
  assert.strictEqual(bad({ series: ['KXGOLD15M'] }), false);
  assert.strictEqual(bad({ contracts: 4 }), false);
  assert.strictEqual(bad({ hold: 'exit' }), false);
  assert.strictEqual(bad({ kill: { afterFills: 20, netBelow: 5, lossStreak: 5 } }), false);
  assert.strictEqual(bad({ lookMinHours: 1 }), false);
  assert.strictEqual(bad({ extra: 1 }), false);
  assert.deepStrictEqual(lh.activeLongholdRules([RULE, Object.assign({}, RULE, { contracts: 9 })]), [], 'one bad entry refuses the registry');
  assert.deepStrictEqual(lh.activeLongholdRules([RULE, RULE]), [], 'a repeated id refuses the registry');
};

gates.LH3 = () => {
  // Consequence: one market per event per arm, the one whose YES mid is nearest 0.5 among those in the arm's band, ties by ticker, and an out-of-window or one-sided market is never chosen.
  const ms = [mk('A1', '0.1000', '0.1400'), mk('A2', '0.2300', '0.2500'), mk('B1', '0.8000', '0.8400'), mk('B2', '0.8800', '0.9000'), mk('C', '0.5000', '0.5200'), mk('X', '0.0000', '0.2000'),
    mk('Y', '0.2000', '0.2200', { close_time: new Date(NOW + 30 * 3600000).toISOString() })];
  const c = lh.longholdCandidates(RULE, 'KXTRUMPAPPROVE', ms, NOW);
  // arm A (NO paid 0.75 to 0.90 = YES bid 0.10 to 0.25): A1 NO 0.90, A2 NO 0.77 -> A2 has the mid nearer 0.5. Arm B (NO 0.10 to 0.25 = YES bid 0.75 to 0.90): B1 NO 0.20, B2 NO 0.12 -> B1 nearer.
  assert.deepStrictEqual(c.map((x) => x.arm + ':' + x.ticker.split('-').pop()), ['A:A2', 'B:B1']);
  assert.strictEqual(lh.longholdCandidates(RULE, 'KXTRUMPAPPROVE', [mk('T2', '0.2000', '0.2200'), mk('T1', '0.2000', '0.2200')], NOW)[0].ticker.split('-').pop(), 'T1', 'ties by ticker');
};

gates.LH4 = () => {
  // Consequence: the row is priced from the SINGLE-MARKET read. A list copy that said 0.20 but a fresh read that says 0.30 records the fresh price, and a fresh quote that left the band records nothing.
  const cand = { rule: RULE.id, arm: 'A', event: 'KXTRUMPAPPROVE-26NOV13', series: 'KXTRUMPAPPROVE', ticker: 'KXTRUMPAPPROVE-26NOV13-A2' };
  const fresh = lh.longholdRow(RULE, cand, mk('A2', '0.2000', '0.2200'), NOW);
  assert.strictEqual(fresh.source, 'single-market');
  assert.deepStrictEqual([fresh.yesBid, fresh.touch, fresh.price, fresh.contracts, fresh.wouldFill, fresh.settled], [0.2, 0.8, 0.81, 3, true, false], 'NO touch 0.80 plus the 1c slip');
  assert.strictEqual(lh.longholdRow(RULE, cand, mk('A2', '0.4000', '0.4200'), NOW), null, 'out of band now: nothing recorded');
  assert.strictEqual(lh.longholdRow(RULE, cand, mk('A2', '0.2000', '0.2200', { yes_bid_size_fp: '2.00' }), NOW).wouldFill, false, 'thin touch cannot fill 3');
  assert.strictEqual(lh.longholdRow(RULE, cand, mk('A9', '0.2000', '0.2200'), NOW), null, 'a different market is not the candidate');
  const src = code(read('functions', 'kalshiLongholdLib.js'));
  assert.ok(/longholdRow\(d\.rule, c, await args\.market\(c\.ticker\)/.test(src), 'the row is built from args.market (the single read), not the list');
};

gates.LH5 = () => {
  // Consequence: net is the cash basis on 3 contracts with the unrounded fee 0.07*p*(1-p) per contract.
  const row = { side: 'no', price: 0.81, contracts: 3 };
  const fee = 0.07 * 0.81 * 0.19;
  assert.strictEqual(lh.longholdOutcome(row, 'no').pnl, Math.round(3 * (1 - 0.81 - fee) * 10000) / 10000);
  assert.strictEqual(lh.longholdOutcome(row, 'yes').pnl, Math.round(3 * -(0.81 + fee) * 10000) / 10000);
  assert.strictEqual(lh.longholdOutcome(row, 'void'), null);
};

const fillRows = (pnls, over) => pnls.map((p, i) => Object.assign({ rule: RULE.id, arm: 'A', event: 'E' + i, settled: true, wouldFill: true, pnl: p, closeMs: NOW + i * 1000, atMs: NOW + i }, over || {}));
gates.LH6 = () => {
  // Consequence, the registered kill rules: an arm latches at net under -$15 after 20 fills, or after 5 losses in a row; the other arm is unaffected; and it stays latched after a recovery.
    assert.strictEqual(lh.armVerdict(RULE, fillRows(Array(10).fill([-1.4, 0]).flat()), 'A').tripped, false, '-14 is not under -15');
  assert.strictEqual(lh.armVerdict(RULE, fillRows(Array(10).fill([-1.6, 0]).flat()), 'A').tripped, true, '-16 after 20 fills is');
  assert.strictEqual(lh.armVerdict(RULE, fillRows(Array(9).fill([-1.8, 0]).flat().concat([-1])), 'A').tripped, false, 'the net rule waits for 20 fills');
  assert.strictEqual(lh.armVerdict(RULE, fillRows([0.2, -1, -1, -1, -1, -1]), 'A').reason, '5 losses in a row');
  assert.strictEqual(lh.armVerdict(RULE, fillRows([-1, -1, -1, -1, 1, -1]), 'A').tripped, false);
  assert.strictEqual(lh.armVerdict(RULE, fillRows(Array(5).fill(-1)), 'B').tripped, false, 'arms are separate');
  assert.strictEqual(lh.armVerdict(RULE, fillRows([-1, -1, -1, -1, -1, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9]), 'A').tripped, true, 'a later recovery does not lift it');
  assert.strictEqual(lh.armVerdict(RULE, fillRows(Array(5).fill(-1), { wouldFill: false }), 'A').tripped, false, 'only fillable settled rows count as fills');
};

gates.LH7 = async () => {
  // Consequence: a latched arm stays off (no row, nothing priced past the check), another arm still records, and a stored latch under an OLD rearmAt no longer binds (a reviewed edit re-arms). An unreadable latch writes nothing.
  const ms = [mk('A2', '0.2000', '0.2200'), mk('B1', '0.8000', '0.8400')];
  const run = async (latch, over) => { const wrote = [], reads = []; const r = await lh.runLongholdTick(Object.assign({ now: NOW, rules: [RULE], seen: new Set(), listMarkets: async () => ms, market: async (t) => { reads.push(t); return ms.find((m) => m.ticker === t); },
    readLatch: async () => latch, record: async (row) => { wrote.push(row); } }, over || {})); return { r, wrote, reads }; };
  // the minute picks (rule, series) by minute number; find a minute that lists KXTRUMPAPPROVE
  let when = NOW; while (lh.longholdSeriesDue([RULE], when)[0].series !== 'KXTRUMPAPPROVE') when += 60000;
  const at = (o) => Object.assign({ now: when }, o);
  const base = await run({}, at({}));
  assert.deepStrictEqual(base.wrote.map((x) => x.arm).sort(), ['A', 'B']);
  const latched = await run({ FIXTURE_LH: { A: { tripped: true, rearmAt: RULE.rearmAt } } }, at({}));
  assert.deepStrictEqual(latched.wrote.map((x) => x.arm), ['B'], 'arm A is off, arm B still records');
  const old = await run({ FIXTURE_LH: { A: { tripped: true, rearmAt: '2026-10-01' } } }, at({}));
  assert.deepStrictEqual(old.wrote.map((x) => x.arm).sort(), ['A', 'B'], 'a latch from before the reviewed re-arm does not bind');
  const broken = await run(null, at({ readLatch: async () => { throw new Error('x'); } }));
  assert.strictEqual(broken.wrote.length, 0, 'fail closed on an unreadable latch');
  const twice = new Set(); await run({}, at({ seen: twice })); const again = await run({}, at({ seen: twice }));
  assert.strictEqual(again.wrote.length, 0, 'the same event and arm is not tried again by this instance');
};

gates.LH8 = async () => {
  // Consequence: the request count is bounded by code constants whatever the market list holds: one list read, at most 3 single reads, and a failed list or price read changes nothing else.
  const many = []; for (let i = 0; i < 40; i++) many.push(mk('M' + i, '0.2000', '0.2200', { event_ticker: 'EV' + i, ticker: 'KXTRUMPAPPROVE-EV' + i + '-X' }));
  let lists = 0, singles = 0; let when = NOW; while (lh.longholdSeriesDue([RULE], when)[0].series !== 'KXTRUMPAPPROVE') when += 60000;
  const r = await lh.runLongholdTick({ now: when, rules: [RULE], seen: new Set(), listMarkets: async () => { lists++; return many; }, market: async (t) => { singles++; return many.find((m) => m.ticker === t); }, readLatch: async () => ({}), record: async () => {} });
  assert.deepStrictEqual([lists, singles, r.written], [1, lh.LIMITS.maxPriceReadsPerMinute, 3]);
  assert.ok(lh.LIMITS.maxListReadsPerMinute === 1 && lh.LIMITS.maxPriceReadsPerMinute <= 3 && lh.LIMITS.maxSettleReadsPerSweep <= 3);
  const f1 = await lh.runLongholdTick({ now: when, rules: [RULE], seen: new Set(), listMarkets: async () => { throw new Error('down'); }, market: async () => { throw new Error('x'); }, readLatch: async () => ({}), record: async () => {} });
  assert.strictEqual(f1.written, 0);
  const f2 = await lh.runLongholdTick({ now: when, rules: [RULE], seen: new Set(), listMarkets: async () => many, market: async () => { throw new Error('slow'); }, readLatch: async () => ({}), record: async () => { throw new Error('w'); } });
  assert.strictEqual(f2.written, 0, 'failed reads and writes are swallowed');
  const pairs = {}; for (let i = 0; i < 4; i++) pairs[lh.longholdSeriesDue([RULE], NOW + i * 60000)[0].series] = 1;
  assert.deepStrictEqual(Object.keys(pairs).sort(), ['KXTRUMPAPPROVE', 'KXVHGCB'], 'round robin visits every series');
};

gates.LH9 = async () => {
  // Consequence: settling fills in the result and net, trips the latch from the settled rows and stores it, and reads at most 3 markets.
  const rows = []; for (let i = 0; i < 6; i++) rows.push({ rule: RULE.id, arm: 'A', event: 'E' + i, ticker: 'T' + i, side: 'no', price: 0.81, contracts: 3, settled: false, wouldFill: true, closeMs: NOW - 3600000 + i, atMs: NOW - 18000000 + i });
  const store = rows.map((r) => Object.assign({}, r)); const wrote = {}; let reads = 0, latchPatch = null;
  const out = await lh.settleLongholdRows({ now: NOW, rules: [RULE], readOpen: async () => store.filter((r) => !r.settled), market: async () => { reads++; return { result: 'yes' }; },
    update: async (id, p) => { const r = store.find((x) => lh.rowId(x) === id); Object.assign(r, p); wrote[id] = p; }, readSettled: async () => store.filter((r) => r.settled), readLatch: async () => ({}), writeLatch: async (p) => { latchPatch = p; } });
  assert.deepStrictEqual([out.settled, reads], [3, 3]);
  assert.strictEqual(Object.values(wrote)[0].won, false);
  const out2 = await lh.settleLongholdRows({ now: NOW, rules: [RULE], readOpen: async () => store.filter((r) => !r.settled), market: async () => ({ result: 'yes' }),
    update: async (id, p) => { Object.assign(store.find((x) => lh.rowId(x) === id), p); }, readSettled: async () => store.filter((r) => r.settled), readLatch: async () => ({}), writeLatch: async (p) => { latchPatch = p; } });
  assert.strictEqual(out2.settled, 3);
  assert.deepStrictEqual(out2.latched, ['FIXTURE_LH/A'], '5 straight losses latch the arm');
  assert.strictEqual(latchPatch.FIXTURE_LH.A.tripped, true);
  assert.strictEqual(latchPatch.FIXTURE_LH.A.rearmAt, RULE.rearmAt);
};

gates.LH10 = () => {
  // Consequence: the nightly rows are compact and carry no ticker, event or id; the return rule is reported as numbers with the owner's approval always required.
  const rows = fillRows([1, 1, -1]).map((r) => Object.assign(r, { ticker: 'SECRET-T', event: 'SECRET-E' }));
  const rep = lh.longholdReport([RULE], rows, NOW + 86400000);
  const text = JSON.stringify(rep);
  assert.ok(!/SECRET|KX/.test(text), 'no ticker or event');
  assert.deepStrictEqual([rep[0].arms[0].fillable, rep[0].arms[0].returnRule.ownerApprovalNeeded, rep[0].arms[0].returnRule.statsMet, rep[0].arms[1].rows], [3, true, false, 0]);
};

gates.LH11 = () => {
  // Consequence: NO ORDER IS POSSIBLE from this module. It imports nothing, names no order, slot, sizing, L1 or signing code, no write except its two collections, and the wiring adds only a public GET and its own documents.
  const src = code(read('functions', 'kalshiLongholdLib.js'));
  assert.deepStrictEqual([...src.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), [], 'no imports at all');
  assert.ok(!/\b(fetch|sign\w*|privateKey|private_key|createOrder|portfolio|POST|kalshiLiveLib|kalshiSlot\w*|firebase\w*|getFirestore|sendOrder|client_order_id)\b/i.test(src), 'no network, signing, order or Firestore code in the library');
  const idx = code(read('functions', 'index.js'));
  const block = idx.slice(idx.indexOf('activeLongholdRules().length'), idx.indexOf('failure = e;', idx.indexOf('activeLongholdRules().length')));
  assert.ok(block.length > 500 && !/kalshiLiveOrders|kalshiSlot|kalshiLiveSession|live\.|slotLib|runL1|sendOrder|KALSHI_LIVE_KEY|sessRef|sizingRef/.test(block), 'the wiring touches no order, slot, session or sizing path');
  assert.deepStrictEqual([...new Set([...block.matchAll(/collection\(([^)]*)\)/g)].map((m) => m[1]))].sort(), ['longholdLib.CONTROL_COLLECTION', 'longholdLib.COLLECTION'].sort());
  assert.ok(/if \(!armedOn && longholdLib/.test(idx), 'it never runs while an armed test order is on');
  // nothing that decides an order reads the rows
  for (const f of ['kalshiLiveLib.js', 'kalshiSlotLib.js', 'kalshiSlotRunLib.js', 'kalshiSignalLib.js']) if (fs.existsSync(path.join(root, 'functions', f))) assert.ok(!/kalshiLongholdRows|kalshiLongholdLib/.test(read('functions', f)), f + ' does not read the long-hold log');
  assert.ok(!/kalshiLongholdRows|kalshiLongholdControl/.test(read('firestore.rules')) || /allow (read|write): if false/.test(read('firestore.rules')), 'no client rule opens the collections');
};

gates.LH13 = async () => {
  // Consequence: slow reads cannot hold the minute function. Past the code-constant deadline no further read is started, rows already written stay, and an unsafe event id is skipped and counted, never written.
  const many = []; for (let i = 0; i < 6; i++) many.push(mk('M' + i, '0.2000', '0.2200', { event_ticker: 'EV' + i, ticker: 'KXTRUMPAPPROVE-EV' + i + '-X' }));
  let when = NOW; while (lh.longholdSeriesDue([RULE], when)[0].series !== 'KXTRUMPAPPROVE') when += 60000;
  let t = 0, singles = 0; const wrote = [];
  const r = await lh.runLongholdTick({ now: when, rules: [RULE], seen: new Set(), clock: () => t, readLatch: async () => ({}), listMarkets: async () => { t += 8000; return many; },
    market: async (k) => { singles++; t += 9000; return many.find((m) => m.ticker === k); }, record: async (row) => { wrote.push(row); } });
  assert.ok(lh.LIMITS.tickDeadlineMs <= 20000);
  assert.strictEqual(r.timedOut, true);
  assert.ok(singles <= 2, 'reads stop at the deadline: ' + singles);
  assert.strictEqual(wrote.length, singles, 'what was priced before the deadline is still recorded');
  const bad = [mk('Z', '0.2000', '0.2200', { event_ticker: 'KXTRUMPAPPROVE/../x' })];
  const w2 = []; const r2 = await lh.runLongholdTick({ now: when, rules: [RULE], seen: new Set(), readLatch: async () => ({}), listMarkets: async () => bad, market: async (k) => bad[0], record: async (row) => { w2.push(row); } });
  assert.deepStrictEqual([r2.unsafe >= 1, w2.length], [true, 0]);
  const idx = code(read('functions', 'index.js'));
  assert.ok(/orderBy\("atMs", "desc"\)\.limit\(2000\)/.test(idx), 'the report read is newest-first and bounded');
};

gates.LH12 = () => {
  // Consequence: with the registry empty the report adds no field and the minute function takes no new branch.
  const rep = code(read('functions', 'kalshiReportLib.js'));
  assert.ok(/if \(lr\.length\) longhold =/.test(rep), 'the field exists only when a rule is registered');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) { try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
  process.exit(failed ? 1 : 0);
})();
