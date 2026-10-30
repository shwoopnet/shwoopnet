'use strict';
// OI1 to OI4: the open interest entry condition and the cheap side rule of the second slot (Oct 30, 2026, the owner's probe of the research session's GEN6 core).
// Consequence: a signal that cannot be read, or is under the line, must send no order; a strategy without the condition is exactly what it was.
const assert = require('assert');
const slot = require('../functions/kalshiSlotLib');
const run = require('../functions/kalshiSlotRunLib');
const strat = (entry) => ({ id: 'OICORE', readme: 'kalshi-scalper/README.md#GEN6', series: ['KXBTC15M'], entry: Object.assign({ sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120 }, entry),
  exit: { stopBid: 0.02, targetBid: 0.99, mustExitLeftSec: 60 }, contractsPerOrder: 5, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 5, minNet: { afterFills: 40, net: -6 } }, forwardReadDate: '2026-11-13', reviewedAt: '2026-10-29' });
const gates = {};
gates.OI1 = () => {
  assert.ok(slot.validateSlotStrategy(strat({ oiRiseMin: 86300 })).ok, 'cheap side with an open interest line is a valid entry');
  assert.ok(slot.validateSlotStrategy(strat({})).ok, 'and so is one without the condition (nothing existing changes)');
  assert.ok(!slot.validateSlotStrategy(strat({ oiRiseMin: 5 })).ok, 'a line under 1000 contracts is refused');
  assert.ok(!slot.validateSlotStrategy(strat({ oiRiseMin: 'x' })).ok);
  assert.ok(!slot.validateSlotStrategy(strat({ sideRule: 'sideways' })).ok);
};
const input = (oiRise) => ({ strategyId: 'OICORE', ticker: 'KXBTC15M-26OCT301200-00', side: 'yes', limit: 0.2, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 528, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: Date.parse('2026-10-30T16:57:30Z'), oiRise });
gates.OI2 = () => {
  const flags = { enabled: true, registry: [strat({ oiRiseMin: 86300 })], everUsed: true };
  const chk = (oi) => slot._testOnly.slotOrderCheckWith(flags, input(oi));
  assert.ok(chk(90000).allowed, 'a rise over the line may trade: ' + JSON.stringify(chk(90000).reasons));
  assert.ok(!chk(86299).allowed, 'under the line sends no order');
  assert.ok(!chk(undefined).allowed && !chk(null).allowed && !chk(NaN).allowed, 'an unreadable rise sends no order');
  const plain = { enabled: true, registry: [strat({})], everUsed: true };
  assert.ok(slot._testOnly.slotOrderCheckWith(plain, input(undefined)).allowed, 'no condition, no requirement');
};
gates.OI3 = () => {
  const f = run._testOnly.oiRiseFromCandles, close = 1793000000;
  const c = (end, oi) => ({ end_period_ts: end, open_interest_fp: String(oi) });
  assert.strictEqual(f([c(close - 360, 1000), c(close - 300, 1), c(close - 180, 88000)], close), 87000, 'the candle ending 180 s before the close minus the one ending 360 s before it');
  assert.strictEqual(f([c(close - 180, 88000)], close), null, 'a missing candle is null, never a guess');
  assert.strictEqual(f([c(close - 360, 1000), { end_period_ts: close - 180 }], close), null, 'a candle without open interest is null');
  assert.strictEqual(f(null, close), null);
  assert.strictEqual(f([], NaN), null);
};
gates.OI4 = () => {
  const fs = require('fs'), path = require('path');
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(/sideRule === "cheap" \? \(yesPrice < noPrice \? "yes" : "no"\)/.test(src), 'cheap means the side with the lower price');
  assert.ok(/oiRiseMin/.test(src) && /oiRise,\s*position/.test(src) && /exchangeIndex[^;]*oiRise,/.test(src), 'the rise is passed to the gate and stored on the order');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
