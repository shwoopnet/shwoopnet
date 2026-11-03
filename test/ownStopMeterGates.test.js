// The Loss stop tile shows each strategy's own stop used (Nov 2, 2026).
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const fn = (name) => new RegExp('  function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\}\\n').exec(html)[0];
const reg = /  var KAL_SLOT_REGISTERED = \[[^\]]*\];\n/.exec(html)[0];
const lib = new Function('Date', 'Number', 'Math', 'String', 'Object', reg + fn('kalshiStrategyOf') + fn('kalshiRiskMeter') + fn('kalshiOwnStops') + '; return { kalshiOwnStops, kalshiRiskMeter };')(Date, Number, Math, String, Object);
const NOW = Date.parse('2026-11-02T18:00:00Z');
const s = { sizing: true, sizeBase: 100 };                     // the stop is 12% of $100 = $12
const l1 = (pnl, extra) => Object.assign({ strategy: 'L1', ticker: 'KXDOGE15M-26NOV021215-15', side: 'yes', count: 10, fillCount: '10', maxCost: 9.3, settled: true, result: pnl < 0 ? 'exit' : 'yes', settledPnl: pnl, ts: NOW - 3600000 }, extra || {});
const sl = (pnl, extra) => Object.assign({ strategy: 'SLOT', slotId: 'OICORE', ticker: 'KXBTC15M-26NOV021215-15', side: 'no', count: 10, fillCount: '10', maxCost: 2, settled: true, result: pnl < 0 ? 'yes' : 'no', settledPnl: pnl, ts: NOW - 3600000 }, extra || {});
const gates = {};
gates.OM1 = () => {
  // each strategy is judged on its own orders: an L1 loss of $6 is 50% of L1's own $12 stop whatever OICORE did, and the reverse
  const r = lib.kalshiOwnStops([l1(-6), sl(5)], s, NOW);
  assert.deepStrictEqual(r.map((x) => x.id), ['L1', 'OICORE', 'CHEAP1'], 'one meter per strategy, CHEAP1 included (Nov 3, 2026)');
  assert.strictEqual(r[2].fraction, 0, 'CHEAP1 has no orders here: 0% used');
  assert.ok(Math.abs(r[0].fraction - 0.5) < 1e-9, 'L1 own ' + r[0].fraction); assert.strictEqual(r[1].fraction, 0, 'a profitable OICORE shows 0% used');
  const r2 = lib.kalshiOwnStops([l1(3), sl(-2)], s, NOW);
  assert.strictEqual(r2[0].fraction, 0); assert.ok(Math.abs(r2[1].fraction - 2 / 12) < 1e-9, 'OICORE own ' + r2[1].fraction);
};
gates.OM2 = () => {
  // the account meter over both is unchanged by the split, and no orders reads 0% for each strategy
  const both = lib.kalshiRiskMeter([l1(-6), sl(-2)], s, NOW);
  assert.ok(Math.abs(both.fraction - 8 / 12) < 1e-9);
  const none = lib.kalshiOwnStops([], s, NOW); assert.ok(none.every((x) => x.fraction === 0));
  // an order older than 24 hours and a hand close are not counted
  const old = lib.kalshiOwnStops([l1(-11, { ts: NOW - 90000000 }), l1(-11, { result: 'hand' })], s, NOW); assert.strictEqual(old[0].fraction, 0);
};
gates.OM3 = () => {
  // wiring: the line is drawn under the account meter, percentages only
  assert.ok(/kal-risk-own">Own stops: ' \+ kalshiOwnStops\(allOrders, s, now\)/.test(html));
  assert.ok(!/kalshiMoney/.test(fn('kalshiOwnStops')));
  assert.ok(/\.kal-acct-risk \.kal-risk-own\{ order:4;/.test(html));
};
let failed = 0; for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + ': ' + e.message); } }
if (failed) process.exit(1);
