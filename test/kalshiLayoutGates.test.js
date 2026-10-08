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

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
