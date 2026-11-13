'use strict';
// LD1 to LD9: OICORE's size ladder (Nov 3, 2026, the owner: "yes build it", on the refinement chat's scaling spec).
// Nov 13, 2026: the Risk Analyst, under the owner's grant of the risk parameters, set the steps to 20, 25, 30 (bases $0, $1,000, $1,350), the win rate lines to 14% up and 10% down, and the climb to 15 fills and 5 days.
// Consequence: OICORE may send more than 20 contracts ONLY when its own settled record earns each step and the sizing base can carry it; a bad stretch takes the size down at once,
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
  assert.deepStrictEqual(L.steps.slice(), [20, 25, 30], 'the steps set Nov 13, 2026');
  assert.ok(L.steps[0] >= OI.contractsPerOrder, 'the first step is at or above the registry size (an invalid ladder falls back to the smaller registry size)');
  assert.ok(Math.max(...L.steps) <= slot.SLOT_LADDER_MAX_CONTRACTS && slot.SLOT_LADDER_MAX_CONTRACTS === 30, 'never above 30 contracts');
  assert.deepStrictEqual(L.minBase.slice(), [0, 1000, 1350], 'the sizing base each step needs');
  assert.deepStrictEqual([L.upWinRate, L.downWinRate], [0.14, 0.10], 'win rate lines matched to a cheap-side strategy');
  assert.ok(Object.isFrozen(slot.SLOT_LADDERS) && Object.isFrozen(L) && Object.isFrozen(L.steps), 'frozen: nothing at run time can change it');
  assert.ok(!slot.validLadder(Object.assign({}, L, { steps: [5, 25, 30] }), OI), 'a ladder whose first step is below the registry size is refused (the strategy then sends its registry size)');
  assert.ok(!slot.validLadder(Object.assign({}, L, { steps: [20, 25, 31] }), OI), 'a step above 30 is refused');
  assert.strictEqual(slot.slotLadderState(OI, [], 800).size, 20, 'with no record the size is the bottom step, 20');
};

gates.LD2 = () => {
  const s = slot.slotLadderState(OI, [], 800);
  assert.deepStrictEqual([s.laddered, s.step, s.size], [true, 0, 20], 'no record: the first step');
  assert.strictEqual(s.dailyCap, 48, 'daily loss cap at 20 contracts is 2.5 a contract ($50), held to 6% of an $800 base ($48)');
  assert.strictEqual(s.ddStop, 96, 'drawdown stop at 20 contracts is 5 a contract ($100), held to 12% of an $800 base ($96)');
  const other = Object.assign({}, OI, { id: 'OTHERX' });
  assert.strictEqual(slot.slotLadderState(other, [], 800).laddered, false, 'a strategy with no ladder keeps its registry size and the base-scaled caps');
};

gates.LD3 = () => {
  // 15 fills over 6 days, 5 wins of +$7 and 10 losses of -$0.90: win 33%, net +$26, profit factor about 3.9. That earns the next step.
  const good = run(15, 6, 5, 7, 0.9);
  const big = slot.slotLadderState(OI, good, 1000);
  assert.deepStrictEqual([big.step, big.size], [1, 25], 'a good 15 fill, 6 day record steps up to 25 when the base is $1,000');
  const small = slot.slotLadderState(OI, good, 900);
  assert.deepStrictEqual([small.step, small.size], [1, 20], 'with a $900 base the step is earned but the size stays 20 (25 needs $1,000)');
  assert.deepStrictEqual(slot.slotLadderState(OI, good.slice().reverse(), 1000).size, 25, 'the order of the documents does not matter: the replay sorts by settlement');
};

gates.LD4 = () => {
  assert.strictEqual(slot.slotLadderState(OI, run(15, 3, 5, 7, 0.9), 2000).size, 20, '15 fills in only 4 days since the review: no step (5 days are required)');
  assert.strictEqual(slot.slotLadderState(OI, run(14, 8, 5, 7, 0.9), 2000).size, 20, '14 fills: no step (15 are required)');
  assert.strictEqual(slot.slotLadderState(OI, run(15, 6, 5, 7, 0.9), 2000).size, 25, '15 good fills over 6 days: one step');
  assert.deepStrictEqual([L.upFills, L.upDays], [15, 5], 'the faster climb set Nov 13, 2026');
};

gates.LD5 = () => {
  assert.strictEqual(slot.slotLadderState(OI, run(15, 6, 2, 20, 0.9), 2000).size, 20, 'win rate 13%, under 14%: no step even with a good net');
  assert.strictEqual(slot.slotLadderState(OI, run(15, 6, 3, 12, 0.9), 2000).size, 25, 'win rate 20% with large wins (net +$25.20): steps up');
  assert.strictEqual(slot.slotLadderState(OI, run(15, 6, 5, 2, 0.9), 2000).size, 20, 'wins too small (net +$1): no step');
  assert.strictEqual(slot.slotLadderState(OI, run(15, 6, 4, 6, 0.9), 2000).size, 20, 'profit factor about 2.4 but net +$14.10, under 1 x 20 contracts: no step');
};

