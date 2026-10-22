'use strict';
// Self-hosted fonts (Oct 22, 2026). Consequence: the page asks no font service for anything, so a visitor's network address stays on this site, and a missing file shows up here and not as a silent fallback font.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const gates = {};

gates.FN1 = () => {
  assert.ok(!/fonts\.googleapis\.com|fonts\.gstatic\.com/.test(html), 'no call to a font service');
  const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
  const rules = [...css.matchAll(/@font-face\{[^}]*\}/g)].map((m) => m[0]);
  assert.deepStrictEqual(rules.map((r) => r.match(/font-family:'([^']+)'/)[1] + ' ' + r.match(/font-weight:([\d ]+);/)[1].trim()), ['Public Sans 400 700', 'IBM Plex Mono 400', 'IBM Plex Mono 500', 'Titan One 400'], 'every family and weight the page uses has a local rule');
  rules.forEach((r) => {
    const file = r.match(/url\(([^)]+)\)/)[1];
    assert.ok(!/^https?:/.test(file) && /^fonts\/[\w-]+\.woff2$/.test(file), file + ' is a local file');
    const buf = fs.readFileSync(path.join(root, file));
    assert.strictEqual(buf.slice(0, 4).toString('latin1'), 'wOF2', file + ' is a real woff2 file');
    assert.ok(buf.length > 5000 && buf.length < 60000, file + ' is a sensible size');
    assert.ok(/font-display:swap/.test(r), 'text shows at once in a fallback and swaps when the font arrives');
  });
  assert.ok(/<link rel="preload" href="fonts\/PublicSans-latin\.woff2" as="font" type="font\/woff2" crossorigin>/.test(html), 'the main font is preloaded (a font preload needs crossorigin even when local)');
};

gates.FN2 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(!/- fonts/.test(cfg), 'the font files are published with the site');
  const readme = fs.readFileSync(path.join(root, 'fonts', 'README.md'), 'utf8');
  assert.ok(/SIL Open Font License/.test(readme), 'the licence is recorded next to the files');
  ['PublicSans-latin.woff2', 'IBMPlexMono-400-latin.woff2', 'IBMPlexMono-500-latin.woff2', 'TitanOne-latin.woff2'].forEach((f) => assert.ok(readme.includes(f), f + ' is listed'));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
