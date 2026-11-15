// EVENT830 and CFRTIK were cut from live trading on Nov 15, 2026 (owner: the goal is five live strategies at cash profit factor 1.3 or better; both were far under it).
// The consequence: no new order for either can be sent, while an order already open still settles under its own hold-to-settlement rules instead of the 25c fallback stop a removed strategy gets.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const slot = require('../functions/kalshiSlotLib');
const root = path.join(__dirname, '..');
const run = fs.readFileSync(path.join(root, 'functions', 'kalshiSlotRunLib.js'), 'utf8');
const gates = {};

gates['NP1 production entries can name only OICORE: EVENT830 and CFRTIK send no new order'] = () => {
  assert.deepStrictEqual(slot.activeSlotStrategies().map((x) => x.id), ['OICORE']);
  assert.deepStrictEqual([...slot.SLOT_NO_NEW_ENTRIES].sort(), ['CFRTIK', 'EVENT830']);
  assert.ok(Object.isFrozen(slot.SLOT_NO_NEW_ENTRIES), 'nothing can add or remove an id at run time');
};

gates['NP2 both stay REGISTERED, so an open order keeps its hold-to-settlement rules and the exit pass and settle sweep still read them'] = () => {
  const ids = slot.SLOT_STRATEGIES.map((x) => x.id);
  assert.ok(ids.includes('EVENT830') && ids.includes('CFRTIK'));
  assert.ok(slot.SLOT_HOLD_ALLOWED.includes('EVENT830') && slot.SLOT_HOLD_ALLOWED.includes('CFRTIK'));
  assert.ok(slot.slotWatch(), 'the exit pass keeps watching');
};

gates['NP3 the engine reads the entry list for entries and the full registry for exits and the settle sweep'] = () => {
  assert.ok(/const strategies = strategiesNow\(\)/.test(run), 'entries use the active list');
  const regUses = (run.match(/const registry = registryNow\(\)/g) || []).length;
  assert.ok(regUses >= 2, 'exits and the settle sweep use the full registry (found ' + regUses + ')');
  assert.ok(/registryNow = \(\) => \(flags === undefined \? slotLib\.SLOT_STRATEGIES/.test(run));
};

gates['NP4 putting one back is a reviewed edit of one list: an id absent from it enters again'] = () => {
  const full = slot._testOnly.activeSlotStrategiesWith({ enabled: true, registry: slot.SLOT_STRATEGIES }).map((x) => x.id);
  assert.deepStrictEqual(full, ['OICORE', 'EVENT830', 'CFRTIK'], 'the flag path (tests only) still sees the whole registry');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
