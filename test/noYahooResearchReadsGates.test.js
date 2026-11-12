'use strict';
// Nov 11, 2026 (owner): no automated reads from Yahoo on the research side. Yahoo's terms (legal.yahoo.com/us/en/yahoo/terms/otos, clauses 2(d)(9), 2(e), 2(d)(10)) forbid automated access, scraping and building databases without express permission, with no research exemption. The REF recorder's Yahoo adapter and the perps cash saver were removed; this keeps a Yahoo host from coming back unnoticed.
// functions/ (the Brief's market strip, marketTapeTick) is NOT covered here on purpose: on Nov 12, 2026 the owner chose to restore the Yahoo-based strip and accepted the terms risk knowingly (PR reverting #783). The research side stays off Yahoo.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const gates = {};
const BLOCKED = /(^|[^a-z0-9])([a-z0-9.-]*yahoo\.com|[a-z0-9.-]*yahooapis\.com)(?![a-z0-9])/i;
const list = (dir, re) => fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => re.test(f)).map((f) => path.join(dir, f)) : [];
const scan = (files) => {
  const hits = [];
  for (const f of files) fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => { if (BLOCKED.test(line)) hits.push(path.relative(root, f) + ':' + (i + 1)); });
  return hits;
};

// NY1: no workflow and no script names a Yahoo host. Comments are scanned too: a host in a comment next to code is how it starts.
gates.NY1 = () => {
  const files = [...list(path.join(root, '.github', 'workflows'), /\.ya?ml$/), ...list(path.join(root, 'scripts'), /\.(py|js|sh)$/)];
  assert.ok(files.length > 15, 'the recorder workflows and scripts are found');
  const hits = scan(files);
  assert.deepStrictEqual(hits, [], 'no Yahoo host in a workflow or script: ' + hits.join(', '));
};

// NY2: the watchlist, the REF adapters and the signal logger's allowlist and registry name none either.
gates.NY2 = () => {
  const hits = scan([
    path.join(root, 'kalshi-scalper', 'workers', 'RECREF_WATCHLIST.json'),
    path.join(root, 'scripts', 'ref_adapters.py'),
    path.join(root, 'scripts', 'record_signals.py'),
  ]);
  assert.deepStrictEqual(hits, [], 'no Yahoo host in the watchlist, adapters or signal logger: ' + hits.join(', '));
  const src = fs.readFileSync(path.join(root, 'scripts', 'record_signals.py'), 'utf8');
  const m = /ALLOWLIST\s*=\s*frozenset\(\{([\s\S]*?)\}\)/.exec(src);
  assert.ok(m, 'the allowlist is found');
  for (const h of [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1])) assert.ok(!BLOCKED.test(h), h + ' is a Yahoo host');
};

// NY3: the retired recorders stay gone.
gates.NY3 = () => {
  assert.ok(!fs.existsSync(path.join(root, '.github', 'workflows', 'record-perps-cash.yml')), 'the cash saver schedule is gone');
  assert.ok(!fs.existsSync(path.join(root, 'scripts', 'record_perps_cash.py')), 'the cash saver script is gone');
  assert.ok(!/yahoo1m|standalone_refs/.test(fs.readFileSync(path.join(root, 'scripts', 'record_ref.py'), 'utf8') + fs.readFileSync(path.join(root, 'scripts', 'ref_adapters.py'), 'utf8')), 'no Yahoo adapter or standalone reference');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
