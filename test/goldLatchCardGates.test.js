'use strict';
// GL1 to GL5: the gold card shows the real kill latch (Nov 12, 2026, the owner). Consequence: a card must never read HEALTHY while the latch is close to firing or has fired.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
function fn(name) {
  const at = html.indexOf('  function ' + name + '(');
  assert.ok(at >= 0, name + ' is in the page');
  let i = html.indexOf('{', at), depth = 0, q = null;
  for (; i < html.length; i++) {
    const c = html[i];
    if (q) { if (c === '\\') i++; else if (c === q) q = null; continue; }
    if (c === "'" || c === '"') { q = c; continue; }
    if (c === '/' && html[i + 1] === '/') { i = html.indexOf('\n', i); continue; }
    if (c === '{') depth++;
    if (c === '}') { depth--; if (depth === 0) break; }
  }
  return html.slice(at, i + 1);
}
const line = (name) => { const m = new RegExp('  var ' + name + ' = .*\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const names = ['kalshiBoardFillCost', 'kalshiBoardCash', 'kalshiBoardRows', 'kalshiGoldLatch', 'kalshiGoldLatchBadge', 'kalshiGoldLatchHtml'];
const P = new Function('Math', 'Number', 'isFinite', 'String', line('KAL_GOLD_LATCH') + names.map(fn).join('\n') + '; return { KAL_GOLD_LATCH, ' + names.join(', ') + ' };')(Math, Number, isFinite, String);
const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');
const T0 = P.KAL_GOLD_LATCH.rearmAt;
// A settled gold exit with a stored result p, k minutes after the re-arm.
const trade = (k, p) => ({ series: 'KXGOLD15M', ts: T0 + k * 60000, settled: true, fillCount: 1, count: 1, result: 'exit', settledPnl: p });
const run = (pnls) => P.kalshiGoldLatch(pnls.map((p, i) => trade(i + 1, p)), null, false, NaN);

gates.GL1 = () => {
  // the constants are the bot's, so the card cannot judge against a different line than the code that stops orders
  const lib = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiGoldKillLib.js'), 'utf8');
  const g = require('../functions/kalshiGoldKillLib').GOLD_KILL;
  assert.strictEqual(P.KAL_GOLD_LATCH.drawdown, g.drawdownDollars);
  assert.strictEqual(P.KAL_GOLD_LATCH.netFloor, g.netFloor);
  assert.strictEqual(P.KAL_GOLD_LATCH.afterTrades, g.netAfterTrades);
  assert.strictEqual(P.KAL_GOLD_LATCH.rearmAt, g.rearmAt);
  assert.strictEqual(P.KAL_GOLD_LATCH.series, g.series);
  assert.ok(lib.length > 0);
};
gates.GL2 = () => {
  // the replay trips on exactly the bot's two rules, and trades before the re-arm count for nothing
  const dd = run([5, -30, -30]);   // peak 5, now -55: 60 below the peak, past the $58.75 line
  assert.ok(dd.tripped && dd.trip === 'drawdown');
  const net = run(Array(39).fill(-0.6).concat([-0.7]));   // 40 trades, -24.1 net, under -20
  assert.ok(net.tripped && net.trip === 'net');
  const early = run(Array(39).fill(-0.6));   // 39 trades: the net rule has not started
  assert.ok(!early.tripped, 'the net floor needs 40 trades');
  const old = P.kalshiGoldLatch([trade(-5, -100)], null, false, NaN);
  assert.strictEqual(old.n, 0, 'a trade before the re-arm is history');
  assert.ok(!old.tripped);
};
gates.GL3 = () => {
  const B = P.kalshiGoldLatchBadge;
  assert.strictEqual(B(run([1, 1, 1])), null, 'healthy leaves the ordinary badge to decide');
  assert.strictEqual(B(run(Array(30).fill(-0.5))).text, 'NEAR KILL', 'net -15 at 30 trades is within 25 percent of the -20 floor');
  assert.strictEqual(B(run(Array(29).fill(-0.6))), null, 'under 30 trades the net is not called near');
  assert.strictEqual(B(run([2, -45])).text, 'NEAR KILL', 'drawdown 45 is within 25 percent of the 58.75 line');
  assert.strictEqual(B(run([2, -20])), null, 'drawdown 20 is not near');
  assert.strictEqual(B(run([5, -30, -30])).text, 'TRIPPED');
  assert.strictEqual(B(P.kalshiGoldLatch([], { tripped: true, rule: 'net' }, false, NaN)).text, 'TRIPPED', 'a stored tripped latch shows TRIPPED');
  assert.strictEqual(B(P.kalshiGoldLatch([], { tripped: false }, false, NaN)), null);
  assert.strictEqual(B(null), null);
};
gates.GL4 = () => {
  const h = P.kalshiGoldLatchHtml(run(Array(30).fill(-0.5)), esc, money);
  assert.ok(/Gold kill latch/.test(h) && /30 of 40/.test(h), 'names the latch and the 40 trades');
  assert.ok(/-\$20/.test(h) && /\$58\.75/.test(h), 'names the floor and the line');
  assert.ok(/-\$15\.00/.test(h), 'the net goes through money');
  const masked = P.kalshiGoldLatchHtml(run(Array(30).fill(-0.5)), esc, () => '****');
  assert.ok(!/-\$15/.test(masked), 'Privacy view masks our own dollars');
  assert.ok(/Tripped/.test(P.kalshiGoldLatchHtml(run([5, -30, -30]), esc, money)));
  assert.ok(/may be short/.test(P.kalshiGoldLatchHtml(P.kalshiGoldLatch([], null, true, T0 + 1), esc, money)), 'a list that does not reach the re-arm says so');
  // the page wires it: the badge and the block come from the latch, and no new read or listener was added
  assert.ok(/kalshiGoldLatchBadge\(s\.latch\) \|\| kalshiStratBadge\('live'/.test(html));
  assert.ok(/latchHtml: s\.latch \? kalshiGoldLatchHtml\(s\.latch, esc, money\)/.test(html));
  assert.ok(!/kalshiLiveControl', 'sizing'/.test(html), 'the page does not listen to the sizing document');
};
gates.GL5 = () => {
  // the public repo carries no live figure: the code holds the design constants only
  const code = names.map(fn).join('\n') + line('KAL_GOLD_LATCH');
  const nums = (code.replace(/'(?:[^'\\]|\\.)*'/g, "''").match(/\d+\.\d+|\d{2,}/g) || []).map(Number);
  const allowed = new Set([58.75, 20, 40, 30, 10, 100, 10000, 1000, 2026, 60000, 0.75, 1e-9]);
  nums.forEach((n) => assert.ok(allowed.has(n) || n < 10, 'unexpected figure ' + n + ' in the latch code: ' + code.slice(Math.max(0, code.indexOf(String(n)) - 30), code.indexOf(String(n)) + 20)));
  assert.ok(!/balance|\bbase\b/i.test(code), 'no balance in the latch code');
  assert.ok(!new RegExp(String.fromCharCode(0x2014)).test(code + fs.readFileSync(__filename, 'utf8')), 'no em dash');
};
let failed = 0;
for (const [name, f] of Object.entries(gates)) {
  try { f(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
