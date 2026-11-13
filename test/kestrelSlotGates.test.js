'use strict';
// AU1 to AU5: KESTREL was a capped probe in the second slot (Nov 10, 2026) and was RETIRED on Nov 11, 2026 (the owner: "existing duplicates should be killed. Why are we running multiple of the same strategies?"):
// it was L1's favourite entry on AUD/USD held to settlement, the same mechanism gold L1 already runs. Each gate states the consequence: it can no longer send an order, AUD/USD is not a slot market and its
// quotes are no longer read for the slot, AUD/USD still never goes back on L1, an order it already holds is still exited and settled (kalshiSlotRunGates RET1 to RET3), and its record and return rule stay written down.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const CLOSE = Date.parse('2026-11-12T15:00:00Z');
const T = 'KXAUDUSD15M-26NOV121000-00';
const NOW = CLOSE - 360000;
const gates = {};
const input = (o) => Object.assign({
  strategyId: 'KESTREL', ticker: T, side: 'yes', limit: 0.92, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 360, now: NOW,
}, o || {});

gates['AU1 KESTREL is out of the registry, the hold list, the allowed and reserved series and the slot ticker shape, so the entry gate refuses it whatever the market does'] = () => {
  assert.ok(!slot.SLOT_STRATEGIES.some((s) => s.id === 'KESTREL') && !slot.SLOT_HOLD_ALLOWED.includes('KESTREL'));
  assert.ok(!slot.SLOT_SERIES_ALLOWED.includes('KXAUDUSD15M') && !Object.prototype.hasOwnProperty.call(slot.SLOT_SERIES_RESERVED, 'KXAUDUSD15M'), 'AUD/USD is not a slot market and reserved to nobody');
  for (const side of ['yes', 'no']) for (const limit of [0.88, 0.92, 0.97]) {
    const r = slot.slotOrderCheck(input({ side, limit }));
    assert.strictEqual(r.allowed, false, 'refused: ' + side + ' ' + limit + ' ' + JSON.stringify(r.reasons));
  }
  const old = { id: 'KESTREL', readme: 'kalshi-scalper/README.md#SLOT-KESTREL', series: ['KXAUDUSD15M'], entry: { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 },
    exit: { holdToSettle: true }, contractsPerOrder: 3, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -15 } }, forwardReadDate: '2026-12-22', reviewedAt: '2026-11-10' };
  assert.ok(!slot.validateSlotStrategy(old).ok, 'the old registry entry no longer validates (series and hold lists)');
};
gates['AU2 the minute function no longer reads AUD/USD quotes for the slot: the rolling quote read is deleted and only a calendar strategy can add a read'] = () => {
  assert.strictEqual(typeof slot.slotRollingSeriesDue, 'undefined', 'slotRollingSeriesDue is gone');
  assert.deepStrictEqual(slot.slotCalendarSeriesDue(slot.SLOT_STRATEGIES, NOW), [], 'no listed release window now, so no extra read (EVENT830 stays)');
  const idx = code(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8'));
  assert.ok(!/slotRollingSeriesDue|KESTREL/.test(idx), 'index.js no longer asks for a rolling read');
  assert.ok(/slotLib\.slotCalendarSeriesDue\(slotLib\.activeSlotStrategies\(\), now\)\.concat\(slotLib\.slotSessionSeriesDue\(slotLib\.activeSlotStrategies\(\), now\)\)\.filter\(/.test(idx), 'the calendar read for EVENT830 is unchanged (SPXOI1 adds only its own weekday-session read, slotSessionSeriesDue, nothing for any other seat)');
};
gates['AU3 AUD/USD never goes back on L1: not on L1_SERIES, still paused, and the L1 size lock refuses any L1 order there'] = () => {
  assert.ok(!live.L1_SERIES.includes('KXAUDUSD15M'), 'not an L1 market');
  assert.ok(live.PAUSED_SERIES.includes('KXAUDUSD15M'), 'still paused for L1');
  assert.strictEqual(live.maxContractsFor('KXAUDUSD15M'), 0, 'the L1 size lock refuses an L1 order for it');
  const liveSrc = code(fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8'));
  assert.ok(!/KESTREL|XRPYES10/.test(liveSrc), 'the L1 library names no slot strategy');
};
gates['AU4 a KESTREL order already open is not stranded: it is sold or settled and still counts in the shared stop (the engine gates RET1 to RET3 prove it end to end)'] = () => {
  const run = fs.readFileSync(path.join(root, 'test', 'kalshiSlotRunGates.test.js'), 'utf8');
  assert.ok(/RET1 an open order of a retired strategy is not stranded/.test(run) && /\['KESTREL', 'KXAUDUSD15M-/.test(run), 'the engine test covers a KESTREL order');
  assert.ok(slot.SLOT_EVER_USED === true && slot.slotWatch() === true, 'the slot keeps watching, so exits and the settle sweep run');
};
gates['AU5 the record and the return rule stay written down in the README'] = () => {
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/^## SLOT-KESTREL/m.test(readme), 'the pre-registration stays');
  const sec = readme.slice(readme.indexOf('## SLOT-KESTREL'), readme.indexOf('## SHADOW-WEEK1'));
  assert.ok(/Retired Nov 11, 2026 \(KESTREL, live probe\)/.test(sec) && /existing duplicates should be killed/.test(sec) && /Return rule/.test(sec), 'a dated retired note with the owner\'s words and the return rule');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name.split(' ')[0] + ' ' + name.slice(name.indexOf(' ') + 1)); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
process.exit(failed ? 1 : 0);
