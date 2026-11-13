'use strict';
// Recorder OINIGHTLY (Nov 13, 2026, research only): Kalshi's public one minute candles with open interest for the 13 OICORE shadow places, one UTC day at a time. It reads one public host, holds no secret,
// places no order, sends no auth header, writes only to its own data branch, is not published with the site and stops by itself on 2026-12-31.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_oi_nightly.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-oi-nightly.yml'), 'utf8');
const hoursFixture = path.join(root, 'kalshi-scalper', 'workers', 'oicand', 'hours_fixture_MADE_UP.json');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('oi', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));

// OI1: it can never trade or sign anything: one public host, GET only, one endpoint, no auth, no order word, nothing read from the environment, no import from functions/.
gates.OI1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)].filter((h) => h !== 'https://github.com').sort(), ['https://api.elections.kalshi.com'], 'the only host it requests is Kalshi public data');
  assert.ok(/\/markets\/candlesticks\?/.test(code) && !/\/portfolio|\/orders\b|order_id|create_order|placeOrder|\/exchange\//.test(code), 'only the public candlesticks endpoint; no order or account endpoint');
  assert.ok(!/PRIVATE|SECRET|Authorization|Bearer|ACCESS[-_]?KEY|SIGNATURE|API[-_]?KEY|PASSPHRASE|TOKEN|KALSHI-ACCESS|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no write method');
  assert.ok(!/os\.environ|getenv/.test(code), 'it reads nothing from the environment');
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  const mentions = fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_oi_nightly|record-oi-nightly|oinightly/i.test(fs.readFileSync(path.join(fnDir, f), 'utf8')));
  assert.deepStrictEqual(mentions, [], 'nothing in functions/ mentions it');
  assert.ok(!/record_oi_nightly|record-oi-nightly|oinightly/i.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
};

// OI2: the workflow pushes only its own data branch, touches only the built-in token, has no inputs, never cancels a running job, is pinned, and its schedule is one run a day plus one retry.
gates.OI2 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin oi-data/.test(wf) && !/git push[^\n]*\b(main|quote-data)\b/.test(wf), 'it pushes oi-data only, never main or quote-data');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['oinightly'], 'it adds its own folder and nothing wider');
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-oi-nightly\s*\n\s*cancel-in-progress: false/.test(wf), 'one group, a running job is never cancelled');
  assert.ok(/workflow_dispatch: \{\}/.test(wf) && !/inputs:/.test(wf), 'the manual trigger takes no inputs');
  assert.ok(/timeout-minutes: 15/.test(wf), 'a short job');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'every action pinned by commit SHA');
  assert.ok(!/pip install|npm install|curl |wget /.test(wf), 'installs nothing: the script uses the standard library only');
  assert.ok(/ref: main/.test(wf) && /python3 code\/scripts\/record_oi_nightly\.py "data\/oinightly\/\$DAY" --hours code\/kalshi-scalper\/workers\/oicand\/OI_HOURS_TABLE\.json --day "\$DAY"/.test(wf), 'script and table come from main, data goes under oinightly/');
  assert.ok(/already recorded/.test(wf), 'the retry start exits at once if the day is on the data branch');
  assert.ok(!/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  assert.deepStrictEqual([...wf.matchAll(/cron: "([^"]+)"/g)].map((x) => x[1]), ['40 0 * * *', '40 6 * * *'], 'one run a day and one retry six hours later');
};

// OI3: neither the workflow nor the script is published with the site.
gates.OI3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither is published with the site');
};

// OI4: the stop date exists, is in the future, and the script and the workflow agree on it.
gates.OI4 = () => {
  const o = py('print(json.dumps({"end": m.END_UTC, "e": m.END_EPOCH, "before": m.past_end(m.END_EPOCH - 1), "at": m.past_end(m.END_EPOCH)}))');
  assert.strictEqual(o.end, '2026-12-31T23:59:00Z');
  assert.ok(o.e * 1000 > Date.now(), 'the stop date is in the future (if this fails, the recorder has already stopped: extend it on purpose)');
  assert.deepStrictEqual([o.before, o.at], [false, true]);
  assert.ok(/2026-12-31T23:59:00Z/.test(wf), 'the workflow gate carries the same end date');
};

