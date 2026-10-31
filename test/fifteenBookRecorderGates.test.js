'use strict';
// Recorder R6 (Oct 29, 2026, research only): the whole-window book and trade tape of the five 15 minute markets the bot trades. It reads public data, holds no secret, places no
// order, writes only to a data branch, is not published with the site and stops by itself on 2026-11-13.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_15m_book.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-15m-book.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('r6', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// FB1: it can never trade or sign anything, whatever it is changed into, and it records exactly the five series.
gates.FB1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)], ['https://external-api.kalshi.com'], 'the only host is Kalshi public market data');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code));
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code.replace(/\/orderbooks?/g, '')), 'no account or order endpoint (the public order book is not an order)');
  const series = [...new Set([...code.matchAll(/KX[A-Z0-9]+/g)].map((x) => x[0]))].sort();
  assert.deepStrictEqual(series, ['KXBTC15M', 'KXDOGE15M', 'KXETH15M', 'KXGOLD15M', 'KXXRP15M'], 'exactly the five 15 minute series, nothing else');
  assert.deepStrictEqual(py('print(json.dumps(list(m.SERIES)))'), ['KXGOLD15M', 'KXBTC15M', 'KXETH15M', 'KXDOGE15M', 'KXXRP15M']);
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  const mentions = fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_15m_book|record-15m-book/.test(fs.readFileSync(path.join(fnDir, f), 'utf8')));
  assert.deepStrictEqual(mentions, [], 'nothing in functions/ mentions it');
  assert.ok(!/record_15m_book|record-15m-book|book15r6/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
};

// FB2: the workflow pushes only the data branch, uses only the built-in token, and each job fits inside the 6 hour limit.
gates.FB2 = () => {
  assert.ok(/cron: "5,35 \* \* \* \*"/.test(wf) && /cron: "20,50 \* \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'triggered every 15 minutes (:05, :20, :35, :50), 4 hour jobs');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['book15r6'], 'it adds its own folder and nothing wider');
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-15m-book\s*\n\s*cancel-in-progress: false/.test(wf), 'one group, a running job is never cancelled, so runs never overlap');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'every action pinned by commit SHA');
  assert.ok(!/pip install|npm install|curl |wget /.test(wf), 'installs nothing: the script uses the standard library only');
  assert.ok(/ref: main/.test(wf) && /python3 code\/scripts\/record_15m_book\.py "data\/book15r6\/\$STAMP"/.test(wf));
  assert.ok(!/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
};

// FB3: neither the workflow nor the script is published with the site.
gates.FB3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither is published with the site');
};

// FB4: book rows mean what the reader thinks: best first, a missing level empty (never zero), cut to 5, times and Date kept, a missing ticker or a failed read gets no row.
gates.FB4 = () => {
  const out = py(`
deep = [["0.%02d00" % i, "%d.00" % (10 * i)] for i in range(1, 9)]
body = {"orderbooks": [
  {"ticker": "G", "orderbook_fp": {"no_dollars": [["0.4400", "590.00"], ["0.4500", "1346.93"]], "yes_dollars": deep}},
  {"ticker": "X", "orderbook_fp": {"yes_dollars": [["0.5", "1"]]}},
  {"ticker": "E", "orderbook_fp": {}}]}
mk = {"G": ("KXGOLD15M", "C"), "B": ("KXBTC15M", "C"), "E": ("KXETH15M", "C")}
rows, allp = m.batch_rows(10, 12, "Thu, 29 Oct 2026 19:09:28 GMT", mk, body)
none_rows, none_all = m.batch_rows(10, 12, "d", mk, None)
print(json.dumps({"cols": len(m.BOOK_COLS), "g": rows.get("G"), "keys": sorted(rows), "all": allp, "none": [none_rows, none_all], "url": m.batch_url(["A", "B"]),
  "single": m.book_row(1, 2, "d", "T", "S", "C", {"orderbook_fp": {"yes_dollars": [["0.1", "5"]]}}), "junk": m.book_row(1, 2, "d", "T", "S", "C", None)}))`);
  assert.strictEqual(out.cols, out.g.length, 'one value per column');
  assert.deepStrictEqual(out.g.slice(0, 6), [10, 12, 'Thu, 29 Oct 2026 19:09:28 GMT', 'G', 'KXGOLD15M', 'C'], 'send and receive time, Date header, ticker, series, close');
  assert.deepStrictEqual(out.g.slice(6, 11), [0.08, 0.07, 0.06, 0.05, 0.04], 'a deep book is cut to the best 5, best first');
  assert.deepStrictEqual(out.g.slice(11, 16), [80, 70, 60, 50, 40], 'and their sizes');
  assert.deepStrictEqual(out.g.slice(16, 21), [0.45, 0.44, '', '', ''], 'NO bids best first, a missing level empty, never zero');
  assert.deepStrictEqual(out.g.slice(21, 26), [1346.93, 590, '', '', '']);
  assert.deepStrictEqual(out.keys, ['G'], 'a ticker missing from the answer (B), one not asked for (X) and an empty book (E) get no row');
  assert.strictEqual(out.all, false, 'and the batch counts as incomplete');
  assert.deepStrictEqual(out.none, [{}, false], 'a failed read is no row');
  assert.ok(/\/markets\/orderbooks\?tickers=A&tickers=B$/.test(out.url), 'the batched read repeats tickers=');
  assert.deepStrictEqual(out.single.slice(6, 8), [0.1, ''], 'the per-market read uses the same row');
  assert.strictEqual(out.junk, null);
};

