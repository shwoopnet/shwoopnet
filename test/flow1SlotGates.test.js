'use strict';
// FL1 to FL5: FLOW1, the seller-flow probe (Nov 4, 2026, the owner: "can probably go live"). Consequence: it buys the cheap Bitcoin side ONLY when takers were net selling it in the 3 minutes
// before the look, at most 5 contracts; a missing, partial or positive flow sends nothing, and the flow is computed from every public trade in the fixed span.
const assert = require('assert');
const fs = require('fs'), path = require('path');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const F = slot.SLOT_STRATEGIES.find((s) => s.id === 'FLOW1');
const gates = {};
gates.FL1 = () => {
  assert.ok(F && slot.validateSlotStrategy(F).ok, 'FLOW1 is registered and valid');
  assert.deepStrictEqual([F.series.slice(), F.entry.sideRule, F.entry.priceMin, F.entry.priceMax, F.entry.leftMaxSec, F.entry.leftMinSec, F.entry.flowMax], [['KXBTC15M'], 'cheap', 0.05, 0.5, 180, 120, -0.036]);
  assert.strictEqual(F.contractsPerOrder, 5); assert.strictEqual(F.exit.holdToSettle, true);
  assert.deepStrictEqual([F.killRules.maxConsecutiveLosses, F.killRules.minNet.afterFills, F.killRules.minNet.net], [15, 40, -10]);
  assert.ok(slot.SLOT_HOLD_ALLOWED.includes('FLOW1'));
  const bad = JSON.parse(JSON.stringify(F)); bad.entry.flowMax = 0.2;
  assert.ok(!slot.validateSlotStrategy(bad).ok, 'a positive flow line (buying) is refused');
};
gates.FL2 = () => {
  const f = run._testOnly.flowFromTrades, t = (sec, side, n) => ({ created_time: new Date(sec * 1000).toISOString(), taker_side: side, count_fp: String(n) });
  const tape = [t(100, 'no', 10), t(101, 'no', 10), t(102, 'no', 10), t(110, 'yes', 5), t(111, 'yes', 5)];
  assert.strictEqual(f(tape, 'yes', 100, 200), -0.5, 'takers sold YES 30 (bought NO) and bought YES 10: (10 - 30) / 40');
  assert.strictEqual(f(tape, 'no', 100, 200), 0.5, 'the same tape from the NO side');
  assert.strictEqual(f(tape.slice(0, 4), 'yes', 100, 200), null, 'fewer than 5 trades: no reading (S-FLOW1 dropped those windows)');
  assert.strictEqual(f([t(99, 'no', 30), t(200, 'yes', 10)].concat(tape.slice(0, 3)), 'yes', 100, 200), null, 'trades outside [start, end) do not count');
  assert.strictEqual(f(Array.from({ length: 5 }, () => t(100, 'no', 5)), 'yes', 100, 200), -1, 'identical trades all count (no de-duplication)');
  assert.strictEqual(f(null, 'yes', 0, 1), null);
};
const NOW = Date.parse('2026-11-20T16:57:30Z');
const input = (flow, extra) => Object.assign({ strategyId: 'FLOW1', ticker: 'KXBTC15M-26NOV201200-00', side: 'yes', limit: 0.2, step: 1, depthAtTouch: 1000, slotOrders: [], l1Orders: [],
  slotOrdersComplete: true, lockTxn: true, lock: null, position: 0, sizingBase: 800, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: NOW, flow }, extra || {});
gates.FL3 = () => {
  const ok = slot.slotOrderCheck(input(-0.2));
  assert.ok(ok.allowed && ok.count === 5, 'net selling: 5 contracts: ' + JSON.stringify(ok));
  assert.ok(slot.slotOrderCheck(input(-0.036)).allowed, 'exactly the line trades');
  assert.ok(!slot.slotOrderCheck(input(-0.035)).allowed && !slot.slotOrderCheck(input(0.4)).allowed, 'above the line: no order');
  for (const b of [undefined, null, NaN, -2]) assert.ok(!slot.slotOrderCheck(input(b)).allowed, 'unreadable or impossible flow: no order');
  const w = slot.slotOrderCheck(input(-0.2, { wanted: 50 }));
  assert.ok(w.allowed && w.count === 5, 'never more than 5');
};
gates.FL4 = () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/path: "\/markets\/trades"/.test(src) && /min_ts: String\(closeSec - 360\), max_ts: String\(closeSec - 180\)/.test(src), 'the engine reads the public tape for 360 to 180 s before the close, with no key');
  assert.ok(/if \(page === FLOW_PAGES - 1\) ok = false;/.test(src), 'a read that needs more pages than allowed is partial and sends nothing');
  assert.ok(/oiRise, flow, position/.test(src), 'the flow goes into the gate');
};
gates.FL5 = () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(/var KAL_SLOT_REGISTERED = \['OICORE', 'EVENT830', 'FLOW1'\];/.test(html) && /FLOW1: \{ name: 'Seller flow'/.test(html) && /<span id="kalRulesSlotFlow">FLOW1,/.test(html), 'the Bot page lists FLOW1');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
