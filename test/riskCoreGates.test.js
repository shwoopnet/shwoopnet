'use strict';
// Risk core P1 (inert): the pure account and seat layers. Invented round numbers only.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const libPath = path.join(root, 'functions', 'kalshiRiskCoreLib.js');
const lib = require(libPath);
const libSrc = fs.readFileSync(libPath, 'utf8');
const fee = (c, p) => Math.ceil(0.07 * c * p * (1 - p) * 100) / 100;   // an invented fee shape, a parameter of the library
const gates = {};

const seat = (id, tier, contracts, extra) => Object.assign({ id, tier, contracts, price: 0.9, startedAtMs: 1000, openContracts: 0 }, extra || {});

gates.RC1 = () => { // the account ceilings follow the base and the dollar ceiling
  assert.strictEqual(lib.windowCeiling(1000), 80);
  assert.strictEqual(lib.openMoneyCap(1000), 120);
  assert.strictEqual(lib.openMoneyCap(5000), 150, 'open money never above 150 dollars');
  assert.strictEqual(lib.stopsBudget(1000), 300);
  for (const bad of [0, -5, NaN, undefined, null, 'x', Infinity * 0]) { assert.strictEqual(lib.windowCeiling(bad), 0); assert.strictEqual(lib.openMoneyCap(bad), 0); assert.strictEqual(lib.stopsBudget(bad), 0); }
};

gates.RC2 = () => { // seat maximum loss per tier
  assert.strictEqual(lib.seatMaxLoss(seat('t', 'trial', 3), 1000), 18, 'a trial seat with no floor can lose its margin');
  assert.strictEqual(lib.seatMaxLoss(seat('t', 'trial', 3, { netFloor: -6 }), 1000), 24, 'net floor minus 18 dollars');
  assert.strictEqual(lib.seatMaxLoss(seat('f', 'full', 10), 1000), 60);
  assert.strictEqual(lib.seatMaxLoss(seat('p', 'proven', 20), 1000), 100, '5 x contracts');
  assert.strictEqual(lib.seatMaxLoss(seat('p', 'proven', 30), 1000), 120, '12 percent of the base binds');
  assert.strictEqual(lib.seatMaxLoss(seat('p', 'proven', 30), 5000), 150, 'dollar ceiling binds');
  assert.strictEqual(lib.seatMaxLoss(seat('x', 'mystery', 3), 1000), Infinity, 'an unknown tier can never be admitted');
};

gates.RC3 = () => { // the stops budget admits or refuses at three invented bases
  // base 826: budget 247.8. Two full seats (120) fit, four (240) fit, a fifth (300) does not.
  let live = [];
  for (let i = 0; i < 4; i++) { const r = lib.admitSeat(live, seat('f' + i, 'full', 10), 826); assert.strictEqual(r.admit, true); live.push(seat('f' + i, 'full', 10)); }
  const r5 = lib.admitSeat(live, seat('f4', 'full', 10), 826);
  assert.strictEqual(r5.admit, false); assert.strictEqual(r5.reason, 'stops_budget'); assert.strictEqual(r5.used, 300);
  // five trial seats fit at 826 (90 of 247.8)
  live = []; for (let i = 0; i < 5; i++) live.push(seat('t' + i, 'trial', 3));
  assert.strictEqual(lib.allSeatsWorstCase(live, 826).ok, true);
  // base 1000: budget 300. Four full (240) plus three trial (54) = 294 fits, a fourth trial (312) does not.
  live = [0, 1, 2, 3].map((i) => seat('f' + i, 'full', 10)).concat([0, 1, 2].map((i) => seat('t' + i, 'trial', 3)));
  assert.strictEqual(lib.allSeatsWorstCase(live, 1000).ok, true);
  assert.strictEqual(lib.admitSeat(live, seat('t3', 'trial', 3), 1000).admit, false);
  // base 1350: budget 405. 4 full + 4 trial = 312 fits; adding a proven seat of 30 contracts (150 at this base) is 462 and waits; one of 15 (75) is 387 and fits.
  live = [0, 1, 2, 3].map((i) => seat('f' + i, 'full', 10)).concat([0, 1, 2, 3].map((i) => seat('t' + i, 'trial', 3)));
  assert.strictEqual(lib.allSeatsWorstCase(live, 1350).total, 312);
  assert.strictEqual(lib.admitSeat(live, seat('p', 'proven', 30), 1350).admit, false);
  assert.strictEqual(lib.admitSeat(live, seat('p', 'proven', 15), 1350).admit, true);
  // a probe counts like a trial seat: with the proven seat of 15 in, one probe (18) makes 405, exactly the budget, and fits; a second does not
  const withProven = live.concat([seat('p', 'proven', 15)]);
  assert.strictEqual(lib.admitSeat(withProven, seat('pr1', 'probe', 1), 1350).admit, true);
  assert.strictEqual(lib.admitSeat(withProven.concat([seat('pr1', 'probe', 1)]), seat('pr2', 'probe', 1), 1350).admit, false);
  // no base, nothing is admitted
  assert.strictEqual(lib.admitSeat([], seat('t', 'trial', 3), 0).admit, false);
  assert.strictEqual(lib.admitSeat([], seat('t', 'trial', 3), NaN).admit, false);
};