// FB5: 3 failed batches IN A ROW switch the window to one read per market; a good batch resets the count and never triggers it.
gates.FB5 = () => {
  const out = py(`
a = m.Batching(); r1 = [a.note(x) for x in (False, False, True, False, False, True, True)]
b = m.Batching(); r2 = [b.note(x) for x in (False, False, False, True)]
t = m.Tally("KXGOLD15M", "G")
print(json.dumps([r1, r2, m.coverage_row("C", t, b.fallback)[6], m.coverage_row("C", t, a.fallback)[6]]))`);
  assert.deepStrictEqual(out[0], [false, false, false, false, false, false, false], 'never three in a row: stays batched');
  assert.deepStrictEqual(out[1], [false, false, true, true], 'three in a row: falls back for the rest of the window');
  assert.deepStrictEqual(out.slice(2), [1, 0], 'batch_fallback lands in coverage');
  assert.ok(/if st != 429:\s*\n\s*win\.batching\.note/.test(code), 'a refusal (429) is not counted as a broken batched read');
};

// FB6: the tape follows the cursor until it is empty (a full 1,000 row page never ends the read), drops a repeated trade id and counts it, stores no id, and fills coverage.
gates.FB6 = () => {
  const out = py(`
tr = lambda i, c="2.5": {"trade_id": "id%d" % i, "ticker": "T", "created_time": "t%d" % i, "yes_price_dollars": "0.9", "count_fp": c, "taker_outcome_side": "yes", "no_price_dollars": "0.1"}
pages = [(200, {"trades": [tr(i) for i in range(1000)], "cursor": "c1"}), (429, None), (200, {"trades": [tr(999)] + [tr(i) for i in range(1000, 1500)], "cursor": "c2"}),
         (500, None), (200, {"trades": [tr(1500, "1")], "cursor": ""})]
urls = []
def fake(url):
    urls.append(url); st, body = pages.pop(0); return st, body, ""
clock = [0.0]
s = m.Stream(1.0, fetch=fake, clock=lambda: clock[0], sleep=lambda d: clock.__setitem__(0, clock[0] + d))
t = m.Tally("KXBTC15M", "T"); got = []
ok = m.sweep_tape(s, "T", 1000, 1900, t, got.extend)
t.volume, t.result = "3751", "yes"
row = m.coverage_row("C", t, False)
print(json.dumps({"ok": ok, "rows": len(got), "first": got[0], "pages": t.pages, "dupes": t.dupes, "trades": t.trades, "sum": t.sum_count, "urls": urls, "n429": s.n429,
  "cov": dict(zip(m.COVER_COLS, row)), "cols": m.TRADE_COLS}))`);
  assert.strictEqual(out.ok, true);
  assert.strictEqual(out.rows, 1501, 'a 1,000 row page did not end the read: every unique trade is written');
  assert.strictEqual(out.dupes, 1, 'the trade repeated across a page edge is written once and counted');
  assert.strictEqual(out.pages, 3);
  assert.ok(/min_ts=1000&max_ts=1905&limit=1000$/.test(out.urls[0]) && /cursor=c1$/.test(out.urls[1]) && /cursor=c1$/.test(out.urls[2]) && /cursor=c2$/.test(out.urls[4]),
    'the whole window plus 5 seconds; a refused or failed page is asked again with the same cursor');
  assert.deepStrictEqual(out.first, ['T', 't0', '0.9', '2.5', 'yes'], 'price, size, taker side and exchange time as returned');
  assert.deepStrictEqual(out.cols, ['ticker', 'created_time', 'yes_price_dollars', 'count_fp', 'taker_outcome_side'], 'no trade_id column');
  assert.ok(!JSON.stringify(out.first).includes('id0'), 'the id is not stored');
  assert.strictEqual(out.cov.tape_trades, 1501);
  assert.strictEqual(out.cov.dupes_dropped, 1);
  assert.strictEqual(out.cov.tape_sum_count, 3751, 'the summed size sits next to the exchange volume, so a short tape shows as a number');
  assert.deepStrictEqual([out.cov.volume_fp, out.cov.result, out.cov.tape_pages], ['3751', 'yes', 3]);
  const cap = py(`
def fake(url): return 200, {"trades": [], "cursor": "again"}, ""
s = m.Stream(1.0, fetch=fake, clock=lambda: 0.0, sleep=lambda d: None)
t = m.Tally("KXBTC15M", "T")
print(json.dumps([m.sweep_tape(s, "T", 0, 900, t, lambda r: None, max_pages=4), t.pages, t.notes]))`);
  assert.deepStrictEqual(cap, [false, 4, ['tape page cap']], 'an endless cursor is stopped and the tape marked, never silently cut');
};

