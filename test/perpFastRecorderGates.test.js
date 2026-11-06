'use strict';
// The 30 second perps recorder (Nov 5, 2026, the owner: "Faster data, then 10 to 20 tests"): research only. Public GETs, no secret, writes only to the data branch, records only around the open and close, stops itself.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_perps_fast.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-perps-fast.yml'), 'utf8');
const gates = {};
const py = (body) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, datetime as dt, tempfile, os, gzip
spec = importlib.util.spec_from_file_location('rf', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${body}`], { encoding: 'utf8' }).trim().split('\n').pop());

// PF1: no key, no write call, no account or order endpoint; it reuses the hourly recorder's public URL and columns.
gates.PF1 = () => {
  const code = script.replace(/"""[\s\S]*?"""/, '').replace(/#.*$/gm, '');
  assert.ok(/base\.URL/.test(code) && /base\.COLUMNS/.test(code) && /base\.rows/.test(code), 'same public list and columns as record_perps.py');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|method\s*=\s*["'](POST|PUT|DELETE)/i.test(code), 'no key, no signing, no write call');
  assert.ok(!/\/portfolio|orders/.test(code), 'no account or order endpoint');
};

// PF2: the workflow touches only the built-in token, pushes only the data branch, never cancels a running job, and is not published.
gates.PF2 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'only the built-in token');
  assert.ok(/git push -q origin perp-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'data branch only');
  assert.ok(/cancel-in-progress: false/.test(wf) && /permissions:\s*\n\s*contents: write/.test(wf), 'one job at a time, contents write only');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'not published with the site');
};

// PF3: windows follow New York time (so daylight saving moves them), weekdays only.
gates.PF3 = () => {
  const r = py(`
u = dt.timezone.utc
f = lambda s: (m.current_window(dt.datetime.fromisoformat(s).replace(tzinfo=u)) or [None])[0]
print(json.dumps([f('2026-11-05T14:35:00'), f('2026-11-05T21:00:00'), f('2026-11-05T18:00:00'), f('2026-11-07T14:35:00'), f('2026-07-06T13:35:00'), f('2026-11-05T13:35:00')]))`);
  assert.deepStrictEqual(r, ['open', 'close', null, null, 'open', null], 'Nov open 14:35Z, close 21:00Z, midday no, Saturday no, July open 13:35Z (EDT), Nov 13:35Z is before the window');
};

// PF4: inside a window it records to the window end; a second start for the same window and a start after the stop date record nothing; a failed read costs one sample.
gates.PF4 = () => {
  const r = py(`
u = dt.timezone.utc
d = tempfile.mkdtemp()
clock = [dt.datetime(2026, 11, 5, 15, 29, 0, tzinfo=u)]
def now(): return clock[0]
def sleep(s): clock[0] = clock[0] + dt.timedelta(seconds=30)
calls = [0]
def fetch():
    calls[0] += 1
    if calls[0] == 2: raise RuntimeError('429')
    return [{"ticker": "KXAAPLPERP", "price": "6.9", "reference_price": {"price": "6.8"}}]
a = m.main(d, now, fetch, sleep)
p = os.path.join(d, '2026-11-05', 'open.csv.gz')
rows = gzip.open(p, 'rt').read().strip().split('\\n')
clock[0] = dt.datetime(2026, 11, 5, 15, 29, 30, tzinfo=u)
b = m.main(d, now, fetch, sleep)
clock[0] = dt.datetime(2027, 2, 27, 15, 0, 0, tzinfo=u)
c = m.main(d, now, fetch, sleep)
print(json.dumps([a, len(rows) - 1, calls[0], b, c, os.listdir(d)]))`);
  assert.strictEqual(r[0], 0);
  assert.strictEqual(r[2], 2, 'two reads in the last minute of the 10:30 ET window');
  assert.strictEqual(r[1], 1, 'one row: the failed read cost one sample, not the window');
  assert.strictEqual(r[3], 0, 'a second start for the same window does nothing');
  assert.strictEqual(r[4], 0, 'past the stop date it records nothing');
  assert.deepStrictEqual(r[5], ['2026-11-05'], 'nothing else was written');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
