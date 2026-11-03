'use strict';
// The low-frequency quote recorder (Nov 3, 2026, research only, RECDAILY): public GET only, no secret, writes only to the quote-data branch, driven by a watchlist file, not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'scripts', 'record_daily.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-daily.yml'), 'utf8');
const watch = JSON.parse(fs.readFileSync(path.join(root, 'kalshi-scalper', 'workers', 'RECDAILY_WATCHLIST.json'), 'utf8'));
const gates = {};
const py = (code) => execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('rd', ${JSON.stringify(path.join(root, 'scripts', 'record_daily.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${code}`], { encoding: 'utf8' });

// D1: it can never trade or sign anything, whatever it is changed into.
gates.D1 = () => {
  const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code), 'it reads Kalshi public market data');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=|data\s*=\s*b?["'{]|POST|PUT|DELETE/i.test(code), 'no key, no signing, no write call (urlopen of a bare Request is a GET)');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code), 'no account or order endpoint');
  assert.ok(!/os\.environ|getenv/.test(code), 'it reads no environment variable, so no secret');
};

// D2: the workflow pushes only the data branch, uses only the built-in token, and cannot overlap itself.
gates.D2 = () => {
  assert.ok(/cron: "7,37 \* \* \* \*"/.test(wf), 'every 30 minutes');
  assert.ok(/timeout-minutes: 15/.test(wf), 'a run is short');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/git add daily/.test(wf), 'it stages only daily/');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
  assert.ok(/cancel-in-progress: false/.test(wf), 'two runs never overlap');
  assert.ok(/workflow_dispatch/.test(wf), 'it can be started by hand');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- kalshi-scalper/.test(cfg), 'none of it is published with the site');
};

// D3: what is polled comes from the watchlist alone, and the watchlist holds no series the live bot trades.
gates.D3 = () => {
  const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
  assert.ok(!/KX[A-Z0-9]{2,}/.test(code), 'the script names no ticker of its own');
  assert.ok(watch.watch.length > 0);
  for (const e of watch.watch) assert.ok(!/15M$/.test(e.series), e.series + ' is a 15 minute series (the live bot and the other recorders cover those)');
  const tests = new Set(watch.watch.map((e) => e.test));
  for (const t of ['BARRIER1', 'NOWCAST1', 'FEDIMPL1']) assert.ok(tests.has(t), t);
  assert.ok(!tests.has('USWEEP1'), 'no favourite watch items: the owner held the favourite-and-hold ban strictly (Nov 3, 2026)');
};

// D4: a market is kept only inside its window (or when the series keeps all open markets), and the rows have one value per column.
gates.D4 = () => {
  const out = JSON.parse(py(`
cfg = {"tests": ["T"], "window_hours": 30, "keep_all_open": False}
now = 1_800_000_000
mk = lambda c: {"ticker": "A", "close_time": m.iso(c), "yes_bid_dollars": "0.9"}
row = m.quote_row(now, now, "d", "S", cfg, dict(mk(now + 3600), event_ticker="E", status="active", open_time="o"))
print(json.dumps({"n": len(m.QUOTE_COLS), "row": len(row), "in": m.wanted(mk(now + 29 * 3600), cfg, now), "far": m.wanted(mk(now + 31 * 3600), cfg, now),
  "past": m.wanted(mk(now - 3600), cfg, now), "all": m.wanted(mk(now + 20 * 86400), dict(cfg, keep_all_open=True), now), "mins": row[9]}))`));
  assert.strictEqual(out.n, out.row);
  assert.strictEqual(out.in, true); assert.strictEqual(out.far, false); assert.strictEqual(out.past, false); assert.strictEqual(out.all, true);
  assert.strictEqual(out.mins, 60);
};

// D5: a run is idempotent: the output file is named for its 30 minute slot, so a re-run of the slot replaces it.
gates.D5 = () => {
  const out = JSON.parse(py(`print(json.dumps([m.slot_of(1_800_000_000 + 1799) == m.slot_of(1_800_000_000 + 1), m.slot_of(1_800_000_000 + 1800) - m.slot_of(1_800_000_000 + 1)]))`));
  assert.deepStrictEqual(out, [true, 1800]);
  assert.ok(/daily", "quotes", day, hhmm/.test(script), 'quotes are written to a slot named file');
};

// D6: a refused read (429) is counted and ends that listing; it is never a crash and never silently dropped.
gates.D6 = () => {
  const out = JSON.parse(py(`
m._sleep = lambda x: None
m.http_get = lambda url: (429, None, "")
ms, calls, n429, bad, date = m.list_markets("S", "open")
print(json.dumps([ms, calls, n429, bad]))`));
  assert.deepStrictEqual(out, [[], 2, 2, true]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }
