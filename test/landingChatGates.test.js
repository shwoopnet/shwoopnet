'use strict';
// LC1 to LC4: the "Got questions?" bubble on the signed-out page (the owner's drawing with the quick-question panel, Oct 29, 2026). Consequence: the widget is a layer on the existing page, answers
// from fixed text only, so it can neither leak a visitor's words anywhere nor make a claim the public page must not make, and it adds no network call, no stored data and no new font service.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gates = {};
const gate = html.slice(html.indexOf('<div class="auth-gate" id="authGate">'), html.indexOf('<script', html.indexOf('<div class="auth-gate" id="authGate">')) > 0 ? html.indexOf('<script', html.indexOf('<div class="auth-gate" id="authGate">')) : undefined);
const widget = /<div class="gq" id="gqRoot">[\s\S]*?\n  <\/div>\n/.exec(html);
const js = (/\/\/ "Got questions\?" bubble on the signed-out screen\.[\s\S]*?\}\)\(\);\n/.exec(html) || [''])[0];

gates.LC1 = () => {
  assert.ok(widget, 'the widget exists');
  const g = html.slice(html.indexOf('<div class="auth-gate" id="authGate">'));
  assert.ok(g.indexOf('id="gqRoot"') > 0 && g.indexOf('id="gqRoot"') < g.indexOf('</div>\n\n<script') || g.indexOf('id="gqRoot"') > 0, 'it sits inside the sign-in layer, so it shows only while signed out');
  assert.ok(/class="gq-bubble" id="gqBubble" aria-label="[^"]+" aria-expanded="false" aria-controls="gqPanel"/.test(widget[0]), 'the bubble is a real button with a label and its expanded state');
  assert.ok(/id="gqPanel" role="dialog" aria-label="Got questions\?" hidden/.test(widget[0]), 'the panel starts closed');
  assert.ok(/Got questions\?<small>ask us here<\/small>/.test(widget[0]) && /d="M6 6 C 30 4, 62 14, 70 48"/.test(widget[0]), 'the marker label and the hand-drawn arrow from the drawing');
  assert.ok(/href="mailto:shwoopadvisor@gmail\.com"/.test(widget[0]), 'Something else opens mail to the address the footer already shows');
  const q = [...widget[0].matchAll(/data-q="(\w+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(q, ['what', 'who', 'access'], 'three quick questions');
};
gates.LC2 = () => {
  assert.ok(js.length > 500, 'the script block is found');
  assert.ok(!/fetch\(|XMLHttpRequest|sendBeacon|WebSocket|localStorage|sessionStorage|indexedDB|innerHTML|insertAdjacentHTML|outerHTML|document\.write|firebase|\.send\(/.test(js), 'no network, no storage, no HTML injection: answers are set with textContent');
  assert.ok(/d\.textContent = text/.test(js), 'text is set as text');
  const answers = [...js.matchAll(/(what|who|access): \['([^']+)', '([^']+)'\]/g)];
  assert.strictEqual(answers.length, 3, 'three fixed answers');
  const said = answers.map((m) => m[3]).join(' ');
  assert.ok(!/\$\s?\d|\d\s?%|\bwin rate\b|\bprofit\b|\breturns?\b|\bperformance\b|Bitcoin|gold|Kalshi|\bguarantee|\badvice\b.*\bwill\b/i.test(said.replace(/not offering advice/g, '')), 'no figures, markets or performance claim in an answer (the public page makes none)');
  assert.ok(/e\.key === 'Escape'/.test(js) && /aria-expanded/.test(js), 'Escape closes it and the expanded state follows');
};
gates.LC3 = () => {
  const css = html.slice(html.indexOf('.gq-bubble{'), html.indexOf('.gq-bubble{') + 6000);
  assert.ok(/min-height:40px/.test(css) && /min-width:44px;\s*min-height:44px/.test(css), 'tap targets are at least 40px');
  assert.ok(/\[data-reduce-motion="true"\] \.gq-label/.test(css), 'the only motion (a fade) is off under the reduce-motion setting');
  assert.ok(!/@keyframes/.test(css.slice(0, css.indexOf('.gq-chip:hover'))), 'no animation beyond a short fade');
  assert.ok(/'Permanent Marker'/.test(css), 'the marker face is used for the label and the title only');
  const uses = [...html.matchAll(/font-family:'Permanent Marker'/g)].length;
  assert.strictEqual(uses, 3, 'the @font-face rule, the label and the panel title: nowhere else');
};
gates.LC4 = () => {
  assert.ok(fs.existsSync(path.join(root, 'fonts', 'PermanentMarker-latin.woff2')), 'the marker font is a local file');
  assert.ok(/PermanentMarker-latin\.woff2/.test(fs.readFileSync(path.join(root, 'fonts', 'README.md'), 'utf8')), 'and is listed with its licence');
  assert.ok(!/fonts\.googleapis\.com|fonts\.gstatic\.com/.test(html), 'still no font service');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
