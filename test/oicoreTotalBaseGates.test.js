'use strict';
// OB1 to OB4: OICORE's total-balance base (Nov 16, 2026, the owner's decision; the Risk Analyst reviews). Consequence: only OICORE may be sized off prediction cash plus FRESH perps equity; every
// failure of the perps read can only make OICORE smaller; and the perps figure reaches no other risk path (gate AT5 in accountTotalGates names this one reader).
const assert = require('assert');
const fs = require('fs'), path = require('path');
const base = require('../functions/kalshiOicoreBaseLib');
const slot = require('../functions/kalshiSlotLib');
const NOW = Date.parse('2026-11-20T16:57:30Z');
const gates = {};

gates.OB1 = () => {
  const ok = (d) => base.oicoreBase({ predictionBase: 212, perpsDoc: d, now: NOW });
  const f = ok({ equity: 674.33, at: NOW - 60000 });
  assert.deepStrictEqual([f.base, f.source], [886.33, 'total'], 'fresh: prediction cash plus perps equity');
  assert.strictEqual(ok({ equity: 674.33, at: NOW - 19 * 60000 }).source, 'total', 'just inside 20 minutes is fresh');
  for (const [name, d] of [['stale', { equity: 674.33, at: NOW - 21 * 60000 }], ['future', { equity: 674.33, at: NOW + 5 * 60000 }], ['missing', null], ['not an object', 'x'], ['no equity', { at: NOW }], ['zero equity', { equity: 0, at: NOW }],
    ['negative', { equity: -5, at: NOW }], ['NaN', { equity: NaN, at: NOW }], ['no time', { equity: 100 }], ['string time', { equity: 100, at: 'now' }]]) {
    const r = ok(d); assert.deepStrictEqual([r.base, r.source], [212, 'prediction_only'], name + ' gives prediction cash only');
  }
  for (const p of [0, -5, NaN, undefined, null]) assert.strictEqual(base.oicoreBase({ predictionBase: p, perpsDoc: { equity: 500, at: NOW }, now: NOW }).base, 0, 'an unusable prediction base is never rescued by perps money');
  // It can only raise the base when the figure is fresh, and a failed read is the cap (smaller): the OICORE size at the fallback is never above the size at the total.
  const L = slot.SLOT_LADDERS.OICORE;
  for (const pred of [100, 212, 500]) assert.ok(slot.slotLadderState(slot.SLOT_STRATEGIES[0], [], pred).size <= slot.slotLadderState(slot.SLOT_STRATEGIES[0], [], pred + 674.33).size, 'the fallback is never larger');
  void L;
};

// The stops on the new base, in dollars (the Risk Analyst sets these for the owner; this pins what the code does today at the $886 account).
gates.OB2 = () => {
  const s = slot.slotLadderState(slot.SLOT_STRATEGIES[0], [], 886.33);
  assert.strictEqual(s.size, 20, 'the bottom step at a $886 base');
  assert.ok(Math.abs(s.ddStop - 100) < 1e-9, 'drawdown stop $100: ' + s.ddStop);
  assert.ok(Math.abs(s.dailyCap - 50) < 1e-9, 'daily cap $50: ' + s.dailyCap);
  const p = slot.slotLadderState(slot.SLOT_STRATEGIES[0], [], 212);
  assert.strictEqual(p.size, 5, 'prediction cash only at $212'); assert.ok(p.ddStop < 30, 'and a drawdown stop under $30: ' + p.ddStop);
};

// Only the engine and the minute function read it; the lib reads only equity and at; the window cap gets its own prediction base.
gates.OB3 = () => {
  const dir = path.join(__dirname, '..', 'functions');
  const users = fs.readdirSync(dir).filter((x) => x.endsWith('.js') && /kalshiOicoreBaseLib|readPerpsDoc/.test(fs.readFileSync(path.join(dir, x), 'utf8'))).sort();
  assert.deepStrictEqual(users, ['index.js', 'kalshiSlotRunLib.js'], 'only the engine and the minute function name the base lib: ' + users.join(','));
  const lib = fs.readFileSync(path.join(dir, 'kalshiOicoreBaseLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/require\(|fetch|Firestore|Date\.now|process\.env/.test(lib), 'the base lib is pure');
  assert.deepStrictEqual([...new Set([...lib.matchAll(/\bd\.(\w+)/g)].map((m) => m[1]))].sort(), ['at', 'equity'], 'the lib reads only the two named fields of the perps document');
  const eng = fs.readFileSync(path.join(dir, 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/windowBase: sh\.sizeBase/.test(eng) && /s\.id === oiBaseLib\.STRATEGY_ID \? oiBase\.base : sh\.sizeBase/.test(eng), 'only OICORE gets the total base, and the window cap is told the prediction base');
  assert.ok(/sh\.sizeBase\)\) \{ skipAll\("no_shared_risk"\)|!\(sh\.sizeBase > 0\)/.test(eng), 'the shared figures check still runs on the prediction base');
  const lib2 = fs.readFileSync(path.join(dir, 'kalshiSlotLib.js'), 'utf8');
  assert.ok(/i\.windowCapFraction \* \(isNum\(i\.windowBase\)/.test(lib2), 'the window cap reads windowBase');
};

// The shared stop, the slot's own stop and the shard check stay on the prediction base in the engine.
gates.OB4 = () => {
  const eng = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8');
  assert.ok(/prof\.stopFraction \* sh\.sizeBase/.test(eng), 'the slot own loss stop is on the prediction base');
  assert.ok(!/stopFraction \* oiBase|floor.*oiBase/.test(eng), 'no stop reads the OICORE base');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
