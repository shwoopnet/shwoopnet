'use strict';
// SC1 to SC6: OICORE's size cap (Nov 16, 2026, the owner's popup: "YES, ship the OICORE size cap").
// Consequence: OICORE never sends more than (12% of the sizing base) / $4.50 contracts (floor 1), so its own drawdown stop, held to 12% of the base, is never smaller than about $4.50 a contract
// at a small account; the cap can only lower a size; and only the sizing base (prediction cash) feeds it.
const assert = require('assert');
const fs = require('fs'), path = require('path');
const slot = require('../functions/kalshiSlotLib');
const OI = slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE');
const L = slot.SLOT_LADDERS.OICORE;
const NOW = Date.parse('2026-11-20T16:57:30Z');
const input = (slotOrders, base, extra) => Object.assign({ strategyId: 'OICORE', ticker: 'KXBTC15M-26NOV201200-00', side: 'yes', limit: 0.13, step: 1, depthAtTouch: 1000, slotOrders, l1Orders: [],
  slotOrdersComplete: true, lockTxn: true, lock: null, position: 0, sizingBase: base, windowCapFraction: 0.055, killLatch: null, secondsLeft: 150, now: NOW, oiRise: 90000 }, extra || {});
const chk = (o, base, extra) => slot.slotOrderCheck(input(o, base, extra));
const gates = {};

gates.SC1 = () => {
  assert.strictEqual(L.sizeCapFraction, 0.12);
  assert.strictEqual(L.sizeCapPerContract, 4.5);
  assert.ok(slot.validLadder(L, OI), 'the ladder with its cap is valid');
  assert.ok(!slot.validLadder(Object.assign({}, L, { sizeCapFraction: 0.2 }), OI), 'a cap looser than 12% of the base is refused');
  assert.ok(!slot.validLadder(Object.assign({}, L, { sizeCapPerContract: 0 }), OI), 'a zero per contract figure is refused');
  assert.ok(!slot.validLadder(Object.assign({}, L, { sizeCapPerContract: undefined }), OI), 'one key without the other is refused');
};

// The stop math at the bases the owner and the Risk Analyst named ($200, $225, $300, $500, $835): the size, the drawdown stop (the smaller of 5 a contract, 12% of the base and the $150 ceiling) and dollars of stop per contract.
gates.SC2 = () => {
  const rows = [[200, 5, 24], [225, 6, 27], [300, 8, 36], [500, 13, 60], [835, 20, 100]];
  for (const [base, size, stop] of rows) {
    const s = slot.slotLadderState(OI, [], base);
    assert.strictEqual(s.size, size, 'size at a $' + base + ' base');
    assert.ok(Math.abs(s.ddStop - stop) < 1e-9, 'drawdown stop at a $' + base + ' base is $' + stop + ', got ' + s.ddStop);
    assert.ok(s.ddStop / s.size >= 4.5 - 1e-9, 'the stop is at least $4.50 a contract at $' + base + ': ' + (s.ddStop / s.size));
    assert.ok(s.dailyCap <= 0.06 * base + 1e-9, 'the daily cap stays within 6% of the base');
  }
  assert.strictEqual(slot.slotLadderState(OI, [], 835).sizeCap, 22, 'the cap itself at $835 is 22, above the 20 contract step, so the step is what is sent');
};

// It only lowers: a large base leaves every step as it was, and an earned step is cut only when the base cannot carry it.
gates.SC3 = () => {
  for (const base of [1350, 2000, 5000, 100000]) assert.strictEqual(slot.slotLadderState(OI, [], base).size, 20, 'the bottom step is unchanged at a $' + base + ' base');
  assert.ok(slot.slotLadderState(OI, [], 100000).size <= L.steps[0], 'never above the step');
  // Floor 1: a tiny base still allows one contract (the gate then decides whether it fits), and a missing or bad base gives the floor too.
  assert.strictEqual(slot.slotLadderState(OI, [], 20).size, 1);
  assert.strictEqual(slot.slotLadderState(OI, [], 0).size, 1);
  assert.strictEqual(slot.slotLadderState(OI, [], NaN).size, 1);
  // Monotone in the base: a larger base never gives a smaller size.
  let prev = 0;
  for (let b = 0; b <= 2000; b += 25) { const z = slot.slotLadderState(OI, [], b).size; assert.ok(z >= prev, 'monotone at ' + b); prev = z; }
};

// The order gate sends no more than the cap, whatever a caller asks for.
gates.SC4 = () => {
  const a = chk([], 200);
  assert.ok(a.allowed && a.count <= 5, 'at $200 the gate sends at most 5: ' + JSON.stringify(a));
  const b = chk([], 500, { wanted: 30 });
  assert.ok(b.allowed && b.count <= 13, 'a caller asking for 30 at $500 gets at most 13: ' + JSON.stringify(b));
  const c = chk([], 835);
  assert.ok(c.allowed && c.count === 20, 'at $835 the step of 20 is sent: ' + JSON.stringify(c));
};

// Only prediction cash feeds the base: the cap reads the sizing base argument and nothing from the perps account.
gates.SC5 = () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotLib.js'), 'utf8');
  assert.ok(!/perps|equity|account_equity/i.test(src.slice(src.indexOf('function ladderSizeCap'), src.indexOf('function slotLadderState'))), 'the cap function names no perps field');
  assert.strictEqual(slot.slotLadderState(OI, [], 500).size, slot.slotLadderState(OI, [], 500, { perpsTotal: 99999 }).size, 'an extra argument changes nothing');
};

// A stop at the strategy's own drawdown still refuses orders at the cap size: 12% of a $225 base is $27.
gates.SC6 = () => {
  const day = 86400000;
  const loss = (k) => ({ id: 'S-OICORE-X-' + k, strategy: 'SLOT', slotId: 'OICORE', ticker: 'KXBTC15M-26NOV010000-00', side: 'no', step: 1, count: 6, fillCount: 6, maxCost: 1, status: 'filled', settled: true, result: 'yes', settledPnl: -3, ts: Date.parse('2026-11-18T00:00:00Z') + k * 1000, settledAt: Date.parse('2026-11-18T00:00:00Z') + k * 1000 });
  void day;
  const nine = Array.from({ length: 9 }, (_, k) => loss(k));   // $27 down at a $225 base
  const r = chk(nine, 225);
  assert.ok(!r.allowed && /drawdown stop|daily loss cap/.test(r.reasons.join(' ')), 'a $27 fall at a $225 base stops new orders: ' + JSON.stringify(r.reasons));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
