'use strict';
// The owner (Oct 30, 2026): "dont care for this running pop up style - placement". The Running pill opens a small pop-over under the pill (Pause bot, Flatten all, Rules and limits), not a card across the whole Account card covering Bot status; the status lines are in Bot status only.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
gates.R1 = () => {
  assert.ok(/\[data-card="account"\] \.kal-botmenu\{ position:relative; \}/.test(html), 'the pop-over is anchored to the pill');
  assert.ok(/\.kal-botmenu \.kal-botmenu-body\{ position:absolute; left:auto; right:0; top:calc\(100% \+ 8px\); width:340px/.test(html), 'a compact 340px pop-over directly under the pill');
  assert.ok(/max-width:900px\)\{ \.kal-console \.kal-card\[data-card="account"\] \.kal-botmenu \.kal-botmenu-body\{ width:min\(300px, calc\(100vw - 72px\)\)/.test(html), 'narrower than the screen on a phone');
};
gates.R2 = () => {
  assert.ok(/getElementById\('kalL1Status'\)\.hidden = running;/.test(html), 'the running status lines are hidden in the pop-over (Bot status has them)');
  assert.ok(/m\.open && !m\.contains\(e\.target\)\)\{ m\.open = false; \}/.test(html) && /e\.key === 'Escape'\)\{ var m = document\.getElementById\('kalBotMenu'\)/.test(html), 'it closes when you tap elsewhere or press Escape');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
