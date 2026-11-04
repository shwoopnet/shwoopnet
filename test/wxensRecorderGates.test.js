'use strict';
// The ensemble temperature recorder (Nov 3, 2026, research only, WXENS1): public GET only, no secret, writes only to the quote-data branch, driven by a watchlist file, not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'scripts', 'record_wxens.py'), 'utf8');
const reader = fs.readFileSync(path.join(root, 'kalshi-scalper', 'src', 'scalper', 'wxens1.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-wxens.yml'), 'utf8');
const watch = JSON.parse(fs.readFileSync(path.join(root, 'kalshi-scalper', 'workers', 'WXENS1_WATCHLIST.json'), 'utf8'));
const strip = (s) => s.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (code) => execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rw', ${JSON.stringify(path.join(root, 'scripts', 'record_wxens.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${code}`], { encoding: 'utf8' });

// W1: it can never trade or sign anything, whatever it is changed into.
gates.W1 = () => {
  for (const [name, src] of [['recorder', script], ['reader', reader]]) {
    const code = strip(src);
    assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=|data\s*=\s*b?["'{]|POST|PUT|DELETE/i.test(code), name + ': no key, no signing, no write call');
    assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code), name + ': no account or order endpoint');
  }
  const code = strip(script);
  assert.ok(!/os\.environ|getenv/.test(code), 'the recorder reads no environment variable, so no secret');
  const hosts = new Set((code.match(/https:\/\/[a-z0-9.-]+/g) || []));
  assert.deepStrictEqual([...hosts].sort(), ['https://api.weather.gov', 'https://ensemble-api.open-meteo.com', 'https://external-api.kalshi.com', 'https://mesonet.agron.iastate.edu']);
};

// W2: the workflow pushes only the data branch, uses only the built-in token, and cannot overlap itself.
gates.W2 = () => {
  assert.ok(/cron: "12 \* \* \* \*"/.test(wf), 'hourly');
  assert.ok(/timeout-minutes: 10/.test(wf));
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/git add wxens/.test(wf), 'it stages only wxens/');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf));
  assert.ok(/cancel-in-progress: false/.test(wf) && /workflow_dispatch/.test(wf));
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- kalshi-scalper/.test(cfg), 'none of it is published with the site');
};

// W3: what is polled comes from the watchlist alone: only daily HIGH series, none a 15 minute series, 14 cities with a standard offset.
gates.W3 = () => {
  assert.ok(!/KX[A-Z0-9]{2,}/.test(strip(script)), 'the script names no ticker of its own');
  assert.strictEqual(watch.cities.length, 14);
  for (const c of watch.cities) {
    assert.ok(/^KXHIGH[A-Z]+$/.test(c.series), c.series);
    assert.ok(Number.isInteger(c.std_offset_h) && c.std_offset_h <= -5 && c.std_offset_h >= -8, c.key);
    assert.ok(Math.abs(c.lat) < 90 && Math.abs(c.lon) < 180);
  }
  assert.deepStrictEqual(watch.ensemble_models, ['gfs_seamless', 'ecmwf_ifs025', 'icon_seamless']);
  assert.deepStrictEqual(watch.due_local_hours, [7, 10]);
};

// W4: the looks follow local STANDARD time and one run makes one ensemble call; a re-run of an hour has the same slot.
gates.W4 = () => {
  const out = JSON.parse(py(`