// OI5: one network call inside http_get, redirects refused, one request stream a second apart with backoff, a hard budget, and the same constants as the generator oi_nightly_job.py.
gates.OI5 = () => {
  assert.strictEqual((code.match(/\.open\(/g) || []).length, 1, 'one network call in the file');
  assert.ok(/class _NoRedirect[\s\S]*?return None/.test(script) && /build_opener\(_NoRedirect\)/.test(code), 'a redirect is never followed');
  const o = py('print(json.dumps({"gap": m.GAP_S, "max": m.MAX_REQUESTS, "tries": m.MAX_TRIES, "b": m.BACKOFF_S, "bm": m.BACKOFF_MAX_S, "fail": m.MAX_FAIL_RUN, "ua": m.UA, "n": len(m.SERIES)}))');
  assert.ok(o.gap >= 1.0, 'at least one second between requests');
  assert.ok(o.max <= 120, 'a hard budget of 120 requests a run');
  assert.deepStrictEqual([o.tries, o.b, o.bm, o.fail], [4, 2, 30, 3]);
  assert.strictEqual(o.n, 13, 'the 13 places');
  assert.ok(!/@|\bcontact\b/i.test(o.ua['User-Agent']) && /research/.test(o.ua['User-Agent']), 'a generic User-Agent');
  const gen = fs.readFileSync(path.join(root, 'kalshi-scalper', 'workers', 'oicand', 'oi_nightly_job.py'), 'utf8');
  const arr = (s, name) => (s.match(new RegExp(name + ' = \\[([^\\]]*)\\]')) || [])[1].replace(/\s/g, '');
  assert.strictEqual(arr(script, 'SERIES'), arr(gen, 'SERIES'), 'same 13 series as the generator');
  const set = (s, name) => (s.match(new RegExp(name + ' = \\{([^}]*)\\}')) || [])[1].replace(/\s/g, '');
  assert.strictEqual(set(script, 'REL'), set(gen, 'REL'), 'same EVENT830 skip dates as the generator');
  assert.strictEqual(set(script, 'EV830'), set(gen, 'EV830'), 'same EVENT830 series as the generator');
};

// OI6: the hand case (EXPECTED_hand_nightly.md, written before the script): requests for two days, the refusals, and the parser's rows.
gates.OI6 = () => {
  const o = py(`
h = json.load(open(${JSON.stringify(hoursFixture)}))
req = lambda d: m.build_requests(d, h)
a, b = req("2026-11-17"), req("2026-11-16")
resp = {"markets": [{"market_ticker": "KXXRP15M-26NOV170830-30", "candlesticks": [
  {"end_period_ts": 1794921840, "open_interest_fp": "100.00", "volume_fp": "3.00", "price": {"open_dollars": "0.1900", "high_dollars": "0.2100", "low_dollars": "0.1900", "close_dollars": "0.2000", "mean_dollars": "0.2000", "previous_dollars": "0.1900"},
   "yes_bid": {"open_dollars": "0.1900", "high_dollars": "0.2000", "low_dollars": "0.1900", "close_dollars": "0.1900"}, "yes_ask": {"open_dollars": "0.2000", "high_dollars": "0.2200", "low_dollars": "0.2000", "close_dollars": "0.2100"}},
  {"end_period_ts": 1794921900, "volume_fp": "0.00", "price": {"close_dollars": "0.2000"}}]}]}
print(json.dumps({"a": [[x["id"], x["close"], x["tickers"], x["start_ts"], x["end_ts"]] for x in a], "b": [[x["id"], x["close"], x["tickers"]] for x in b], "n13": req("2026-11-13"), "dst": req("2027-03-14"), "ok13": req("2027-03-13"),
                  "rows": m.rows_from("2026-11-17", "2026-11-17T13:30:00Z", resp), "url": m.url_for(a[0])}))`);
  assert.deepStrictEqual(o.a, [['c0001', '2026-11-17T13:30:00Z', ['KXETH15M-26NOV170830-30', 'KXXRP15M-26NOV170830-30'], 1794921780, 1794922080], ['c0002', '2026-11-17T13:45:00Z', ['KXXRP15M-26NOV170845-45'], 1794922680, 1794922980]], 'EUR/USD is dropped at 13:30Z on a release date');
  assert.deepStrictEqual(o.b, [['c0001', '2026-11-16T13:30:00Z', ['KXETH15M-26NOV160830-30', 'KXEURUSD15M-26NOV160830-30', 'KXXRP15M-26NOV160830-30']], ['c0002', '2026-11-16T13:45:00Z', ['KXXRP15M-26NOV160845-45']]]);
  assert.strictEqual(o.n13, null, 'a day before 2026-11-14 is refused');
  assert.strictEqual(o.dst, null, 'a day on or after 2027-03-14 (daylight saving) is refused');
  assert.deepStrictEqual(o.ok13, [], '2027-03-13 is accepted (the fixture table has no Saturday hours, so no requests)');
  assert.deepStrictEqual(o.rows, [
    ['2026-11-17', '2026-11-17T13:30:00Z', 'KXXRP15M-26NOV170830-30', '1794921840', '100.00', '3.00', '0.1900', '0.2100', '0.1900', '0.2000', '0.2000', '0.1900', '0.1900', '0.2000', '0.1900', '0.1900', '0.2000', '0.2200', '0.2000', '0.2100'],
    ['2026-11-17', '2026-11-17T13:30:00Z', 'KXXRP15M-26NOV170830-30', '1794921900', '', '0.00', '', '', '', '0.2000', '', '', '', '', '', '', '', '', '', '']], 'a missing value is empty, never zero');
  assert.ok(/market_tickers=KXETH15M-26NOV170830-30,KXXRP15M-26NOV170830-30&start_ts=1794921780&end_ts=1794922080&period_interval=1$/.test(o.url));
};

// OI7: the whole run against a fake exchange: files written, coverage per request, a failed request does not end the run, three failures in a row stop asking, the script exits 0, and a refused day or a missing table writes nothing.
gates.OI7 = () => {
  const o = py(`
import tempfile, os, csv, io, contextlib
m.time.sleep = lambda s: None
resp = {"markets": [{"market_ticker": "KXXRP15M-26NOV170830-30", "candlesticks": [{"end_period_ts": 1794921840, "open_interest_fp": "100.00", "volume_fp": "3.00", "price": {"close_dollars": "0.2000"}}]}]}
calls = []
def fake(url): calls.append(url); return 200, resp
m.http_get = fake
def run(day, hours):
    d = tempfile.mkdtemp(); out = os.path.join(d, "o")
    with contextlib.redirect_stdout(io.StringIO()):
        rc = m.main([out, "--hours", hours, "--day", day])
    rd = lambda n: list(csv.reader(open(os.path.join(out, n)))) if os.path.exists(os.path.join(out, n)) else None
    return rc, rd("candles.csv"), rd("coverage.csv")
rc, cand, cov = run("2026-11-17", ${JSON.stringify(hoursFixture)})
n_ok = len(calls); calls.clear()
m.http_get = lambda url: (500, None)
rc2, cand2, cov2 = run("2026-11-17", ${JSON.stringify(hoursFixture)})
rc3, c3, v3 = run("2026-11-13", ${JSON.stringify(hoursFixture)})
rc4, c4, v4 = run("2026-11-17", "/nonexistent/hours.json")
print(json.dumps({"rc": [rc, rc2, rc3, rc4], "cand": len(cand) - 1, "cov": cov, "n_ok": n_ok, "cov2": cov2, "c3": c3, "c4": c4}))`);
  assert.deepStrictEqual(o.rc, [0, 0, 0, 0], 'the script always exits 0');
  assert.strictEqual(o.cand, 2, 'two candle rows, one per request');
  assert.deepStrictEqual(o.cov, [['day', 'close_time', 'request_id', 'tickers_asked', 'tickers_answered', 'candles', 'status', 'tries'], ['2026-11-17', '2026-11-17T13:30:00Z', 'c0001', '2', '1', '1', '200', '1'], ['2026-11-17', '2026-11-17T13:45:00Z', 'c0002', '1', '1', '1', '200', '1']]);
  assert.strictEqual(o.n_ok, 2, 'one request per close');
  assert.deepStrictEqual(o.cov2.slice(1).map((r) => [r[2], r[6]]), [['c0001', '500'], ['c0002', '500']], 'a failed request is a coverage row, not a crash');
  assert.strictEqual(o.c3, null, 'a refused day writes nothing');
  assert.strictEqual(o.c4, null, 'a missing hours table writes nothing');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
if (failed) process.exit(1);