gates.LD6 = () => {
  // Earn the step to 25, then lose 3 x 25 = $75 from the best point: back to 20 at once.
  const good = run(15, 6, 5, 7, 0.9);
  const losses = Array.from({ length: 25 }, (_, k) => ord(-3, 7 + k * 0.1));
  const s = slot.slotLadderState(OI, good.concat(losses), 2000);
  assert.deepStrictEqual([s.step, s.size], [0, 20], 'a $75 drawdown at 25 contracts steps back down to 20');
  const s2 = slot.slotLadderState(OI, good.concat(losses.slice(0, 24)), 2000);
  assert.strictEqual(s2.size, 25, 'just under the line ($72): still 25');
  const bottom = slot.slotLadderState(OI, Array.from({ length: 100 }, (_, k) => ord(-0.9, k * 0.2)), 2000);
  assert.strictEqual(bottom.size, 20, 'never below the first step');
};

gates.LD7 = () => {
  // Only the strategy's own final results since reviewedAt count: hand closes, other strategies, unsettled orders and anything before reviewedAt do not earn a step.
  const good = run(40, 15, 11, 7, 0.9);
  const hand = good.map((o) => Object.assign({}, o, { result: 'hand' }));
  assert.strictEqual(slot.slotLadderState(OI, hand, 2000).size, 20, 'hand-closed orders earn nothing');
  const other = good.map((o) => Object.assign({}, o, { slotId: 'OTHERX' }));
  assert.strictEqual(slot.slotLadderState(OI, other, 2000).size, 20, "another strategy's record earns nothing");
  const open = good.map((o) => Object.assign({}, o, { settled: false, result: undefined, settledPnl: null }));
  assert.strictEqual(slot.slotLadderState(OI, open, 2000).size, 20, 'open orders earn nothing');
  const early = good.map((o) => Object.assign({}, o, { ts: o.ts - 30 * DAY, settledAt: o.settledAt - 30 * DAY }));
  assert.strictEqual(slot.slotLadderState(OI, early, 2000).size, 20, 'results before reviewedAt earn nothing');
};

const NOW = Date.parse('2026-11-20T16:57:30Z');
const input = (slotOrders, base, extra) => Object.assign({ strategyId: 'OICORE', ticker: 'KXBTC15M-26NOV201200-00', side: 'yes', limit: 0.13, step: 1, depthAtTouch: 1000, slotOrders, l1Orders: [],
  slotOrdersComplete: true, lockTxn: true, lock: null, position: 0, sizingBase: base, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: NOW, oiRise: 90000 }, extra || {});
const chk = (o, base, extra) => slot.slotOrderCheck(input(o, base, extra));

gates.LD8 = () => {
  const two = chk(run(30, 12, 10, 7, 0.9), 1350);
  assert.ok(two.allowed && two.count === 30, 'two good 15 fill stretches earn two steps, and $1,350 carries 30: ' + JSON.stringify(two));
  const good = run(15, 6, 5, 7, 0.9);
  const a = chk(good, 1000);
  assert.ok(a.allowed && a.count === 25, 'the gate sends 25 once the step is earned and the base is $1,000: ' + JSON.stringify(a));
  const b = chk(good, 900);
  assert.ok(b.allowed && b.count === 20, 'and 20 at a $900 base: ' + JSON.stringify(b));
  const c = chk([], 800, { wanted: 25 });
  assert.ok(c.allowed && c.count === 20, 'a caller asking for more never gets more than the ladder allows');
  const d = chk([], 800, { depthAtTouch: 20 });
  assert.ok(d.allowed && d.count === 5, 'the depth share still cuts the size (25% of 20 at the touch)');
};

gates.LD9 = () => {
  // The drawdown stop: from a best result of +$20, a fall of $96 (5 x 20 contracts, held to 12% of an $800 base) refuses every new order.
  const up = [ord(10, 1), ord(10, 2)];
  const down = Array.from({ length: 10 }, (_, k) => ord(-10, 3 + k * 0.01));   // ten losses (not many small ones, which would trip the 24 in a row kill first)
  const r = chk(up.concat(down), 800);
  assert.ok(!r.allowed && /drawdown stop/.test(r.reasons.join(' ')), 'a $100 fall from the best result stops new orders: ' + JSON.stringify(r.reasons));
  const ok = chk(up.concat(down.slice(0, 9)), 800);
  assert.ok(ok.allowed || !/drawdown stop/.test(ok.reasons.join(' ')), 'a $90 fall does not trip the $96 stop');
  // An open order counts as lost in the drawdown.
  const openOne = Object.assign(ord(0, 4), { settled: false, result: undefined, settledPnl: null, maxCost: 15, fillCount: 20, count: 20 });
  const s = slot.slotLadderState(OI, up.concat(down.slice(0, 9), [openOne]), 800);
  assert.ok(s.drawdown >= 105 - 1e-9, 'an open order is counted as lost in the drawdown: ' + s.drawdown);
  // The daily loss cap scales with the contract count: $48 at 20 contracts on an $800 base (6% of base binds).
  const today = Array.from({ length: 4 }, (_, k) => ord(-12.1, (NOW - T0) / DAY - 0.5 + k * 0.001));
  const d = chk(today, 800);
  assert.ok(!d.allowed && /daily loss cap/.test(d.reasons.join(' ')), 'a $48.40 day at 20 contracts reaches the $48 daily cap: ' + JSON.stringify(d.reasons));
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
