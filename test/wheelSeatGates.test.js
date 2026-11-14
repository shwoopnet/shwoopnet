'use strict';
// Gates for the wheel seat wiring, built INERT (functions/kalshiWheelLib.js, docs/WHEEL_SEAT_WIRING.md, docs/ROTATION_LANE.md 5, 5a, 6, 8).
// Each states the consequence: with no seat registered nothing can be sent, and no seat can be admitted, enlarged or re-armed except by a reviewed edit.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const wheel = require('../functions/kalshiWheelLib');
const slot = require('../functions/kalshiSlotLib');

const root = path.join(__dirname, '..');
const V = wheel._testOnly.validateWheelSeatWith, A = wheel._testOnly.activeWheelSeatsWith;
const FL = { ruleIds: ['RULEA', 'RULEB', 'RULEC', 'RULED', 'RULEE', 'RULEF', 'RULEG'] };
const T = 'KXBTC15M-26NOV131015-15';
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? (e.name === 'node_modules' ? [] : walk(path.join(d, e.name))) : [path.join(d, e.name)]);

const seat = (o) => Object.assign({
  id: 'SEATA', ruleId: 'RULEA', readme: 'docs/WHEEL_ADMIT_LIST.md#seat-a', series: ['KXBTC15M'],
  entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120 },
  exit: { stopBid: 0.02, targetBid: 0.9, mustExitLeftSec: 60 }, contractsPerOrder: 3,
  killRules: { maxConsecutiveLosses: 30, minNet: { afterFills: 5, net: -18 } }, probation: true,
  forwardReadDate: '2026-12-20', reviewedAt: '2026-11-12', popupDate: '2026-11-12',
}, o || {});
const bad = (s, flags) => assert.strictEqual(V(flags || FL, s).ok, false, JSON.stringify(V(flags || FL, s).errors));

// W1: no seat exists, nothing is admitted, the slot registry is exactly what it was.
assert.deepStrictEqual(wheel.WHEEL_SEATS, []);
assert.strictEqual(Object.isFrozen(wheel.WHEEL_SEATS), true);
assert.deepStrictEqual(wheel.activeWheelSeats(), []);
assert.strictEqual(wheel.WHEEL_FULL_SEATS_ENABLED, false);
assert.deepStrictEqual(slot.SLOT_STRATEGIES.map((s) => s.id), ['OICORE', 'EVENT830', 'CFRTIK', 'SPXOI1'], 'the wheel must not add a strategy to the slot registry');
assert.deepStrictEqual(wheel.WHEEL_RULE_IDS, []);
// With the production (empty) rule list not even a well formed seat is valid.
assert.strictEqual(wheel.validateWheelSeat(seat()).ok, false);

// W2: a well formed probation seat is valid once its rule is on the list, and maps to a valid slot strategy with no scale-in power.
assert.strictEqual(V(FL, seat()).ok, true, JSON.stringify(V(FL, seat()).errors));
const mapped = wheel.seatToSlotStrategy(seat());
assert.strictEqual(slot.validateSlotStrategy(mapped).ok, true);
assert.strictEqual(mapped.scaleIn.maxSteps, 1);
assert.strictEqual(mapped.contractsPerOrder * mapped.scaleIn.maxSteps <= 3, true);

