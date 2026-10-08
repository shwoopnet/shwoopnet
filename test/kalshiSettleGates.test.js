'use strict';
// A filled trade is settled in the records whether or not a session is running. Before this, only the session's own minute check settled
// orders, so a trade that finished after a loss stop (or after the 24 hours) stayed "open" for ever and never reached the win and loss counts.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');
const fnSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const gates = {};

const mk = (id, over) => Object.assign({ id, ticker: 'T-' + id, side: 'yes', count: 2, fillCount: '2.00', maxCost: 1.86, status: 'filled', strategy: 'L1' }, over);
function world(orders, results) {
  const updates = [], reads = [];
  const store = { async openFilled() { return orders.filter((o) => o.status === 'filled'); }, async updateTest(id, patch) { updates.push([id, patch]); } };
  const fetchFn = async (url) => {
    const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
    reads.push(tk);
    if (results[tk] === 'down') return { status: 503, text: async () => 'down' };
    return { status: 200, text: async () => JSON.stringify({ market: { result: results[tk] || '' } }) };
  };
  return { store, fetchFn, updates, reads };
}

gates.S1 = async () => {
  const w = world([mk('lost'), mk('won', { side: 'no' }), mk('open'), mk('done', { settled: true, result: 'yes', settledPnl: 0.1 }), mk('nofill', { status: 'no fill', fillCount: '0.00' }), mk('nocost', { maxCost: undefined })],
    { 'T-lost': 'no', 'T-won': 'no', 'T-open': '' });
  const r = await live.settleOpenOrders({ store: w.store, fetchFn: w.fetchFn, nowMs: 1 });
  const u = Object.fromEntries(w.updates);
  assert.deepStrictEqual(Object.keys(u).sort(), ['lost', 'won'], 'only finished markets are settled');
  assert.deepStrictEqual([u.lost.settled, u.lost.result, u.lost.settledPnl], [true, 'no', -1.86], 'a loss costs the whole order');
  assert.deepStrictEqual([u.won.result, u.won.settledPnl], ['no', 0.14], 'a win pays $1 a contract less the cost');
  assert.ok(!w.reads.includes('T-done') && !w.reads.includes('T-nofill') && !w.reads.includes('T-nocost'), 'settled, unfilled and cost-less orders are not even read');
  assert.strictEqual(r.settled, 2);
};

gates.S2 = async () => {
  const w = world([mk('a'), mk('b')], { 'T-a': 'down', 'T-b': 'yes' });
  const r = await live.settleOpenOrders({ store: w.store, fetchFn: w.fetchFn, nowMs: 1 });
  assert.deepStrictEqual(w.updates.map((x) => x[0]), ['b'], 'a failed read leaves that order open for the next minute and does not stop the others');
  assert.strictEqual(r.settled, 1);
  const many = world(Array.from({ length: 30 }, (_, i) => mk('o' + i)), {});
  await live.settleOpenOrders({ store: many.store, fetchFn: many.fetchFn, nowMs: 1, max: 5 });
  assert.strictEqual(many.reads.length, 5, 'at most max markets are read in one run');
};

gates.S3 = () => {
  const f = live.settledFields({ side: 'yes', count: 2, fillCount: '1.00', maxCost: 1.86 }, 'yes');
  assert.strictEqual(f.settledPnl, 0.07, 'a half filled order pays and costs in proportion');
  assert.strictEqual(live.settledFields({ side: 'yes', fillCount: '1', maxCost: 0.93 }, 'no').settledPnl, -0.93, 'a one contract order from before size scaling has count 1');
};

gates.S4 = () => {
  const i = fnSrc.indexOf('exports.kalshiLiveArmed');
  const body = fnSrc.slice(i, fnSrc.indexOf('exports.kalshiBookRecorder'));
  const sweep = body.indexOf('live.settleOpenOrders');
  assert.ok(sweep > body.indexOf('live.runL1Tick'), 'it runs after the tick');
  assert.ok(sweep > body.indexOf('if (sessionOn && !armedOn)') && !/if \(sessionOn[^\n]*\{[^}]*settleOpenOrders/.test(body), 'and not only while a session is on');
  assert.ok(/try \{\s*await live\.settleOpenOrders[\s\S]*?\} catch \(e\) \{/.test(body), 'a failure in it cannot fail the tick');
  assert.ok(/async openFilled\(\)/.test(fnSrc), 'the store can list filled orders');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
