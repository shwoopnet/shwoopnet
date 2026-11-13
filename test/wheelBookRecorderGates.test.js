'use strict';
// Recorder WHEELBOOK (Nov 12, 2026, research only): order books of the sports and esports markets the wheel's cards read. Public data, no secret, no order, own weekly data branch,
// stops by itself on 2027-01-31. Tennis (phase 2) is in the code and OFF.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_wheelbook.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-wheelbook.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const wfCode = wf.replace(/#[^\n]*/g, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('wb', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// WB1: public host only, no key, no auth header, GET only, no account or order path, no Firestore.
gates.WB1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)], ['https://api.elections.kalshi.com'], 'the only host is Kalshi public market data');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|\/margin/.test(code.replace(/\/orderbooks?/g, '')), 'no account, order or margin endpoint');
  assert.ok(!/firebase|firestore|admin\.initializeApp/i.test(code) && !/^\s*(from|import)\s+[^\n]*functions/m.test(script));
  const fnDir = path.join(root, 'functions');
  assert.deepStrictEqual(fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_wheelbook|record-wheelbook/.test(fs.readFileSync(path.join(fnDir, f), 'utf8'))), []);
};

// WB2: redirects are refused, urlopen is gone, a URL off the host is refused by the stream.
gates.WB2 = () => {
  assert.ok(!/urlopen/.test(code) && /_NoRedirect/.test(code) && /build_opener\(_NoRedirect\)/.test(code) && /_OPENER\.open\(/.test(code));
  const r = py(`
import threading, http.server
class T(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/a":
            self.send_response(302); self.send_header("Location", "http://127.0.0.1:%d/b" % self.server.other); self.end_headers()
        else:
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"x":"INTERNAL"}')
b = http.server.HTTPServer(("127.0.0.1", 0), T); b.other = 0
a = http.server.HTTPServer(("127.0.0.1", 0), T); a.other = b.server_address[1]
for srv in (a, b): threading.Thread(target=srv.serve_forever, daemon=True).start()
st, body, date = m.http_get("http://127.0.0.1:%d/a" % a.server_address[1])
bad = None
try: m.Stream(0.5, fetch=lambda u: (200, {}, "")).get("https://evil.example.com/x")
except AssertionError: bad = "refused"
print(json.dumps({"status": st, "body": body is not None, "bad": bad}))`);
  assert.strictEqual(r.status, 302);
  assert.strictEqual(r.body, false);
  assert.strictEqual(r.bad, 'refused');
};

// WB3: the workflow pushes only its own weekly orphan branch, with the built-in token, six tries, pinned actions, minimal permissions, never cancelling.
gates.WB3 = () => {
  assert.ok(/cron: "5,35 \* \* \* \*"/.test(wf) && /cron: "20,50 \* \* \* \*"/.test(wf) && (wf.match(/- cron:/g) || []).length === 2 && /--cycle-hours 4/.test(wf));
  assert.ok(/timeout-minutes: 330/.test(wf));
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'only the built-in token');
  assert.ok(/wheelbook-\$\(date -u \+%G\)w\$\(date -u \+%V\)/.test(wf), 'branch wheelbook-<ISO year>w<week>');
  assert.ok(/git push -q origin "\$BRANCH"/.test(wf) && !/git push[^\n]*\b(main|quote-data|nc-data)\b/.test(wfCode), 'pushes its own branch only');
  assert.ok(!/quote-data|nc-data|sports-data|kalshi-pull-data/.test(wfCode + code.replace(/#.*/g, '')), 'never touches another data branch');
  assert.ok(/git checkout -q --orphan "\$BRANCH"/.test(wf), 'created as an orphan branch');
  assert.ok(/for i in 1 2 3 4 5 6; do git push/.test(wf), 'six-try push loop');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['wheelbook'], 'adds its own folder only');
  assert.ok(/wheelbook\/\$STAMP/.test(wf) && /ref: main/.test(wf));
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n\s*actions: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and actions write only');
  assert.ok(/concurrency:\s*\n\s*group: record-wheelbook\s*\n\s*cancel-in-progress: false/.test(wf), 'a running job is never cancelled');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'actions pinned by SHA');
  assert.ok(!/pip install|npm install|curl |wget |pull_request_target/.test(wf));
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'not published with the site');
};

