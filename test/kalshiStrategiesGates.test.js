'use strict';
// ST1 to ST4: the strategy switch on the Bot page (the owner, Oct 29, 2026).
// Consequence: with no probe the page must draw exactly what it drew before (L1's own order array), and a probe's orders must never be counted as L1's.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const block = (n) => { const m = new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'not found: ' + n); return m[1]; };
const names = ['kalshiSlotIds', 'kalshiViewSelection', 'kalshiViewOrders', 'kalshiOrdersSummary', 'kalshiStrategySwitchHtml', 'kalshiProbeHtml'];
const stubs = 'function kalDayKey(ms){ return new Date(ms).toISOString().slice(0,10); }\nfunction kalshiOrderPnl(o){ return typeof o.settledPnl === "number" ? o.settledPnl : null; }\nfunction kalshiAgeText(s){ return s + "s"; }\nfunction kalTime(ms){ return "t" + ms; }\nfunction kalshiShortTicker(t){ return t; }\n';
let f;
try { f = new Function(stubs + names.map(block).join('\n') + '; return { ' + names.join(', ') + ' };')(); } catch (e) { console.log('FAIL setup: ' + e.message); process.exit(1); }
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const l1 = [{ ts: 1, fillCount: 1, settledPnl: 0.1 }];
const slot = [{ ts: 2, slotId: 'GOLD-X', fillCount: 1, settledPnl: -0.9, side: 'yes', ticker: 'T' }, { ts: 3, slotId: 'GOLD-X', fillCount: 1, settled: false }];
gates.ST1 = () => {
  assert.strictEqual(f.kalshiViewOrders('ALL', l1, []), l1, 'no probe: the very same array, so nothing changes');
  assert.strictEqual(f.kalshiViewSelection('GOLD-X', []), 'L1');
  assert.strictEqual(f.kalshiViewSelection('GONE', ['GOLD-X']), 'ALL', 'a name that no longer exists falls back to Overall');
};
gates.ST2 = () => {
  assert.deepStrictEqual(f.kalshiViewOrders('L1', l1, slot), l1, 'L1 never includes a probe order');
  assert.deepStrictEqual(f.kalshiViewOrders('GOLD-X', l1, slot), slot, 'a probe never includes L1 orders');
  assert.strictEqual(f.kalshiViewOrders('ALL', l1, slot).length, 3);
  assert.deepStrictEqual(f.kalshiSlotIds([{ ts: 1, slotId: 'A' }, { ts: 2, slotId: 'A' }, { ts: 3 }, { slotId: 'B' }]), ['A'], 'only orders with an id and a time name a strategy');
};
gates.ST3 = () => {
  const s = f.kalshiOrdersSummary(slot, 5);
  assert.strictEqual(s.n, 1); assert.strictEqual(s.lost, 1); assert.strictEqual(s.open.length, 1); assert.strictEqual(s.net, -0.9);
  const h = f.kalshiProbeHtml('<img src=x>', s, 5, esc, (v) => '$' + v);
  assert.ok(!/<img/.test(h), 'a strategy name is escaped');
  assert.ok(!/<img/.test(f.kalshiStrategySwitchHtml('ALL', ['<img src=x>'], esc)));
};
gates.ST4 = () => {
  assert.ok(/watchKalshiSlot: function/.test(html) && /collection\(db, 'kalshiSlotOrders'\)/.test(html), 'the page listens to the slot orders');
  assert.ok(!/(setDoc|addDoc|updateDoc|deleteDoc)\([^)]*kalshiSlot/.test(html), 'and never writes them');
  assert.ok(/id="kalStrat"[^>]*hidden/.test(html), 'the switch starts hidden');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
