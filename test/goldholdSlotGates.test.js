// GOLDHOLD (Nov 9, 2026, the owner: "cost GOLDHOLD first"): gold L1's own entry held to settlement, 1 contract, in the second slot.
// Consequence: the one favourite-and-hold strategy is capped to about $1 an order, can never sell or hedge L1's contracts, and latches itself off after 3 straight losses or -$1.50 after 30 fills.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib.js');
const live = require('../functions/kalshiLiveLib.js');
const gh = slot.SLOT_STRATEGIES.find((s) => s.id === 'GOLDHOLD');
const gates = {};

gates.GH1 = () => {
  assert.ok(gh, 'GOLDHOLD is registered');
  assert.strictEqual(slot.validateSlotStrategy(gh).ok, true, JSON.stringify(slot.validateSlotStrategy(gh)));
  assert.deepStrictEqual([...gh.series], ['KXGOLD15M'], 'gold only');
  assert.deepStrictEqual({ ...gh.entry }, { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, "L1's own band and look");
  assert.ok(live.L1_WINDOW_MS[0] >= gh.entry.leftMinSec * 1000 && live.L1_WINDOW_MS[1] <= gh.entry.leftMaxSec * 1000 + 1, "the entry window covers L1's 6 minute look: " + live.L1_WINDOW_MS);
  assert.strictEqual(gh.contractsPerOrder, 1, 'one contract');
  assert.strictEqual(gh.scaleIn.maxSteps, 1, 'never more than one contract open in a market');
  assert.deepStrictEqual({ ...gh.exit }, { holdToSettle: true }, 'held to settlement: no stop, no target, no sale');
};
gates.GH2 = () => {
  assert.ok(slot.SLOT_HOLD_ALLOWED.includes('GOLDHOLD'), 'it is on the reviewed list that may hold to settlement');
  assert.deepStrictEqual({ maxConsecutiveLosses: gh.killRules.maxConsecutiveLosses, afterFills: gh.killRules.minNet.afterFills, net: gh.killRules.minNet.net }, { maxConsecutiveLosses: 3, afterFills: 30, net: -1.5 }, 'latch off at 3 straight losses or net under -$1.50 after 30 fills');
  assert.ok(gh.reviewedAt <= slot.SLOT_LAST_REVIEWED_ON);
  // The money at stake: one contract at the top of the band plus a 1c fee, against the slot caps at the $979.25 base.
  const caps = slot.slotCaps(979.25);
  assert.ok(0.98 <= caps.perOrder && caps.perOrder < 10, 'one order is about $1 and far inside the per order cap ' + caps.perOrder);
  assert.ok(caps.daily >= 2 * 0.98, 'the daily cap still allows its trades, and ends the day after a few losses: ' + caps.daily);
  assert.strictEqual(slot.SLOT_MAX_CONTRACTS_PER_ORDER >= gh.contractsPerOrder, true);
};
gates.GH3 = () => {
  const readme = fs.readFileSync(path.join(__dirname, '..', 'kalshi-scalper', 'README.md'), 'utf8');
  const i = readme.indexOf('## SLOT-GOLDHOLD');
  assert.ok(i > 0 && gh.readme === 'kalshi-scalper/README.md#SLOT-GOLDHOLD', 'its pre-registration is written before the first order');
  const sec = readme.slice(i, i + 4000);
  assert.ok(/favourite-and-hold/i.test(sec) && /lifting that ban/.test(sec), 'the registration says plainly it is favourite-and-hold and that merging lifts the owner ban');
  assert.ok(/3 straight losses/.test(sec) && /-\$1\.50 after 30 fills/.test(sec), 'the kill rules are registered');
};
gates.GH4 = () => {
  // Another strategy cannot copy it: only listed ids may hold, and the series list still comes from the allowed set.
  const copy = Object.assign({}, gh, { id: 'COPYGOLD' });
  const v = slot.validateSlotStrategy(copy);
  assert.strictEqual(v.ok, false, 'a copy under another id is refused');
  assert.ok(v.errors.some((e) => /reviewed list that may hold/.test(e)), v.errors.join('; '));
};
gates.GH5 = () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.ok(/var KAL_SLOT_REGISTERED = \['OICORE', 'EVENT830', 'GOLDHOLD'\];/.test(html), 'the Strategies table lists it');
  assert.ok(/GOLDHOLD: \{ name: 'Gold hold', markets: 'Gold'/.test(html), 'it carries its label and market');
  assert.ok(/id="kalRulesSlotGoldHold"/.test(html) && /no early sell/.test(html), 'the Rules text says it holds with no early sell');
  assert.ok(/GOLDHOLD \(1 contract, gold held to settlement\)/.test(html), 'the Start confirmation names it');
};
gates.GH6 = () => {
  // The order gate, as the bot calls it: inside the band and the look it sends exactly one contract; outside either it sends nothing; and it may sit beside L1's order on the SAME side but never against it.
  const NOW = Date.parse('2026-11-10T16:00:00Z'), T = 'KXGOLD15M-26NOV101115-00';
  const base = (o) => Object.assign({ strategyId: 'GOLDHOLD', ticker: T, side: 'yes', limit: 0.92, step: 1, depthAtTouch: 500, slotOrders: [], l1Orders: [], slotOrdersComplete: true, lockTxn: true, lock: null, position: 0, sizingBase: 979.25, windowCapFraction: 0.055, secondsLeft: 360, now: NOW }, o || {});
  const ok = slot.slotOrderCheck(base());
  assert.strictEqual(ok.allowed, true, JSON.stringify(ok.reasons));
  assert.strictEqual(ok.count, 1, 'exactly one contract');
  assert.ok(ok.cost > 0.9 && ok.cost < 1.05, 'about a dollar at risk: ' + ok.cost);
  for (const [why, o] of [['too cheap (0.86)', { limit: 0.86 }], ['above the band (0.98)', { limit: 0.98 }], ['too early (500 s left)', { secondsLeft: 500 }], ['too late (300 s left)', { secondsLeft: 300 }]]) {
    assert.strictEqual(slot.slotOrderCheck(base(o)).allowed, false, why + ': no order');
  }
  const l1 = { strategy: 'L1', ticker: T, series: 'KXGOLD15M', side: 'yes', count: 15, fillCount: '15', maxCost: 14.2, addonCost: 0, status: 'filled', settled: false, ts: NOW - 30000 };
  assert.strictEqual(slot.slotOrderCheck(base({ l1Orders: [l1] })).allowed, true, "beside L1's order on the same side is allowed");
  assert.strictEqual(slot.slotOrderCheck(base({ side: 'no', limit: 0.92, l1Orders: [l1] })).allowed, false, "against L1's order (the opposite side) is refused: that would be a hedge");
};
for (const [n, f] of Object.entries(gates)) { f(); console.log('ok   ' + n); }
