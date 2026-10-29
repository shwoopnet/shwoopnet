'use strict';
// Gates for the second slot, PHASE A (functions/kalshiSlotLib.js, docs/SECOND_SLOT_DESIGN.md). Each states the consequence, not the mechanism.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const libSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiSlotLib.js'), 'utf8');
const NOW = Date.parse('2026-11-03T15:00:00Z');
const W = slot._testOnly.slotOrderCheckWith, AS = slot._testOnly.activeSlotStrategiesWith;
const T = 'KXBTC15M-26NOV031015-15';
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');

// A strategy used only by these tests. It is NOT in the registry.
const GOOD = () => ({
  id: 'TESTA', readme: 'kalshi-scalper/README.md#SLOT-TESTA', series: ['KXBTC15M', 'KXGOLD15M'],
  entry: { sideRule: 'favourite', priceMin: 0.6, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 },
  exit: { stopBid: 0.4, targetBid: 0.95, mustExitLeftSec: 90 },
  contractsPerOrder: 4, scaleIn: { maxSteps: 2, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true },
  killRules: { maxConsecutiveLosses: 3, minNet: { afterFills: 20, net: -3 } }, forwardReadDate: '2026-12-01', reviewedAt: '2026-10-29',
});
const ON = (extra) => ({ enabled: true, registry: [GOOD()], ...(extra || {}) });
const slotOrder = (o) => Object.assign({ strategy: 'SLOT', slotId: 'TESTA', ticker: T, series: 'KXBTC15M', side: 'yes', step: 1, count: 4, fillCount: '4', maxCost: 3.0, status: 'filled', settled: false, ts: NOW - 120000 }, o);
const l1Order = (o) => Object.assign({ strategy: 'L1', ticker: T, series: 'KXBTC15M', side: 'yes', count: 1, fillCount: '1', maxCost: 0.95, addonCost: 0, status: 'filled', settled: false, ts: NOW - 60000 }, o);
const input = (o) => Object.assign({
  strategyId: 'TESTA', ticker: T, side: 'yes', limit: 0.75, step: 1, depthAtTouch: 100, slotOrders: [], l1Orders: [], slotOrdersComplete: true,
  lockTxn: true, lock: null, position: 0, sizingBase: 500, windowCapFraction: 0.055, secondsLeft: 500, now: NOW,
}, o || {});
const gates = {};

