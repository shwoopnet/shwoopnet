// Two features were removed on purpose, and their tests were left behind
// asserting they still existed:
//   - desktop notifications (#195)
//   - the Labs page and its forward-test record (#208)
// Those tests failed on main for weeks, which teaches everyone to ignore a red
// suite. They are replaced by the claim that is actually true now: the
// features stay gone. If one is wanted back it should return deliberately,
// with new tests, not by reviving one of these identifiers by accident.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
// Comments may still explain the history; only code counts.
const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '').replace(/<!--[\s\S]*?-->/g, '');

const gates = {};

// Nothing may raise an OS-level notification or prompt for the permission.
gates.G1 = () => {
  assert.ok(!/new Notification\(/.test(code), 'no code may construct a browser Notification');
  assert.ok(!/Notification\.requestPermission/.test(code), 'no code may prompt for notification permission');
};

// The Labs page and its forward-test record stay gone.
gates.G2 = () => {
  assert.ok(!/id="page-labs"/.test(code), 'the Labs page must stay removed');
  ['FORWARD_TEST_STRATEGY_LABELS', 'forwardTestSnapshots'].forEach((name) =>
    assert.ok(!code.includes(name), 'removed Labs identifier is back: ' + name));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); }
  catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
