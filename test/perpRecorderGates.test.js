'use strict';
// The perps funding recorder (Oct 21, 2026): research only. It reads public data with one GET, holds no secret, writes only to a data branch, and is not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'scripts', 'record_perps.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-perps.yml'), 'utf8');
const gates = {};

gates.R1 = () => {
  const code = script.replace(/"""[\s\S]*?"""/, '').replace(/#.*$/gm, '');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2\/margin\/markets/.test(code), 'it reads the public perps list');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|method\s*=\s*["'](POST|PUT|DELETE)/i.test(code), 'no key, no signing, no write call');
  assert.ok(!/\/portfolio|orders/.test(code), 'no account or order endpoint');
};

gates.R2 = () => {
  assert.ok(/cron: "7 \* \* \* \*"/.test(wf), 'hourly');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin perp-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
};

gates.R3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither the workflow nor the script is published with the site');
};

// The row builder keeps the funding premium's inputs, handles a missing mark, and the header matches the row width.
gates.R4 = () => {
  const out = execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rp', ${JSON.stringify(path.join(root, 'scripts', 'record_perps.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
mk = [{"ticker": "KXBTCPERP", "asset_class": "Crypto", "status": "active", "bid": "1", "ask": "2", "price": "1.5", "reference_price": {"price": "1.4", "ts_ms": 1}, "settlement_mark_price": None, "open_interest": "9", "funding_cap": 0.02, "funding_deadband": 0.0001}]
r = m.rows(mk, "T")
print(json.dumps([len(m.COLUMNS), len(r[0]), r[0][m.COLUMNS.index("reference_price")], r[0][m.COLUMNS.index("settlement_mark")], r[0][m.COLUMNS.index("funding_cap")]]))
`], { encoding: 'utf8' });
  assert.deepStrictEqual(JSON.parse(out), [17, 17, '1.4', '', 0.02]);
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
