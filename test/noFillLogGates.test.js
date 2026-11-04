'use strict';
// NF1: why an order did not fill is kept (Nov 4, 2026, the refinement chat: a third of gold orders and 8 OICORE orders ended "no fill" with no reason). Log only:
// Kalshi's own order status goes onto the order document when Kalshi returns one, and no code reads it back.
const assert = require('assert');
const fs = require('fs'), path = require('path');
const live = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
const run = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSlotRunLib.js'), 'utf8');
const gates = {};
gates.NF1 = () => {
  const re = /\.\.\.\(d\.status \? \{ kalshiStatus: String\(d\.status\)\.slice\(0, 24\) \} : \{\}\)/;
  assert.ok(re.test(live) && re.test(run), 'L1 and the second slot both keep Kalshi\'s order status');
  for (const src of [live, run]) assert.strictEqual((src.match(/kalshiStatus/g) || []).length, 1, 'written once and read nowhere in that file');
  assert.ok(/answeredAtMs: Date\.now\(\)/.test(run), 'the slot also keeps when the answer came');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
