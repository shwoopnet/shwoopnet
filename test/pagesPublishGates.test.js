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
  assert.deepStrictEqual(published.sort(), ['404.html', 'apple-touch-icon.png', 'favicon-64.png', 'fonts', 'icon-192.png', 'icon-512.png', 'index.html', 'manifest.webmanifest', 'og-image.png', 'robots.txt', 'sw.js'], 'only the app, its own 404 page and robots.txt (Oct 22, 2026), its self-hosted fonts (Oct 22, 2026), its home screen icon and the phone alerts files (the manifest and the service worker, Oct 20, 2026), the tab icon, the two install icons and the link preview image (brand mark A, Oct 20, 2026) are published; add anything else to the exclude list in _config.yml (published now: ' + published.join(', ') + ')');
  for (const must of ['functions', 'kalshi-scalper', 'docs', 'CLAUDE.md', 'firestore.rules']) assert.ok(excluded.has(must), must + ' is not served');
  // The review notes (security, server, mutation) used to sit in the repo root with a line each in the exclude list; since Oct 21, 2026 they live under docs/reviews/, which is excluded as a whole, so a new note cannot be published by forgetting a line.
  for (const f of ['SECURITY_REVIEW.md', 'SERVER_REVIEW_2026-10-08.md', 'REVIEW_NOTES.md', 'MUTATION_NOTES.md']) assert.ok(tracked().some((t) => t.file === 'docs/reviews/' + f) && !tracked().some((t) => t.file === f), f + ' lives under docs/reviews, not the root');
};

// The home screen icon the page points to must be the file that is published, a real 180 by 180 PNG (iOS ignores SVG here and would draw a plain letter instead).
gates.P3 = () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(/<link rel="apple-touch-icon" href="apple-touch-icon\.png">/.test(html), 'the page names the icon');
  const png = fs.readFileSync(path.join(root, 'apple-touch-icon.png'));
  assert.strictEqual(png.slice(1, 4).toString(), 'PNG', 'it is a PNG');
  assert.deepStrictEqual([png.readUInt32BE(16), png.readUInt32BE(20)], [180, 180], 'at 180 by 180');
};

// Texts and chats show the link preview from og-image.png and phones install from the manifest icons, so each file must exist at the size it claims; a wrong-size file is silently cropped or ignored.
gates.P4 = () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const size = (f) => { const b = fs.readFileSync(path.join(root, f)); assert.strictEqual(b.slice(1, 4).toString(), 'PNG', f + ' is a PNG'); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
  assert.ok(html.includes('content="https://shwoopnet.github.io/og-image.png"'), 'the preview image is named by absolute address');
  assert.deepStrictEqual(size('og-image.png'), [1200, 630], 'the preview image is 1200 by 630');
  const man = JSON.parse(fs.readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'));
  for (const i of man.icons) assert.deepStrictEqual(size(i.src).join('x'), i.sizes, i.src + ' is the size the manifest claims');
  assert.deepStrictEqual(size('favicon-64.png'), [64, 64], 'the tab icon is 64 by 64');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
