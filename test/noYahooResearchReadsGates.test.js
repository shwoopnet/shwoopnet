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

// NY2 and NY3: the REF adapters, the REF recorder, the signal logger and the perps cash saver are gone and stay gone (a Yahoo reader would have to come back as a new file).
gates.NY2 = () => {
  for (const f of ['ref_adapters.py', 'record_ref.py', 'record_signals.py', 'record_perps_cash.py']) assert.ok(!fs.existsSync(path.join(root, 'scripts', f)), f + ' is gone');
  assert.ok(!fs.existsSync(path.join(root, '.github', 'workflows', 'record-perps-cash.yml')), 'the cash saver schedule is gone');
  const hits = scan([path.join(root, 'kalshi-scalper', 'workers', 'RECREF_WATCHLIST.json')]);
  assert.deepStrictEqual(hits, [], 'no Yahoo host in the kept watchlist: ' + hits.join(', '));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