import time
from datetime import datetime, timezone
ts = lambda s: int(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
c = {"key": "X", "std_offset_h": -6}
print(json.dumps({"a": m.due_targets(c, ts("2026-07-01 13:12"), {7, 10}), "b": m.due_targets(c, ts("2026-07-01 16:12"), {7, 10}), "c": m.due_targets(c, ts("2026-07-01 14:12"), {7, 10}),
  "s": [m.slot_of(1_800_000_000 + 3599) == m.slot_of(1_800_000_000 + 1), m.slot_of(1_800_000_000 + 3600) - m.slot_of(1_800_000_000 + 1)]}))`));
  assert.deepStrictEqual(out.a, [['L0_07', '2026-07-01'], ['L1_07', '2026-07-02']], 'in July 13:12 UTC is 07:12 STANDARD time in a UTC-6 city');
  assert.deepStrictEqual(out.b, [['L1_10', '2026-07-02']]);
  assert.deepStrictEqual(out.c, []);
  assert.deepStrictEqual(out.s, [true, 3600]);
  assert.ok(/"ens", day|os\.path\.join\(data_dir, ROOT, name, day, hh/.test(script), 'files are named for the slot');
};

// W5: a refused read (429) is counted and ends that listing; it is never a crash and never silently dropped.
gates.W5 = () => {
  const out = JSON.parse(py(`
m._sleep = lambda x: None
m.http_get = lambda url: (429, None, "")
ms, calls, n429, bad, date = m.list_markets("S", "open")
print(json.dumps([ms, calls, n429, bad]))`));
  assert.deepStrictEqual(out, [[], 2, 2, true]);
};

// W6: the reader holds the registered constants and nothing that scores before the registered read.
gates.W6 = () => {
  const code = strip(reader);
  for (const re of [/SD_F, MIN_RATIO, ASK_LO, ASK_HI, MAX_PER_DAY = 1\.5, 3\.0, 0\.03, 0\.30, 2/, /BIAS_DAYS, BIAS_MIN_DAYS, MIN_MODELS = 14, 5, 2/, /MIN_TRADES, FULL_TRADES, STOP_DATE = 150, 300, "2027-02-28"/, /PF_BAR, Z_BAR = 1\.5, 5\.27/])
    assert.ok(re.test(code), String(re));
  const count = code.slice(code.indexOf('def cmd_count'), code.indexOf('def cmd_run'));
  assert.ok(!/results_by_ticker|net_stress|verdict/.test(count), 'the count command reads no outcome');
  const reg = fs.readFileSync(path.join(root, 'kalshi-scalper', 'workers', 'WXENS1_NOTES.md'), 'utf8');
  assert.ok(/Open-Meteo/.test(reg) && /how to turn it off/i.test(reg));
};

// W7 (WXLOW1): the lows ride in the same ensemble call, every low table is named with a _low suffix beside the highs, and the lows watchlist names only KXLOWT series.
gates.W7 = () => {
  assert.ok(watch.cities.every((c) => /^KXLOWT[A-Z]+$/.test(c.low_series)), 'every city has a KXLOWT series in the watchlist');
  assert.strictEqual(new Set(watch.cities.map((c) => c.low_series)).size, 14);
  assert.ok(!/KX[A-Z0-9]{2,}/.test(strip(script)), 'the script still names no ticker');
  const code = strip(script);
  assert.ok(/daily=%s/.test(code) && /temperature_2m_max,temperature_2m_min/.test(code), 'one ensemble request carries both variables');
  assert.strictEqual((code.match(/OPENMETEO,/g) || []).length, 1, 'one ensemble call site');
  for (const t of ['ens_low', 'nws_low', 'quotes_low', 'events_low', 'results_low', 'obs_low']) assert.ok(code.includes('"' + t + '"'), t);
};

// W8 (RECPATCH1): a second hourly start (30 minutes later) must not record the same UTC hour twice: when the hour's files exist the run makes no call and logs no due city; `redo` overrides.
gates.W8 = () => {
  assert.ok(/cron: "12 \* \* \* \*"/.test(wf) && /cron: "42 \* \* \* \*"/.test(wf), 'a second trigger 30 minutes after the first');
  const out = JSON.parse(py(`
import tempfile, os
d = tempfile.mkdtemp()
calls = []
m.http_get = lambda url: (calls.append(url), (500, None, ""))[1]
m.due_targets = lambda c, now, h: [("x", "y")]
now = 1_800_000_000
day, hh = m.time.strftime("%Y-%m-%d", m.time.gmtime(now)), m.time.strftime("%H", m.time.gmtime(m.slot_of(now)))
p = os.path.join(d, "wxens", "ens", day); os.makedirs(p); open(os.path.join(p, hh + ".csv.gz"), "wb").write(b"x")
r1 = m.run(${JSON.stringify(path.join(root, 'kalshi-scalper', 'workers', 'WXENS1_WATCHLIST.json'))}, d, now=now, results=False)
n1 = len(calls)
r2 = m.run(${JSON.stringify(path.join(root, 'kalshi-scalper', 'workers', 'WXENS1_WATCHLIST.json'))}, d, now=now, results=False, redo=True)
print(json.dumps([r1[4], n1, r2[4] > 0, len(calls) > 0]))`));
  assert.deepStrictEqual(out, [0, 0, true, true]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }
