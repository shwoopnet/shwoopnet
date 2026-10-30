'use strict';
// The Bot status card says what today's orders did (the owner, Oct 26, 2026): sent, filled, not filled, and any whose answer was lost. It only reads the orders the page already holds.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('unbalanced ' + name);
}
const KAL_EDGE = /var KAL_EDGE_MIN = [^\n]*\n/.exec(html)[0];
const KAL_INFO = /var KAL_STRATEGY_INFO = \{[\s\S]*?\n  \};/.exec(html)[0];
const STRAT_OF = /  function kalshiStrategyOf\(o\)\{[^\n]*\n/.exec(html)[0];
const f = new Function("var KAL_TZ = 'America/Chicago';\n" + KAL_EDGE + '\n' + KAL_INFO + '\n' + STRAT_OF + '\n' + ['kalDayKey', 'kalshiActivePairs', 'kalshiIsActive', 'kalshiTodayWork', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiPerfStats', 'kalshiPricePaid', 'kalshiEdgeCheck'].map(fnSource).join('\n') + '; return { kalshiTodayWork, kalshiEdgeCheck };')();
const NOW = Date.parse('2026-10-26T18:00:00Z');   // 1 PM Central
const MIN = 60000;

gates.W1 = () => {
  // A miss must be visible: an order that did not fill is not a quiet success.
  const w = f.kalshiTodayWork([
    { strategy: 'L1', series: 'KXGOLD15M', ts: NOW - 5 * MIN, status: 'filled' },
    { strategy: 'L1', series: 'KXGOLD15M', ts: NOW - 20 * MIN, status: 'filled' },
    { strategy: 'L1', series: 'KXGOLD15M', ts: NOW - 40 * MIN, status: 'no fill' },
    { strategy: 'L1', series: 'KXGOLD15M', ts: NOW - 60 * MIN, status: 'unknown' },
  ], NOW);
  assert.deepStrictEqual([w.sent, w.filled, w.noFill, w.problem], [4, 2, 1, 1]);
  assert.strictEqual(w.lastTs, NOW - 5 * MIN);
};
gates.W2 = () => {
  // Yesterday's orders and other strategies never count toward today.
  const w = f.kalshiTodayWork([
    { strategy: 'L1', series: 'KXGOLD15M', ts: NOW - 30 * 3600000, status: 'filled' },
    { strategy: 'OW1', ts: NOW - 5 * MIN, status: 'filled' },
    { ts: NaN, strategy: 'L1', series: 'KXGOLD15M', status: 'filled' },
  ], NOW);
  assert.strictEqual(w.sent, 0);
  assert.strictEqual(w.lastTs, null);
  assert.strictEqual(f.kalshiTodayWork(null, NOW).sent, 0);
};
gates.W3 = () => {
  // The rows are drawn only for a running bot whose orders have loaded, and they never write anything.
  const render = html.slice(html.indexOf('function renderKalshiStatus('), html.indexOf('function renderKalshiStatus(') + 6000);
  assert.ok(/running && kalshiOrdersLoaded/.test(render), 'rows need a running bot and loaded orders');
  const helper = fnSource('kalshiTodayWork');
  assert.ok(!/setDoc|httpsCallable|runTransaction/.test(helper), 'read only');
};

// Settled orders: 'win' pays (1 - price) a contract, a loss costs the price.
const settled = (series, n, price, lossEvery, endTs) => Array.from({ length: n }, (_, i) => {
  const loss = lossEvery && i % lossEvery === lossEvery - 1;
  return { strategy: 'L1', series: 'KXGOLD15M', series, ts: endTs - (n - i) * 60000, settled: true, count: 2, fillCount: '2', price, averageFillPrice: String(price), settledPnl: loss ? -price * 2 : (1 - price) * 2 };
});
gates.W4 = () => {
  // The edge is the win rate against the average price paid: 9 wins in 10 at 93c is losing money, and the card must say so.
  const e = f.kalshiEdgeCheck(settled('KXGOLD15M', 40, 0.93, 10, NOW - 8 * 86400000), NOW);
  assert.ok(e.enough && Math.abs(e.winRate - 90) < 1e-9 && Math.abs(e.breakEven - 93) < 1e-9, 'win rate ' + e.winRate + ' against ' + e.breakEven);
  assert.ok(e.edgeCents < 0, 'a win rate under break-even is a negative edge');
};
gates.W5 = () => {
  // A handful of trades says nothing, so no verdict is drawn; and only the last 100 count.
  assert.strictEqual(f.kalshiEdgeCheck(settled('KXGOLD15M', 5, 0.93, 0, NOW), NOW).enough, false);
  assert.strictEqual(f.kalshiEdgeCheck(settled('KXGOLD15M', 150, 0.93, 0, NOW), NOW).n, 100);
};
gates.W6 = () => {
  // Best and worst market need at least two markets with a few trades each in the last 7 days.
  const gold = settled('KXGOLD15M', 6, 0.93, 0, NOW), btc = settled('KXBTC15M', 6, 0.93, 2, NOW);
  const e = f.kalshiEdgeCheck(gold.concat(btc), NOW);
  assert.ok(e.best && e.worst && e.best.net > e.worst.net, 'best beats worst');
  assert.strictEqual(f.kalshiEdgeCheck(gold, NOW).best, null);
};

gates.W7 = () => {
  // A NO order's average fill is written as the YES price (7c for a 93c NO). The break-even is what was PAID for the side bought, so a mixed book of YES and NO buys at 93c breaks even at 93%, not 50%.
  const mk = (i, side) => ({ strategy: 'L1', series: 'KXGOLD15M', series: 'KXGOLD15M', ts: NOW - (40 - i) * 60000, settled: true, side, count: 1, fillCount: '1', maxCost: 0.93, price: 0.93,
    averageFillPrice: side === 'no' ? '0.07' : '0.93', settledPnl: i % 10 === 9 ? -0.93 : 0.07 });
  const orders = Array.from({ length: 40 }, (_, i) => mk(i, i % 2 ? 'no' : 'yes'));
  const e = f.kalshiEdgeCheck(orders, NOW);
  assert.ok(Math.abs(e.breakEven - 93) < 0.5, 'break-even ' + e.breakEven);
  assert.ok(Math.abs(e.winRate - 90) < 1e-9);
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
if (failed) process.exit(1);
