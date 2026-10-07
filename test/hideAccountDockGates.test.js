'use strict';
// The "Hide account pop-up" setting is per USER: it is written to the account's settings (so it follows the user to
// another device), read back on sign-in, and starts off. A device-only switch would let the pop-up reappear on every
// new browser, which is the thing it was asked not to do.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

gates.H1 = () => {
  assert.ok(/\[data-hide-account-dock="true"\] #alpacaDock\{ display:none !important; \}/.test(html), 'the attribute hides the whole pop-up, whichever way its own code shows it');
  assert.ok(/id="hideDockToggle" role="switch" aria-checked="false"/.test(html), 'a settings switch that starts off');
};

gates.H2 = () => {
  const fn = /function applyHideDockPref\(hidden, skipSync\)\{([\s\S]*?)\n  \}/.exec(html)[1];
  assert.ok(/syncUserSetting\('hideAccountDock', hidden\)/.test(fn) && /if\(!skipSync\)/.test(fn), 'a click is saved to the account');
  assert.ok(/data-hide-account-dock/.test(fn), 'and applied to the page');
  assert.ok(/shapeUserSettings[\s\S]{0,400}/.test(html) && /hideAccountDock: s\.hideAccountDock === true,/.test(html), 'read from the account, and only a literal true hides it');
  assert.ok(/applyHideDockPref\(shaped\.hideAccountDock, true\);/.test(html), 'applied when the account loads, without writing it straight back');
  assert.ok(/hideAccountDock: hideDockToggleBtn\.getAttribute\('aria-checked'\) === 'true',/.test(html), 'a first-ever sync carries the current choice into the account');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
