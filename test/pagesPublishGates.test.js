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
  assert.deepStrictEqual(published.sort(), ['index.html'], 'only the app is published; add anything else to the exclude list in _config.yml (published now: ' + published.join(', ') + ')');
  for (const must of ['functions', 'kalshi-scalper', 'docs', 'CLAUDE.md', 'SECURITY_REVIEW.md', 'SERVER_REVIEW_2026-10-08.md', 'firestore.rules']) assert.ok(excluded.has(must), must + ' is not served');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
