'use strict';
// Gates for what GitHub Pages publishes. Pages serves the whole repository, so a file that is not the app must be excluded in _config.yml, and a
// committed symlink that points at nothing makes the Jekyll build crash (three merges once failed to go live because of one).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const gates = {};
const tracked = () => execFileSync('git', ['ls-files', '-s'], { cwd: root, encoding: 'utf8' }).split('\n').filter(Boolean).map((l) => ({ mode: l.split(' ')[0], file: l.split('\t')[1] }));

// A symlink in the repository is a build failure waiting to happen: one to a local research folder broke the site build in seconds.
gates.P1 = () => {
  const links = tracked().filter((t) => t.mode === '120000').map((t) => t.file);
  assert.deepStrictEqual(links, [], 'no committed symlinks (Jekyll cannot resolve one that points outside the checkout): ' + links.join(', '));
};

// The site is the app. Every other top-level file or folder is excluded, so review notes, function source, rules and research are not served.
gates.P2 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  const excluded = new Set([...cfg.matchAll(/^\s*-\s+(\S+)\s*$/gm)].map((m) => m[1]));
  const top = new Set(tracked().map((t) => t.file.split('/')[0]));
  const published = [...top].filter((n) => !excluded.has(n) && !n.startsWith('.') && !n.startsWith('_'));
  assert.deepStrictEqual(published.sort(), ['apple-touch-icon.png', 'index.html'], 'only the app and its home screen icon are published; add anything else to the exclude list in _config.yml (published now: ' + published.join(', ') + ')');
  for (const must of ['functions', 'kalshi-scalper', 'docs', 'CLAUDE.md', 'SECURITY_REVIEW.md', 'SERVER_REVIEW_2026-10-08.md', 'firestore.rules']) assert.ok(excluded.has(must), must + ' is not served');
};

// The home screen icon the page points to must be the file that is published, a real 180 by 180 PNG (iOS ignores SVG here and would draw a plain letter instead).
gates.P3 = () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(/<link rel="apple-touch-icon" href="apple-touch-icon\.png">/.test(html), 'the page names the icon');
  const png = fs.readFileSync(path.join(root, 'apple-touch-icon.png'));
  assert.strictEqual(png.slice(1, 4).toString(), 'PNG', 'it is a PNG');
  assert.deepStrictEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [180, 180], 'at 180 by 180');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
