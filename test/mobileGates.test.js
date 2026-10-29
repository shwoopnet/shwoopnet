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

// The bottom bar labels are readable (12px), not 9.5px.
gates.M2 = () => {
  assert.ok(/@media \(max-width:900px\)\{\s*\.side-nav-item\{ font-size:12px; min-width:64px; \}/.test(css), 'the bottom bar items are 12px with room for a thumb');
};

// A phone has the viewport meta, and the menus that open on it are sheets the width of the screen, not boxes anchored to a button that run off an edge.
gates.M3 = () => {
  assert.ok(/<meta name="viewport" content="width=device-width, initial-scale=1/.test(html), 'viewport meta');
  assert.ok(/\.kal-tools-body\{ position:fixed; left:12px; right:12px;/.test(css), 'the Tools menu is a full-width sheet on a phone');
};

// M4: the small tap targets found by measuring the phone layout (Oct 25, 2026). Consequence: a thumb can hit the trade list's page arrows, the Running pill, the legal line, the contact email and the Layout menu's tick boxes, and the Bot header's buttons sit on one row under the status.
// M5: found by a touch scan at 360, 390 and 430 wide (Oct 25, 2026): the bottom bar buttons were 39px and the notification panel's tabs 34px. Consequence: a thumb can hit every tab of the bar and of the panel.
gates.M5 = () => {
  assert.ok(/#kalLayoutReset\{ min-height:40px; \}/.test(css), 'the Reset layout button is 40px on a phone (found by scanning the Bot page with data, Oct 25, 2026)');
  assert.ok(/@media \(max-width: 900px\)\{[\s\S]*?\.side-nav-item\{ min-height:44px; \}/.test(css) && /max-width:900px\)\{ \.kal-notif-tabs \.kal-pill\{ min-height:40px; \}/.test(css), 'bottom bar items are 44px and the panel tabs 40px on a phone');
};
gates.M4 = () => {
  const m = /@media screen and \(max-width:700px\)\{\s*\.kal-link\{([^}]*)\}([\s\S]*?)\n  \}/.exec(css);
  assert.ok(m, 'a phone block for tap targets exists');
  assert.ok(/min-width:40px/.test(m[1]) && /min-height:40px/.test(m[1]), 'the page arrows are 40px');
  const all = m[0];
  assert.ok(/#kalL1Pill\{ min-height:40px/.test(all) && /\.site-footer summary\{ padding:12px 8px; \}/.test(all) && /\.front-foot a\{ display:inline-block; padding:12px 0; \}/.test(all), 'the Running pill, the legal line and the contact email are 40px or more');
  assert.ok(/\.kal-layout-body label\{[^}]*min-height:40px/.test(all) && /input\[type="checkbox"\]\{ width:22px; height:22px/.test(all), 'the Layout menu rows are 40px with a 22px tick box');
  assert.ok(/\.trades-header-right \.kal-status\{ flex:1 0 100%; \}/.test(all), 'the status takes its own line, so Privacy, Tools, Layout and the bell fit on one');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
