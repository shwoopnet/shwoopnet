'use strict';
// Phones (Oct 21, 2026 audit, measured on a 390px render). A finger needs 36 to 44px; the smallest controls were 19 to 26px and the bottom bar labels 9.5px. Each gate states the consequence.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '');
const gates = {};

// A button, select or switch on a phone is at least 40px tall (the switch through an invisible larger hit area), so a tap lands.
gates.M1 = () => {
  const block = /@media \(max-width:700px\)\{\s*\.kal-mini\{ min-height:40px;[\s\S]*?\n  \}/.exec(css);
  assert.ok(block, 'a phone block for control sizes exists');
  for (const sel of ['.kal-mini', '.kal-btn', 'select.kal-input', '.tf-btn', '#signOutBtn', '#resetPrefsBtn', '#kalTradeFilter']) assert.ok(block[0].includes(sel), sel + ' is sized for a thumb');
  assert.ok(/min-height:40px/.test(block[0]) && /\.settings-toggle-switch::after\{ content:''; position:absolute; inset:-10px -6px; \}/.test(block[0]), 'at least 40px, and the switch has a larger hit area');
};

// The bottom bar labels are readable (11px), not 9.5px.
gates.M2 = () => {
  assert.ok(/@media \(max-width:900px\)\{\s*\.side-nav-item\{ font-size:11px; min-width:64px; \}/.test(css), 'the bottom bar items are 11px with room for a thumb');
};

// A phone has the viewport meta, and the menus that open on it are sheets the width of the screen, not boxes anchored to a button that run off an edge.
gates.M3 = () => {
  assert.ok(/<meta name="viewport" content="width=device-width, initial-scale=1/.test(html), 'viewport meta');
  assert.ok(/\.kal-tools-body\{ position:fixed; left:12px; right:12px;/.test(css), 'the Tools menu is a full-width sheet on a phone');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