// W3: every way of loosening or enlarging a seat is refused.
bad(seat({ ruleId: 'NOPE' }));                                       // unknown rule id
bad(seat({ contractsPerOrder: 11 }));                                // 11 contracts
bad(seat({ contractsPerOrder: 4 }));                                 // a $4 order: probation is exactly 3 contracts
bad(seat({ probation: false, contractsPerOrder: 11 }), Object.assign({ fullSeatsEnabled: true }, FL));
bad(seat({ probation: false, contractsPerOrder: 10 }));              // full seats are off by default, even for a perfect spec
assert.strictEqual(V(Object.assign({ fullSeatsEnabled: true }, FL), seat({ probation: false, contractsPerOrder: 10 })).ok, true);
{ const s = seat(); delete s.killRules; bad(s); }                    // a missing kill
bad(seat({ killRules: { maxConsecutiveLosses: 30 } }));
bad(seat({ killRules: { maxConsecutiveLosses: 30, minNet: { afterFills: 5, net: -30 } } }));   // a net floor looser than minus 18
bad(seat({ exit: { holdToSettle: false } }));                        // a loosened exit
bad(seat({ exit: { holdToSettle: true } }));                         // hold to settlement needs the reviewed hold list, which a seat id is not on
bad(seat({ exit: { stopBid: 0.02, targetBid: 0.9, mustExitLeftSec: 10 } }));   // not out before settlement
bad(seat({ entry: { sideRule: 'favourite', priceMin: 0.88, priceMax: 0.95, leftMaxSec: 180, leftMinSec: 120 } }));   // a favourite at 88c or above
bad(seat({ entry: { sideRule: 'cheap', priceMin: 0.05, priceMax: 0.9, leftMaxSec: 180, leftMinSec: 120 } }));        // any probation band reaching 88c
bad(seat({ extra: 1 }));                                             // an unknown field
bad(seat({ series: ['KXDOGE15M'] }));                                // a market the slot does not allow
bad(seat({ popupDate: undefined }));
bad(seat({ reviewedAt: '2099-01-01' }));                             // a future reviewedAt would blind the kill rules

// W3b (security review): the probation floor applies from fill 5 at the latest; a seat id may not reuse a registered or keyed id; caps default to probation.
bad(seat({ killRules: { maxConsecutiveLosses: 30, minNet: { afterFills: 6, net: -18 } } }));
bad(seat({ id: 'OICORE' }));
bad(seat({ id: 'EVENT830' }));
bad(seat({ id: 'CFRTIK' }));
assert.strictEqual(V(Object.assign({ allowedIds: ['OICORE'] }, FL), seat({ id: 'OICORE' })).errors.some((x) => /already exists/.test(x)), false);
assert.strictEqual(wheel.wheelSeatCaps({ probation: 'yes' }, 100000).perOrder, 3);
assert.strictEqual(wheel.wheelSeatCaps({}, 100000).perOrder, 3);
assert.strictEqual(wheel.wheelSeatCaps(null, 100000).perOrder, 3);

// W4: at most 5 probation seats, repeated ids and any single bad entry refuse the whole list.
const mk = (n) => Array.from({ length: n }, (_, i) => seat({ id: 'SEAT' + 'ABCDEFG'[i], ruleId: 'RULE' + 'ABCDEFG'[i] }));
assert.strictEqual(A(FL, mk(5)).length, 5);
assert.strictEqual(A(FL, mk(6)).length, 0, 'a sixth probation seat refuses every seat');
assert.strictEqual(A(FL, [seat(), seat()]).length, 0);
assert.strictEqual(A(FL, mk(2).concat([seat({ id: 'SEATZ', ruleId: 'NOPE' })])).length, 0);

// W5: caps. The smaller of the slot's cap and the seat's own always wins.
assert.strictEqual(wheel.wheelSeatCaps(seat(), 100000).perOrder, 3);
assert.strictEqual(wheel.wheelSeatCaps(seat(), 40).perOrder, slot.slotCaps(40).perOrder);
assert.strictEqual(wheel.wheelSeatCaps(seat(), 0).perOrder, 0);
assert.strictEqual(wheel.wheelSeatCaps(seat({ probation: false }), 100000).perOrder, 10);
assert.strictEqual(wheel.wheelSeatCaps(seat(), 100000).daily, slot.slotCaps(100000).daily);

// W6: the net floor latch refuses further orders; a latch stays until a reviewed edit moves reviewedAt.
const order = (i, pnl, o) => Object.assign({ strategy: 'SLOT', slotId: 'SEATA', ticker: T, series: 'KXBTC15M', side: 'yes', step: 1, count: 3, fillCount: 3, status: 'filled',
  maxCost: 3, settled: true, result: 'no', settledPnl: pnl, ts: Date.parse('2026-11-13T10:00:00Z') + i * 1000 }, o || {});
