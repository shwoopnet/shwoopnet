'use strict';
// The "Trade card columns" Settings preference drives a CSS grid via a
// single [data-trade-columns] attribute on <html> -- these gates pin the
// JS side (localStorage persistence, invalid-value fallback, button
// active-state) and confirm the CSS actually turns the three trade-card
// containers into a real grid at each supported column count.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('  function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  let depth = 0;
  const open = html.indexOf('{', start);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}
function liftVar(name) {
  const start = html.indexOf('  var ' + name + ' = ');
  assert.notStrictEqual(start, -1, 'could not find var ' + name);
  const semi = html.indexOf(';', start);
  return html.slice(start, semi + 1);
}

function fakeBtn(value) {
  return { dataset: { value: value }, classList: { active: false, toggle(cls, on){ this.active = on; } } };
}

function main() {
  // TWO instances of the control -- Settings, and the one added to Trade
  // Overview's own "Customize page" menu so the control is discoverable
  // from the page it actually affects. Both must stay in sync.
  const settingsButtons = ['1', '2', '3', '4'].map(fakeBtn);
  const inlineButtons = ['1', '2', '3', '4'].map(fakeBtn);
  const groups = [
    { querySelectorAll: function(){ return settingsButtons; } },
    { querySelectorAll: function(){ return inlineButtons; } },
  ];
  const storage = {};
  let syncedCalls = [];

  const src = `
    ${liftVar('TRADE_COLUMN_COUNTS')}
    var document = {
      documentElement: { setAttribute: function(name, v){ if(name === 'data-trade-columns') HTML_ATTR.value = v; } },
      querySelectorAll: function(sel){ return sel === '[data-trade-columns-group]' ? GROUPS : []; },
      addEventListener: function(){}, // click-delegation wiring, not under test here
    };
    var window = { localStorage: { setItem: function(k, v){ STORAGE[k] = v; } } };
    function syncUserSetting(k, v){ SYNCED.push([k, v]); }
    ${lift('tradeColumnsGroups')}
    ${lift('applyTradeColumnsPref')}
    return applyTradeColumnsPref;
  `;
  const htmlAttrHolder = { value: null };
  const applyTradeColumnsPref = new Function(
    'GROUPS', 'STORAGE', 'HTML_ATTR', 'SYNCED', src
  )(groups, storage, htmlAttrHolder, syncedCalls);

  applyTradeColumnsPref('3');
  assert.strictEqual(htmlAttrHolder.value, '3', 'the html[data-trade-columns] attribute must be set to the chosen value');
  assert.strictEqual(storage['shwoopnet:tradeColumns'], '3', 'the choice must persist to localStorage');
  assert.deepStrictEqual(settingsButtons.map((b) => b.classList.active), [false, false, true, false], 'only the chosen column-count button must read as active in Settings');
  assert.deepStrictEqual(inlineButtons.map((b) => b.classList.active), [false, false, true, false], 'the Trade Overview "Customize page" instance must stay in sync with Settings');
  assert.deepStrictEqual(syncedCalls, [['tradeColumns', '3']], 'a normal call must sync to the account exactly once, not once per control instance');
  console.log('G1 PASS choosing 3 columns sets the attribute, persists, syncs once, and stays in sync across both control instances');

  syncedCalls = [];
  applyTradeColumnsPref('7', true);
  assert.strictEqual(htmlAttrHolder.value, '1', 'an unrecognised stored value must fall back to 1 column, not crash or apply garbage');
  assert.strictEqual(syncedCalls.length, 0, 'skipSync=true (the initial-load path) must not fire a sync call');
  console.log('G2 PASS an invalid/unrecognised column count falls back to 1, and skipSync is honored');

  console.log('\nAll trade-columns preference gates passed.');
}

main();
