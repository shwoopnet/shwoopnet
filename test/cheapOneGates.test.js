'use strict';
// CH1 to CH5: CHEAP1, the third live strategy (Nov 3, 2026, the owner: "thats what i asked for"): the cheaper Bitcoin side 15c to 49c, 180 to 120 s before the close, 5 contracts,
// held to settlement, ONLY in the windows where OICORE's trigger does not fire. Consequence: it never doubles OICORE's bet, it can never be bigger than 5 contracts, and an unreadable
// open interest reading sends nothing.
const assert = require('assert');
const fs = require('fs'), path = require('path');
const slot = require('../functions/kalshiSlotLib');
const C = slot.SLOT_STRATEGIES.find((s) => s.id === 'CHEAP1');
const O = slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE');
const gates = {};
gates.CH1 = () => {
  assert.ok(C && slot.validateSlotStrategy(C).ok, 'CHEAP1 is registered and valid');
  assert.deepStrictEqual([C.series.slice(), C.entry.sideRule, C.entry.priceMin, C.entry.priceMax, C.entry.leftMaxSec, C.entry.leftMinSec], [['KXBTC15M'], 'no', 0.05, 0.45, 180, 120]);
  assert.strictEqual(C.entry.oiRiseMax, O.entry.oiRiseMin, 'it trades exactly the windows OICORE leaves alone');
  assert.strictEqual(C.contractsPerOrder, 5); assert.strictEqual(C.exit.holdToSettle, true);
  assert.deepStrictEqual([C.killRules.maxConsecutiveLosses, C.killRules.minNet.afterFills, C.killRules.minNet.net], [20, 100, -15]);
  assert.ok(!slot.SLOT_LADDERS || !slot.SLOT_LADDERS.CHEAP1, 'no size ladder: always 5');
};
const NOW = Date.parse('2026-11-20T16:57:30Z');
const input = (id, oiRise, extra) => Object.assign({ strategyId: id, ticker: 'KXBTC15M-26NOV201200-00', side: 'no', limit: 0.3, step: 1, depthAtTouch: 1000, slotOrders: [], l1Orders: [],
  slotOrdersComplete: true, lockTxn: true, lock: null, position: 0, sizingBase: 800, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: NOW, oiRise }, extra || {});
gates.CH2 = () => {
  const lo = slot.slotOrderCheck(input('CHEAP1', 40000));
  assert.ok(lo.allowed && lo.count === 5, 'a quiet window (rise under 86,300): CHEAP1 buys 5: ' + JSON.stringify(lo));
  assert.ok(!slot.slotOrderCheck(input('CHEAP1', 86300)).allowed, 'at the OICORE line: left to OICORE');
  assert.ok(!slot.slotOrderCheck(input('CHEAP1', 200000)).allowed, 'above it: left to OICORE');
  for (const bad of [undefined, null, NaN]) assert.ok(!slot.slotOrderCheck(input('CHEAP1', bad)).allowed, 'an unreadable rise sends nothing');
  assert.ok(!slot.slotOrderCheck(input('OICORE', 40000)).allowed && slot.slotOrderCheck(input('OICORE', 90000)).allowed, 'and OICORE still trades only its own windows');
};
gates.CH3 = () => {
  assert.ok(!slot.slotOrderCheck(input('CHEAP1', 40000, { limit: 0.04 })).allowed, 'under 5c: no');
  assert.ok(!slot.slotOrderCheck(input('CHEAP1', 40000, { limit: 0.46 })).allowed, 'over 45c: no');
  assert.ok(!slot.slotOrderCheck(input('CHEAP1', 40000, { side: 'yes' })).allowed, 'NO side only');
  assert.ok(!slot.slotOrderCheck(input('CHEAP1', 40000, { secondsLeft: 200 })).allowed, 'outside 180 to 120 s: no');
  const w = slot.slotOrderCheck(input('CHEAP1', 40000, { wanted: 50 }));
  assert.ok(w.allowed && w.count === 5, 'a caller asking for more never gets more than 5');
};
gates.CH4 = () => {
  // A strategy entry with oiRiseMax is validated like oiRiseMin.
  const bad = JSON.parse(JSON.stringify(C)); bad.entry.oiRiseMax = 5;
  assert.ok(!slot.validateSlotStrategy(bad).ok, 'a line under 1000 contracts is refused');
  assert.deepStrictEqual(slot.SLOT_HOLD_ALLOWED.slice(), ['OICORE', 'CHEAP1']);
};
gates.CH5 = () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/oiRiseMax/.test(src) && /left to OICORE/.test(src), 'the engine reads the open interest for CHEAP1 too and skips OICORE windows before any order');
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(/var KAL_SLOT_REGISTERED = \['OICORE', 'CHEAP1'\];/.test(html) && /CHEAP1: \{ name: 'Cheap side'/.test(html), 'the Bot page lists CHEAP1 with its own chip and row');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