const wideSeats = () => [
  seat('probe', 'probe', 1, { startedAtMs: 10 }),
  seat('trialA', 'trial', 3, { startedAtMs: 500 }),
  seat('trialB', 'trial', 3, { startedAtMs: 100 }),
  seat('fullA', 'full', 10, { startedAtMs: 900 }),
  seat('provenA', 'proven', 20, { startedAtMs: 800 }),
];
const byId = (a) => Object.fromEntries(a.map((x) => [x.id, x]));

gates.RC4 = () => { // priority order and determinism: shuffling the input never changes the output
  const base = 1000;
  const ref = lib.allocateWindow(wideSeats(), base, 0, 0, fee);
  assert.deepStrictEqual(ref.map((x) => x.id), ['provenA', 'fullA', 'trialB', 'trialA', 'probe'], 'proven, full, trial (longest record first), probe');
  const perms = [[4, 3, 2, 1, 0], [2, 0, 4, 1, 3], [1, 3, 0, 4, 2], [3, 4, 1, 2, 0]];
  for (const p of perms) { const s = wideSeats(); assert.deepStrictEqual(lib.allocateWindow(p.map((i) => s[i]), base, 0, 0, fee), ref); }
};

gates.RC5 = () => { // when the window ceiling binds the lowest tier is squeezed first
  const base = 1000;   // ceiling 80
  const free = byId(lib.allocateWindow(wideSeats(), base, 0, 0, fee));
  for (const id of Object.keys(free)) assert.strictEqual(free[id].skip, null, id + ' fits an empty window');
  const tight = byId(lib.allocateWindow(wideSeats(), base, 55, 0, fee));   // 25 left
  assert.strictEqual(tight.provenA.contracts, free.provenA.contracts, 'proven is served in full first');
  assert.ok(tight.fullA.contracts >= 1 && tight.fullA.contracts < free.fullA.contracts, 'full is sized down to what is left');
  assert.strictEqual(tight.trialB.skip, 'window_ceiling'); assert.strictEqual(tight.trialA.skip, 'window_ceiling'); assert.strictEqual(tight.probe.skip, 'window_ceiling');
  const sent = Object.values(tight).reduce((a, r) => a + r.cost, 0);
  assert.ok(sent <= 25 + 1e-9, 'never more than the money left in the window');
};

gates.RC6 = () => { // under one contract sends nothing and says window_ceiling
  const r = byId(lib.allocateWindow([seat('t', 'trial', 3)], 1000, 79.5, 0, fee));   // 0.5 dollars left, one contract at 0.9 costs more
  assert.strictEqual(r.t.contracts, 0); assert.strictEqual(r.t.skip, 'window_ceiling'); assert.strictEqual(r.t.cost, 0);
  const open = byId(lib.allocateWindow([seat('t', 'trial', 3)], 1000, 0, 119.5, fee));   // open money is what is short
  assert.strictEqual(open.t.skip, 'window_ceiling');
  const sized = byId(lib.allocateWindow([seat('t', 'trial', 3)], 1000, 77.5, 0, fee));   // 2.5 left: two contracts fit, three do not
  assert.strictEqual(sized.t.contracts, 2); assert.strictEqual(sized.t.skip, null);
};