// WB4: it stops by itself on 2027-01-31 23:59 UTC, in the workflow's first step AND the script.
gates.WB4 = () => {
  const out = py(`print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH)]))`);
  assert.deepStrictEqual(out, ['2027-01-31T23:59:00Z', false, true]);
  assert.ok(/date -u -d '2027-01-31T23:59:00Z' \+%s/.test(wf) && /go=false/.test(wf));
  const steps = wf.split(/\n      - name: /).slice(2);
  assert.ok(steps.length === 6 && steps.every((s) => /if: "?(always\(\) && |!cancelled\(\) && )?steps\.gate\.outputs\.go == 'true'/.test(s)), 'every later step is skipped after the end date');
  assert.ok(/if past_end\(now\):\s*\n\s*print\([^\n]*\)\s*\n\s*return 0/.test(code), 'the script exits at once after the end date');
};

// WB5: phase 1 is exactly the nine series; tennis is in the code and OFF.
gates.WB5 = () => {
  const out = py(`print(json.dumps({"p1": list(m.PHASE1_SERIES), "p2": list(m.PHASE2_SERIES), "on": m.PHASE2_ENABLED, "live": list(m.SERIES),
    "tier": m.tier_for("KXITFMATCH", "KXITFMATCH-26NOV100722AB", 0, 9999999999)}))`);
  assert.deepStrictEqual(out.p1, ['KXCS2GAME', 'KXCS2MAP', 'KXCS2TOTALMAPS', 'KXDOTA2GAME', 'KXDOTA2MAP', 'KXDOTA2TOTALMAPS', 'KXESOCCERGAME', 'KXLIGAPROMATCH', 'KXEBASKETBALLGAME']);
  assert.deepStrictEqual(out.p2, ['KXITFMATCH', 'KXITFWMATCH', 'KXATPCHALLENGERMATCH', 'KXWTACHALLENGERMATCH']);
  assert.strictEqual(out.on, false, 'phase 2 is OFF');
  assert.deepStrictEqual(out.live, out.p1, 'the recorded list is phase 1 only');
  assert.strictEqual(out.tier, null, 'a tennis market is never polled while phase 2 is off');
  assert.ok(/^PHASE2_ENABLED = False/m.test(script));
  const found = [...new Set([...code.matchAll(/KX[A-Z0-9]+/g)].map((x) => x[0]))].sort();
  assert.deepStrictEqual(found, [...out.p1, ...out.p2].sort(), 'no other series in the code');
};

// WB6: the tier comes from the ticker clock (US Eastern, with daylight saving), the market's open and whether it is open, never a result.
gates.WB6 = () => {
  const out = py(`
S = m.start_epoch("KXESOCCERGAME-26NOV100722GIGIMADD")
S2 = m.start_epoch("KXCS2GAME-26AUG151900AAABBB")
t = m.tier_for
es = "KXESOCCERGAME-26NOV100722GIGIMADD"; cs = "KXCS2GAME-26NOV100722AAABBB"; mp = "KXCS2MAP-26NOV100722AAABBB-1"; lg = "KXLIGAPROMATCH-26NOV100722AAABBB"
op = S - 9000
print(json.dumps({"S": S, "S2": S2, "bad": m.start_epoch("KXFOO-NOCLOCK"),
 "es": [t("KXESOCCERGAME", es, op, op - 1), t("KXESOCCERGAME", es, op, op + 1), t("KXESOCCERGAME", es, op, S - 601), t("KXESOCCERGAME", es, op, S - 600), t("KXESOCCERGAME", es, op, S + 3000), t("KXESOCCERGAME", es, op, S + 3000, False)],
 "lg": [t("KXLIGAPROMATCH", lg, op, S - 121), t("KXLIGAPROMATCH", lg, op, S - 120)],
 "cs": [t("KXCS2GAME", cs, op, S - 2701), t("KXCS2GAME", cs, op, S - 2700), t("KXCS2GAME", cs, op, S - 1), t("KXCS2GAME", cs, op, S)],
 "map": [t("KXCS2MAP", mp, op, S - 2701), t("KXCS2MAP", mp, op, S - 2700), t("KXCS2MAP", mp, op, S + 5000)],
 "tot": t("KXCS2TOTALMAPS", "KXCS2TOTALMAPS-26NOV100722AAABBB-2", op, S), "noclock": [t("KXLIGAPROMATCH", "KXLIGAPROMATCH-X", 100, 99), t("KXLIGAPROMATCH", "KXLIGAPROMATCH-X", 100, 101)]}))`);
  assert.strictEqual(out.S, 1794313320, 'Nov 10 07:22 Eastern (standard time) is 12:22 UTC');
  assert.strictEqual(out.S2, Date.UTC(2026, 7, 15, 23, 0) / 1000, 'Aug 15 19:00 Eastern (daylight time) is 23:00 UTC');
  assert.strictEqual(out.bad, null);
  assert.deepStrictEqual(out.es, [null, 'slow', 'slow', 'fast', 'fast', null]);
  assert.deepStrictEqual(out.lg, [null, 'fast']);
  assert.deepStrictEqual(out.cs, [null, 'slow', 'slow', 'fast']);
  assert.deepStrictEqual(out.map, [null, 'slow', 'slow'], 'map markets are slow only');
  assert.strictEqual(out.tot, null, 'total-maps markets are listed, never polled');
  assert.deepStrictEqual(out.noclock, [null, 'slow'], 'no readable clock: slow from the open');
  assert.ok(!/result|settle/.test(code.slice(code.indexOf('def tier_for'), code.indexOf('def candle_start'))), 'the tier never reads a result');
};

// WB7: row-on-change as a pure function: the first look stores, an identical top 5 does not, any change in a price or size (either side) does, and an emptied book is stored.
gates.WB7 = () => {
  const out = py(`
f = m.ChangeFilter()
row = lambda yes, no: ["p", 1, 2, "d", "fast", "T"] + m.levels_cells(yes, no)
a = row([(0.9, 10), (0.89, 5)], [(0.1, 7)])
r = [f.keep("T", a), f.keep("T", row([(0.9, 10), (0.89, 5)], [(0.1, 7)])), f.keep("T", row([(0.9, 11), (0.89, 5)], [(0.1, 7)])),
     f.keep("T", row([(0.9, 11), (0.89, 5)], [(0.1, 8)])), f.keep("T", row([], [])), f.keep("T", row([], [])), f.keep("U", row([], []))]
empty = row([], [])
print(json.dumps({"r": r, "empty": empty[6:], "cols": len(m.BOOK_COLS), "n": len(a)}))`);
  assert.deepStrictEqual(out.r, [true, false, true, true, true, false, true]);
  assert.ok(out.empty.every((x) => x === ''), 'an emptied book is a row of empty levels, never zeros');
  assert.strictEqual(out.cols, out.n);
};

// WB8: a poll row is written for EVERY poll (kept or not, failed or not), with the send and receive time, Date header, tier, asked, answered and status.
gates.WB8 = () => {
  const out = py(`
import tempfile, os
class O:
    def __init__(s): s.w = {}
    def write(s, n, rows): s.w.setdefault(n, []).extend(rows)
state = m.State()
for t in ("A", "B"): state.known[t] = {"series": "KXLIGAPROMATCH", "event": "E", "open": 0, "close": None, "tally": m.Tally("KXLIGAPROMATCH", t, "E", "", "", 0, False)}
ob = lambda t: {"ticker": t, "orderbook_fp": {"yes_dollars": [["0.4000", "5.00"]], "no_dollars": [["0.5000", "9.00"]]}}
answers = [(200, {"orderbooks": [ob("A"), ob("B")]}, "Thu, 12 Nov 2026 20:00:00 GMT"), (200, {"orderbooks": [ob("A"), ob("B")]}, "d2"), (500, None, ""), (200, {"orderbooks": [ob("A")]}, "d4")]
clock = [100.0]
s = m.Stream(0.5, fetch=lambda u: answers.pop(0), clock=lambda: clock[0], sleep=lambda d: clock.__setitem__(0, clock[0] + d))
out_ = O(); flt = m.ChangeFilter(); b = m.Batching(); ids = [0, 7]
for _ in range(4): m.poll_chunk(s, state, out_, flt, b, "fast", ["A", "B"], ids, 100.0)
polls = out_.w["polls"]
print(json.dumps({"polls": polls, "book": len(out_.w["book_fast"]), "cols": m.POLL_COLS}))`);
  assert.strictEqual(out.polls.length, 4, 'one poll row per poll, even when nothing was stored and when the read failed');
  assert.strictEqual(out.book, 2, 'only the first look stored a book row for each ticker; the identical ones did not');
  assert.deepStrictEqual(out.polls.map((p) => p[7]), [200, 200, 500, 200], 'HTTP status kept');
  assert.deepStrictEqual(out.polls.map((p) => [p[5], p[6]]), [[2, 2], [2, 2], [2, 0], [2, 1]], 'asked and answered');
  assert.strictEqual(out.polls[0][3], 'Thu, 12 Nov 2026 20:00:00 GMT', 'the server Date header is kept');
  assert.ok(out.polls.every((p) => typeof p[1] === 'number' && typeof p[2] === 'number' && p[4] === 'fast'));
  assert.deepStrictEqual(out.cols, ['poll_id', 't_send_ms', 't_recv_ms', 'server_date_header', 'tier', 'tickers_asked', 'tickers_answered', 'http_status']);
  assert.ok(/out\.write\("polls"/.test(code));
};

// WB9: the read rate is bounded: 2 streams, 0.5 s between calls, a 429 waits 2 s and doubles, a hard request budget ends a run, batches are split under the cap.
gates.WB9 = () => {
  const out = py(`
calls = []; answers = [429, 429, 200]
def fake(u): st = answers.pop(0); return st, ({} if st == 200 else None), ""
clock = [0.0]
def sleep(d): calls.append(round(d, 3)); clock[0] += d
bud = [2]
s = m.Stream(0.5, fetch=fake, clock=lambda: clock[0], sleep=sleep, budget=bud)
for _ in range(3): s.get(m.BASE + "/x")
bad = None
try: m.Stream(0.4)
except AssertionError: bad = "refused"
print(json.dumps({"sleeps": calls, "n429": s.n429, "ex": s.exhausted(), "bad": bad, "gaps": [m.BOOK_GAP_S, m.HOUSE_GAP_S, m.BACKOFF_S, m.BACKOFF_MAX_S], "b": m.rate_budget(), "cap": [m.BATCH_MAX, m.REQUEST_BUDGET, m.FAST_EVERY_S, m.SLOW_EVERY_S]}))`);
  assert.deepStrictEqual(out.sleeps, [2, 4], 'a 429 waits 2 s then 4');
  assert.strictEqual(out.n429, 2);
  assert.strictEqual(out.ex, true, 'the budget is exhausted after its calls');
  assert.strictEqual(out.bad, 'refused');
  assert.ok(out.gaps[0] >= 0.5 && out.gaps[1] >= 1.5 && out.gaps[2] >= 2 && out.gaps[3] <= 30);
  assert.ok(out.cap[0] <= 100 && out.cap[1] <= 20000 && out.cap[2] === 3 && out.cap[3] === 60);
  assert.strictEqual(out.b.streams, 2);
  assert.ok(out.b.avg_per_min <= 40 && out.b.peak_per_min <= 100);
  assert.strictEqual((code.match(/\bStream\(/g) || []).length, 2, 'only two streams are made');
  assert.ok(/for i in range\(0, len\(tickers\), BATCH_MAX\)/.test(code), 'a busy hour is split into batches under the cap');
};

// WB10: candle reads and results are raw answer bodies with a manifest; the candle batches stay under the cell cap; only closed markets the recorder watched are read.
gates.WB10 = () => {
  const out = py(`
import tempfile, os, gzip
d = tempfile.mkdtemp(); r = m.RawStore(os.path.join(d, "a"))
r.save(m.BASE + "/markets?series_ticker=KXCS2GAME&status=settled&limit=1000", 200, {"markets": [{"ticker": "T", "result": ""}], "cursor": ""}, 5)
r.save(m.BASE + "/markets/candlesticks?market_tickers=A,B&start_ts=1&end_ts=2&period_interval=1", 500, None, 6)
man = json.load(open(os.path.join(d, "a", "manifest.json")))
body = json.load(gzip.open(os.path.join(d, "a", "0001.json.gz"), "rt"))
items = [("T%d" % i, 1000 + 60 * i, 1000 + 60 * i + 14400) for i in range(300)] + [("BIG", 0, 700000)]
bs = m.pack_candle_batches(items)
cells = [((b - a) / 60.0) * len(t) for t, a, b in bs]
print(json.dumps({"man": man, "body": body, "n": sum(len(t) for t, a, b in bs), "maxc": max(cells[:-1] + [0]) if False else max(c for (t, a, b), c in zip(bs, cells) if len(t) > 1), "maxt": max(len(t) for t, a, b in bs), "files": sorted(os.listdir(os.path.join(d, "a")))}))`);
  assert.deepStrictEqual(out.files, ['0001.json.gz', 'manifest.json'], 'NNNN.json.gz files and a manifest.json, a failed read has no body file');
  assert.strictEqual(out.man.files[0].file, '0001.json.gz');
  assert.strictEqual(out.man.files[0].path, '/markets');
  assert.strictEqual(out.man.files[0].params.status, 'settled');
  assert.strictEqual(out.man.files[1].file, null);
  assert.strictEqual(out.man.files[1].status, 500);
  assert.deepStrictEqual(out.body, { markets: [{ ticker: 'T', result: '' }], cursor: '' }, 'the answer is kept as given (an empty result stays empty)');
  assert.strictEqual(out.n, 301, 'every market is in exactly one batch');
  assert.ok(out.maxc <= 9000 && out.maxt <= 90, 'window minutes x tickers stays under the 10,000 limit');
  assert.ok(/market_tickers=%s&start_ts=%d&end_ts=%d&period_interval=1/.test(code));
  assert.ok(/state\.closed\[t\]/.test(code) && /c \+ CANDLE_DELAY_S/.test(code), 'only markets the recorder itself saw close, after the close');
};

// WB11: the tape is read once after each close, the cursor followed to the end, ids de-duplicated and NOT stored; coverage carries pages, trades, duplicates and the summed size beside volume.
gates.WB11 = () => {
  const out = py(`
tr = lambda i, c="2.5": {"trade_id": "id%d" % i, "ticker": "T", "created_time": "t%d" % i, "yes_price_dollars": "0.9", "count_fp": c, "taker_outcome_side": "yes", "no_price_dollars": "0.1"}
pages = [(200, {"trades": [tr(i) for i in range(1000)], "cursor": "c1"}), (429, None), (200, {"trades": [tr(999)] + [tr(i) for i in range(1000, 1500)], "cursor": "c2"}),
         (500, None), (200, {"trades": [tr(1500, "1")], "cursor": ""})]
urls = []
def fake(url):
    urls.append(url); st, body = pages.pop(0); return st, body, ""
clock = [0.0]
s = m.Stream(1.5, fetch=fake, clock=lambda: clock[0], sleep=lambda d: clock.__setitem__(0, clock[0] + d))
t = m.Tally("KXCS2GAME", "T", "E", "", "", 0, False); saved = []
ok = m.sweep_tape(s, "T", 1000, 1900, t, lambda u, st, b, tr_: saved.append(b))
t.volume, t.result = "3751", "yes"
cov = dict(zip(m.COVER_COLS, m.coverage_row(t)))
cap = m.Tally("KXCS2GAME", "T", "E", "", "", 0, False)
s2 = m.Stream(1.5, fetch=lambda u: (200, {"trades": [], "cursor": "again"}, ""), clock=lambda: 0.0, sleep=lambda d: None)
ok2 = m.sweep_tape(s2, "T", 0, 900, cap, lambda *a: None, max_pages=4)
print(json.dumps({"ok": ok, "pages": t.pages, "dupes": t.dupes, "trades": t.trades, "urls": urls, "cov": cov, "first": saved[0]["trades"][0], "text": json.dumps(saved), "cap": [ok2, cap.pages, cap.notes]}))`);
  assert.strictEqual(out.ok, true);
  assert.strictEqual(out.trades, 1501, 'a full 1,000 row page did not end the read');
  assert.strictEqual(out.dupes, 1);
  assert.strictEqual(out.pages, 3);
  assert.ok(/min_ts=1000&max_ts=1905&limit=1000$/.test(out.urls[0]) && /cursor=c1$/.test(out.urls[1]) && /cursor=c1$/.test(out.urls[2]) && /cursor=c2$/.test(out.urls[4]), 'a refused or failed page is asked again with the same cursor');
  assert.deepStrictEqual(out.first, { ticker: 'T', created_time: 't0', yes_price_dollars: '0.9', count_fp: '2.5', taker_outcome_side: 'yes' }, 'ticker, time, YES price, count, taker side');
  assert.ok(!/trade_id|"id0"|no_price/.test(out.text), 'the id is not stored');
  assert.strictEqual(out.cov.tape_trades, 1501);
  assert.strictEqual(out.cov.dupes_dropped, 1);
  assert.strictEqual(out.cov.tape_sum_count, 3751);
  assert.deepStrictEqual([out.cov.volume_fp, out.cov.result, out.cov.tape_pages], ['3751', 'yes', 3]);
  assert.deepStrictEqual(out.cap, [false, 4, ['tape page cap']], 'an endless cursor is stopped and marked');
  assert.ok(/TAPE_DELAY_S = 60/.test(code) && /tape\[t\] = max\(now, c \+ TAPE_DELAY_S\)/.test(code), 'read about 60 seconds after the close, once');
};

// WB12: the standing rule: recorder files are a FORWARD record, nothing is read back, tuned or scored in the script.
gates.WB12 = () => {
  assert.ok(!/profit|pnl|backtest|held.?out/i.test(code), 'the recorder scores and tunes nothing');
  assert.ok(/Nothing here is tuned on or read back as a result/.test(script));
};

// WB13: R6's Bitcoin and Ethereum run to Dec 31 (Nov 12, 2026, the owner).
gates.WB13 = () => {
  const r6 = fs.readFileSync(path.join(root, 'scripts', 'record_15m_book.py'), 'utf8');
  assert.ok(/^END_UTC = "2026-12-31T23:59:00Z"/m.test(r6) && /^ETH_END_UTC = "2026-12-31T23:59:00Z"/m.test(r6));
};

// WB14: a market that is no longer open is never polled again (the Nov 12, 2026 fault: the listed close was the far expiry, so settled markets were polled to it), and it is queued
// for its tape and candle reads; a half-read listing closes nothing.
gates.WB14 = () => {
  const out = py(`
S = "KXESOCCERGAME"
def mkt(t): return {"ticker": t, "event_ticker": "E", "open_time": "2026-11-12T10:00:00Z", "close_time": "2026-11-26T10:00:00Z"}
A, B = "KXESOCCERGAME-26NOV121000AAABBB", "KXESOCCERGAME-26NOV121000CCCDDD"
state = m.State()
now = m.parse_t("2026-11-12T11:00:00Z")
pages = {"open": [{"markets": [mkt(A), mkt(B)], "cursor": ""}, {"markets": [mkt(B)], "cursor": ""}, None]}
def fake(url):
    if "/markets?series_ticker=" in url and "status=open" in url:
        if "KXESOCCERGAME" in url:
            b = pages["open"].pop(0)
            return (200, b, "") if b is not None else (500, None, "")
        return 200, {"markets": [], "cursor": ""}, ""
    return 200, {"markets": []}, ""
clock = [0.0]
s = m.Stream(0.5, fetch=fake, clock=lambda: clock[0], sleep=lambda d: None)
r1 = m.discover(s, state, now * 1000, now * 1000)
w1 = sorted(state.watch(now + 3 * 3600))
r2 = m.discover(s, state, (now + 300) * 1000, (now + 300) * 1000)      # A has left the open list; its listed close is 14 days away
w2 = sorted(state.watch(now + 3 * 3600))
r3 = m.discover(s, state, (now + 600) * 1000, (now + 600) * 1000)      # a failed listing closes nothing
print(json.dumps({"r1": r1, "w1": w1, "r2": r2, "w2": w2, "r3": r3, "known": sorted(state.known), "closed": sorted(state.closed), "A": A, "B": B}))`);
  assert.deepStrictEqual(out.r1, []);
  assert.deepStrictEqual(out.w1, [out.A, out.B].sort(), 'both open markets are watched');
  assert.deepStrictEqual(out.r2, [out.A], 'a market gone from the open list is closed at once, with 14 days left on its listed close');
  assert.deepStrictEqual(out.w2, [out.B], 'a market no longer open is never polled again');
  assert.deepStrictEqual(out.r3, [], 'a listing that failed does not close anything');
  assert.deepStrictEqual(out.known, [out.B]);
  assert.deepStrictEqual(out.closed, [out.A]);
  assert.ok(!/state\.closed\[t\] = state\.known\.pop\(t\)[\s\S]{0,40}and now/.test(code) && !/t not in seen and \(m\["close"\]/.test(code), 'closing no longer waits for the listed close time');
};

// WB15: after a market leaves the open list its real close time is set (the market read's close_time if it is in the past, else the round that saw it gone), so its tape and candles are read.
gates.WB15 = () => {
  const out = py(`
now = m.parse_t("2026-11-12T11:00:00Z")
rd = lambda body, st=200: m.market_closed_at(m.Stream(0.5, fetch=lambda u: (st, body, ""), sleep=lambda d: None), "T", now)
a = rd({"market": {"status": "finalized", "close_time": "2026-11-12T10:41:00Z"}})
b = rd({"market": {"status": "finalized", "close_time": "2026-11-26T10:00:00Z"}})
c = rd(None, 500)
d = rd({"market": {"status": "open", "close_time": "2026-11-12T10:41:00Z"}})
print(json.dumps({"a": a[0] - now, "b": b[0] - now, "c": c[0] - now, "d": d[0] - now, "note": a[1]}))`);
  assert.strictEqual(out.a, -19 * 60, 'a past close_time on a not-open market is used');
  assert.strictEqual(out.b, 0, 'a future close_time is the far expiry: use the round that saw it gone');
  assert.strictEqual(out.c, 0, 'an unreadable market read falls back to the round that saw it gone');
  assert.strictEqual(out.d, 0, 'a market the read still calls open takes the discovery round');
  assert.ok(/market_closed_at\(stream, t, now\)/.test(code) && /sweep_tape\(stream, t, m\["open"\], m\["close"\], tl, raw\.save\)/.test(code), 'the tape is swept to the real close');
  assert.ok(/\[\^\\n\]*stream\.get\("%s\/markets\/%s" % \(BASE, t\)\)/.test(code) || /markets\/%s" % \(BASE, t\)/.test(code));
};

// WB16: the second look is provable per market: every poll's asked tickers are recoverable from polls_tickers.csv (the latest earlier row of the same tier and chunk).
gates.WB16 = () => {
  const out = py(`
class O:
    def __init__(s): s.w = {}
    def write(s, n, rows): s.w.setdefault(n, []).extend(rows)
state = m.State()
for t in ("A", "B", "C"): state.known[t] = {"series": "KXLIGAPROMATCH", "event": "E", "open": 0, "close": None, "tally": m.Tally("KXLIGAPROMATCH", t, "E", "", "", 0, False)}
ob = lambda t: {"ticker": t, "orderbook_fp": {"yes_dollars": [["0.4000", "5.00"]], "no_dollars": [["0.5000", "9.00"]]}}
def reply(asked): return (200, {"orderbooks": [ob(t) for t in asked]}, "d")
seq = [["A", "B"], ["A", "B"], ["A", "B"], ["B"], ["B"], ["B", "C"], ["A", "B"]]
cur = []
s = m.Stream(0.5, fetch=lambda u: reply(cur[0]), clock=lambda: 1.0, sleep=lambda d: None)
o = O(); flt = m.ChangeFilter(); b = m.Batching(); ids = [0, 7]; pids = []
for a in seq:
    cur[:] = [a]; m.poll_chunk(s, state, o, flt, b, "fast", a, ids, 100.0); pids.append("7-%d" % ids[0])
# a second chunk of a different tier does not disturb the first
cur[:] = [["C"]]; m.poll_chunk(s, state, o, flt, b, "slow", ["C"], ids, 100.0)
rows = o.w["polls_tickers"]
def asked_at(pid, tier, chunk="0"):
    n = int(pid.split("-")[1]); best = None
    for r in rows:
        if r[1] == tier and r[2] == chunk and int(r[0].split("-")[1]) <= n: best = r[3]
    return best
print(json.dumps({"rows": rows, "recovered": [asked_at(p, "fast") for p in pids], "seq": ["|".join(a) for a in seq], "cols": m.ASKED_COLS, "files": [f.name.split("/")[-1] for f in []]}))`);
  assert.deepStrictEqual(out.recovered, out.seq, 'the asked tickers of every poll are recoverable');
  assert.strictEqual(out.rows.filter((r) => r[1] === 'fast').length, 4, 'a row is written only when the asked set changes (A|B, B, B|C, A|B)');
  assert.deepStrictEqual(out.cols, ['poll_id', 'tier', 'chunk', 'tickers']);
  assert.ok(/\("polls_tickers", ASKED_COLS\)/.test(code) && /chunk=i \/\/ BATCH_MAX/.test(code), 'the file is created and each batch has its own chunk');
};

// WB17: results are also read over 48 hours at a low rate (first thing in each job, then every 6 hours), beside the 2 hour read every 10 minutes.
gates.WB17 = () => {
  const out = py(`print(json.dumps([m.RESULTS_LOOKBACK_S, m.RESULTS_EVERY_S, m.RESULTS_WIDE_LOOKBACK_S, m.RESULTS_WIDE_EVERY_S]))`);
  assert.deepStrictEqual(out, [7200, 600, 172800, 21600]);
  assert.ok(/now >= next_wide/.test(code) && /next_res = next_wide = next_clock = 0\.0|next_disc = next_res = next_wide = next_clock = 0\.0/.test(code), 'the wide read runs when the job starts');
  assert.ok(/min_close_ts=%d" % int\(now - RESULTS_WIDE_LOOKBACK_S\)/.test(code));
};

// WB14: self-chaining (Nov 12, 2026): dispatches this workflow only, on main, after the push, with no sleep; no chain for a past-end, under 2 minute or empty run; cron stays; timeout covers the longest job.
gates.WB14 = () => {
  const chain = wf.split(/\n      - name: /).pop();
  assert.ok(/^Chain the next job/.test(chain));
  assert.ok(/if: "!cancelled\(\) && steps\.gate\.outputs\.go == 'true'"/.test(chain));
  assert.ok(!/sleep /.test(chain), 'no gap: dispatched at once');
  assert.ok(/2027-01-31T23:59:00Z/.test(chain) && /-lt 120/.test(chain) && /nothing was recorded: not chaining/.test(chain), 'end date, 2 minute and empty-run guards');
  assert.ok(/RUN_START: \$\{\{ steps\.gate\.outputs\.start \}\}/.test(chain) && !/github\.run_started_at/.test(wfCode));
  assert.ok(wf.indexOf('Commit and push the data branch') < wf.indexOf('Chain the next job'), 'after the data push');
  assert.deepStrictEqual([...wf.matchAll(/gh workflow run ([^\n]+)/g)].map((x) => x[1].trim()), ['record-wheelbook.yml --ref main']);
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf));
  assert.ok(/timeout-minutes: 330/.test(wf));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
