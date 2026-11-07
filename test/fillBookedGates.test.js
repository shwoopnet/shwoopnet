'use strict';
// Fill-booked results and the OICORE streak kill (Nov 7, 2026, the owner's decision). Plain node + assert.
// Consequence under test: a settled order is booked at the cash it really cost, so the loss stop and the kill rules no longer read about $30 a week worse than the account;
// an order still OPEN stays at its worst case; and OICORE's streak kill is 24, not 18.
const assert = require('assert');
const live = require('../functions/kalshiLiveLib');
const slot = require('../functions/kalshiSlotLib');

const gates = {};
const near = (a, b, m) => assert.ok(Math.abs(a - b) < 1e-6, (m || '') + ' got ' + a + ' want ' + b);

// A real Dogecoin order from the Nov 7 report: 12 YES at a 0.92 limit, filled at 0.92 with a 0.0051 fee per contract, worst-case booking 0.926 a contract.
const yes12 = (o) => Object.assign({ strategy: 'L1', side: 'yes', count: 12, fillCount: '12', maxCost: 11.12, averageFillPrice: '0.92', averageFeePaid: '0.0051', settled: false }, o);
// A NO order: Kalshi gives averageFillPrice as the YES price, so the cash cost of a NO contract is 1 minus it.
const no12 = (o) => Object.assign({ strategy: 'L1', side: 'no', count: 12, fillCount: '12', maxCost: 10.9, averageFillPrice: '0.11', averageFeePaid: '0.0068', settled: false }, o);

gates.FB1 = () => {
  near(live.fillCost(yes12(), 12, 12), 12 * (0.92 + 0.0051), 'a YES order costs price plus fee per contract');
  near(live.fillCost(no12(), 12, 12), 12 * (0.89 + 0.0068), 'a NO order costs 1 minus the YES fill price, plus fee');
  near(live.fillCost(yes12({ fillCount: '6' }), 6, 12), 6 * (0.92 + 0.0051), 'a partial fill pays for what filled');
  // every unreadable input falls back to the limit booking in proportion
  for (const bad of [{ averageFillPrice: null }, { averageFillPrice: '' }, { averageFillPrice: 'x' }, { averageFillPrice: '0' }, { averageFillPrice: '1' }, { averageFeePaid: null }, { averageFeePaid: '-1' }, { side: 'maybe' }]) {
    near(live.fillCost(yes12(bad), 12, 12), 11.12, 'fails closed to maxCost for ' + JSON.stringify(bad));
  }
  // a cash figure above the limit booking is never used (the booking is the ceiling)
  near(live.fillCost(yes12({ averageFillPrice: '0.99' }), 12, 12), 11.12, 'never above the limit booking');
};

gates.FB2 = () => {
  const win = live.settledFields(yes12(), 'yes');
  near(win.settledPnl, 12 - 12 * (0.92 + 0.0051), 'a settled win is booked at cash');
  assert.ok(win.settledPnl > 12 - 11.12, 'and is better than the limit booking');
  const loss = live.settledFields(yes12(), 'no');
  near(loss.settledPnl, -12 * (0.92 + 0.0051), 'a settled loss is booked at cash');
  const exit = live.settledFields(yes12({ exitCount: 12, exitProceeds: 6.8 }), 'exit');
  near(exit.settledPnl, 6.8 - 12 * (0.92 + 0.0051), 'an early sell is the sale proceeds minus the cash cost');
  const old = live.settledFields({ side: 'yes', count: 12, fillCount: '12', maxCost: 11.12 }, 'no');
  near(old.settledPnl, -11.12, 'an order with no fill price is exactly what it was');
};

// The loss stop (botRisk): a settled order is counted at cash, an open order at its worst case.
gates.FB3 = async () => {
  const settledLoss = yes12({ settled: true, result: 'no', ts: 1 });
  const r = await live.botRisk({ store: {}, since: 0, orders: [settledLoss], nowMs: 5 });
  near(r.net, -12 * (0.92 + 0.0051), 'a settled loss reads at cash in the stop');
  const settledWin = yes12({ settled: true, result: 'yes', ts: 1 });
  const w = await live.botRisk({ store: {}, since: 0, orders: [settledWin], nowMs: 5 });
  near(w.net, 12 - 12 * (0.92 + 0.0051), 'a settled win reads at cash');
  // An open order is not fetched here (no network): prove the settled/open split in the source instead.
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(/else \{ net \+= proceeds - paid \* soldShare; openCost \+= paid \* \(1 - soldShare\)/.test(src), 'an open order stays at its worst-case cost (maxCost) in the stop');
};

// One footing: the slot's copy equals the live copy on many fixtures, and the slot's own accounting reads cash too.
gates.FB4 = () => {
  const sides = ['yes', 'no'], avgs = ['0.05', '0.5', '0.92', '0.995', null, 'x'], fees = ['0.0051', '0', null, '2'], counts = [[12, 12], [6, 12], [0, 12]];
  let n = 0;
  for (const side of sides) for (const a of avgs) for (const f of fees) for (const [got, want] of counts) {
    const t = { side, maxCost: 11.12, averageFillPrice: a, averageFeePaid: f, count: want, fillCount: got };
    const x = live.fillCost(t, got, want), y = slot.fillCost(t, got, want);
    assert.ok((Number.isNaN(x) && Number.isNaN(y)) || Math.abs(x - y) < 1e-12, 'live and slot fillCost agree ' + JSON.stringify(t)); n++;
  }
  assert.ok(n > 100);
  const t = yes12({ strategy: 'SLOT', slotId: 'OICORE', settled: true, result: 'no', settledPnl: null });
  const o = slot.slotSettledFields(t, 'no');
  near(o.settledPnl, live.settledFields(t, 'no').settledPnl, 'a slot settle equals an L1 settle for the same order');
};

// OICORE's streak kill is 24 (the owner, Nov 7, 2026: 18 was likely a luck kill of a strategy at fill-booked PF near 1.8: 10 losses in a row already).
gates.FB5 = () => {
  const oi = slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE');
  assert.strictEqual(oi.killRules.maxConsecutiveLosses, 24);
  assert.deepStrictEqual(oi.killRules.minNet, { afterFills: 40, net: -6 }, 'the net kill is unchanged');
  const mk = (k) => ({ strategy: 'SLOT', slotId: 'OICORE', ticker: 'KXBTC15M-26NOV071000-00-' + k, side: 'yes', count: 10, fillCount: '10', maxCost: 1, settled: true, result: 'no', settledPnl: -0.5, ts: 1e12 + k, settledAt: 1e12 + k });
  const run = (n) => slot.killCheck(Object.assign({}, oi, { reviewedAt: '2000-01-01', killRules: { maxConsecutiveLosses: 24, minNet: { afterFills: 1000, net: -1e9 } } }), Array.from({ length: n }, (_, k) => mk(k)), null);
  assert.strictEqual(run(23).killed, false, '23 losses in a row is not a kill');
  assert.strictEqual(run(24).killed, true, '24 is');
  assert.ok(/must be 1 to 30/.test(require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'kalshiSlotLib.js'), 'utf8')), 'the validator allows up to 30');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
