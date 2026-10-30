'use strict';
// The owner (Oct 30, 2026): "a pop-up that force logs out ... if they're on an outdated version". Chosen in the pop-up menu: block the page until they reload, and keep them signed in. Per user means per browser: each one compares its own loaded copy with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const fn = (name) => { const i = html.indexOf('  function ' + name + '('); assert.ok(i >= 0, name + ' exists'); const j = html.indexOf('\n  }\n', i); return html.slice(i, j + 4); };

gates.U1 = () => {
  const m = fn('siteUpdateModal');
  assert.ok(/role', 'alertdialog'/.test(m) && /aria-modal/.test(m), 'the pop-up is a modal alert dialog');
  assert.ok(!/close|dismiss|Escape|signOut|sign out/i.test(m.replace(/you stay signed in/g, '')), 'it has no close button and never signs anyone out');
  assert.ok(/location\.reload\(\)/.test(m), 'its one button reloads the page');
  assert.ok(/\.upd-modal\{ position:fixed; inset:0; z-index:2000/.test(html), 'it covers the whole page above everything');
  assert.ok(!/upd-bar/.test(html), 'the small pill is gone');
};
gates.U2 = () => {
  const c = fn('kalshiBuildCheck');
  assert.ok(/method: 'HEAD', cache: 'no-store'/.test(c), 'a header only check that bypasses the cache');
  assert.ok(/ae\.value/.test(c) && /INPUT/.test(c), 'it never throws away something being typed');
  assert.ok(/shwoopnet:updReload/.test(c) && /120000/.test(c), 'loop guard: a reload just made does not block again');
  assert.ok(!/currentUserIsAdmin|kalshiFeedOn/.test(c), 'the check is not limited to the admin or to the Bot page');
};
gates.U3 = () => {
  assert.ok(/kalshiBuildCheck\(\); setInterval\(function\(\)\{ if\(document\.visibilityState === 'visible'\)\{ kalshiBuildCheck\(\); \} \}, 300000\);/.test(html), 'the baseline is taken at load for everyone and re-checked every 5 minutes while the page is showing');
  assert.ok(/visibilitychange[\s\S]{0,200}kalshiResume\(\)/.test(html) && /pageshow/.test(html), 'it also checks when the tab or Home Screen app comes back');
};
let failed = 0;
for (const [name, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
