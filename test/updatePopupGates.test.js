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
  assert.ok(/shwoopnet:updReload/.test(c) && /kalshiUpdateDecision\(/.test(c) && /120000/.test(html.slice(html.indexOf('function kalshiUpdateDecision'), html.indexOf('function siteUpdateModal'))), 'loop guard: a reload just made does not block again (in the decision)');
  assert.ok(!/currentUserIsAdmin|kalshiFeedOn/.test(c), 'the check is not limited to the admin or to the Bot page');
};
gates.U3 = () => {
  assert.ok(/kalshiBuildCheck\(\); setInterval\(function\(\)\{ if\(document\.visibilityState === 'visible'\)\{ kalshiBuildCheck\(\); \} \}, 300000\);/.test(html), 'the baseline is taken at load for everyone and re-checked every 5 minutes while the page is showing');
  assert.ok(/visibilitychange[\s\S]{0,200}kalshiResume\(\)/.test(html) && /pageshow/.test(html), 'it also checks when the tab or Home Screen app comes back');
};
gates.U6 = () => {
  // The owner, Oct 31, 2026: "constantly getting new version reload". Consequence: a burst of merges gives one prompt for the final version, not one per merge; a stale app is still told at once; the loop guard stays.
  const src = html.slice(html.indexOf('  function kalshiUpdateDecision(o){'), html.indexOf('  function siteUpdateModal(){'));
  const decide = new Function(src + '; return kalshiUpdateDecision;')();
  const M = 60000, base = { baseline: 'A', pending: null, loadedAt: 0, reloadedAt: 0 };
  let d = decide({ ...base, tag: 'B', now: 10 * M });
  assert.deepStrictEqual([d.action, d.pending.tag], ['wait', 'B'], 'the first sighting of a changed site waits');
  d = decide({ ...base, tag: 'C', pending: d.pending, now: 15 * M });
  assert.deepStrictEqual([d.action, d.pending.tag], ['wait', 'C'], 'a second merge five minutes later restarts the wait for the newest version instead of prompting for each');
  d = decide({ ...base, tag: 'C', pending: d.pending, now: 20 * M });
  assert.strictEqual(d.action, 'prompt', 'the same version seen again five minutes later is stable: one prompt');
  assert.strictEqual(decide({ ...base, tag: 'A', pending: { tag: 'B', since: 0 }, now: 99 * M }).pending, null, 'back to the loaded version: nothing to offer and the wait is forgotten');
  assert.strictEqual(decide({ ...base, tag: 'B', now: 7 * 3600000, loadedAt: 0 }).action, 'prompt', 'a copy loaded more than 6 hours ago is told at once');
  assert.strictEqual(decide({ ...base, tag: 'B', now: 10 * M, reloadedAt: 9.5 * M }).action, 'accept', 'a reload just made and still different is accepted, not trapped');
  const justReloaded = { ...base, reloadedAt: 20 * M, now: 25 * M, pending: { tag: 'B', since: 20 * M } };
  assert.strictEqual(decide({ ...justReloaded, tag: 'B', now: 25 * M }).action, 'wait', 'right after an update the next one waits longer (15 minutes), so an update burst never loops the owner');
  assert.strictEqual(decide({ ...justReloaded, tag: 'B', now: 36 * M }).action, 'prompt', 'and then it is offered');
  assert.strictEqual(decide({ ...base, tag: '', now: 1 }).action, 'none', 'no tag from the server: nothing');
  assert.strictEqual(decide({ ...base, baseline: null, tag: 'A', now: 1 }).action, 'accept', 'the first look at the site becomes the loaded copy');
};
let failed = 0;
for (const [name, f] of Object.entries(gates)) { try { f(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
