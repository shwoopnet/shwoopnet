'use strict';
// The sign-in screen must not leave a scroll bar on the page behind it (the owner, Oct 24, 2026: "it builds a scroll bar a lot of the time and it doesnt actually scroll anything"). Consequence: while the gate is showing, the document does not
// scroll; once the gate is hidden the app scrolls as before; and the gate itself still scrolls when its own content is taller than the window.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
const gates = {};
gates.G1 = () => {
  assert.ok(/html:has\(#authGate:not\(\[hidden\]\)\), html:has\(#authGate:not\(\[hidden\]\)\) body\{ overflow:hidden; \}/.test(css), 'while the gate is showing, the page behind it does not scroll');
  assert.ok(!/(^|\n)\s*(html|body)\s*\{[^}]*overflow:\s*hidden/.test(css), 'and there is no unconditional overflow:hidden on the document, so the signed-in app still scrolls');
  assert.ok(/\.auth-gate\{[^}]*position:fixed;[^}]*overflow-y:auto/.test(css), 'the gate is a fixed layer that scrolls itself when its content is taller than the window');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
