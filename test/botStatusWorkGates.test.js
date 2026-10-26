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
const f = new Function("var KAL_TZ = 'America/Chicago';\n" + ['kalDayKey', 'kalshiTodayWork'].map(fnSource).join('\n') + '; return { kalshiTodayWork };')();
const NOW = Date.parse('2026-10-26T18:00:00Z');   // 1 PM Central
const MIN = 60000;

gates.W1 = () => {
  // A miss must be visible: an order that did not fill is not a quiet success.
  const w = f.kalshiTodayWork([
    { strategy: 'L1', ts: NOW - 5 * MIN, status: 'filled' },
    { strategy: 'L1', ts: NOW - 20 * MIN, status: 'filled' },
    { strategy: 'L1', ts: NOW - 40 * MIN, status: 'no fill' },
    { strategy: 'L1', ts: NOW - 60 * MIN, status: 'unknown' },
  ], NOW);
  assert.deepStrictEqual([w.sent, w.filled, w.noFill, w.problem], [4, 2, 1, 1]);
  assert.strictEqual(w.lastTs, NOW - 5 * MIN);
};
gates.W2 = () => {
  // Yesterday's orders and other strategies never count toward today.
  const w = f.kalshiTodayWork([
    { strategy: 'L1', ts: NOW - 30 * 3600000, status: 'filled' },
    { strategy: 'OW1', ts: NOW - 5 * MIN, status: 'filled' },
    { ts: NaN, strategy: 'L1', status: 'filled' },
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

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
if (failed) process.exit(1);
