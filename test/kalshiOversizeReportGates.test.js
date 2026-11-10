// The nightly report's oversize section (Oct 29, 2026): orders bigger than today's code could size them. Zero is normal; rows carry series, count, limit and time only.
const assert = require('assert');
const lib = require('../functions/kalshiReportLib');
const NOW = Date.parse('2026-10-29T00:00:00Z');
const ord = (o) => Object.assign({ ticker: 'KXXRP15M-26OCT28-T1', side: 'yes', count: 1, fillCount: 1, avgFill: 0.93, status: 'filled', settled: true, result: 'yes', settledPnl: 0.1, ts: NOW - 3600000, entryLead: '6m', orderId: 'SECRET-ORDER-ID', clientOrderId: 'L1-SECRET' }, o);
const gates = {};

gates.OV1 = () => {
  const ok = lib.buildReport([ord({}), ord({ ticker: 'KXGOLD15M-26OCT28-T1', count: 20, fillCount: 20 }), ord({ ticker: 'KXBTC15M-26OCT28-T1', count: 1, fillCount: 1 })], NOW, 24, false);
  assert.deepStrictEqual(ok.oversize, { count: 0, orders: [] }, 'valid sizes, gold ladder included, report zero');
};
gates.OV2 = () => {
  const r = lib.buildReport([ord({ ticker: 'KXXRP15M-26OCT28-T1', count: 12, fillCount: 12, entryLead: undefined, ts: NOW - 7200000 }), ord({})], NOW, 24, false);
  assert.strictEqual(r.oversize.count, 1);
  assert.deepStrictEqual(r.oversize.orders[0], { ts: new Date(NOW - 7200000).toISOString(), series: 'KXXRP15M', count: 12, max: 1 });
  assert.ok(!/SECRET|orderId|clientOrderId/.test(JSON.stringify(r)), 'no ids, even with the new section');
  assert.strictEqual(lib.buildReport([ord({ ticker: 'KXXRP15M-26OCT28-T1', count: undefined, fillCount: 12 })], NOW, 24, false).oversize.count, 1, 'a filled size counts when the intended size is missing');
  assert.strictEqual(lib.buildReport([ord({ ticker: 'KXXRP15M-26OCT28-T1', ts: NOW - 99 * 3600000, count: 12, fillCount: 12 })], NOW, 24, false).oversize.count, 0, 'only the window asked for');
};
gates.OV4 = () => {
  // Dogecoin was removed on Nov 9, 2026: its older orders (any size) are history and never show as oversize; one placed after the cutoff would.
  const old = lib.buildReport([ord({ ticker: 'KXDOGE15M-26NOV02-T1', count: 13, fillCount: 13, ts: Date.parse('2026-11-02T15:00:00Z') })], Date.parse('2026-11-09T12:00:00Z'), 24 * 10, false);
  assert.strictEqual(old.oversize.count, 0, 'an old Dogecoin order is not an oversize alarm');
  const fresh = lib.buildReport([ord({ ticker: 'KXDOGE15M-26NOV10-T1', count: 5, fillCount: 5, ts: Date.parse('2026-11-10T15:00:00Z') })], Date.parse('2026-11-10T16:00:00Z'), 24, false);
  assert.strictEqual(fresh.oversize.count, 1, 'a Dogecoin order after the removal is flagged (the size lock allows 0)');
};
gates.OV3 = () => {
  const a = lib.buildReport([ord({})], NOW, 24, true), b = lib.buildReport([ord({})], NOW, 24, false);
  for (const k of Object.keys(b)) if (k !== 'oversize') assert.ok(k in a, k + ' unchanged');
  assert.deepStrictEqual(Object.keys(a.orders[0]).sort(), ['addon', 'answerMs', 'answeredAtMs', 'askSize', 'avgFee', 'avgFill', 'bidSize', 'count', 'depthAtLimit', 'depthLevels', 'entryLead', 'exitAt', 'exitAvg', 'exitBid', 'kalshiStatus', 'limit', 'orderedCount', 'price', 'result', 'rise3', 'seenAsk', 'seenBid', 'sentAtMs', 'settledPnl', 'shareOfDepth', 'side', 'smooth', 'startLateMs', 'startToSendMs', 'status', 'tickStartMs', 'ticker', 'ts'].sort(), 'per-order rows unchanged');
};
for (const [n, f] of Object.entries(gates)) { f(); console.log('ok   ' + n); }
