'use strict';
// LM1 to LM3: OICORE's limit sits 1c above the touch (Nov 3, 2026, the owner: "build 1", on the refinement chat's S-LIM1 read: 6 of 24 limits went unfilled because the
// ask moved up 1c within seconds, and 3 of those 6 won). Consequence: OICORE pays at most 1c a contract more and catches fills it used to miss; it never goes past its own band,
// no other strategy changes, and the cost the caps check is the higher limit.
const assert = require('assert');
const fs = require('fs'), path = require('path');
const slot = require('../functions/kalshiSlotLib');
const OI = slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE');
const gates = {};
gates.LM1 = () => {
  assert.deepStrictEqual(Object.assign({}, slot.SLOT_LIMIT_SLIP), { OICORE: 0.01 }, 'only OICORE, 1c');
  assert.ok(Object.isFrozen(slot.SLOT_LIMIT_SLIP) && slot.SLOT_LIMIT_SLIP_MAX === 0.02, 'frozen, and never more than 2c for any strategy');
  assert.strictEqual(slot.slotLimitFor(OI, 0.18), 0.19, '18c touch: 19c limit');
  assert.strictEqual(slot.slotLimitFor(OI, 0.06), 0.07, '6c touch: 7c limit');
  assert.strictEqual(slot.slotLimitFor(OI, 0.50), 0.50, 'at the 50c top of the band: no slip past the band');
  assert.strictEqual(slot.slotLimitFor(OI, 0.495), 0.5, 'never past priceMax');
  assert.strictEqual(slot.slotLimitFor(Object.assign({}, OI, { id: 'OTHERX' }), 0.18), 0.18, 'any other strategy: the touch, unchanged');
};
gates.LM2 = () => {
  // The gate costs the order at the higher limit, so every cap sees the worst price it can pay.
  const input = (limit) => ({ strategyId: 'OICORE', ticker: 'KXBTC15M-26NOV201200-00', side: 'no', limit, step: 1, depthAtTouch: 1000, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
    lockTxn: true, lock: null, position: 0, sizingBase: 800, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: Date.parse('2026-11-20T16:57:30Z'), oiRise: 90000 });
  const a = slot.slotOrderCheck(input(0.18)), b = slot.slotOrderCheck(input(0.19));
  assert.ok(a.allowed && b.allowed && b.cost > a.cost, 'the 19c limit costs more than 18c in the caps: ' + a.cost + ' vs ' + b.cost);
};
gates.LM3 = () => {
  // The engine: the band test is on the quoted price, the limit goes into the gate and into Kalshi's body, and a NO buy moves the YES price the other way.
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/const limitSide = slotLib\.slotLimitFor\(s, sidePrice\);/.test(src), 'the engine asks the library for the limit');
  assert.ok(/const touch = side === "yes" \? limitSide : Math\.round\(\(1 - limitSide\) \* 100\) \/ 100;/.test(src), 'a NO limit 1c higher is a YES price 1c lower in the order body');
  assert.ok(/check\(\{ strategyId: s\.id, ticker, side, limit: limitSide,/.test(src), 'the gate sees the higher limit');
  assert.ok(src.indexOf('outside the band') < src.indexOf('const limitSide'), 'the band test is on the quoted price, before the slip');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