gates.RC7 = () => { // a seat's own caps bind before the shared money: a trial seat never exceeds 3 contracts or 3 dollars an order
  const r = byId(lib.allocateWindow([seat('t', 'trial', 10, { price: 0.95 }), seat('f', 'full', 50), seat('pr', 'probe', 5)], 100000, 0, 0, fee));
  assert.ok(r.t.contracts <= 3 && r.t.cost <= 3);
  assert.ok(r.f.contracts <= 10 && r.f.cost <= 20);
  assert.ok(r.pr.contracts <= 1);
  const full = byId(lib.allocateWindow([seat('f', 'full', 10, { price: 0.95 })], 300, 0, 0, fee));
  assert.ok(full.f.cost <= 7.5 && full.f.contracts < 10, 'the base-linked order cap shrinks a full order');
  const own = byId(lib.allocateWindow([seat('t', 'trial', 3, { openContracts: 3 })], 1000, 0, 0, fee));
  assert.strictEqual(own.t.skip, 'seat_cap', 'its own open contracts count against its own size');
  assert.strictEqual(byId(lib.allocateWindow([seat('x', 'mystery', 3)], 1000, 0, 0, fee)).x.skip, 'unknown_tier');
};

gates.RC8 = () => { // no caps raised by any input: bad numbers become zero and cost fails closed
  for (const bad of [NaN, -3, undefined, null, 'ten', Infinity]) {
    const caps = lib.seatCaps(seat('f', 'full', bad), 1000);
    assert.ok(caps.contracts <= lib.FULL.contracts && caps.orderCap <= 20 && caps.dailyCap <= 20);
    assert.ok(lib.seatCaps(seat('f', 'full', 10), bad).orderCap === 0, 'a bad base gives a zero cap');
    assert.strictEqual(lib.seatOrderCost(3, 0.9, () => NaN), Infinity);
  }
  assert.strictEqual(lib.seatOrderCost(0, 0.9, fee), Infinity);
  assert.strictEqual(lib.seatOrderCost(3, 1.5, fee), Infinity);
  assert.strictEqual(lib.seatOrderCost(3, 0.9, undefined), Infinity, 'no fee function, no order');
  assert.ok(Math.abs(lib.seatOrderCost(3, 0.9, fee) - (2.7 + fee(3, 0.9))) < 1e-12);
  const none = lib.allocateWindow([seat('t', 'trial', 3, { price: NaN })], 1000, 0, 0, fee);
  assert.strictEqual(none[0].contracts, 0);
  assert.deepStrictEqual(lib.allocateWindow('nope', 1000, 0, 0, fee), []);
  const worse = lib.allocateWindow(wideSeats(), 1000, NaN, -50, fee);   // bad spent figures never add room beyond the ceiling
  assert.ok(worse.reduce((a, x) => a + x.cost, 0) <= lib.windowCeiling(1000) + 1e-9);
};

gates.RC9 = () => { // constants equal kalshiSlotLib's where they overlap
  const slot = require(path.join(root, 'functions', 'kalshiSlotLib.js'));
  assert.strictEqual(lib.ORDER_CAP_FRACTION, slot.SLOT_CAP_FRACTIONS.perOrder);
  assert.strictEqual(lib.ORDER_CAP_CEILING, slot.SLOT_CAP_CEILINGS.perOrder);
  assert.strictEqual(lib.DAILY_CAP_FRACTION, slot.SLOT_CAP_FRACTIONS.daily);
  assert.strictEqual(lib.DAILY_CAP_CEILING, slot.SLOT_CAP_CEILINGS.daily);
  assert.strictEqual(lib.FULL.contracts, slot.SLOT_MAX_CONTRACTS_PER_ORDER, 'a full seat is the slot default size');
  assert.ok(lib.TRIAL.orderCap <= slot.SLOT_CAP_CEILINGS.perOrder && lib.TRIAL.dailyCap <= slot.SLOT_CAP_CEILINGS.daily);
  assert.ok(lib.PROVEN.dailyCeiling >= slot.SLOT_CAP_CEILINGS.daily && lib.PROVEN.lossCeiling >= slot.SLOT_CAP_CEILINGS.lifetime);
};

