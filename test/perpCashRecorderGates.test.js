'use strict';
// The perps cash price saver (Nov 6, 2026, V2's request: Yahoo keeps only about 7 days of 1 minute bars): research only. Public GETs, no secret, writes only to the data branch, stops itself.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_perps_cash.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-perps-cash.yml'), 'utf8');
const gates = {};
const py = (body) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, datetime as dt, tempfile, os, gzip
spec = importlib.util.spec_from_file_location('rc', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${body}`], { encoding: 'utf8' }).trim().split('\n').pop());

// PC1: no key, no write call, no account or order endpoint, only the two public hosts.
gates.PC1 = () => {
  const code = script.replace(/"""[\s\S]*?"""/, '').replace(/#.*$/gm, '');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2\/margin\/markets/.test(code) && /query2\.finance\.yahoo\.com/.test(code), 'the public perps list and Yahoo only');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|method\s*=\s*["'](POST|PUT|DELETE)/i.test(code), 'no key, no signing, no write call');
  assert.ok(!/\/portfolio|orders/.test(code), 'no account or order endpoint');
};

// PC2: the workflow touches only the built-in token, pushes only the data branch, never cancels a running job, is not published, and runs after the US after-hours session (Tuesday to Saturday UTC).
gates.PC2 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'only the built-in token');
  assert.ok(/git push -q origin perp-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'data branch only');
  assert.ok(/cancel-in-progress: false/.test(wf) && /permissions:\s*\n\s*contents: write/.test(wf), 'one job at a time, contents write only');
  assert.ok(/cron: "0 2,3,4 \* \* 2-6"/.test(wf), 'three starts after the US after-hours session ends (01:00 UTC), Tuesday to Saturday UTC');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'not published with the site');
};

// PC3: symbols follow the perps list: crypto skipped, equities by title (BRK.B becomes BRK-B), indexes and commodities by the fixed map, the three index futures always added, no duplicates.
gates.PC3 = () => {
  const r = py(`
mk = [{"title": "AAPL", "asset_class": "Equities"}, {"title": "BRK.B", "asset_class": "Equities"}, {"title": "AAPL", "asset_class": "Equities"}, {"title": "0.0001 BTC", "asset_class": "Crypto"}, {"title": "US Tech 100", "asset_class": "Indices"}, {"title": "US500", "asset_class": "Indices"}, {"title": "Gold", "asset_class": "Metals"}, {"title": "WTI Crude Oil", "asset_class": "Energy"}]
print(json.dumps(m.symbols_from(mk)))`);
  assert.deepStrictEqual(r, ['AAPL', 'BRK-B', '^NDX', '^GSPC', 'GC=F', 'CL=F', 'ES=F', 'NQ=F', 'RTY=F']);
};

// PC4: parsing keeps bars with a close and leaves a missing field empty; a body that is not a chart is no rows.
gates.PC4 = () => {
  const r = py(`
body = json.dumps({"chart": {"result": [{"meta": {"symbol": "AAPL"}, "timestamp": [100, 160, 220], "indicators": {"quote": [{"open": [1, None, 3], "high": [2, 2, 4], "low": [1, 1, 3], "close": [1.5, None, 3.5], "volume": [10, 20, None]}]}}]}})
print(json.dumps([m.parse_bars(body), m.parse_bars("not json"), m.parse_bars('{"chart": {"result": null}}')]))`);
  assert.deepStrictEqual(r[0], [[100, 'AAPL', 1, 2, 1, 1.5, 10], [220, 'AAPL', 3, 4, 3, 3.5, '']]);
  assert.deepStrictEqual(r[1], []);
  assert.deepStrictEqual(r[2], []);
};

// PC5: the first run asks for the 7 day backfill and later runs for 2 days; a failed symbol costs only itself; a second start the same day and a start after the stop date record nothing; too few symbols writes nothing.
gates.PC5 = () => {
  const r = py(`
d = tempfile.mkdtemp(); out = os.path.join(d, 'cash1m')
mk = lambda: [{"title": "AAPL", "asset_class": "Equities"}, {"title": "MSFT", "asset_class": "Equities"}, {"title": "NVDA", "asset_class": "Equities"}]
seen = []
def get(url):
    seen.append(url.split('/chart/')[1].split('?')[0] + ('7d' if 'range=7d' in url else '2d'))
    if 'MSFT' in url: raise RuntimeError('boom')
    sym = url.split('/chart/')[1].split('?')[0]
    return json.dumps({"chart": {"result": [{"meta": {"symbol": sym}, "timestamp": [100], "indicators": {"quote": [{"open": [1], "high": [1], "low": [1], "close": [1], "volume": [5]}]}}]}})
nosleep = lambda s: None
a = m.main(out, dt.date(2026, 11, 6), mk, get, nosleep)
rows = gzip.open(os.path.join(out, '2026-11-06.csv.gz'), 'rt').read().strip().split('\\n')
n1 = len(seen)
b = m.main(out, dt.date(2026, 11, 6), mk, get, nosleep)
c = m.main(out, dt.date(2027, 2, 27), mk, get, nosleep)
a2 = m.main(out, dt.date(2026, 11, 7), mk, get, nosleep)
rng2 = [s for s in seen[n1:] if s.endswith('2d')]
def bad(url): raise RuntimeError('down')
e = m.main(os.path.join(d, 'x'), dt.date(2026, 11, 9), mk, bad, nosleep)
print(json.dumps([a, len(rows) - 1, sorted(set(s[-2:] for s in seen[:n1])), b, c, a2, len(rng2) > 0, e, os.path.exists(os.path.join(d, 'x', '2026-11-09.csv.gz'))]))`);
  assert.strictEqual(r[0], 0, 'the first run writes');
  assert.strictEqual(r[1], 5, 'six symbols asked (three stocks and the three index futures), one failed (MSFT): five rows, the failure cost only itself');
  assert.deepStrictEqual(r[2], ['7d'], 'the first run asks for the 7 day backfill');
  assert.strictEqual(r[3], 0, 'a second start the same day does nothing');
  assert.strictEqual(r[4], 0, 'past the stop date it records nothing');
  assert.strictEqual(r[5], 0, 'the next day writes');
  assert.strictEqual(r[6], true, 'later runs ask for 2 days');
  assert.strictEqual(r[7], 1, 'with every read failing nothing is written and the run says so');
  assert.strictEqual(r[8], false, 'and no file is left behind');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
