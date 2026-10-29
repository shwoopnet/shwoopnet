// The nightly report's oversize section (Oct 29, 2026): orders bigger than today's code could size them. Zero is normal; rows carry series, count, limit and time only.
const assert = require('assert');
const lib = require('../functions/kalshiReportLib');
const NOW = Date.parse('2026-10-29T00:00:00Z');
const ord = (o) => Object.assign({ ticker: 'KXDOGE15M-26OCT28-T1', side: 'yes', count: 3, fillCount: 3, avgFill: 0.93, status: 'filled', settled: true, result: 'yes', settledPnl: 0.1, ts: NOW - 3600000, entryLead: '6m', orderId: 'SECRET-ORDER-ID', clientOrderId: 'L1-SECRET' }, o);
const gates = {};

gates.OV1 = () => {
  const ok = lib.buildReport([ord({}), ord({ ticker: 'KXGOLD15M-26OCT28-T1', count: 20, fillCount: 20 }), ord({ ticker: 'KXBTC15M-26OCT28-T1', count: 1, fillCount: 1 })], NOW, 24, false);
  assert.deepStrictEqual(ok.oversize, { count: 0, orders: [] }, 'valid sizes, gold ladder included, report zero');
};
gates.OV2 = () => {
  const r = lib.buildReport([ord({ count: 12, fillCount: 12, entryLead: undefined, ts: NOW - 7200000 }), ord({})], NOW, 24, false);
  assert.strictEqual(r.oversize.count, 1);
  assert.deepStrictEqual(r.oversize.orders[0], { ts: new Date(NOW - 7200000).toISOString(), series: 'KXDOGE15M', count: 12, max: 3 });
  assert.ok(!/SECRET|orderId|clientOrderId/.test(JSON.stringify(r)), 'no ids, even with the new section');
  assert.strictEqual(lib.buildReport([ord({ count: undefined, fillCount: 12 })], NOW, 24, false).oversize.count, 1, 'a filled size counts when the intended size is missing');
  assert.strictEqual(lib.buildReport([ord({ ts: NOW - 99 * 3600000, count: 12, fillCount: 12 })], NOW, 24, false).oversize.count, 0, 'only the window asked for');
};
gates.OV3 = () => {
  const a = lib.buildReport([ord({})], NOW, 24, true), b = lib.buildReport([ord({})], NOW, 24, false);
  for (const k of Object.keys(b)) if (k !== 'oversize') assert.ok(k in a, k + ' unchanged');
  assert.deepStrictEqual(Object.keys(a.orders[0]).sort(), ['avgFill', 'count', 'entryLead', 'result', 'settledPnl', 'side', 'status', 'ticker', 'ts'], 'per-order rows unchanged');
};
for (const [n, f] of Object.entries(gates)) { f(); console.log('ok   ' + n); }
