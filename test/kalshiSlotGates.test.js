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
function walk(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === 'node_modules' || e.name === '.git' || e.name === 'data') continue;
    const f = path.join(dir, e.name);
    if (e.isSymbolicLink()) continue;
    if (e.isDirectory()) out.push(...walk(f)); else out.push(f);
  }
  return out;
}

gates['the module is admitted with exactly one strategy, OICORE, fixed in code, and nothing stored can add or enlarge it; nothing else imports it'] = () => {
  assert.strictEqual(slot.SLOT_ENABLED, true);
  assert.strictEqual(slot.SLOT_EVER_USED, true, 'once admitted, watching is never set back');
  assert.strictEqual(slot.slotActive(), true);
  assert.strictEqual(slot.slotWatch(), true);
  assert.strictEqual(slot.SLOT_LAST_REVIEWED_ON, '2026-10-30');
  assert.ok(Object.isFrozen(slot.SLOT_STRATEGIES));
  assert.strictEqual(slot.SLOT_STRATEGIES.length, 1, 'exactly one strategy is admitted');
  const o = slot.SLOT_STRATEGIES[0];
  assert.ok(Object.isFrozen(o) && Object.isFrozen(o.entry) && Object.isFrozen(o.exit) && Object.isFrozen(o.killRules) && Object.isFrozen(o.killRules.minNet) && Object.isFrozen(o.scaleIn) && Object.isFrozen(o.series), 'every level is frozen');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(o)), {
    id: 'OICORE', readme: 'kalshi-scalper/README.md#SLOT-OICORE', series: ['KXBTC15M'],
    entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRiseMin: 86300 },
    exit: { holdToSettle: true }, contractsPerOrder: 5,
    scaleIn: { maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true },
    killRules: { maxConsecutiveLosses: 18, minNet: { afterFills: 40, net: -6 } },
    forwardReadDate: '2026-11-13', reviewedAt: '2026-10-30',
  });
  const v = slot.validateSlotStrategy(o);
  assert.ok(v.ok, 'the admitted strategy is valid: ' + (v.errors || []).join('; '));
  assert.strictEqual(o.contractsPerOrder, 5);
  assert.ok(o.contractsPerOrder <= slot.SLOT_MAX_CONTRACTS_PER_ORDER, 'never above the per-order ceiling');
  assert.strictEqual(o.exit.holdToSettle, true);
  assert.ok(slot.SLOT_HOLD_ALLOWED.includes(o.id), 'holding to settlement is only for reviewed ids');
  assert.deepStrictEqual([...slot.SLOT_HOLD_ALLOWED], ['OICORE']);
  assert.ok(o.scaleIn.maxSteps * o.contractsPerOrder <= slot.SLOT_MAX_OPEN_CONTRACTS_PER_MARKET, 'all steps together fit the open contracts ceiling');
  assert.ok(o.reviewedAt <= slot.SLOT_LAST_REVIEWED_ON, 'reviewedAt is not after the last reviewed date');
  assert.ok(o.series.every((x) => slot.SLOT_SERIES_ALLOWED.includes(x)));
  assert.deepStrictEqual(slot.activeSlotStrategies().map((x) => x.id), ['OICORE'], 'the production lookup returns exactly the registry entry');
  assert.strictEqual(slot.activeSlotStrategies.length, 0, 'the production lookup takes no flags');
  assert.strictEqual(slot.slotOrderCheck.length, 1);
  // A hand-built or unregistered strategy still cannot enter, whatever it claims.
  assert.strictEqual(slot.slotOrderCheck(input()).allowed, false, 'TESTA is not in the registry');
  for (const f of walk(root).filter((x) => /\.(js|json|yml|yaml|sh|html|md)$/.test(x) && !/[\\/]test[\\/]|[\\/]docs[\\/]|CLAUDE\.md$|kalshiSlotLib\.js$|kalshiSlotRunLib\.js$|kalshiSlotStoreLib\.js$|kalshiLiveLib\.js$|functions[\\/]index\.js$|kalshi-scalper[\\/]README\.md$/.test(x))) {
    const txt = fs.readFileSync(f, 'utf8');
    // The Bot page may READ the slot's orders (the strategy switch, Oct 29, 2026) and nothing else of the slot: no library, no run or store code, no control latch, no direction lock.
    if (/index\.html$/.test(f)) { assert.ok(!/kalshiSlot(Lib|Run|Store|Control)|kalshiLiveDirection/.test(txt) && !/(setDoc|addDoc|updateDoc|deleteDoc|runTransaction)\([^)]*kalshiSlot/.test(txt), 'the page only reads kalshiSlotOrders'); continue; }
    assert.ok(!/kalshiSlot/.test(txt), path.relative(root, f) + ' must not mention the slot library (phase B3: only the slot libraries, functions/kalshiLiveLib.js behind slotOn and functions/index.js behind SLOT_ON may; checked recursively, including functions/, scripts/, workflows and package files)');
  }
  // The one prose exemption: the pre-registration file the strategy's own `readme` field points to. It is Markdown, so it cannot run anything, and it must carry the admitted id.
  const prereg = fs.readFileSync(path.join(root, 'kalshi-scalper', 'README.md'), 'utf8');
  assert.ok(prereg.includes('SLOT-OICORE') && /SLOT_STRATEGIES/.test(prereg), 'the registered readme anchor exists in the pre-registration file');
  const c = code(libSrc);
  assert.ok(!/fetch|firebase|getFirestore|liveRequest|\.collection\(|crypto|Date\.now|new Date\(|process\.env|Math\.random|performance|setTimeout|setInterval|import\(|globalThis|\beval\b|https?:|child_process|\bfs\b/.test(c), 'the library must have no network, store, clock, environment, randomness, timer or signing code');
  assert.deepStrictEqual([...c.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), ['"./kalshiSignalLib"']);
};
gates['a switch on alone does nothing: the switch needs a valid registered strategy, and a stored value cannot add one'] = () => {
  // Admitted state: the production switch is on, so the "switch alone" property is proved through the injected-flags path, which is how the gate always proved it.
  assert.deepStrictEqual(AS({ enabled: true }).map((x) => x.id), ['OICORE'], 'with no registry given the only strategies are the shipped ones');
  assert.deepStrictEqual(AS({ enabled: true, registry: [] }), []);
  assert.deepStrictEqual(AS({ enabled: false, registry: [GOOD()] }), [], 'a registry with the switch off is nothing');
  assert.deepStrictEqual(AS({ enabled: true, registry: slot.SLOT_STRATEGIES }).map((x) => x.id), ['OICORE'], 'the shipped registry passes the same validation');
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
    (s) => { s.killRules.maxConsecutiveLosses = 21; }, (s) => { s.killRules.maxConsecutiveLosses = 0; }, (s) => { s.killRules.minNet.net = 1; }, (s) => { s.killRules.minNet.net = -61; }, (s) => { delete s.killRules; },
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
  assert.strictEqual(d({ side: 'no', l1Orders: [l1Order({ status: 'no fill', fillCount: '0' })] }).allow, true, 'an order that did not fill holds nothing');
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
  assert.ok(Math.abs(day.net - (1.2 - 3.0 - 1.0)) < 1e-9, 'the sold half of the open order is a realised loss of 1.00 (no proceeds), not invisible until settlement');
  assert.ok(Math.abs(day.openCost - (1.0 + 1.5)) < 1e-9);
  assert.ok(Math.abs(day.worst - (day.net - day.openCost)) < 1e-9);
  assert.deepStrictEqual(Object.keys(day).sort(), ['addonAtRisk', 'net', 'openCost', 'trades', 'worst']);
  const life = slot.slotRiskContract(orders, NOW).lifetime;
  assert.ok(Math.abs(life.net - (1.2 - 3.0 + 9 - 1.0)) < 1e-9);
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
  // base 500 * 5.5% = 27.5 window cap; L1 used 25.4 and one gold contract of room (1.05) stays reserved for L1, so only about one contract of $0.79 fits
  const r1 = W(ON(), input({ l1Orders: [l1Order({ maxCost: 25.4 })] }));
  assert.strictEqual(r1.allowed, true); assert.strictEqual(r1.count, 1);
  const r2 = W(ON(), input({ l1Orders: [l1Order({ maxCost: 26.4 })] }));
  assert.strictEqual(r2.allowed, false, 'no whole contract fits the shared window');
  const other = W(ON(), input({ l1Orders: [l1Order({ maxCost: 27.4, ticker: 'KXBTC15M-26NOV031030-30' })] }));
  assert.strictEqual(other.allowed, true, 'another window is not affected');
  assert.strictEqual(W(ON(), input({ windowCapFraction: 0.2 })).allowed, false, 'a window fraction above L1\'s own is refused');
};
gates['hard caps hold: contracts per order, open per market, depth share, dollars per order, window and total'] = () => {
  const big = Object.assign(GOOD(), { contractsPerOrder: 10, scaleIn: { maxSteps: 1, minGapSec: 60, sameSideOnly: true, requirePriorFilled: true } });
  const F = { enabled: true, registry: [big] };
  assert.strictEqual(W(F, input({ limit: 0.62, wanted: 50, depthAtTouch: 1000, sizingBase: 500 })).count, 7, 'cut by the $5 per-order cap (base 500, 1%): 7 contracts at about $0.65');
  assert.strictEqual(W(F, input({ limit: 0.62, depthAtTouch: 20, sizingBase: 500 })).count, 5, 'depth share 25% of 20');
  assert.strictEqual(W(F, input({ limit: 0.62, depthAtTouch: 3, sizingBase: 500 })).allowed, false, '25% of 3 is under one contract');
  assert.strictEqual(W(F, input({ depthAtTouch: null })).allowed, false, 'unknown depth refuses');
  const held = [slotOrder({ count: 6, fillCount: '6', maxCost: 4.0, step: 1 })];
  assert.strictEqual(W(F, input({ limit: 0.62, depthAtTouch: 1000, sizingBase: 500, slotOrders: held, step: 1 })).allowed, false, 'step 1 already attempted');
  const two = Object.assign(GOOD(), { contractsPerOrder: 5 });
  const r = W({ enabled: true, registry: [two] }, input({ step: 2, limit: 0.62, depthAtTouch: 1000, sizingBase: 500, slotOrders: [slotOrder({ count: 6, fillCount: '6', maxCost: 1.0 })] }));
  assert.strictEqual(r.allowed, true); assert.strictEqual(r.count, 4, 'open per market is 10: six held leaves four');
  const tot = [slotOrder({ ticker: 'KXETH15M-26NOV031030-30', series: 'KXETH15M', maxCost: 11.5, count: 1, fillCount: '1', side: 'yes' })];
  assert.strictEqual(W(ON(), input({ slotOrders: tot, sizingBase: 400 })).allowed, false, 'total open cap $12 (base 400) leaves $0.50, under one contract at 75c');
};
gates['the slot has its own daily and lifetime loss caps on top of the shared stop'] = () => {
  // A list of settled pnls in time order, each on its own market, ending `endAgo` ms ago. Wins are interleaved so the consecutive-loss kill rule is not what stops the order.
  const seq = (pnls, endAgo) => pnls.map((p, k) => slotOrder({ ticker: 'KXETH15M-26NOV02' + (1000 + k) + '-15', settled: true, result: p > 0 ? 'yes' : 'no', settledPnl: p, ts: NOW - endAgo - (pnls.length - k) * 1000 }));
  const wide = Object.assign(GOOD(), { killRules: { maxConsecutiveLosses: 5, minNet: { afterFills: 100, net: -60 } } });
  const F = { enabled: true, registry: [wide] };
  assert.strictEqual(W(F, input({ sizingBase: 250, slotOrders: seq([-3, 0.1, -3], 3600000) })).allowed, false, 'daily: settled losses reach the $5 cap');
  assert.strictEqual(W(F, input({ sizingBase: 250, slotOrders: seq([-1, 0.1, -1], 3600000) })).allowed, true);
  assert.strictEqual(W(F, input({ sizingBase: 250, slotOrders: [slotOrder({ ticker: 'KXETH15M-26NOV031030-30', maxCost: 5.5, count: 8, fillCount: '8' })] })).allowed, false, 'daily: an open order counts as lost');
  assert.strictEqual(W(F, input({ sizingBase: 250, slotOrders: seq([-4, 0.1, -4, 0.1, -4, 0.1, -4, 0.1], 5 * 86400000) })).allowed, false, 'lifetime cap holds when the daily window is clean');
  assert.strictEqual(W(F, input({ sizingBase: 250, slotOrders: [], slotOrdersComplete: false })).allowed, false, 'a partial read cannot prove the lifetime figure');
};
gates['caps scale with the sizing base, never pass their ceilings, and an unusable base gives no caps and no order'] = () => {
  const keys = Object.keys(slot.SLOT_CAP_FRACTIONS);
  const a = slot.slotCaps(250), d = slot.slotCaps(500);
  for (const k of keys) assert.ok(Math.abs(d[k] - 2 * a[k]) < 1e-9, k + ' doubles when the base doubles (below its ceiling)');
  assert.deepStrictEqual([a.daily, a.lifetime, a.perOrder], [5, 15, 2.5], 'base 250');
  assert.deepStrictEqual([slot.slotCaps(400).perWindow, slot.slotCaps(400).openTotal], [8, 12], 'base 400');
  for (const b of [1e3, 1e4, 1e6, 1e12, Number.MAX_VALUE]) for (const k of keys) assert.ok(slot.slotCaps(b)[k] <= slot.SLOT_CAP_CEILINGS[k] + 1e-9, k + ' stays under its ceiling at base ' + b);
  for (const k of keys) assert.strictEqual(slot.slotCaps(1e9)[k], slot.SLOT_CAP_CEILINGS[k], k + ' sits at its ceiling for a huge base');
  for (const bad of [0, -500, NaN, Infinity, '500', null, undefined, {}]) {
    for (const k of keys) assert.strictEqual(slot.slotCaps(bad)[k], 0, 'zero ' + k + ' for base ' + String(bad));
    assert.strictEqual(W(ON(), input({ sizingBase: bad })).allowed, false, 'no order for base ' + String(bad));
  }
  assert.strictEqual(W(ON(), input({ sizingBase: 500 })).allowed, true, 'a usable base still trades');
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
  assert.strictEqual(slot.slotSellCount({ order: o, position: 9, haveClaim: true, othersUnsold: 5 }), 4, 'own unsold, not the whole position (L1 holds the rest)');
  assert.strictEqual(slot.slotSellCount({ order: o, position: 2, haveClaim: true, othersUnsold: 0 }), 2, 'capped at what the account holds');
  assert.strictEqual(slot.slotSellCount({ order: o, position: 0, haveClaim: true, othersUnsold: 0 }), 0);
  assert.strictEqual(slot.slotSellCount({ order: o, position: -7, haveClaim: true, othersUnsold: 0 }), 0, 'a YES order never sells against a NO position');
  assert.strictEqual(slot.slotSellCount({ order: { ...o, side: 'no' }, position: -7, haveClaim: true, othersUnsold: 0 }), 4);
  assert.strictEqual(slot.slotSellCount({ order: { ...o, side: 'no' }, position: 7, haveClaim: true, othersUnsold: 0 }), 0);
  assert.strictEqual(slot.slotSellCount({ order: o, position: 9, haveClaim: false, othersUnsold: 0 }), 0, 'no lease on the market, no sale');
  assert.strictEqual(slot.slotSellCount({ order: o, position: null, haveClaim: true, othersUnsold: 0 }), 0, 'unreadable position');
  assert.strictEqual(slot.slotSellCount({ order: { ...o, strategy: 'L1' }, position: 9, haveClaim: true, othersUnsold: 0 }), 0, 'an L1 order is never a slot sale');
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
  // Phase B2 rewrite (docs/SECOND_SLOT_WIRING.md section 7): the live library may now know the slot, but only through the one module and the one gate; the exit watch is still untouched.
  assert.deepStrictEqual([...live_src.matchAll(/require\("(\.\/kalshiSlot[A-Za-z]*)"\)/g)].map((m) => m[1]), ['./kalshiSlotLib'], 'the live library requires only the pure slot library');
  assert.ok(!/SLOT_|kalshiSlotRun/.test(live_src.replace(/\/\/.*$/gm, '')), 'no slot constant and no run library in code');
  const exitBody = live_src.slice(live_src.indexOf('async function runExitWatch'), live_src.indexOf('// ---- Flatten: the owner'));
  // Review round 2: the L1 exit watch now knows the slot in exactly two places, both behind slotOn(args): it subtracts the slot's contracts from the shared account position before selling,
  // and it gives its close lease back. Every other line of it, and the order list it iterates, is unchanged and still L1 only.
  const slotLines = exitBody.replace(/\/\/.*$/gm, '').split('\n').filter((l) => /slot/i.test(l)).map((l) => l.trim());
  assert.ok(slotLines.length > 0 && slotLines.every((l) => /slotOn\(args\)|slotHeld|args\.slot|slot contracts|second slot|the slot|slot's|Slot only/i.test(l)), 'every slot line in the L1 exit watch is a guarded one: ' + slotLines.join(' | '));
  assert.ok(/if \(slotOn\(args\)\) leased\.push/.test(exitBody) && /if \(slotOn\(args\)\) \{\s*\n\s*try \{ slotHeld = await args\.slot\.unsoldOn/.test(exitBody));
  // Phase B3 rewrite (docs/SECOND_SLOT_WIRING.md section 7): the collections now have rules, each admin read and no client write; the latch and the leases still have none. Each stays a gate on a smaller surface.
  const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
  for (const c of ['kalshiSlotOrders', 'kalshiLiveDirection']) assert.ok(new RegExp('match /' + c + '/\\{id\\} \\{\\s*allow read: if isAdmin\\(\\);\\s*allow write: if false;\\s*\\}').test(rules), c + ' is admin read and no client write');
  assert.ok(!/kalshiSlotControl|kalshiLiveClosing/.test(rules.replace(/\/\/.*$/gm, '')), 'the kill latch and the close leases have no rule: closed to every browser');
  assert.ok(!/kalshiSlot/.test(fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8').replace(/\/\/.*$/gm, '').replace(/require\("\.\/kalshiSlot[A-Za-z]*"\)/g, '').replace('document: "kalshiSlotOrders/{id}"', '')), 'index.js names the slot only through the three requires and the one phone alert trigger on the slot orders (Oct 30, 2026); the collection names live in the store library');
};

gates['the named entry points: only one entry gate exists, losses stop at the limit, kills stay tripped'] = () => {
  const wk = slot.windowKey(T);
  assert.strictEqual(slot.slotMayEnter, undefined, 'slotMayEnter is gone: it accepted a caller-built strategy');
  assert.strictEqual(slot.slotSideRule, undefined, 'slotSideRule is gone: it hard-coded position 0 and no lock');
  assert.strictEqual(slot.slotOrderCheckWith, undefined, 'the flag-taking gate is test-only, not a production export');
  assert.strictEqual(slot.slotMayEnterWith, undefined);
  const r = slot.slotRiskForL1({ slotOrders: [slotOrder({ maxCost: 2 }), slotOrder({ ticker: 'KXBTC15M-26NOV031030-30', maxCost: 1.5 }), slotOrder({ settled: true, result: 'no', settledPnl: -1.25, ts: NOW - 1000 })], windowKey: wk, now: NOW });
  assert.strictEqual(r.windowSpent, 5, 'gross spend in that window: 2 open plus 3 for the settled one');
  assert.strictEqual(r.openAtRisk, 2);
  assert.strictEqual(r.windowAtRisk, undefined, 'the ambiguous windowAtRisk name is gone');
  assert.strictEqual(r.settledPnl24h, -1.25);
  const losing = (n) => Array.from({ length: n }, (_, i) => slotOrder({ settled: true, result: 'no', settledPnl: -1, fillCount: '4', ts: NOW - 100000 + i, step: 1 }));
  assert.strictEqual(slot.slotKillStatus(losing(3), GOOD()).killed, true, 'three losses in a row trip the kill');
  assert.strictEqual(slot.slotKillStatus(losing(2), GOOD()).killed, false);
  const rec = slot.slotOrderRecord({ strategyId: 'TESTA', ticker: T, side: 'yes', step: 1, count: 4, limit: 0.75, maxCost: 3.1, ts: NOW });
  assert.strictEqual(rec.id, 'S-TESTA-' + T + '-1');
  assert.strictEqual(rec.strategy, 'SLOT');
  assert.strictEqual(slot.validateStrategy(GOOD()).ok, true);
  assert.strictEqual(slot.validateStrategy(Object.assign(GOOD(), { contractsPerOrder: 11 })).ok, false);
};


// ---- Review round: one gate per blocker or high finding (each fails against the earlier library) ----------------------------------------------------
const WIDE = () => Object.assign(GOOD(), { killRules: { maxConsecutiveLosses: 5, minNet: { afterFills: 100, net: -60 } } });
const WF = { enabled: true, get registry() { return [WIDE()]; } };
const lossAt = (ago, pnl, k) => slotOrder({ ticker: 'KXETH15M-26NOV02' + (1000 + (k || 0)) + '-15', series: 'KXETH15M', settled: true, result: 'no', settledPnl: pnl, ts: NOW - ago });

gates['H1 one order can never overshoot the daily or lifetime loss cap: its own cost must fit in what is left'] = () => {
  assert.ok(slot.SLOT_CAP_FRACTIONS.perOrder <= slot.SLOT_CAP_FRACTIONS.daily, 'a single order may not be bigger than the daily cap, at any base');
  for (const b of [50, 250, 1000, 1e4]) assert.ok(slot.slotCaps(b).perOrder <= slot.slotCaps(b).daily + 1e-9 || slot.slotCaps(b).daily === slot.SLOT_CAP_CEILINGS.daily, 'per order never above daily at base ' + b);
  const prior = (p, ago) => [lossAt(ago, p, 1)];
  assert.strictEqual(W(WF, input({ sizingBase: 250, slotOrders: prior(-4.9, 3600000) })).allowed, false, 'a 4.90 loss leaves 0.10 of daily room: no whole contract');
  const r = W(WF, input({ sizingBase: 250, slotOrders: prior(-4.0, 3600000), limit: 0.75 }));
  assert.ok(r.allowed && r.cost <= 1.0 + 1e-9, 'only what fits in the last $1.00: cost ' + r.cost);
  assert.strictEqual(W(WF, input({ sizingBase: 250, slotOrders: prior(-14.9, 5 * 86400000) })).allowed, false, 'lifetime: 0.10 left');
  const l = W(WF, input({ sizingBase: 250, slotOrders: prior(-14.0, 5 * 86400000) }));
  assert.ok(l.allowed && l.cost <= 1.0 + 1e-9, 'lifetime room is $1.00');
  // worst case afterwards never passes the caps
  const worstAfter = (orders) => slot.slotRiskContract(orders, NOW).day.worst - W(WF, input({ sizingBase: 250, slotOrders: orders })).cost;
  assert.ok(worstAfter(prior(-4.0, 3600000)) >= -slot.slotCaps(250).daily - 1e-9);
};

gates['H16 the per-order ceiling is never above the daily ceiling, so one order cannot break the daily cap alone at any base'] = () => {
  assert.ok(slot.SLOT_CAP_CEILINGS.perOrder <= slot.SLOT_CAP_CEILINGS.daily);
  assert.ok(slot.SLOT_CAP_FRACTIONS.perOrder <= slot.SLOT_CAP_FRACTIONS.daily);
  assert.ok(slot.SLOT_CAP_CEILINGS.daily <= slot.SLOT_CAP_CEILINGS.lifetime && slot.SLOT_CAP_CEILINGS.perWindow <= slot.SLOT_CAP_CEILINGS.openTotal);
};

gates['H2 scale-in is refused after the previous step was stopped out or sold, after any earlier exit, and a failed step is not retried'] = () => {
  const step1 = (o) => slotOrder(Object.assign({ step: 1, ts: NOW - 120000, maxCost: 3 }, o));
  const at2 = (orders) => W(ON(), input({ step: 2, slotOrders: orders, limit: 0.62, depthAtTouch: 1000, sizingBase: 5000 }));
  assert.strictEqual(at2([step1()]).allowed, true, 'a step 1 still fully open may be scaled into');
  assert.strictEqual(at2([step1({ exitCount: 4, exitProceeds: 1.2 })]).allowed, false, 'step 1 stopped out: no averaging down');
  assert.strictEqual(at2([step1({ exitCount: 1, exitProceeds: 0.3 })]).allowed, false, 'any earlier exit on the ticker blocks scaling');
  assert.strictEqual(at2([step1({ settled: true, result: 'exit', settledPnl: -1.8, exitCount: 4 })]).allowed, false);
  const retry = W(ON(), input({ slotOrders: [slotOrder({ status: 'error', fillCount: '0', settled: false })] }));
  assert.strictEqual(retry.allowed, false, 'a failed step is not retried under the same client order id');
  assert.strictEqual(W(ON(), input({ slotOrders: [slotOrder({ status: 'no fill', fillCount: '0' })] })).allowed, false);
};

gates['H3 a slot close sells nothing for settled, hand-closed, errored or unfilled orders, and never L1\'s contracts'] = () => {
  const s = (o, extra) => slot.slotSellCount(Object.assign({ order: slotOrder(o), position: 5, haveClaim: true, othersUnsold: 0 }, extra || {}));
  assert.strictEqual(s({}), 4);
  assert.strictEqual(s({ settled: true, result: 'hand', exitCount: 0 }), 0, 'already closed by hand or Flatten');
  assert.strictEqual(s({ settled: true, result: 'exit', exitCount: 4 }), 0);
  assert.strictEqual(s({ status: 'error' }), 0);
  assert.strictEqual(s({ status: 'no fill', fillCount: '0' }), 0);
  assert.strictEqual(s({ status: 'sending', fillCount: '0' }), 0);
  assert.strictEqual(s({ exitCount: 4 }), 0, 'everything already sold');
  assert.strictEqual(s({}, { othersUnsold: 3 }), 2, 'position 5 minus L1\'s 3 leaves 2, not the raw position');
  assert.strictEqual(s({}, { othersUnsold: 5 }), 0);
  assert.strictEqual(s({}, { othersUnsold: undefined }), 0, 'the other engines\' holding must be known');
  assert.strictEqual(s({}, { othersUnsold: -1 }), 0);
};

gates['H4 the production gate looks the strategy up in the registry; a hand-built strategy, a flags override or a missing lock proof cannot enter'] = () => {
  assert.strictEqual(slot.slotOrderCheck(input({ strategyId: 'EVIL' })).allowed, false);
  assert.strictEqual(slot.slotOrderCheck(Object.assign(input(), { strategy: GOOD(), registry: [GOOD()], enabled: true })).allowed, false, 'extra fields are ignored; the registry is code');
  assert.strictEqual(W({ enabled: true, registry: [GOOD()] }, input({ strategyId: 'EVIL' })).allowed, false, 'an id that is not in the registry');
  assert.strictEqual(W(ON(), input({ lockTxn: undefined })).allowed, false, 'no proof the lock was taken in the order transaction');
  assert.strictEqual(W(ON(), input({ lockTxn: 'yes' })).allowed, false);
  assert.strictEqual(W(ON(), input()).allowed, true, 'and with the proof it passes');
  assert.ok(!/slotMayEnter|slotSideRule/.test(code(libSrc)), 'the weaker wrappers are gone');
};

gates['H5 a realised stop-out is a loss in the shared stop at once, not only after a settle sweep'] = () => {
  const sold = slotOrder({ count: 4, fillCount: '4', maxCost: 3, exitCount: 4, exitProceeds: 2.5, settled: false });
  const r = slot.slotRiskForBotRisk([sold], 0);
  assert.ok(Math.abs(r.net - (-0.5)) < 1e-9 && r.openCost === 0 && Math.abs(r.worst + 0.5) < 1e-9, JSON.stringify(r));
  const f = slot.slotSettledFields(sold, 'exit');
  assert.deepStrictEqual(f, { settled: true, result: 'exit', settledPnl: -0.5 }, 'the exit engine records an early sale with slotSettledFields(order, "exit")');
  assert.deepStrictEqual(slot.slotSettledFields(sold, 'exit'), live.settledFields(sold, 'exit'));
  const done = Object.assign({}, sold, f);
  assert.ok(Math.abs(slot.slotRiskForBotRisk([done], 0).net + 0.5) < 1e-9, 'and it counts exactly once after the record is settled');
  const half = slot.slotRiskForBotRisk([slotOrder({ count: 4, fillCount: '4', maxCost: 3, exitCount: 2, exitProceeds: 0.5 })], 0);
  assert.ok(Math.abs(half.net - (0.5 - 1.5)) < 1e-9 && Math.abs(half.openCost - 1.5) < 1e-9, 'a partial exit realises its share');
};

gates['H6 the window figure for L1 is the gross spend and a sold or settled slot order still occupies its window'] = () => {
  const sold = slotOrder({ count: 4, fillCount: '4', maxCost: 3, exitCount: 4, exitProceeds: 2.5 });
  const r = slot.slotRiskForL1({ slotOrders: [sold], windowKey: slot.windowKey(T), now: NOW });
  assert.strictEqual(r.windowSpent, 3, 'sold, but still spent in the window');
  assert.strictEqual(r.openAtRisk, 0);
  assert.strictEqual(slot.slotWindowSpent([sold], T), 3);
  const settledOne = slotOrder({ settled: true, result: 'exit', settledPnl: -0.5, exitCount: 4, maxCost: 2.7 });
  assert.strictEqual(slot.slotWindowSpent([settledOne], T), 2.7);
  // wired the obvious way, the window cap stays shared: L1 sees the slot's spend even after the slot sold
  const afterSale = W(ON(), input({ slotOrders: [slotOrder({ ticker: T, maxCost: 26, exitCount: 4, exitProceeds: 20, fillCount: '4', step: 9 })], l1Orders: [] }));
  assert.strictEqual(afterSale.allowed, false, 'the slot itself also sees its sold spend as used window room');
};

gates['H7 kill rules are sticky, ordered by settlement time, and a reviewed edit re-arms only results settled after reviewedAt'] = () => {
  const S = GOOD();
  const mk = (k, pnl, at) => slotOrder({ ticker: 'KXBTC15M-26NOV02' + (1000 + k) + '-15', settled: true, result: pnl < 0 ? 'no' : 'yes', settledPnl: pnl, ts: NOW - 1e6 + k, settledAt: at });
  const T0 = NOW - 5e5;
  const three = [mk(1, -1, T0 + 1), mk(2, -1, T0 + 2), mk(3, -1, T0 + 3)];
  assert.strictEqual(slot.killCheck(S, three, null).killed, true);
  const lateWin = mk(0, 2, T0 + 10);           // placed first, settled last
  assert.strictEqual(slot.killCheck(S, [...three, lateWin], null).killed, true, 'a late-settling win cannot un-kill the three-loss streak');
  const earlyWin = mk(0, 2, T0 + 2.5);          // settled between loss 2 and 3
  assert.strictEqual(slot.killCheck(S, [three[0], three[1], earlyWin, three[2]], null).killed, false, 'a win that settled in between really did break the streak');
  const old = [-1, -1, -1].map((p, k) => Object.assign(mk(k + 10, p, Date.parse('2026-10-20T00:00:00Z') + k), { ts: Date.parse('2026-10-20T00:00:00Z') + k }));
  assert.strictEqual(slot.killCheck(Object.assign(GOOD(), { reviewedAt: '2026-10-01' }), old, null).killed, true, 'old losses count while reviewedAt is older');
  assert.strictEqual(slot.killCheck(GOOD(), old, null).killed, false, 'a reviewed edit with a later reviewedAt re-arms a streak kill: only newer results count');
  const net = Array.from({ length: 20 }, (_, k) => mk(30 + k, k % 2 ? 1 : -3, T0 + k * 10));
  assert.strictEqual(slot.killCheck(Object.assign(GOOD(), { reviewedAt: '2026-10-01' }), net, null).killed, true);
  assert.strictEqual(slot.validateSlotStrategy(Object.assign(GOOD(), { reviewedAt: '2099-01-01' })).ok, false, 'a reviewedAt in the future would blind the kill rules and is rejected');
  assert.strictEqual(slot.validateSlotStrategy(Object.assign(GOOD(), { reviewedAt: slot.SLOT_LAST_REVIEWED_ON })).ok, true);
  assert.strictEqual(slot.killCheck(Object.assign(GOOD(), { reviewedAt: '2026-10-29' }), [], { killedAt: NOW }).killed, true, 'a latch newer than reviewedAt blocks, and a future reviewedAt cannot hide it');
};

gates['H8 an order with a missing or odd ts still counts in the day and lifetime loss figures, and the gate refuses on it'] = () => {
  const noTs = slotOrder({ ts: undefined, settled: true, result: 'no', settledPnl: -9 });
  const stamp = slotOrder({ ts: { seconds: 1 }, settled: true, result: 'no', settledPnl: -9 });
  for (const o of [noTs, stamp]) {
    assert.strictEqual(slot.slotRiskForBotRisk([o], NOW - 86400000).net, -9);
    assert.strictEqual(slot.slotRiskContract([o], NOW).day.net, -9);
  }
  assert.strictEqual(slot.slotRiskForBotRisk([slotOrder({ ts: undefined, status: 'sending', fillCount: '0' })], 0).openCost, 3);
  assert.strictEqual(W(ON(), input({ slotOrders: [noTs] })).allowed, false, 'the gate will not trade on books it cannot date');
};

gates['H9 a malformed ticker is refused, never thrown on, and a failed-step id cannot be built twice'] = () => {
  for (const t of ['KXBTC15M-26NOV031015', 'KXGOLD15M-26OCT291015-T4012.99', 'KXBTC15M-26NOV031015-B1-X', 'kxbtc15m-26nov031015-15', '', null, undefined, 42, 'KXXRP15M-26NOV031015-15'])
    assert.doesNotThrow(() => assert.strictEqual(W(ON(), input({ ticker: t })).allowed, false), 'ticker ' + t);
  assert.strictEqual(W(ON(), input({ ticker: 'KXGOLD15M-26NOV031015-00', slotOrders: [], l1Orders: [] })).allowed, true);
};

gates['H10 any order with fills counts as money whatever its status, and an exit or loss with no readable pnl is booked as lost'] = () => {
  const odd = slotOrder({ count: 3, fillCount: '3', maxCost: 2.7, status: 'error', settled: false });
  const rc = slot.slotRiskContract([odd], NOW);
  assert.ok(Math.abs(rc.openTotal - 2.7) < 1e-9);
  assert.strictEqual(rc.openContractsByTicker[T], 3);
  assert.strictEqual(slot.slotRiskForBotRisk([odd], 0).trades, 1);
  assert.ok(Math.abs(slot.slotRiskForBotRisk([odd], 0).worst + 2.7) < 1e-9);
  assert.strictEqual(slot.slotWindowSpent([odd], T), 2.7);
  const exitNull = slotOrder({ count: 3, fillCount: '3', maxCost: 2.7, settled: true, result: 'exit', settledPnl: null, exitCount: 3 });
  assert.ok(Math.abs(slot.slotRiskForBotRisk([exitNull], 0).net + 2.7) < 1e-9, 'an exit with no pnl books the whole amount paid');
  const lossNull = slotOrder({ settled: true, result: 'no', settledPnl: null, maxCost: 5, count: 4, fillCount: '4' });
  assert.ok(Math.abs(slot.slotRiskForBotRisk([lossNull], 0).net + 5) < 1e-9, 'a settled loss with a null pnl is derived from its result, not zero');
  assert.strictEqual(slot.directionDecision({ ticker: T, side: 'no', l1Orders: [], slotOrders: [odd], lock: null, position: 0 }).allow, false, 'an errored order with fills still holds its side');
  assert.strictEqual(W(ON(), input({ sizingBase: 250, slotOrders: [slotOrder({ status: 'error', fillCount: '4', maxCost: 5.0, step: 7 })], limit: 0.75 })).allowed, false, 'and its dollars are in the caps');
};

gates['H11 parity: the same fixture orders give the same net, open cost, worst and trades through botRisk and slotRiskForBotRisk'] = async () => {
  const mk = (o) => Object.assign({ ticker: T, side: 'yes', count: 4, fillCount: '4', maxCost: 3, status: 'filled', ts: NOW - 60000, settled: false }, o);
  const base = [
    mk({}), mk({ exitCount: 2, exitProceeds: 0.5 }), mk({ exitCount: 4, exitProceeds: 2.5 }), mk({ fillCount: '3' }),
    mk({ side: 'no', ...live.settledFields(mk({ side: 'no' }), 'yes'), }), mk({ ...live.settledFields(mk({}), 'yes') }), mk({ ...live.settledFields(mk({ exitCount: 4, exitProceeds: 2.5 }), 'exit') }),
    mk({ ...live.settledFields(mk({ exitCount: 4, exitProceeds: 1.0 }), 'exit'), exitCount: 4, exitProceeds: 1.0 }), mk({ settled: true, result: 'hand', settledPnl: null }),
    mk({ status: 'error', fillCount: '2' }), mk({ count: 2, fillCount: '1', maxCost: 1.5 }),
  ];
  const l1 = base.map((o, i) => Object.assign({ id: 'a' + i, strategy: 'L1', ticker: 'KXBTC15M-26NOV03' + (1000 + i) + '-15' }, o));
  const sl = base.map((o, i) => Object.assign({ id: 'a' + i, strategy: 'SLOT', slotId: 'TESTA' }, o, { ticker: 'KXBTC15M-26NOV03' + (1000 + i) + '-15' }));
  const fetchFn = async () => ({ status: 200, text: async () => JSON.stringify({ market: { result: '' } }) });
  const a = await live.botRisk({ store: { updateTest: async () => {} }, since: 0, fetchFn, nowMs: NOW, orders: l1 });
  const b = slot.slotRiskForBotRisk(sl, 0);
  for (const k of ['net', 'openCost', 'worst', 'trades']) assert.ok(Math.abs(a[k] - b[k]) < 1e-9, k + ': botRisk ' + a[k] + ' vs slot ' + b[k]);
  assert.strictEqual(b.addonAtRisk, 0);
};

gates['H12 direction normalises ticker and status case and treats any fills as holding, so it does not rely only on the lock and the position'] = () => {
  const d = (o) => slot.directionDecision(Object.assign({ ticker: T, side: 'no', l1Orders: [], slotOrders: [], lock: null, position: 0 }, o));
  assert.strictEqual(d({ l1Orders: [l1Order({ ticker: T.toLowerCase(), status: 'sending', fillCount: '0' })] }).allow, false, 'lower-cased ticker');
  assert.strictEqual(d({ l1Orders: [l1Order({ ticker: ' ' + T + ' ' })] }).allow, false, 'spaces');
  assert.strictEqual(d({ l1Orders: [l1Order({ status: 'Filled' })] }).allow, false, 'status case');
  assert.strictEqual(d({ l1Orders: [l1Order({ status: 'error', fillCount: '2' })] }).allow, false, 'errored with fills still holds');
  assert.strictEqual(d({ l1Orders: [l1Order({ status: 'error', fillCount: '0' })] }).allow, true);
  for (const bad of ['YES', ' yes', 'bid', 'ask', undefined, null]) assert.strictEqual(d({ l1Orders: [l1Order({ side: bad })] }).allow, false, 'side ' + bad);
};

gates['H13 the slot cannot take the whole window: half the shared cap at most, and one L1 contract of room always stays'] = () => {
  const fav = Object.assign(GOOD(), { entry: { sideRule: 'favourite', priceMin: 0.5, priceMax: 0.9, leftMaxSec: 700, leftMinSec: 300 }, contractsPerOrder: 5 });
  const r = W({ enabled: true, registry: [fav] }, input({ sizingBase: 100, limit: 0.8 }));
  assert.ok(r.allowed, r.reasons.join());
  assert.ok(r.cost <= 0.055 * 100 * slot.SLOT_WINDOW_SHARE + 1e-9, 'at most half the window: ' + r.cost);
  assert.ok(0.055 * 100 - r.cost >= slot.SLOT_L1_RESERVE, 'a gold contract of room is left for L1');
  assert.ok(slot.SLOT_L1_RESERVE >= 0.97, 'the reserve covers a 97c contract');
  const tiny = W({ enabled: true, registry: [fav] }, input({ sizingBase: 20, limit: 0.8 }));
  assert.strictEqual(tiny.allowed, false, 'a small base leaves no room for the slot at all');
};

gates['H14 the inertness gate itself catches env reads, randomness, timers and nested imports'] = () => {
  const banned = /process\.env|Math\.random|performance|setTimeout|setInterval|import\(|globalThis|\beval\b/;
  for (const bad of ['process.env.X', 'Math.random()', 'setTimeout(f,1)', 'setInterval(f,1)', 'import("x")', 'globalThis.x', 'eval("1")', 'performance.now()']) assert.ok(banned.test(bad), bad);
  const os = require('os');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'slotwalk-'));
  fs.mkdirSync(path.join(dir, 'functions', 'sub'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'functions', 'sub', 'x.js'), "require('../kalshiSlotLib')");
  const hits = walk(dir).filter((f) => /kalshiSlot/.test(fs.readFileSync(f, 'utf8')));
  assert.strictEqual(hits.length, 1, 'a nested import is found by the recursive scan');
  fs.rmSync(dir, { recursive: true, force: true });
};

gates['H15 the wiring checklist and the contract names are in the design doc'] = () => {
  const doc = fs.readFileSync(path.join(root, 'docs', 'SECOND_SLOT_DESIGN.md'), 'utf8');
  for (const w of ['windowSpent', 'slotRiskForBotRisk', 'lockTxn', 'settledAt', 'othersUnsold', 'Wiring checklist', 'kalshiHandSoldGates', 'closedByHand', 'two-instance'])
    assert.ok(doc.includes(w), 'the design doc must mention ' + w);
  assert.ok(!/slotMayEnter|slotSideRule|windowAtRisk/.test(doc.split('\n').filter((l) => !/removed/i.test(l)).join('\n')), 'the doc no longer advertises the removed names');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
