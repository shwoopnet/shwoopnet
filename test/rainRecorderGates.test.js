'use strict';
// Recorder RAINCAL (Oct 31, 2026, research only): Kalshi's daily rain markets (KXRAIN) next to the NWS probability of precipitation. It reads public data, holds no secret,
// places no order, sends no auth header, writes only to a data branch, is not published with the site and stops by itself on 2026-12-31.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_rain.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-rain.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, calendar
spec = importlib.util.spec_from_file_location('rr', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));

// RC1: it can never trade or sign anything, whatever it is changed into: two public hosts, one series, no auth, no write call.
gates.RC1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)].filter((h) => h !== 'https://github.com').sort(), ['https://api.weather.gov', 'https://external-api.kalshi.com'], 'the only hosts it requests are Kalshi public market data and the NWS (github.com appears only as text inside the User-Agent)');
  assert.ok((code.match(/github\.com/g) || []).length === 1 && /def user_agent[\s\S]*?github\.com\/%s/.test(code), 'and only there');
  assert.ok(!/PRIVATE|SECRET|Authorization|Bearer|ACCESS[-_]?KEY|SIGNATURE|API[-_]?KEY|TOKEN|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code), 'no account or order endpoint');
  assert.ok(/User-Agent/.test(code), 'the NWS requires a User-Agent (an identification header, not authentication)');
  assert.ok(!/os\.environ\[|getenv/.test(code) && (code.match(/os\.environ\.get\(/g) || []).length === 1 && /GITHUB_REPOSITORY/.test(code), 'the only environment variable it reads is the repository name, for the User-Agent text');
  const series = [...new Set([...code.matchAll(/KX[A-Z0-9]+/g)].map((x) => x[0]))];
  assert.deepStrictEqual(series, ['KXRAIN'], 'exactly the one rain series');
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  const mentions = fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_rain|record-rain|raincal/i.test(fs.readFileSync(path.join(fnDir, f), 'utf8')));
  assert.deepStrictEqual(mentions, [], 'nothing in functions/ mentions it');
  assert.ok(!/record_rain|record-rain|raincal/i.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
};

// RC2: the workflow pushes only the data branch, touches only the built-in token, has no inputs to carry a secret, and each job fits inside its limit.
gates.RC2 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['raincal'], 'it adds its own folder and nothing wider');
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-rain\s*\n\s*cancel-in-progress: false/.test(wf), 'one group, a running job is never cancelled, so runs never overlap');
  assert.ok(/workflow_dispatch: \{\}/.test(wf) && !/inputs:/.test(wf), 'the manual trigger takes no inputs');
  assert.ok(/timeout-minutes: 30/.test(wf), 'a short job');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'every action pinned by commit SHA');
  assert.ok(!/pip install|npm install|curl |wget /.test(wf), 'installs nothing: the script uses the standard library only');
  assert.ok(/ref: main/.test(wf) && /python3 code\/scripts\/record_rain\.py "data\/raincal\/\$STAMP"/.test(wf), 'the script comes from main, the data goes under raincal/');
  assert.ok(!/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  assert.ok(/cron: "4,24,44 11-15 \* \* \*"/.test(wf) && /cron: "14,34,54 11-15 \* \* \*"/.test(wf), 'triggered inside the 11:00 to 15:59 UTC hours when some US city is between 6:00 and 8:00 AM local standard time');
  assert.ok(/cron: "9,29,49 11-15 \* \* \*"/.test(wf), 'a third set of minutes (RECPATCH1): scheduled starts were dropped in every window for three days');
};

// RC3: neither the workflow nor the script is published with the site.
gates.RC3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither is published with the site');
};