gates['the module is inert: empty registry, switch off, no order is ever allowed, and nothing imports it'] = () => {
  assert.strictEqual(slot.SLOT_ENABLED, false);
  assert.deepStrictEqual(slot.SLOT_STRATEGIES, []);
  assert.ok(Object.isFrozen(slot.SLOT_STRATEGIES));
  assert.strictEqual(slot.slotOrderCheck(input()).allowed, false);
  assert.deepStrictEqual(slot.activeSlotStrategies(), []);
  for (const f of fs.readdirSync(path.join(root, 'functions')).filter((x) => x.endsWith('.js') && x !== 'kalshiSlotLib.js')) {
    assert.ok(!/kalshiSlotLib/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')), f + ' must not import the slot library in phase A');
  }
  assert.ok(!/kalshiSlotLib/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')));
  const c = code(libSrc);
  assert.ok(!/fetch|firebase|getFirestore|liveRequest|\.collection\(|crypto|Date\.now|new Date\(/.test(c), 'the library must have no network, store, clock or signing code');
  assert.deepStrictEqual([...c.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), ['"./kalshiSignalLib"']);
};
gates['a switch on alone does nothing: the switch needs a valid registered strategy, and a stored value cannot add one'] = () => {
  assert.deepStrictEqual(AS({ enabled: true }), []);
  assert.strictEqual(W({ enabled: true }, input()).allowed, false);
  assert.strictEqual(W({ enabled: false, registry: [GOOD()] }, input()).allowed, false);
  assert.ok(!/data\(\)|\.get\(|localStorage|request\.data/.test(code(libSrc)));
};
gates['one invalid entry refuses the whole registry, so a typo cannot drop one guard and keep the rest'] = () => {
  const bad = GOOD(); bad.id = 'TESTB'; bad.contractsPerOrder = 11;
  assert.deepStrictEqual(AS({ enabled: true, registry: [GOOD(), bad] }), []);
  assert.deepStrictEqual(AS({ enabled: true, registry: [GOOD(), GOOD()] }), [], 'a repeated id');
  assert.strictEqual(AS({ enabled: true, registry: [GOOD()] }).length, 1);
};
gates['validation rejects anything out of bounds'] = () => {
  assert.ok(slot.validateSlotStrategy(GOOD()).ok, slot.validateSlotStrategy(GOOD()).errors.join('; '));
  const mut = (f) => { const s = GOOD(); f(s); return slot.validateSlotStrategy(s); };
  const rejects = [
    (s) => { s.series = ['KXXRP15M']; }, (s) => { s.series = []; }, (s) => { s.contractsPerOrder = 0; }, (s) => { s.contractsPerOrder = 11; }, (s) => { s.contractsPerOrder = 2.5; },
    (s) => { s.entry.priceMax = 0.99; }, (s) => { s.entry.priceMin = 0.01; }, (s) => { s.entry.leftMaxSec = 899; }, (s) => { s.entry.leftMinSec = 60; },
    (s) => { s.exit.mustExitLeftSec = 10; }, (s) => { s.exit.mustExitLeftSec = 400; }, (s) => { s.exit.stopBid = 0.7; }, (s) => { s.exit.targetBid = 0.8; },
    (s) => { s.scaleIn.maxSteps = 4; }, (s) => { s.scaleIn.sameSideOnly = false; }, (s) => { s.scaleIn.minGapSec = 5; }, (s) => { s.scaleIn.maxSteps = 3; s.contractsPerOrder = 5; },
    (s) => { s.killRules.maxConsecutiveLosses = 6; }, (s) => { s.killRules.minNet.net = 1; }, (s) => { s.killRules.minNet.net = -50; }, (s) => { delete s.killRules; },
    (s) => { s.id = 'bad-id'; }, (s) => { s.readme = 'notes.txt'; }, (s) => { s.forwardReadDate = 'soon'; }, (s) => { s.extra = 1; }, (s) => { delete s.reviewedAt; },
  ];
  rejects.forEach((f, i) => assert.strictEqual(mut(f).ok, false, 'mutation ' + i + ' should be rejected'));
};
gates['an order on the opposite side of an L1 or slot position is blocked; the same side is allowed'] = () => {
  const d = (o) => slot.directionDecision(Object.assign({ ticker: T, side: 'yes', l1Orders: [], slotOrders: [], lock: null, position: 0 }, o));
  assert.strictEqual(d({ l1Orders: [l1Order()] }).allow, true, 'same side as L1');
  assert.strictEqual(d({ side: 'no', l1Orders: [l1Order()] }).allow, false, 'slot NO against an L1 YES is a hedge');
  assert.strictEqual(d({ side: 'yes', slotOrders: [slotOrder({ side: 'no' })] }).allow, false, 'L1 YES against a slot NO is a hedge');
  assert.strictEqual(d({ side: 'no', slotOrders: [slotOrder({ status: 'sending', fillCount: '0' })] }).allow, false, 'an order in flight holds its side');
  assert.strictEqual(d({ side: 'no', slotOrders: [slotOrder({ status: 'unknown' })] }).allow, false, 'an unknown answer holds its side');
  assert.strictEqual(d({ side: 'no', l1Orders: [l1Order({ status: 'no fill' })] }).allow, true, 'an order that did not fill holds nothing');
  assert.strictEqual(d({ side: 'no', l1Orders: [l1Order({ settled: true })] }).allow, true);
  assert.strictEqual(d({ l1Orders: [l1Order(), l1Order({ side: 'no' })] }).allow, false, 'contradictory books refuse everything');
};
gates['two instances racing: the direction lock written first decides, and an unreadable lock, order list or position refuses'] = () => {
  const d = (o) => slot.directionDecision(Object.assign({ ticker: T, side: 'yes', l1Orders: [], slotOrders: [], lock: null, position: 0 }, o));
  assert.strictEqual(d({ lock: { side: 'no' } }).allow, false);
  assert.strictEqual(d({ lock: { side: 'yes' } }).allow, true);
  assert.strictEqual(d({ lock: { side: 'maybe' } }).allow, false);
  assert.strictEqual(d({ l1Orders: null }).allow, false);
  assert.strictEqual(d({ position: null }).allow, false);
  assert.strictEqual(d({ position: -3 }).allow, false, 'the account holds NO (a hand trade), a YES buy would hedge it');
  assert.strictEqual(d({ side: 'no', position: 3 }).allow, false);
  assert.strictEqual(d({ side: 'no', position: -3 }).allow, true);
  assert.strictEqual(d({}).needsLock, true);
  assert.strictEqual(d({ lock: { side: 'yes' } }).needsLock, false);
};
gates['the slot dollars at risk and its settled pnl come back in the shape botRisk returns, so the shared 12% stop can add them'] = () => {
  const orders = [
    slotOrder({ settled: true, result: 'yes', settledPnl: 1.2, ts: NOW - 3600000 }),
    slotOrder({ ticker: 'KXBTC15M-26NOV030945-45', settled: true, result: 'no', settledPnl: -3.0, ts: NOW - 7200000, step: 1 }),
    slotOrder({ ticker: 'KXBTC15M-26NOV022000-00', settled: true, result: 'yes', settledPnl: 9, ts: NOW - 30 * 3600000 }),     // older than 24 hours
    slotOrder({ ts: NOW - 60000, maxCost: 2.0, count: 4, fillCount: '4', exitCount: 2 }),                                      // open, half sold: half of $2 still at risk
    slotOrder({ settled: true, result: 'hand', settledPnl: -50, ts: NOW - 1000 }),                                              // closed by hand: not the slot's result
    slotOrder({ ticker: 'KXETH15M-26NOV031015-15', status: 'sending', fillCount: '0', maxCost: 1.5, ts: NOW - 5000 }),          // in flight: counted in full
  ];
  const day = slot.slotRiskForBotRisk(orders, NOW - 24 * 3600000);
  assert.ok(Math.abs(day.net - (1.2 - 3.0)) < 1e-9);
  assert.ok(Math.abs(day.openCost - (1.0 + 1.5)) < 1e-9);
  assert.ok(Math.abs(day.worst - (day.net - day.openCost)) < 1e-9);
  assert.deepStrictEqual(Object.keys(day).sort(), ['addonAtRisk', 'net', 'openCost', 'trades', 'worst']);
  const life = slot.slotRiskContract(orders, NOW).lifetime;
  assert.ok(Math.abs(life.net - (1.2 - 3.0 + 9)) < 1e-9);
  const rc = slot.slotRiskContract(orders, NOW);
  assert.ok(Math.abs(rc.openTotal - 2.5) < 1e-9);
  assert.ok(Math.abs(rc.openByWindow['26NOV031015'] - 2.5) < 1e-9);
  assert.strictEqual(rc.openContractsByTicker[T], 2);
  assert.ok(Math.abs(slot.slotWindowSpent(orders, T) - (2.0 + 3.0 + 3.0 + 1.5)) < 1e-9, 'window spend is gross, like runL1Tick windowUsed');
};
gates['slot and L1 share one window limit: L1 spend in a window shrinks what the slot may buy'] = () => {
  const r0 = W(ON(), input({ limit: 0.75, depthAtTouch: 100 }));
  assert.strictEqual(r0.allowed, true, r0.reasons.join());
  assert.strictEqual(r0.count, 4);
  assert.strictEqual(r0.cid, 'S-TESTA-' + T + '-1');
  // base 500 * 5.5% = 27.5 window room; L1 already used 26.5 in this window, so only about one contract of $0.79 fits
  const r1 = W(ON(), input({ l1Orders: [l1Order({ maxCost: 26.5 })] }));
  assert.strictEqual(r1.allowed, true); assert.strictEqual(r1.count, 1);
  const r2 = W(ON(), input({ l1Orders: [l1Order({ maxCost: 27.4 })] }));
  assert.strictEqual(r2.allowed, false, 'no whole contract fits the shared window');
  const other = W(ON(), input({ l1Orders: [l1Order({ maxCost: 27.4, ticker: 'KXBTC15M-26NOV031030-30' })] }));
  assert.strictEqual(other.allowed, true, 'another window is not affected');
  assert.strictEqual(W(ON(), input({ windowCapFraction: 0.2 })).allowed, false, 'a window fraction above L1\'s own is refused');
};
gates['hard caps hold: contracts per order, open per market, depth share, dollars per order, window and total'] = () => {
  const big = Object.assign(GOOD(), { contractsPerOrder: 10, scaleIn: { maxSteps: 1, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true } });
  const F = { enabled: true, registry: [big] };
  assert.strictEqual(W(F, input({ limit: 0.62, wanted: 50, depthAtTouch: 1000, sizingBase: 5000 })).count, 9, 'cut by the $6 per-order cap: 9 contracts at about $0.65');
  assert.strictEqual(W(F, input({ limit: 0.62, depthAtTouch: 20, sizingBase: 5000 })).count, 5, 'depth share 25% of 20');
  assert.strictEqual(W(F, input({ limit: 0.62, depthAtTouch: 3, sizingBase: 5000 })).allowed, false, '25% of 3 is under one contract');
  assert.strictEqual(W(F, input({ depthAtTouch: null })).allowed, false, 'unknown depth refuses');
  const held = [slotOrder({ count: 6, fillCount: '6', maxCost: 4.0, step: 1 })];
  assert.strictEqual(W(F, input({ limit: 0.62, depthAtTouch: 1000, sizingBase: 5000, slotOrders: held, step: 1 })).allowed, false, 'step 1 already attempted');
  const two = Object.assign(GOOD(), { contractsPerOrder: 5 });
  const r = W({ enabled: true, registry: [two] }, input({ step: 2, limit: 0.62, depthAtTouch: 1000, sizingBase: 5000, slotOrders: [slotOrder({ count: 6, fillCount: '6', maxCost: 3.0 })] }));
  assert.strictEqual(r.allowed, true); assert.strictEqual(r.count, 4, 'open per market is 10: six held leaves four');
  const tot = [slotOrder({ ticker: 'KXETH15M-26NOV031030-30', series: 'KXETH15M', maxCost: 11.5, count: 1, fillCount: '1', side: 'yes' })];
  assert.strictEqual(W(ON(), input({ slotOrders: tot, sizingBase: 5000 })).allowed, false, 'total open cap $12 leaves $0.50, under one contract at 75c');
};
gates['the slot has its own daily and lifetime loss caps on top of the shared stop'] = () => {
  // A list of settled pnls in time order, each on its own market, ending `endAgo` ms ago. Wins are interleaved so the consecutive-loss kill rule is not what stops the order.
  const seq = (pnls, endAgo) => pnls.map((p, k) => slotOrder({ ticker: 'KXETH15M-26NOV02' + (1000 + k) + '-15', settled: true, result: p > 0 ? 'yes' : 'no', settledPnl: p, ts: NOW - endAgo - (pnls.length - k) * 1000 }));
  const wide = Object.assign(GOOD(), { killRules: { maxConsecutiveLosses: 5, minNet: { afterFills: 100, net: -15 } } });
  const F = { enabled: true, registry: [wide] };
  assert.strictEqual(W(F, input({ slotOrders: seq([-3, 0.1, -3], 3600000) })).allowed, false, 'daily: settled losses reach the $5 cap');
  assert.strictEqual(W(F, input({ slotOrders: seq([-1, 0.1, -1], 3600000) })).allowed, true);
  assert.strictEqual(W(F, input({ slotOrders: [slotOrder({ ticker: 'KXETH15M-26NOV031030-30', maxCost: 5.5, count: 8, fillCount: '8' })] })).allowed, false, 'daily: an open order counts as lost');
  assert.strictEqual(W(F, input({ slotOrders: seq([-4, 0.1, -4, 0.1, -4, 0.1, -4, 0.1], 5 * 86400000) })).allowed, false, 'lifetime cap holds when the daily window is clean');
  assert.strictEqual(W(F, input({ slotOrders: [], slotOrdersComplete: false })).allowed, false, 'a partial read cannot prove the lifetime figure');
};
gates['kill rules fail closed and only a reviewed edit (a later reviewedAt) re-arms'] = () => {
  const S = GOOD();
  const loss = (k) => slotOrder({ ticker: 'KXBTC15M-26NOV02' + (1000 + k) + '-15', settled: true, result: 'no', settledPnl: -0.8, ts: NOW - 100000 + k });
  const win = (k) => slotOrder({ ticker: 'KXBTC15M-26NOV02' + (1000 + k) + '-15', settled: true, result: 'yes', settledPnl: 0.2, ts: NOW - 100000 + k });
  assert.strictEqual(slot.killCheck(S, [loss(1), loss(2)], null).killed, false);
  assert.strictEqual(slot.killCheck(S, [loss(1), loss(2), loss(3)], null).killed, true, 'three in a row');
  assert.strictEqual(slot.killCheck(S, [loss(1), loss(2), win(3), loss(4), loss(5)], null).killed, false, 'a win resets the streak');
  const many = Array.from({ length: 20 }, (_, k) => (k % 2 ? win(k) : loss(k)));     // net -6 after 20 fills (10 x -0.8, 10 x +0.2)
  assert.strictEqual(slot.killCheck(S, many, null).killed, true, 'net below -3 after 20 fills');
  assert.strictEqual(slot.killCheck(S, [], { killedAt: Date.parse('2026-10-30T00:00:00Z') }).killed, true, 'a latch newer than reviewedAt blocks');
  assert.strictEqual(slot.killCheck(S, [], { killedAt: Date.parse('2026-10-28T00:00:00Z') }).killed, false, 'reviewedAt after the latch re-arms it');
  assert.strictEqual(slot.killCheck(S, [], {}).killed, true, 'a latch that cannot be read blocks');
  assert.strictEqual(slot.killCheck(S, [], 'x').killed, true);
};
gates['client order ids are deterministic per strategy, market and step, and never collide with L1, exit or Flatten ids'] = () => {
  assert.strictEqual(slot.slotClientOrderId('TESTA', T, 2), slot.slotClientOrderId('TESTA', T, 2));
  assert.notStrictEqual(slot.slotClientOrderId('TESTA', T, 1), slot.slotClientOrderId('TESTA', T, 2));
  assert.notStrictEqual(slot.slotClientOrderId('TESTA', T, 1), slot.slotClientOrderId('TESTB', T, 1));
  const id = slot.slotClientOrderId('TESTA', T, 1);
  assert.ok(id.length <= 64);
  assert.ok(!id.startsWith('L1-') && !id.startsWith('X-') && !id.startsWith('FLAT-'));
  const x = slot.slotExitClientOrderId(id, 0);
  assert.ok(x.startsWith('SX-') && !x.startsWith('X-'));
  assert.notStrictEqual(slot.slotExitClientOrderId(id, 0), slot.slotExitClientOrderId(id, 1));
  assert.throws(() => slot.slotClientOrderId('bad', T, 1)); assert.throws(() => slot.slotClientOrderId('TESTA', T, 4)); assert.throws(() => slot.slotClientOrderId('TESTA', 'x', 1));
  assert.throws(() => slot.slotExitClientOrderId('L1-' + T, 0));
};
gates['a slot close sells only its own contracts, never more than the account holds, never opens the opposite position'] = () => {
  const o = slotOrder({ count: 5, fillCount: '5', exitCount: 1 });
  assert.strictEqual(slot.slotSellCount({ order: o, position: 9, haveClaim: true }), 4, 'own unsold, not the whole position (L1 holds the rest)');
  assert.strictEqual(slot.slotSellCount({ order: o, position: 2, haveClaim: true }), 2, 'capped at what the account holds');
  assert.strictEqual(slot.slotSellCount({ order: o, position: 0, haveClaim: true }), 0);
  assert.strictEqual(slot.slotSellCount({ order: o, position: -7, haveClaim: true }), 0, 'a YES order never sells against a NO position');
  assert.strictEqual(slot.slotSellCount({ order: { ...o, side: 'no' }, position: -7, haveClaim: true }), 4);
  assert.strictEqual(slot.slotSellCount({ order: { ...o, side: 'no' }, position: 7, haveClaim: true }), 0);
  assert.strictEqual(slot.slotSellCount({ order: o, position: 9, haveClaim: false }), 0, 'no lease on the market, no sale');
  assert.strictEqual(slot.slotSellCount({ order: o, position: null, haveClaim: true }), 0, 'unreadable position');
  assert.strictEqual(slot.slotSellCount({ order: { ...o, strategy: 'L1' }, position: 9, haveClaim: true }), 0, 'an L1 order is never a slot sale');
};
gates['the mirrored constants and the settlement rule stay equal to the live ones'] = () => {
  assert.strictEqual(slot.L1_WINDOW_CAP_FRACTION_MIRROR, live.L1_WINDOW_CAP_FRACTION);
  for (const t of [T, 'KXGOLD15M-26NOV031015-00', 'weird']) assert.strictEqual(slot.windowKey(t), live.windowKey(t));
  for (const o of [{ side: 'yes', count: 4, fillCount: '4', maxCost: 3.1 }, { side: 'no', count: 4, fillCount: '3', maxCost: 3.1, exitCount: 1, exitProceeds: 0.7 }])
    for (const r of ['yes', 'no']) assert.deepStrictEqual(slot.slotSettledFields(o, r), live.settledFields(o, r));
  assert.ok(slot.SLOT_SERIES_ALLOWED.every((s) => live.L1_SERIES.includes(s)));
  assert.deepStrictEqual(slot.SLOT_SERIES_ALLOWED, ['KXBTC15M', 'KXETH15M', 'KXGOLD15M']);
};
gates['the L1 exit watch and settle sweep still read only L1 orders, and the live library has not been edited to know about the slot'] = () => {
  const live_src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(/t\.strategy === "L1" && t\.settled !== true && Number\(t\.fillCount\) > 0\s*\n?\s*&& Number\.isFinite\(Number\(t\.maxCost\)\)/.test(live_src));
  assert.ok(!/SLOT_|kalshiSlot/.test(live_src), 'phase A does not touch runL1Tick, botRisk, the exit watch or Flatten');
  assert.ok(!/kalshiSlotOrders/.test(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8')));
  assert.ok(!/kalshiSlot/.test(fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8')), 'no rule opens the new collection yet; with no rule it is closed to every client');
};

gates['the named entry points: same side may enter, the opposite is blocked both ways, caps only cut, losses stop exactly at the limit, kills stay tripped'] = () => {
  const wk = slot.windowKey(T), base = { strategy: GOOD(), ticker: T, windowKey: wk, side: 'yes', contracts: 4, step: 1, l1Orders: [], slotOrders: [], restingSize: 100, spentToday: 0, spentTotal: 0, sizingBase: 500, now: NOW };
  assert.strictEqual(slot.slotMayEnter(base).ok, false, 'production: switch off, nothing may enter');
  const may = (o) => slot.slotMayEnterWith({ enabled: true }, Object.assign({}, base, o || {}));
  assert.deepStrictEqual([may().ok, may().contracts], [true, 4]);
  assert.strictEqual(may({ l1Orders: [l1Order()] }).ok, true, 'same side as L1 in the same market and window is not a hedge');
  assert.strictEqual(may({ l1Orders: [l1Order({ side: 'no' })] }).ok, false, 'a slot order against an L1 position would hedge');
  assert.strictEqual(may({ slotOrders: [slotOrder({ side: 'no' })] }).ok, false);
  assert.strictEqual(slot.slotSideRule({ side: 'yes', ticker: T, windowKey: wk, l1Orders: [], slotOrders: [slotOrder({ side: 'no' })] }).ok, false);
  assert.strictEqual(slot.slotSideRule({ side: 'no', ticker: T, windowKey: wk, l1Orders: [l1Order()], slotOrders: [] }).ok, false, 'an L1 order against a slot position is blocked too');
  assert.strictEqual(slot.slotSideRule({ side: 'yes', ticker: T, windowKey: wk, l1Orders: [l1Order()], slotOrders: [slotOrder()] }).ok, true);
  for (const bad of [{ l1Orders: null }, { slotOrders: undefined }, { side: 'up' }, { windowKey: 'X' }, { restingSize: undefined }, { now: NaN }])
    assert.strictEqual(may(bad).ok, false, 'malformed input blocks: ' + JSON.stringify(bad));
  const cut = may({ contracts: 10, restingSize: 12 });
  assert.ok(cut.ok && cut.contracts <= 3 && cut.contracts <= 10, 'depth share cuts, never raises');
  assert.ok(may({ contracts: 2 }).contracts <= 2, 'never more than asked');
  assert.strictEqual(may({ spentToday: slot.SLOT_DAILY_LOSS_CAP - 0.01 }).ok, true);
  assert.strictEqual(may({ spentToday: 5 }).ok, false);
  assert.strictEqual(may({ spentToday: 0.1 + 0.2 + 4.7 }).ok, false, 'a float sum that lands on the cap is blocked');
  assert.strictEqual(may({ spentTotal: 15 }).ok, false);
  const r = slot.slotRiskForL1({ slotOrders: [slotOrder({ maxCost: 2 }), slotOrder({ ticker: 'KXBTC15M-26NOV031030-30', maxCost: 1.5 }), slotOrder({ settled: true, settledPnl: -1.25, ts: NOW - 1000 })], windowKey: wk, now: NOW });
  assert.strictEqual(r.windowAtRisk, 2, 'only open slot orders in that window are at risk');
  assert.strictEqual(r.settledPnl24h, -1.25);
  const losing = (n) => Array.from({ length: n }, (_, i) => slotOrder({ settled: true, settledPnl: -1, fillCount: '4', ts: NOW - 100000 + i, step: 1 }));
  assert.strictEqual(slot.slotKillStatus(losing(3), GOOD()).killed, true, 'three losses in a row trip the kill');
  assert.strictEqual(slot.slotKillStatus(losing(2), GOOD()).killed, false);
  const rec = slot.slotOrderRecord({ strategyId: 'TESTA', ticker: T, side: 'yes', step: 1, count: 4, limit: 0.75, maxCost: 3.1, ts: NOW });
  assert.strictEqual(rec.id, 'S-TESTA-' + T + '-1');
  assert.strictEqual(rec.strategy, 'SLOT');
  assert.strictEqual(slot.validateStrategy(GOOD()).ok, true);
  assert.strictEqual(slot.validateStrategy(Object.assign(GOOD(), { contractsPerOrder: 11 })).ok, false);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
