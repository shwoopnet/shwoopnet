'use strict';
// Bot tab layout: the latest five trades with a button for more, and cards that can be rearranged only on request.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

gates.Y1 = () => {
  assert.ok(/var kalshiLiveShow = \{ events: 12, fills: 5 \};/.test(html), 'the trades card opens on the latest five');
  assert.ok(/data-more="fills">Show more/.test(html) && /data-less="fills">Show fewer/.test(html), 'with a way to see more and to go back');
  assert.ok(/data-less'\) === 'fills'\)\{ kalshiLiveShow\.fills = 5;/.test(html), 'show fewer returns to five');
};

gates.Y2 = () => {
  const iife = html.slice(html.indexOf("var KEY = 'kalBotLayout'"), html.indexOf("document.getElementById('kalLayoutReset')"));
  assert.ok(/id="kalLayoutUnlock"/.test(html) && !/id="kalLayoutUnlock"[^>]*checked/.test(html), 'rearranging starts locked');
  assert.ok(!/unlock/.test(/function save\(skipSync\)\{([\s\S]*?)\n    \}/.exec(iife)[1]), 'the unlocked state is never saved, so a normal visit cannot be dragged by accident');
  assert.ok(/e\.target\.closest\(\x27\[data-card\]\x27\)/.test(iife) && /grid\.classList\.contains\('kal-unlocked'\)/.test(iife), 'dragging does nothing while locked');
  assert.ok(/draggable = on/.test(iife) && /data-move/.test(iife), 'cards are draggable only when unlocked, with arrows for touch screens');
  assert.ok(/DEFAULT_ORDER\.indexOf\(k\) > -1/.test(iife), 'an unknown card name in a saved order is ignored');
  assert.ok(/DEFAULT_ORDER\.forEach\(function\(k\)\{ if\(want\.indexOf\(k\) < 0\)/.test(iife), 'a card the saved order does not mention keeps its place');
  assert.ok(!/OPTIONAL = \[[^\]]*'account'/.test(html), 'the account and session cards still cannot be hidden, only moved');
};

gates.Y3 = () => {
  assert.ok(/if\(skipSync !== true && typeof syncUserSetting === 'function'\)\{ syncUserSetting\('kalBotLayout', layout, 300\); \}/.test(html), 'every change is saved to the account unless it just came from there');
  assert.ok(/kalBotLayout: \(s\.kalBotLayout && typeof s\.kalBotLayout === 'object'\) \? s\.kalBotLayout : null,/.test(html), 'and read back, only if it is an object');
  assert.ok(/window\.__kalBotLayout\.set\(shaped\.kalBotLayout\)/.test(html), 'applied on sign-in');
  assert.ok(/layout = next; apply\(\); save\(true\);/.test(html), 'without writing it straight back');
  assert.ok(/\['auto', '1', '2', '3', '4'\]\.indexOf\(String\(l\.cols\)\)/.test(html), 'a bad saved column count cannot get through');
};

// A drag must keep reordering when the pointer is in a gap between cards or over its own preview, and every dragover must accept the
// drop, or some browsers stop part way (a faded card that never makes way).
gates.Y4 = () => {
  const iife = html.slice(html.indexOf("var KEY = 'kalBotLayout'"), html.indexOf("document.getElementById('kalLayoutReset')"));
  const over = /grid\.addEventListener\('dragover', function\(e\)\{([\s\S]*?)\n    \}\);/.exec(iife)[1];
  assert.ok(/e\.preventDefault\(\);/.test(over) && over.indexOf('e.preventDefault()') < over.indexOf('cardNear('), 'every dragover accepts the drop before anything else');
  assert.ok(/function cardNear\(x, y\)/.test(iife) && /if\(c === dragging\)\{ return; \}/.test(iife), 'the nearest other card is used when the pointer is in a gap');
  assert.ok(/dropEffect = 'move'/.test(over) && /grid\.addEventListener\('dragenter'/.test(iife), 'a move is announced on enter and over');
};

// The live books sit in a column right after the trade history (so they land beside it on a wide screen), not in a full-width row
// underneath, and their five figures wrap two across so they fit a column.
gates.Y5 = () => {
  const i = html.indexOf('id="kalTabBot"');
  const order = [...html.slice(i, i + 12000).matchAll(/<div class="([^"]*)" data-card="(\w+)"/g)].map((m) => [m[2], m[1]]);
  const names = order.map((o) => o[0]);
  assert.ok(names.indexOf('books') === names.indexOf('trades') + 1, 'books come straight after trades: ' + names.join(','));
  assert.ok(!/kal-span/.test(order.find((o) => o[0] === 'books')[1]), 'the books card is a column, not a full-width row');
  assert.ok(/\.kal-bot-grid \.kal-books \.kal-row\{ grid-template-columns:1fr 1fr; \}/.test(html), 'each market wraps two figures across inside the column');
  assert.ok(/data-card="account"/.test(html) && /data-card="session"/.test(html), 'the halt and stop cards are still there');
};

// The account re-sends its saved layout on every update to the user document. It must not undo a drag in progress, or a move that has not
// reached the account yet (the card would snap straight back), and a copy it already applied is not applied again.
gates.Y6 = () => {
  const set = /set: function\(l\)\{([\s\S]*?)\n      \}\n    \};/.exec(html)[1];
  assert.ok(/var key = JSON\.stringify\(l\);\s*if\(key === lastRemote\)\{ return; \}/.test(set), 'a copy already applied is not applied again');
  assert.ok(/if\(dragging \|\| Date\.now\(\) - localDirtyAt < 4000\)\{ return; \}/.test(set), 'ignored during a drag and just after our own change');
  assert.ok(/lastRemote = key;/.test(set) && set.indexOf('lastRemote = key') > set.indexOf('localDirtyAt'), 'only a copy that was actually applied is remembered');
  assert.ok(/if\(skipSync !== true\)\{ localDirtyAt = Date\.now\(\); \}/.test(html), 'our own changes mark the layout as ahead of the account');
  assert.ok(/kal-unlocked > \.kal-card\{[^}]*user-select:none/.test(html), 'text inside a card cannot be picked up instead of the card');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