// RC4: the built-in stop date exists, is in the future, and the script and the workflow agree on it.
gates.RC4 = () => {
  const o = py('print(json.dumps({"end": m.END_UTC, "rend": m.RESULTS_END_UTC, "e": m.END_EPOCH, "r": m.RESULTS_END_EPOCH, "before": m.past_end(m.END_EPOCH - 1), "at": m.past_end(m.END_EPOCH), "rbefore": m.results_past_end(m.RESULTS_END_EPOCH - 1), "rat": m.results_past_end(m.RESULTS_END_EPOCH)}))');
  assert.strictEqual(o.end, '2026-12-31T23:59:00Z');
  assert.strictEqual(o.rend, '2027-01-03T23:59:00Z');
  assert.ok(o.e * 1000 > Date.now(), 'the stop date is in the future (if this fails, the recorder has already stopped: extend it on purpose)');
  assert.ok(o.r > o.e, 'the results pass outlives the recording by a few days so the last market days settle');
  assert.deepStrictEqual([o.before, o.at, o.rbefore, o.rat], [false, true, false, true]);
  assert.ok(/2027-01-03T23:59:00Z/.test(wf), 'the workflow gate carries the same results end date');
};

// RC5: EVERY request goes through the backoff helper; a 429 or 503 waits 2 s, doubling to a cap, tried 4 times, never raises; the gap between calls holds.
gates.RC5 = () => {
  assert.strictEqual((code.match(/urlopen\(/g) || []).length, 1, 'one network call in the file');
  assert.ok(/def http_get[\s\S]*?urlopen\(/.test(code) && !/urlopen\(/.test(code.replace(/def http_get[\s\S]*?(?=\nclass Stream)/, '')), 'it is inside http_get');
  assert.deepStrictEqual([...code.matchAll(/\bhttp_get\(/g)].length, 2, 'http_get is defined once and called only by the Stream transport');
  assert.deepStrictEqual([...code.matchAll(/\b(?:kalshi|nws)\.get\(/g)].length >= 3, true, 'the fetch code asks through a Stream');
  const o = py(`
t = [0.0]; slept = []
def clock(): return t[0]
def sleep(s): slept.append(round(s, 3)); t[0] += s
seq = iter([429, 429, 503, 200])
calls = []
def fetch(u): calls.append(u); st = next(seq); return st, ({"ok": 1} if st == 200 else None), ""
s = m.Stream(1.0, {}, fetch=fetch, clock=clock, sleep=sleep)
r = s.get("u1")
# four failures in a row: gives up, returns a status, raises nothing
bad = m.Stream(1.5, {}, fetch=lambda u: (429, None, ""), clock=clock, sleep=sleep)
r2 = bad.get("u2")
# a dropped connection (status 0) is also retried; a 404 is returned at once
seq2 = iter([0, 404, 404]); s3 = m.Stream(1.0, {}, fetch=lambda u: (next(seq2), None, ""), clock=clock, sleep=sleep)
a = s3.get("a"); b = s3.get("b")
print(json.dumps({"r": [r[0], r[1]], "calls": len(calls), "n429": s.n429, "n503": s.n503, "req": s.requests, "slept": slept, "r2": [r2[0], r2[1]], "bad_req": bad.requests,
  "a": a[0], "b": b[0], "s3_req": s3.requests}))`);
  assert.deepStrictEqual(o.r, [200, { ok: 1 }]);
  assert.strictEqual(o.calls, 4); assert.strictEqual(o.n429, 2); assert.strictEqual(o.n503, 1);
  assert.ok(o.slept.includes(2) && o.slept.includes(4) && o.slept.includes(8), 'waits 2, 4, 8 seconds after consecutive refusals: ' + JSON.stringify(o.slept));
  assert.deepStrictEqual(o.r2, [429, null]); assert.strictEqual(o.bad_req, 4, 'gives up after 4 tries');
  assert.deepStrictEqual([o.a, o.b], [404, 404], 'a dropped connection is retried once more and a 404 is returned at once'); assert.strictEqual(o.s3_req, 3);
  assert.throws(() => py('m.Stream(0.5, {})'), /AssertionError/, 'a gap under one second is refused');
  const rb = py('print(json.dumps(m.rate_budget()))');
  assert.ok(rb.kalshi_peak_per_min <= 60 && rb.nws_peak_per_min <= 40, 'peak requests a minute: Kalshi at most 60, NWS at most 40');
};

// RC6: rows mean what the reader thinks: windows, durations, PoP periods that overlap the market day, empty (never zero) for a missing number.
gates.RC6 = () => {
  const o = py(`
close = calendar.timegm((2026, 11, 2, 5, 0, 0))            # Eastern: midnight standard time ending Nov 1
look = close - 17 * 3600
props = {"updateTime": "2026-11-01T11:09:00+00:00", "validTimes": "X", "probabilityOfPrecipitation": {"values": [
  {"validTime": "2026-10-31T13:00:00+00:00/P1DT12H", "value": 3},         # ends 2026-11-02T01:00Z: overlaps the day's end part
  {"validTime": "2026-11-02T05:00:00+00:00/PT6H", "value": 77},           # starts at the close: not in the day
  {"validTime": "2026-11-01T00:00:00+00:00/PT6H", "value": None},
  {"validTime": "2026-10-31T00:00:00+00:00/PT6H", "value": 9},            # ended before the day began
  {"validTime": "garbage", "value": 1}]}}
rows = m.pop_rows(1, "KXRAIN-26NOV01-NYC", "NYC", "KNYC", "OKX/34,45", props, close)
mk = {"ticker": "KXRAIN-26NOV01-NYC", "event_ticker": "KXRAIN-26NOV01", "close_time": "2026-11-02T05:00:00Z", "status": "active", "yes_bid_dollars": "0.0000", "yes_ask_dollars": "0.0100",
      "yes_bid_size_fp": "0.00", "yes_ask_size_fp": "27144.47", "volume_fp": "2642.12"}
q = m.quote_row(5, "Date", mk, look + 600)
print(json.dumps({"dur": [m.duration_s("PT6H"), m.duration_s("P3DT23H"), m.duration_s("P7DT12H"), m.duration_s("PT30M"), m.duration_s("P"), m.duration_s("x"), m.duration_s(None)],
  "vt": [m.parse_valid_time("2026-11-04T12:00:00+00:00/PT6H"), m.parse_valid_time("2026-11-04T12:00:00-05:00/PT6H"), m.parse_valid_time("nope")],
  "rows": rows, "ncols": len(m.POP_COLS), "q": q, "qcols": len(m.QUOTE_COLS),
  "win": [m.in_window(close, close - 18 * 3600 - 1), m.in_window(close, close - 18 * 3600), m.in_window(close, look), m.in_window(close, close - 16 * 3600), m.in_window(close, close - 16 * 3600 + 1)],
  "mfl": [m.min_from_look(close, look), m.min_from_look(close, look - 90)],
  "city": [m.city_of("KXRAIN-26NOV01-WPB"), m.city_of("KXRAIND-26NOV01-WPB"), m.city_of("KXRAIN-26NOV01"), m.city_of(None)],
  "cities": sorted(m.CITIES), "obs": m.obs_row(1, "T", "C", "S", 200, {"properties": {"timestamp": "ts", "textDescription": "Rain", "precipitationLastHour": {"value": None}}})}))`);
  assert.deepStrictEqual(o.dur, [21600, 4 * 86400 - 3600, 7 * 86400 + 12 * 3600, 1800, null, null, null]);
  assert.deepStrictEqual(o.vt[0], [Date.UTC(2026, 10, 4, 12) / 1000, Date.UTC(2026, 10, 4, 18) / 1000]);
  assert.deepStrictEqual([o.vt[1], o.vt[2]], [null, null], 'a non-UTC offset or junk is not guessed at');
  assert.strictEqual(o.rows.length, 2, 'only the periods that overlap the market day: ' + JSON.stringify(o.rows));
  assert.ok(o.rows.every((r) => r.length === o.ncols));
  assert.deepStrictEqual(o.rows.map((r) => r[10]), [3, ''], 'a missing PoP is empty, never zero');
  assert.deepStrictEqual(o.rows[0].slice(5, 8), ['2026-11-01T11:09:00+00:00', '', 'X'], 'updateTime, generatedAt (empty when NWS omits it) and validTimes ride on every row');
  assert.strictEqual(o.q.length, o.qcols);
  assert.deepStrictEqual(o.q.slice(6, 8), [10, 'active']); assert.deepStrictEqual(o.q.slice(8, 14), [0, 0.01, 0, 27144.47, '', 2642.12].map((x, i) => (i === 4 ? null : x)));
  assert.deepStrictEqual(o.win, [false, true, true, true, false], 'the window is 6:00 to 8:00 AM local standard time, ends included');
  assert.deepStrictEqual(o.mfl, [0, -1.5]);
  assert.deepStrictEqual(o.city, ['WPB', null, null, null]);
  assert.strictEqual(o.cities.length, 35, 'all 35 cities of the series from day 1 (the universe rule is applied in the analysis)');
  assert.strictEqual(o.obs[5], '', 'a missing observation number is empty');
};

// RC7: a whole pass with fake streams: only the cities whose window is open are read, a failed read is counted and never raises, the coverage row is always written.
gates.RC7 = () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rain-'));
  const o = py(`
import os, csv
close_e = calendar.timegm((2026, 11, 2, 5, 0, 0)); close_p = calendar.timegm((2026, 11, 2, 8, 0, 0))
def mk(c, close): return {"ticker": "KXRAIN-26NOV01-" + c, "event_ticker": "KXRAIN-26NOV01", "close_time": m.iso(close), "status": "active", "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.44"}
markets = [mk("NYC", close_e), mk("BOS", close_e), mk("LAX", close_p), {"ticker": "KXRAIN-26NOV01-ZZZ", "close_time": m.iso(close_e)}]
now = close_e - 17 * 3600 + 120                        # 7:02 AM Eastern; Pacific is still 4:02 AM
def kfetch(u): return 200, {"markets": markets}, "Date"
def nfetch(u):
    if "BOX/" in u: return 503, None, ""
    if "/gridpoints/" in u: return 200, {"properties": {"updateTime": "U", "probabilityOfPrecipitation": {"values": [{"validTime": m.iso(close_e - 10 * 3600).replace("Z", "+00:00") + "/PT6H", "value": 40}]}}}, ""
    return 200, {"properties": {"timestamp": "T", "textDescription": "Clear"}}, ""
t = [0.0]
def sl(s): t[0] += s
k = m.Stream(1.0, {}, fetch=kfetch, sleep=sl, clock=lambda: t[0]); n = m.Stream(1.5, {}, fetch=nfetch, sleep=sl, clock=lambda: t[0])
out = m.Out(${JSON.stringify(dir)})
cov = m.run_pass(k, n, out, now)
out.close()
rd = lambda name: list(csv.reader(open(os.path.join(${JSON.stringify(dir)}, name + ".csv"))))
print(json.dumps({"cov": cov, "quotes": rd("quotes"), "pop": rd("pop"), "obs": rd("obs"), "cover": rd("coverage"), "kreq": k.requests, "nreq": n.requests}))`);
  assert.deepStrictEqual(o.quotes.slice(1).map((r) => r[3]).sort(), ['BOS', 'NYC'], 'only the Eastern cities, only known cities; Pacific (4:02 AM) is not yet in its window');
  assert.strictEqual(o.kreq, 1, 'one list read for the whole series');
  assert.strictEqual(o.cov.listed, 4); assert.strictEqual(o.cov.in_win, 2);
  assert.ok(o.pop.slice(1).every((r) => r[2] === 'NYC'), 'the failing city (BOS, HTTP 503 after retries) has no PoP rows and is counted');
  assert.strictEqual(o.cov.gridfail, 1);
  assert.strictEqual(o.obs.length, 3, 'an observation row per city, with its HTTP status');
  assert.strictEqual(o.cover.length, 2, 'the coverage row is written');
  assert.ok(o.nreq >= 4 + 3 - 1, 'the failing city was retried through the backoff helper');
  // main() never raises and writes nothing past the end date
  const outdir = fs.mkdtempSync(path.join(os.tmpdir(), 'rain-main-'));
  const r = execFileSync('python3', ['-I', '-c', `
import importlib.util
spec = importlib.util.spec_from_file_location('rr', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.Stream.get = lambda self, url: (_ for _ in ()).throw(RuntimeError("boom"))
print(m.main([${JSON.stringify(outdir)}]))`], { encoding: 'utf8' });
  assert.ok(/recorder error \(ignored\)/.test(r) && /\n0\s*$/.test(r), 'an unexpected error is swallowed and the exit code is 0: ' + r);
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