// FB7: back to back jobs leave no gap and never share a window; the last sweep finishes inside the job.
gates.FB7 = () => {
  const H = 3600, D = 4 * H, T0 = 1793318400; // 2026-10-30 00:00 UTC, a 4 hour boundary
  const out = py(`
D = ${D}; T0 = ${T0}
b1 = m.cycle_boundary(T0 + 3 * 3600 + 50 * 60, D)
c1 = m.owned_closes(T0 + 3 * 3600 + 50 * 60, b1)
s1 = m.job_stop(c1[-1])
b2 = m.cycle_boundary(s1 + 60, D)
c2 = m.owned_closes(s1 + 60, b2)
print(json.dumps({"b": [m.cycle_boundary(T0 + 3 * 3600 + 50 * 60, D) - T0, m.cycle_boundary(T0 + 3 * 3600 + 20 * 60, D) - T0, m.cycle_boundary(T0 + 4 * 3600 + 5 * 60, D) - T0],
  "c1": [c1[0] - T0, c1[-1] - T0, len(c1)], "s1": s1 - c1[-1], "c2first": c2[0] - c1[-1], "overlap": len(set(c1) & set(c2)),
  "maxrun": max(m.job_stop(m.cycle_boundary(T0 + x, D)) - (T0 + x) for x in range(0, D, 60)),
  "budget": m.SWEEP_DELAY_S + m.SWEEP_BUDGET_S}))`);
  assert.deepStrictEqual(out.b, [8 * H, 4 * H, 8 * H], 'started under 30 minutes before a boundary: runs to the one after; otherwise to the next one');
  assert.deepStrictEqual(out.c1, [4 * H, 8 * H, 17], 'every window closing up to and including the boundary');
  assert.strictEqual(out.s1, 600, 'the job stops 10 minutes after its last close, when that window\'s tape has been read');
  assert.strictEqual(out.c2first, 900, 'the next job starts at the very next window: nothing falls between them');
  assert.strictEqual(out.overlap, 0, 'a window belongs to exactly one job');
  assert.ok(out.maxrun <= 4.7 * H, 'a job never runs past about 4.7 hours, inside the 330 minute limit');
  assert.ok(/sleep_until\(pending\.close \+ SWEEP_DELAY_S\)\s*\n\s*finish_window\(house, pending, out, min\(stop_at/.test(code), 'the last sweep is bounded by the job\'s stop');
};

// FB8: the read rate is bounded: 2 streams, at least 0.5 s between calls, a 429 waits at least 2 s and doubles, and is never asked again at once.
gates.FB8 = () => {
  const out = py(`
b = m.rate_budget()
calls = []
answers = [429, 429, 429, 200, 429]
def fake(url): st = answers.pop(0); return st, ({} if st == 200 else None), ""
clock = [0.0]
def sleep(d): calls.append(round(d, 3)); clock[0] += d
s = m.Stream(0.5, fetch=fake, clock=lambda: clock[0], sleep=sleep)
for _ in range(5): s.get("u")
bad = None
try: m.Stream(0.4)
except AssertionError: bad = "refused"
print(json.dumps({"b": b, "sleeps": calls, "n429": s.n429, "gaps": [m.BOOK_GAP_S, m.HOUSE_GAP_S, m.BACKOFF_S, m.BACKOFF_MAX_S, m.BOOK_EVERY_S], "bad": bad}))`);
  assert.strictEqual(out.b.streams, 2);
  assert.ok(out.b.avg_per_min <= 40, 'about 35 public reads a minute on average: ' + out.b.avg_per_min);
  assert.ok(out.b.peak_per_min <= 100, 'at most 100 a minute at the peak: ' + out.b.peak_per_min);
  assert.deepStrictEqual(out.sleeps, [2, 4, 8, 0.5], 'a 429 waits 2 s, then 4, then 8; a good answer resets the wait and the next call keeps the 0.5 s gap');
  assert.strictEqual(out.n429, 4, 'every refusal is counted');
  assert.ok(out.gaps[0] >= 0.5 && out.gaps[1] >= 0.5 && out.gaps[2] >= 2 && out.gaps[3] <= 30 && out.gaps[4] === 2);
  assert.strictEqual(out.bad, 'refused', 'a stream faster than 0.5 s between calls cannot be made');
  assert.strictEqual((code.match(/\bStream\(/g) || []).length, 2, 'only two streams are made');
  assert.ok(!/time\.sleep\(0(\.0+)?\)|while True:\s*\n\s*http_get/.test(code));
};

// FB9: a window with no good poll still gets a coverage row; gold not trading is said, not silent.
gates.FB9 = () => {
  const out = py(`
w = m.Window(1793318400)
w.tally["KXGOLD15M"].notes.append("no open market")
rows = [m.coverage_row(w.close_time, w.tally[s], w.batching.fallback) for s in m.SERIES]
print(json.dumps({"n": len(rows), "w": len(m.COVER_COLS), "g": dict(zip(m.COVER_COLS, rows[0]))}))`);
  assert.strictEqual(out.n, 5, 'one row per series per window, whatever happened');
  assert.strictEqual(out.w, 18);
  assert.deepStrictEqual([out.g.series, out.g.polls, out.g.ok_polls, out.g.note], ['KXGOLD15M', 0, 0, 'no open market']);
  assert.ok(/out\.write\("coverage", \[coverage_row\(win\.close_time, win\.tally\[s\], win\.batching\.fallback\) for s in SERIES\]\)/.test(code), 'every series is written, found or not');
};

// FB10: it stops by itself after 14 days, in the workflow and in the script.
gates.FB10 = () => {
  const out = py(`print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH), len(m.owned_closes(m.END_EPOCH - 1800, m.END_EPOCH + 7200))]))`);
  assert.deepStrictEqual(out, ['2026-11-13T23:59:00Z', false, true, 3], 'no window opening at or after the end is recorded (the last one opens at 23:45 and closes at midnight)');
  assert.ok(/date -u -d '2026-11-13T23:59:00Z' \+%s/.test(wf) && /go=false/.test(wf), 'the workflow checks the end date first');
  const steps = wf.split(/\n      - name: /).slice(2);
  assert.ok(steps.length === 4 && steps.every((s) => /if: (always\(\) && )?steps\.gate\.outputs\.go == 'true'/.test(s)), 'every later step is skipped after the end date');
  assert.ok(/if past_end\(now\):\s*\n\s*print\([^\n]*\)\s*\n\s*return 0/.test(code), 'the script exits at once after the end date');
};

// FB11: R6 replaces R2: the old 15 minute recorder is gone, so the same markets are never read twice.
gates.FB11 = () => {
  assert.ok(!fs.existsSync(path.join(root, '.github', 'workflows', 'record-book15.yml')) && !fs.existsSync(path.join(root, 'scripts', 'record_book15.py')));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
