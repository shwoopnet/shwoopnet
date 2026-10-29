// The profit add-on is clamped to a quarter of the balance-driven base (owner, Oct 29, 2026).
const assert = require('assert');
const fs = require('fs');
const live = require('../functions/kalshiLiveLib.js');
const gates = {};

gates.A1 = () => {
  // A win streak can never lift an order above base plus a quarter of base, however big the pool grows.
  for (const base of [1, 3, 4, 5, 8, 11, 23, 40]) {
    for (const pool of [0, 1, 5, 20, 100, 9999]) {
      const n = live.l1Count(base * 0.93 / 0.02 + 1, 0.93, 40, live.skimAddon({ pool }, 0));
      assert.ok(n <= base + Math.floor(base * 0.25), 'base ' + base + ' pool ' + pool + ' gave ' + n);
    }
  }
};
gates.A2 = () => {
  // A loss at peak size is never more than 1.25 times a base-size loss (same price per contract).
  for (const base of [4, 11, 23, 40]) {
    const peak = live.l1Count(base * 0.93 / 0.02 + 1, 0.93, 40, 9999);
    assert.ok(peak * 0.9 <= 1.25 * base * 0.9 + 1e-9, 'base ' + base + ' peak ' + peak);
  }
};
gates.A3 = () => {
  for (const base of [1, 2, 3]) assert.strictEqual(live.l1Count(base * 0.93 / 0.02 + 1, 0.93, 40, 999), base, 'base ' + base + ' gets no add-on');
  assert.strictEqual(live.addonCap(3), 0);
  assert.strictEqual(live.addonCap(4), 1);
};
gates.A4 = () => {
  // Capped and probe series still get no add-on: the tick forces their fixed size and addon 0.
  const src = fs.readFileSync(__dirname + '/../functions/kalshiLiveLib.js', 'utf8');
  assert.ok(/PROBE_SERIES\.includes\(c\.series\) \|\| CAPPED_SERIES\.includes\(c\.series\)\) \{ count = [^}]*addonUsed = 0;/.test(src));
};
gates.A5 = () => {
  // The clamp never raises a count.
  for (const cash of [50, 200, 509, 1000, 2000]) for (const cap of [1, 5, 12, 40]) for (const addon of [0, 1, 3, 50, 999]) {
    const clamped = live.l1Count(cash, 0.93, cap, addon);
    const base = live.l1Count(cash, 0.93, cap, 0);
    const old = Math.min(base + addon, live.L1_ORDER_CEILING);
    assert.ok(clamped <= old && clamped >= base, [cash, cap, addon].join());
  }
};
gates.A6 = () => {
  // Risk accounting uses the clamped count: addonUsed is count minus the no-add-on count, so it never exceeds addonCap(base).
  const src = fs.readFileSync(__dirname + '/../functions/kalshiLiveLib.js', 'utf8');
  assert.ok(/let addonUsed = sizing \? Math\.max\(0, count - l1Count\(cashLeft, cost1, sizeCap, 0\)\) : 0;/.test(src), 'addonUsed derives from the clamped count');
  const base = live.l1Count(1000, 0.93, 40, 0), used = live.l1Count(1000, 0.93, 40, 9999) - base;
  assert.strictEqual(used, live.addonCap(base));
};
gates.A7 = () => {
  // Replay arithmetic at 6c a win and 90c a loss: largest order and largest single loss before and after.
  const rows = {};
  for (const base of [11, 23, 40]) {
    const before = Math.min(base + 9999, live.L1_ORDER_CEILING), after = base + live.addonCap(base);
    rows[base] = { before, after, lossBefore: before * 0.9, lossAfter: after * 0.9 };
    assert.ok(after <= before);
  }
  assert.deepStrictEqual([rows[11].after, rows[23].after, rows[40].after], [13, 28, 50]);
};

let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + e.message); } }
process.exit(failed ? 1 : 0);
