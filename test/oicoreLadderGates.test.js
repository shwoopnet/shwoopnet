'use strict';
// LD1 to LD9: OICORE's size ladder (Nov 3, 2026, the owner: "yes build it", on the refinement chat's scaling spec).
// Consequence: OICORE may send more than 10 contracts ONLY when its own settled record earns each step and the sizing base can carry it; a bad stretch takes the size down at once,
// the drawdown stop ends new orders, and nothing stored, sent or typed can raise the size. Every number below is a code constant.
const assert = require('assert');
const slot = require('../functions/kalshiSlotLib');
const OI = slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE');
const L = slot.SLOT_LADDERS.OICORE;
const DAY = 86400000, T0 = Date.parse('2026-10-31T00:00:00Z');
// A settled OICORE order with a given result, settled `day` days after T0 (plus a small offset so the order is stable).
let seq = 0;
const ord = (net, day, extra) => { seq += 1; const ts = T0 + day * DAY + seq * 1000; return Object.assign({ id: 'S-OICORE-KXBTC15M-26NOV010000-' + seq + '-1', strategy: 'SLOT', slotId: 'OICORE', ticker: 'KXBTC15M-26NOV010000-00', side: 'no',
  step: 1, count: 10, fillCount: 10, maxCost: 1.4, status: 'filled', settled: true, result: net > 0 ? 'no' : 'yes', settledPnl: net, ts, settledAt: ts }, extra || {}); };
// n fills spread evenly over `days` days, `wins` of them winning +w, the rest losing -l (wins spread through the run).
const run = (n, days, wins, w, l, startDay) => Array.from({ length: n }, (_, k) => ord(k % Math.round(n / wins) === 0 && Math.floor(k / Math.round(n / wins)) < wins ? w : -l, (startDay || 0) + days * (k + 1) / n));
const gates = {};

gates.LD1 = () => {
  assert.ok(OI && L, 'OICORE has a ladder');
  assert.ok(slot.validLadder(L, OI), 'the ladder passes its own checks');
  assert.deepStrictEqual(L.steps.slice(), [10, 12, 15, 20, 30], 'the steps the owner approved');
  assert.strictEqual(L.steps[0], OI.contractsPerOrder, 'the first step is the registry size, so nothing changes until a step is earned');
  assert.ok(Math.max(...L.steps) <= slot.SLOT_LADDER_MAX_CONTRACTS && slot.SLOT_LADDER_MAX_CONTRACTS === 30, 'never above 30 contracts');
  assert.deepStrictEqual(L.minBase.slice(), [0, 825, 900, 1030, 1350], 'the sizing base each step needs (the refinement chat, B4)');
  assert.ok(Object.isFrozen(slot.SLOT_LADDERS) && Object.isFrozen(L) && Object.isFrozen(L.steps), 'frozen: nothing at run time can change it');
  assert.ok(!slot.validLadder(Object.assign({}, L, { steps: [5, 12, 15, 20, 30] }), OI), 'a ladder whose first step is not the registry size is refused (the strategy then sends its registry size)');
  assert.ok(!slot.validLadder(Object.assign({}, L, { steps: [10, 12, 15, 20, 31] }), OI), 'a step above 30 is refused');
};

gates.LD2 = () => {
  const s = slot.slotLadderState(OI, [], 800);
  assert.deepStrictEqual([s.laddered, s.step, s.size], [true, 0, 10], 'no record: the first step');
  assert.strictEqual(s.dailyCap, 25, 'daily loss cap at 10 contracts is $25 (2.5 a contract), under 6% of an $800 base');
  assert.strictEqual(s.ddStop, 50, 'drawdown stop at 10 contracts is $50 (5 a contract)');
  const other = Object.assign({}, OI, { id: 'OTHERX' });
  assert.strictEqual(slot.slotLadderState(other, [], 800).laddered, false, 'a strategy with no ladder keeps its registry size and the base-scaled caps');
};

gates.LD3 = () => {
  // 20 fills over 8 days, 6 wins of +$7 and 14 losses of -$0.90: win 30%, net +$29, profit factor about 3.3. That earns the next step.
  const good = run(20, 8, 6, 7, 0.9);
  const big = slot.slotLadderState(OI, good, 900);
  assert.deepStrictEqual([big.step, big.size], [1, 12], 'a good 20 fill, 8 day record steps up to 12 when the base is $900');
  const small = slot.slotLadderState(OI, good, 800);
  assert.deepStrictEqual([small.step, small.size], [1, 10], 'with an $800 base the step is earned but the size stays 10 (12 needs $825)');
  assert.deepStrictEqual(slot.slotLadderState(OI, good.slice().reverse(), 900).size, 12, 'the order of the documents does not matter: the replay sorts by settlement');
};

gates.LD4 = () => {
  assert.strictEqual(slot.slotLadderState(OI, run(20, 5, 6, 7, 0.9), 2000).size, 10, '20 fills in only 5 days: no step (7 days are required)');
  assert.strictEqual(slot.slotLadderState(OI, run(19, 10, 6, 7, 0.9), 2000).size, 10, '19 fills: no step (20 are required)');
  assert.strictEqual(slot.slotLadderState(OI, run(20, 8, 6, 7, 0.9), 2000).size, 12, '20 good fills over 8 days: one step');
  assert.deepStrictEqual([L.upFills, L.upDays], [20, 7], 'the faster gate the owner chose');
};

gates.LD5 = () => {
  assert.strictEqual(slot.slotLadderState(OI, run(20, 8, 3, 7, 0.9), 2000).size, 10, 'win rate 15%, under 20%: no step');
  assert.strictEqual(slot.slotLadderState(OI, run(20, 8, 5, 2, 0.9), 2000).size, 10, 'wins too small (net negative): no step');
  assert.strictEqual(slot.slotLadderState(OI, run(20, 8, 4, 5.9, 0.9), 2000).size, 10, 'profit factor about 1.6 but net +$9.20, under 1 x 10 contracts: no step');
};

gates.LD6 = () => {
  // Earn the step to 12, then lose 3 x 12 = $36 from the best point: back to 10 at once.
  const good = run(20, 8, 6, 7, 0.9);
  const losses = Array.from({ length: 30 }, (_, k) => ord(-1.2, 9 + k * 0.1));
  const s = slot.slotLadderState(OI, good.concat(losses), 2000);
  assert.deepStrictEqual([s.step, s.size], [0, 10], 'a $36 drawdown at 12 contracts steps back down to 10');
  const s2 = slot.slotLadderState(OI, good.concat(losses.slice(0, 29)), 2000);
  assert.strictEqual(s2.size, 12, 'just under the line ($34.80): still 12');
  const bottom = slot.slotLadderState(OI, Array.from({ length: 100 }, (_, k) => ord(-0.9, k * 0.2)), 2000);
  assert.strictEqual(bottom.size, 10, 'never below the first step');
};

gates.LD7 = () => {
  // Only the strategy's own final results since reviewedAt count: hand closes, other strategies, unsettled orders and anything before reviewedAt do not earn a step.
  const good = run(40, 15, 11, 7, 0.9);
  const hand = good.map((o) => Object.assign({}, o, { result: 'hand' }));
  assert.strictEqual(slot.slotLadderState(OI, hand, 2000).size, 10, 'hand-closed orders earn nothing');
  const other = good.map((o) => Object.assign({}, o, { slotId: 'OTHERX' }));
  assert.strictEqual(slot.slotLadderState(OI, other, 2000).size, 10, "another strategy's record earns nothing");
  const open = good.map((o) => Object.assign({}, o, { settled: false, result: undefined, settledPnl: null }));
  assert.strictEqual(slot.slotLadderState(OI, open, 2000).size, 10, 'open orders earn nothing');
  const early = good.map((o) => Object.assign({}, o, { ts: o.ts - 30 * DAY, settledAt: o.settledAt - 30 * DAY }));
  assert.strictEqual(slot.slotLadderState(OI, early, 2000).size, 10, 'results before reviewedAt earn nothing');
};

const NOW = Date.parse('2026-11-20T16:57:30Z');
const input = (slotOrders, base, extra) => Object.assign({ strategyId: 'OICORE', ticker: 'KXBTC15M-26NOV201200-00', side: 'yes', limit: 0.13, step: 1, depthAtTouch: 1000, slotOrders, l1Orders: [],
  slotOrdersComplete: true, lockTxn: true, lock: null, position: 0, sizingBase: base, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: NOW, oiRise: 90000 }, extra || {});
const chk = (o, base, extra) => slot.slotOrderCheck(input(o, base, extra));

gates.LD8 = () => {
  const two = chk(run(40, 15, 11, 7, 0.9), 900);
  assert.ok(two.allowed && two.count === 15, 'two good 20 fill stretches earn two steps, and $900 carries 15: ' + JSON.stringify(two));
  const good = run(20, 8, 6, 7, 0.9);
  const a = chk(good, 900);
  assert.ok(a.allowed && a.count === 12, 'the gate sends 12 once the step is earned and the base is $900: ' + JSON.stringify(a));
  const b = chk(good, 800);
  assert.ok(b.allowed && b.count === 10, 'and 10 at an $800 base: ' + JSON.stringify(b));
  const c = chk([], 800, { wanted: 25 });
  assert.ok(c.allowed && c.count === 10, 'a caller asking for more never gets more than the ladder allows');
  const d = chk([], 800, { depthAtTouch: 20 });
  assert.ok(d.allowed && d.count === 5, 'the depth share still cuts the size (25% of 20 at the touch)');
};

gates.LD9 = () => {
  // The drawdown stop: from a best result of +$20, a fall of $50 (5 x 10 contracts) refuses every new order.
  const up = [ord(10, 1), ord(10, 2)];
  const down = Array.from({ length: 5 }, (_, k) => ord(-10, 3 + k * 0.01));   // five losses (not 50 small ones, which would trip the 18 in a row kill first)
  const r = chk(up.concat(down), 800);
  assert.ok(!r.allowed && /drawdown stop/.test(r.reasons.join(' ')), 'a $50 fall from the best result stops new orders: ' + JSON.stringify(r.reasons));
  const ok = chk(up.concat(down.slice(0, 4)), 800);
  assert.ok(ok.allowed || !/drawdown stop/.test(ok.reasons.join(' ')), 'a $40 fall does not trip the $50 stop');
  // An open order counts as lost in the drawdown.
  const openOne = Object.assign(ord(0, 4), { settled: false, result: undefined, settledPnl: null, maxCost: 15, fillCount: 10, count: 10 });
  const s = slot.slotLadderState(OI, up.concat(down.slice(0, 4), [openOne]), 800);
  assert.ok(s.drawdown >= 55 - 1e-9, 'an open order is counted as lost in the drawdown: ' + s.drawdown);
  // The daily loss cap scales with the contract count: $25 at 10 contracts on an $800 base.
  const today = Array.from({ length: 3 }, (_, k) => ord(-8.4, (NOW - T0) / DAY - 0.5 + k * 0.001));
  const d = chk(today, 800);
  assert.ok(!d.allowed && /daily loss cap/.test(d.reasons.join(' ')), 'a $25.20 day at 10 contracts reaches the $25 daily cap: ' + JSON.stringify(d.reasons));
};

gates.LD10 = () => {
  // Nothing outside the library can raise the size: the run lib passes no size, the ladder has no stored input, and index.js never mentions it.
  const fs = require('fs'), path = require('path');
  const runSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  const idx = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  assert.ok(!/wanted\s*:/.test(runSrc), 'the tick never passes a wanted size');
  assert.ok(!/SLOT_LADDERS|slotLadderState/.test(idx) && !/SLOT_LADDERS|slotLadderState/.test(runSrc), 'only the library reads the ladder');
  const lib = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotLib.js'), 'utf8');
  const body = lib.slice(lib.indexOf('function slotLadderState('), lib.indexOf('// ---- The one gate every slot order passes'));
  assert.ok(!/Date\.now|new Date\(\)|require\(|firestore|fetch/.test(body), 'the replay is pure: no clock, no network, no store');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
