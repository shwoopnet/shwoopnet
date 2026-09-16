'use strict';
// Requested directly: opening a Setups row's trade detail modal used to
// require landing a click on the small chevron specifically -- a target
// the width of one arrow icon on a row that otherwise looked entirely
// non-interactive. The whole card is the click target now, with a hover
// highlight as the visual cue (see .trade-block:hover), in both the
// equities and crypto Setups lists.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function functionBody(name) {
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

function main() {
  ['renderIntradayBlocks', 'renderCryptoBlocks'].forEach(function(fnName) {
    const body = functionBody(fnName);
    assert.ok(/\.trade-block\[data-symbol\]/.test(body),
      fnName + ' must wire a click listener on the whole .trade-block card, not just the chevron');
    assert.ok(/card\.addEventListener\('click', function\(\)\{ openSetupTradeModal\(card\.dataset\.symbol\); \}\)/.test(body),
      fnName + ' must open the trade modal from the card\'s own click, using its data-symbol');
    assert.ok(!/\.chevron\[data-toggle\]\)\.forEach\(function\(btn\)\{\s*\n\s*btn\.addEventListener\('click'/.test(body),
      fnName + ' must not ALSO wire a separate chevron-only click listener -- one click target, not two overlapping ones');
    console.log('PASS ' + fnName + ' wires the whole card as the click target, not just the chevron');
  });

  // The visual cue: a real :hover rule on .trade-block, not just the
  // chevron's own pre-existing one.
  assert.ok(/\.trade-block:hover\{[^}]*border-color/.test(html),
    '.trade-block itself must have a real hover treatment (border/shadow), the cue that the whole card is clickable');
  console.log('PASS .trade-block has its own hover highlight, not just the chevron');

  console.log('\nAll whole-card-click gates passed.');
}

main();
