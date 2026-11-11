'use strict';
// XR1 to XR4: XRPYES10 was a capped probe in the second slot (Nov 10, 2026) and was RETIRED on Nov 11, 2026 (the owner: "existing duplicates should be killed. Why are we running multiple of the same strategies?"):
// it was L1's favourite entry on XRP at a 10 minute look, held to settlement, so it repeated the mechanism gold L1 already runs. Each gate states the consequence: it can no longer send an order, nothing stored
// or re-typed can bring it back without the reviewed lists being edited on purpose, an order it already holds is still exited and settled (kalshiSlotRunGates RET1 to RET3), and its record and return rule stay written down.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const CLOSE = Date.parse('2026-11-12T15:00:00Z');
const T = 'KXXRP15M-26NOV121000-00';
const NOW = CLOSE - 600000;
const gates = {};
const input = (o) => Object.assign({
  strategyId: 'XRPYES10', ticker: T, side: 'yes', limit: 0.92, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 600, now: NOW,
}, o || {});
const OLD = () => ({ id: 'XRPYES10', readme: 'kalshi-scalper/README.md#SLOT-XRPYES10', series: ['KXXRP15M'], entry: { sideRule: 'yes', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 },
  exit: { holdToSettle: true }, contractsPerOrder: 3, scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -15 } }, forwardReadDate: '2026-12-14', reviewedAt: '2026-11-10' });

gates['XR1 XRPYES10 is out of the registry, the hold list, the allowed series and the slot ticker shape, so the entry gate refuses it whatever the market does'] = () => {
  assert.ok(!slot.SLOT_STRATEGIES.some((s) => s.id === 'XRPYES10') && !slot.SLOT_HOLD_ALLOWED.includes('XRPYES10'));
  assert.ok(!slot.SLOT_SERIES_ALLOWED.includes('KXXRP15M'), 'XRP is not a slot market any more');
  for (const side of ['yes', 'no']) for (const limit of [0.88, 0.92, 0.97]) {
    const r = slot.slotOrderCheck(input({ side, limit }));
    assert.strictEqual(r.allowed, false, 'refused: ' + side + ' ' + limit + ' ' + JSON.stringify(r.reasons));
  }
  // The slot's own ticker shape no longer accepts an XRP market, so even a registered copy could not place an order there until that list is edited on purpose.
  assert.strictEqual(slot.slotOrderCheck(input({ strategyId: 'OICORE', side: 'no', limit: 0.2 })).allowed, false, 'OICORE cannot trade XRP either');
  assert.ok(!slot.validateSlotStrategy(OLD()).ok, 'the old registry entry no longer validates (series and hold lists)');
};
gates['XR2 the minute function reads no XRP quote for the slot and the slot never sits against L1 on XRP (still paused for L1)'] = () => {
  assert.deepStrictEqual(slot.slotCalendarSeriesDue(slot.SLOT_STRATEGIES, NOW), [], 'no calendar window now, so no extra read');
  assert.ok(live.PAUSED_SERIES.includes('KXXRP15M'), 'XRP stays paused for L1 in code (a separate decision)');
  const idx = code(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8'));
  assert.ok(!/XRPYES10|KESTREL/.test(idx), 'index.js names no strategy: the registry is the only place');
  const lib = code(fs.readFileSync(path.join(root, 'functions', 'kalshiSlotLib.js'), 'utf8'));
  assert.ok(!/KXXRP15M|XRPYES10/.test(lib), 'the slot library names neither XRP nor XRPYES10 in code');
};
gates['XR3 an XRPYES10 order already open is not stranded: it is sold or settled and still counts in the shared stop (the engine gates RET1 to RET3 prove it end to end)'] = () => {
  const run = fs.readFileSync(path.join(root, 'test', 'kalshiSlotRunGates.test.js'), 'utf8');
  assert.ok(/RET1 an open order of a retired strategy is not stranded/.test(run) && /\['XRPYES10', 'KXXRP15M-/.test(run), 'the engine test covers an XRPYES10 order');
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/const rules = s \? s\.exit : FALLBACK_EXIT;/.test(src), 'an order whose strategy is gone gets the fallback exit');
  assert.ok(slot.SLOT_EVER_USED === true && slot.slotWatch() === true, 'the slot keeps watching, so exits and the settle sweep run');
};
gates['XR4 the record and the return rule stay written down in the README'] = () => {
  const readme = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(/^## SLOT-XRPYES10/m.test(readme), 'the pre-registration stays');
  const sec = readme.slice(readme.indexOf('## SLOT-XRPYES10'), readme.indexOf('## SLOT-KESTREL'));
  assert.ok(/Retired Nov 11, 2026 \(XRPYES10, live probe\)/.test(sec) && /existing duplicates should be killed/.test(sec) && /Return rule/.test(sec), 'a dated retired note with the owner\'s words and the return rule');
  assert.ok(sec.indexOf('deploy-push.sh') < sec.indexOf('deploy-sizing.sh'), 'the deploy order is written');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name.split(' ')[0] + ' ' + name.slice(name.indexOf(' ') + 1)); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
process.exit(failed ? 1 : 0);