gates.RC10 = () => { // the spec's worst case: every seat losing its maximum together, at every base, is checked by the admission gate, never by luck
  for (const base of [500, 826, 1000, 1350, 2000, 5000]) {
    const live = [];
    for (const c of [seat('f1', 'full', 10), seat('t1', 'trial', 3), seat('p1', 'proven', 25), seat('t2', 'trial', 3), seat('f2', 'full', 10), seat('pr', 'probe', 1), seat('f3', 'full', 10), seat('f4', 'full', 10)]) {
      if (lib.admitSeat(live, c, base).admit) live.push(c);
    }
    const w = lib.allSeatsWorstCase(live, base);
    assert.ok(w.ok && w.total <= lib.stopsBudget(base) + 1e-9, 'admitted seats fit at base ' + base);
  }
};

gates.RC11 = () => { // inert and isolated: requires nothing, and nothing else names it
  assert.ok(!/require\(/.test(libSrc.replace(/\/\/.*$/gm, '')), 'the library requires nothing');
  assert.ok(!/fetch\(|https?:|firebase|admin\.|process\.env|Date\.now|Math\.random/.test(libSrc.replace(/\/\/.*$/gm, '')), 'no network, store, clock or random');
  const files = [];
  const walk = (d) => { for (const n of fs.readdirSync(d, { withFileTypes: true })) { if (n.name === 'node_modules' || n.name.startsWith('.')) continue; const p = path.join(d, n.name); if (n.isDirectory()) walk(p); else files.push(p); } };
  walk(path.join(root, 'functions'));
  files.push(path.join(root, 'index.html'));
  for (const f of files) {
    if (f === libPath || !/\.(js|html|sh|json)$/.test(f)) continue;
    assert.ok(!/kalshiRiskCoreLib/.test(fs.readFileSync(f, 'utf8')), path.relative(root, f) + ' must not reference the risk core');
  }
};

gates.RC12 = () => { // no em dashes in the library, this file or the doc; the doc states no live figures
  assert.ok(!libSrc.includes(String.fromCharCode(8212)) && !fs.readFileSync(__filename, 'utf8').includes(String.fromCharCode(8212)));
  const doc = fs.readFileSync(path.join(root, 'docs', 'RISK_CORE.md'), 'utf8');
  assert.ok(!doc.includes(String.fromCharCode(8212)));
  assert.ok(/not wired|inert/i.test(doc));
};

const D = 24 * 3600 * 1000, NOW = 1000 * D;
gates.RC13 = () => { // R1: a cache only refuses; stale, unreadable or future sends nothing; the daily replay latches when worse
  assert.strictEqual(lib.cachedSeatGate({ atMs: NOW - 60000, drawdown: 10 }, NOW, 60).allow, true);
  assert.strictEqual(lib.cachedSeatGate({ atMs: NOW - 60000, drawdown: 60 }, NOW, 60).reason, 'seat_stopped');
  for (const c of [{ atMs: NOW - 181000, drawdown: 0 }, { atMs: NOW + 5000, drawdown: 0 }, { atMs: NOW }, null, { drawdown: 1 }, { atMs: NaN, drawdown: 1 }]) assert.strictEqual(lib.cachedSeatGate(c, NOW, 60).allow, false);
  assert.strictEqual(lib.cachedSeatGate({ atMs: NOW - 180000, drawdown: 0 }, NOW, 60).allow, true, 'exactly 3 minutes is still fresh');
  assert.strictEqual(lib.cachedSeatGate({ atMs: NOW, drawdown: 0 }, NOW, NaN).allow, false);
  assert.strictEqual(lib.replayDue(NOW - D + 1, NOW), false); assert.strictEqual(lib.replayDue(NOW - D, NOW), true); assert.strictEqual(lib.replayDue(undefined, NOW), true);
  assert.deepStrictEqual(lib.auditCache({ drawdown: 10 }, { drawdown: 25 }), { latch: true, critical: true, reason: 'replay_worse' });
  assert.strictEqual(lib.auditCache({ drawdown: 25 }, { drawdown: 25 }).latch, false, 'latch clears once they agree');
  assert.strictEqual(lib.auditCache({ drawdown: 25 }, { drawdown: 10 }).latch, false, 'a more cautious cache is allowed');
  assert.strictEqual(lib.auditCache({ drawdown: 25 }, null).latch, true);
};
gates.RC14 = () => { // R2: an unclear answer quarantines that seat, blocks that market, counts maxCost as lost; sells or two seats end the session
  const u = (seatId, market, kind, atMs, maxCost, resolved) => ({ seatId, market, kind, atMs, maxCost, resolved });
  const one = lib.unclearAnswerDecision([u('A', 'M1', 'buy', NOW - 1000, 9)], NOW);
  assert.strictEqual(one.endSession, false); assert.deepStrictEqual(one.quarantinedSeats, ['A']); assert.deepStrictEqual(one.blockedMarkets, ['M1']); assert.strictEqual(one.lostTotal, 9); assert.strictEqual(one.lostBySeat.A, 9);
  assert.strictEqual(lib.unclearAnswerDecision([u('A', 'M1', 'sell', NOW, 3)], NOW).endSession, true);
  assert.strictEqual(lib.unclearAnswerDecision([u('A', 'M1', 'exit', NOW, 3)], NOW).reason, 'unclear_exit');
  const two = lib.unclearAnswerDecision([u('A', 'M1', 'buy', NOW - 59 * 60000, 3), u('B', 'M2', 'buy', NOW, 3)], NOW);
  assert.strictEqual(two.endSession, true);
  assert.strictEqual(lib.unclearAnswerDecision([u('A', 'M1', 'buy', NOW - 61 * 60000, 3), u('B', 'M2', 'buy', NOW, 3)], NOW).endSession, false, 'more than 60 minutes apart');
  assert.strictEqual(lib.unclearAnswerDecision([u('A', 'M1', 'buy', NOW, 3), u('A', 'M2', 'buy', NOW, 3)], NOW).endSession, false, 'one seat twice is still one seat');
  const res = lib.unclearAnswerDecision([u('A', 'M1', 'sell', NOW, 3, true)], NOW);
  assert.strictEqual(res.endSession, false); assert.deepStrictEqual(res.blockedMarkets, []); assert.strictEqual(res.reason, 'none');
  assert.strictEqual(lib.unclearAnswerDecision(null, NOW).endSession, false);
};
gates.RC15 = () => { // R3: market sum 30, 25 percent of the touch, no hedging, feed-waiting seats last
  assert.strictEqual(lib.MARKET_CONTRACT_CAP, 30);
  assert.strictEqual(lib.marketOrderContracts(10, 0, 100), 10);
  assert.strictEqual(lib.marketOrderContracts(10, 25, 100), 5, 'only 5 left in the market');
  assert.strictEqual(lib.marketOrderContracts(10, 30, 100), 0);
  assert.strictEqual(lib.marketOrderContracts(10, 0, 20), 5, '25 percent of a touch of 20');
  assert.strictEqual(lib.marketOrderContracts(10, 0, 3), 0, 'under 1 contract sends nothing');
  assert.strictEqual(lib.marketOrderContracts(10, 0, NaN), 0, 'unknown touch sends nothing');
  assert.strictEqual(lib.marketOrderContracts(NaN, 0, 100), 0);
  assert.strictEqual(lib.directionAllowed(null, 'yes'), true); assert.strictEqual(lib.directionAllowed('yes', 'yes'), true);
  assert.strictEqual(lib.directionAllowed('yes', 'no'), false); assert.strictEqual(lib.directionAllowed('no', 'yes'), false); assert.strictEqual(lib.directionAllowed(null, 'both'), false);
  const s = wideSeats(); s[3].waitingOnFeed = true;
  assert.strictEqual(lib.allocateWindow(s, 1000, 0, 0, fee).pop().id, 'fullA', 'a seat waiting on a feed runs last, whatever its tier');
};
gates.RC16 = () => { // R4: rolling 24 hour order budgets
  const times = []; for (let i = 0; i < 40; i++) times.push(NOW - i * 1000);
  assert.deepStrictEqual(lib.seatOrderBudget('S', times, NOW), { allowed: false, used: 40, limit: 40 });
  assert.strictEqual(lib.seatOrderBudget('S', times.slice(1), NOW).allowed, true);
  assert.strictEqual(lib.seatOrderBudget('L1', times, NOW).limit, 60, 'gold has its own listed value');
  assert.strictEqual(lib.ordersInDay(times, NOW + D - 20000), 20, 'orders age out one by one');
  assert.strictEqual(lib.ordersInDay([NOW - D, NOW - D + 1], NOW), 1, 'exactly 24 hours old has left the window');
  assert.strictEqual(lib.ordersInDay([NOW + 1000, NaN, 'x'], NOW), 0, 'future and bad times do not count');
  const many = []; for (let i = 0; i < 300; i++) many.push(NOW - i * 100);
  assert.strictEqual(lib.accountOrderCheck(many, NOW).endSession, true);
  assert.strictEqual(lib.accountOrderCheck(many.slice(1), NOW).endSession, false);
};
gates.RC17 = () => { // R5 reserve and R6 generic ladder
  assert.strictEqual(lib.goldReserveContracts(true), 1); assert.strictEqual(lib.goldReserveContracts(false), 0); assert.strictEqual(lib.goldReserveContracts(undefined), 0);
  const steps = [[500, 10], [999, 10], [1000, 15], [1349, 15], [1350, 20], [1999, 20], [2000, 30], [90000, 30], [NaN, 10], [-4, 10]];
  for (const [b, c] of steps) assert.strictEqual(lib.genericLadderStep(b), c, 'base ' + b);
  assert.deepStrictEqual(Array.from(lib.OICORE_LADDER), [20, 25, 30]);
  const ok = { fills: 15, days: 5, pf: 1.3, net: 15, drawdown: 29, contracts: 10 };
  assert.strictEqual(lib.ladderStepTestsPass(ok), true);
  for (const bad of [{ fills: 14 }, { days: 4.9 }, { pf: 1.29 }, { net: 9.9 }, { drawdown: 30 }, { contracts: 0 }]) assert.strictEqual(lib.ladderStepTestsPass(Object.assign({}, ok, bad)), false);
  assert.strictEqual(lib.ladderStepTestsPass(null), false);
};
gates.RC18 = () => { // R7: two up-moves a day, cooling gaps, stops budget, never limits a down-move
  const up = (seatId, atMs) => ({ seatId, kind: 'up', atMs });
  assert.strictEqual(lib.upMoveAllowed([], NOW, 'A', true).allow, true);
  assert.strictEqual(lib.upMoveAllowed([], NOW, 'A', false).reason, 'stops_budget');
  assert.strictEqual(lib.upMoveAllowed([], NOW, 'A', undefined).allow, false);
  assert.strictEqual(lib.upMoveAllowed([up('B', NOW - 5 * 3600000)], NOW, 'A', true).reason, 'account_cooling');
  assert.strictEqual(lib.upMoveAllowed([up('B', NOW - 6 * 3600000)], NOW, 'A', true).allow, true, '6 hours after, another seat may move');
  assert.strictEqual(lib.upMoveAllowed([up('A', NOW - 23 * 3600000)], NOW, 'A', true).reason, 'seat_cooling');
  assert.strictEqual(lib.upMoveAllowed([up('A', NOW - 24 * 3600000)], NOW, 'A', true).allow, true);
  assert.strictEqual(lib.upMoveAllowed([up('B', NOW - 7 * 3600000), up('C', NOW - 13 * 3600000)], NOW, 'A', true).reason, 'daily_limit');
  assert.strictEqual(lib.upMoveAllowed([up('B', NOW - 7 * 3600000), up('C', NOW - 25 * 3600000)], NOW, 'A', true).allow, true, 'a move over 24 hours old no longer counts');
  assert.strictEqual(lib.upMoveAllowed([{ seatId: 'A', kind: 'down', atMs: NOW - 1000 }], NOW, 'A', true).allow, true, 'a down-move starts no cooling');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