const five = [0, 1, 2, 3, 4].map((i) => order(i, -3.7));
assert.strictEqual(wheel.wheelSeatKilled(seat(), five, null).killed, true, 'net below minus 18 after 5 fills latches the seat');
assert.strictEqual(wheel.wheelSeatKilled(seat(), five.slice(0, 4), null).killed, false);
assert.strictEqual(wheel.wheelSeatKilled(seat(), [], { killedAt: Date.parse('2026-11-13T00:00:00Z') }).killed, true);
assert.strictEqual(wheel.wheelSeatKilled(seat({ reviewedAt: '2026-11-14' }), [], { killedAt: Date.parse('2026-11-13T00:00:00Z') }).killed, false, 'only a reviewed edit that moves reviewedAt re-arms');
assert.strictEqual(wheel.wheelSeatKilled(seat(), [], 'junk').killed, true, 'an unreadable latch fails closed');

// W7: seat orders are ordinary slot orders: they count in the shared stop and the window cap, even if the seat is later removed from any list.
const open = order(9, null, { settled: false, result: undefined, maxCost: 2.7 });
assert.strictEqual(slot.slotRiskForBotRisk([open], 0).openCost > 2.6, true);
assert.strictEqual(slot.slotWindowSpent([open], T) >= 2.7, true);

// W8: shard check refuses when money is short or unknown.
assert.strictEqual(wheel.wheelShardCheck({ avail: 1, cost: 2.7 }).code, 'shard_short');
assert.strictEqual(wheel.wheelShardCheck({ avail: undefined, cost: 2.7 }).ok, false);
assert.strictEqual(wheel.wheelShardCheck({ avail: 5, cost: 2.7 }).ok, true);

// W9: live against shadow, first 20 live orders. Not wired: it only returns a verdict.
const rows = (n, filled, worse) => Array.from({ length: n }, (_, i) => ({ filled: i < filled, fillPrice: 0.2 + worse, shadowPrice: 0.2 }));
assert.strictEqual(wheel.wheelLiveVsShadow(rows(19, 19, 0)), 'wait');
assert.strictEqual(wheel.wheelLiveVsShadow(rows(20, 11, 0)), 'leave seat', 'under 60 percent filled');
assert.strictEqual(wheel.wheelLiveVsShadow(rows(20, 12, 0)), 'stay');
assert.strictEqual(wheel.wheelLiveVsShadow(rows(20, 20, 0.02)), 'leave seat', 'more than 1c worse than the shadow');
assert.strictEqual(wheel.wheelLiveVsShadow(rows(20, 20, 0.01)), 'stay');
assert.strictEqual(wheel.wheelLiveVsShadow(null), 'wait');

// W10: nothing can place an order for a seat today: nothing imports the wheel library, and nothing stored or sent can name a seat.
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const files = walk(path.join(root, 'functions')).filter((f) => /\.js$/.test(f) && !/kalshiWheelLib\.js$/.test(f));
for (const f of files) assert.ok(!/kalshiWheelLib|WHEEL_SEATS|activeWheelSeats/.test(code(fs.readFileSync(f, 'utf8'))), path.basename(f) + ' must not touch the wheel library while it is inert');
const html = code(fs.readFileSync(path.join(root, 'index.html'), 'utf8'));
assert.ok(!/\bWHEEL_SEATS\b|activeWheelSeats|kalshiWheelLib/.test(html));
assert.ok(!/WHEEL_SEATS|wheelSeat/i.test(fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8')));
const lib = code(fs.readFileSync(path.join(root, 'functions', 'kalshiWheelLib.js'), 'utf8'));
assert.ok(!/\b(fetch|firebase|firestore|Date\.now|new Date|process\.env|liveRequest|postOrder|sign)\b/i.test(lib.replace(/require\([^)]*\)/g, '')), 'the wheel library is pure: no network, database, clock or order code');
assert.ok(!/require\((["'])\.\/(?!kalshiSlotLib|kalshiSignalLib)/.test(lib));

console.log('wheelSeatGates: ok');
