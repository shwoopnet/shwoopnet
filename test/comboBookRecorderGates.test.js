'use strict';
// Combo book recorder (Nov 12, 2026, research only): quotes, order book depth and trades of Kalshi combo markets with any posted price, so a paper test of buying NO on them can be priced with real depth.
// It reads public data, holds no secret, places no order, writes no Firestore, writes only to its own combo-data branch, is not published with the site and stops by itself on 2027-01-31.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_combo.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-combo.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('cr', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// CB1: it can never trade or sign anything; the one host is Kalshi's public market data; GET only.
gates.CB1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)], ['https://external-api.kalshi.com']);
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code));
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE|PATCH)|data\s*=\s*b?["']|os\.environ|getenv/i.test(code), 'no key, no auth header, no signing, no write call, no environment secret');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|batched/.test(code), 'no account or order endpoint');
  assert.ok(!/firebase|firestore|admin\.initializeApp/i.test(code));
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script));
  const urls = [...code.matchAll(/"(%s\/[^"]*)"/g)].map((x) => x[1]);
  assert.ok(urls.length >= 2 && urls.every((u) => /^%s\/markets/.test(u)), 'only /markets endpoints are built: ' + urls.join(' | '));
  for (const f of fs.readdirSync(path.join(root, 'functions')).filter((f) => f.endsWith('.js'))) assert.ok(!/record_combo|record-combo|combo-data/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')), f);
  assert.ok(!/record_combo|record-combo|combo-data/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8').replace(/<li>[^\n]*<\/li>/g, '')), 'only the changelog line may name it');
};

// CB2: no redirect is followed, the User-Agent is plain and honest (no browser string, no contact).
gates.CB2 = () => {
  assert.ok(!/urlopen/.test(code) && /build_opener\(_NoRedirect\)/.test(code) && /_OPENER\.open\(/.test(code));
  assert.deepStrictEqual(py('print(json.dumps(m.UA))'), { 'User-Agent': 'shwoopnet-research-recorder' });
  assert.ok(!/Mozilla|Chrome|Safari|@|mailto/.test(script.match(/UA = .*/)[0]));
  const r = py(`
import threading, http.server
class T(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/a":
            self.send_response(302); self.send_header("Location", "http://127.0.0.1:%d/b" % self.server.other); self.end_headers()
        else:
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"x":1}')
b = http.server.HTTPServer(("127.0.0.1", 0), T); b.other = 0
a = http.server.HTTPServer(("127.0.0.1", 0), T); a.other = b.server_address[1]
for srv in (a, b): threading.Thread(target=srv.serve_forever, daemon=True).start()
st, body, date = m.http_get("http://127.0.0.1:%d/a" % a.server_address[1])
print(json.dumps({"status": st, "body": body is not None}))`);
  assert.deepStrictEqual(r, { status: 302, body: false });
};

// CB3: the workflow pushes only its own data branch with the built-in token, never main; minimal permissions; pinned actions; not published with the site.
gates.CB3 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf));
  assert.ok(/git push -q origin combo-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf));
  assert.ok(!/quote-data|nc-data|pol-data|perp-data|sports-data/.test(wf.replace(/#[^\n]*/g, '')), 'it never touches the other data branches');
  assert.ok(/git fetch -q --depth 1 origin combo-data; then git checkout -q -b combo-data FETCH_HEAD; else git checkout -q --orphan combo-data/.test(wf));
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['combo']);
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n\s*actions: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and actions write (the chain dispatch), nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-combo\s*\n\s*cancel-in-progress: false/.test(wf));
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)));
  assert.ok(!/pip install|npm install|curl |wget /.test(wf) && !/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  assert.ok(/ref: main/.test(wf) && /record_combo\.py "data\/combo\/\$STAMP"/.test(wf));
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- docs/.test(cfg), 'workflow, script and docs are not published with the site');
  assert.ok(/timeout-minutes: (\d+)/.test(wf) && Number(wf.match(/timeout-minutes: (\d+)/)[1]) <= 75, 'a stuck job is cut off');
};

// CB4: it stops by itself on 2027-01-31, in the workflow and in the script.
gates.CB4 = () => {
  assert.deepStrictEqual(py('print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH)]))'), ['2027-01-31T23:59:00Z', false, true]);
  assert.ok(/date -u -d '2027-01-31T23:59:00Z' \+%s/.test(wf) && /go=false/.test(wf));
  const steps = wf.split(/\n      - name: /).slice(2);
  assert.ok(steps.length === 6 && steps.every((s) => /if: "?(always\(\) && |!cancelled\(\) && )?steps\.gate\.outputs\.go == 'true'/.test(s)));
  assert.ok(/if past_end\(time\.time\(\)\):\s*\n\s*print\([^\n]*\)\s*\n\s*return 0/.test(code));
};

// CB5: a 429 backs off (doubling, capped); three in a row stop the run early and it stays stopped; the budget is hard; a non-object body is no answer, never an error.
gates.CB5 = () => {
  const out = py(`
clock = [1000.0]; slept = []
def sl(d): slept.append(d); clock[0] += d
s = m.Stream(50, fetch=lambda u: (429, None, ""), clock=lambda: clock[0], sleep=sl)
sts = [s.get("u")[0] for _ in range(5)]
s2 = m.Stream(50, fetch=lambda u: (429, None, "") if s2_n[0] < 2 else (200, {}, "D"), clock=lambda: clock[0], sleep=sl); s2_n = [0]
def f2(u):
    s2_n[0] += 1
    return (429, None, "") if s2_n[0] <= 2 else (200, {}, "D")
s2.fetch = f2
r2 = [s2.get("u")[0] for _ in range(4)]
s3 = m.Stream(2, fetch=lambda u: (200, {}, ""), clock=lambda: clock[0], sleep=sl)
st3 = [s3.get("u")[0] for _ in range(3)]
bad = []
for body in (["list"], "text", None, {"markets": "nope"}, {"markets": None}):
    s4 = m.Stream(10, fetch=lambda u, b=body: (200, b, ""), clock=lambda: clock[0], sleep=sl)
    bad.append(m.list_combos(s4, "open", 3)[4])
print(json.dumps({"sts": sts, "stopped": s.stopped, "calls": s.calls, "r2": r2, "s2stopped": s2.stopped, "st3": st3, "bad": bad, "gap": m.GAP_S, "bo": [m.BACKOFF_S, m.BACKOFF_MAX_S], "slept": slept[:2]}))`);
  assert.deepStrictEqual(out.sts, [429, 429, 429, -2, -2], 'three refusals in a row stop the run');
  assert.strictEqual(out.calls, 3, 'no request is sent after the stop');
  assert.deepStrictEqual(out.r2, [429, 429, 200, 200], 'two refusals then an answer carries on');
  assert.strictEqual(out.s2stopped, false);
  assert.deepStrictEqual(out.st3, [200, 200, -1], 'the request budget is hard');
  assert.deepStrictEqual(out.bad, [false, false, false, false, false]);
  assert.ok(out.gap >= 6 && out.bo[0] >= 5 && out.bo[1] <= 60);
  assert.deepStrictEqual(out.slept, [5, 10], 'the wait doubles');
};

// CB6: bounded requests per run: the constants cap one run at 90 requests, 6 seconds apart (at most 10 a minute), and a run can never ask for more than its caps.
gates.CB6 = () => {
  const c = py('print(json.dumps({"budget": m.BUDGET, "pages": m.MAX_LIST_PAGES, "books": m.MAX_BOOKS, "settled": m.SETTLED_PAGES, "gap": m.GAP_S, "rows": m.MAX_QUOTE_ROWS}))');
  assert.ok(c.pages + c.books + c.settled <= c.budget, 'the caps add up to no more than the budget (Nov 13: no trade reads here any more, record_combo_tape.py reads the combo tape)');
  assert.ok(c.budget <= 100 && 60 / c.gap <= 10);
  const perDay = 48 * c.budget;
  assert.ok(perDay <= 4320, 'at most 4,320 requests a day');
  assert.ok(c.rows <= 500);
  assert.ok(/\*\/30|"11,41 \* \* \* \*"/.test(wf), 'two starts an hour, no more');
  // a fake exchange with 5 full pages of combos: one poll stays inside the caps
  const out = py(`
import tempfile, os
mk = lambda i: {"ticker": "KXMVE-%d" % i, "event_ticker": "E", "exchange_index": 1, "close_time": "2026-11-20T00:00:00Z", "yes_bid_dollars": "0.4000", "yes_ask_dollars": "0.4500", "volume_fp": "10.00"}
urls = []
def fake(u):
    urls.append(u)
    if "/orderbook" in u: return 200, {"orderbook_fp": {"yes_dollars": [["0.3900", "5.00"], ["0.4000", "7.00"]], "no_dollars": [["0.5500", "9.00"]]}}, "D"
    if "/trades" in u: return 200, {"trades": [{"trade_id": "t1", "ticker": "KXMVE-1", "created_time": "x", "yes_price_dollars": "0.4", "count_fp": "1.00", "taker_outcome_side": "yes"}]}, "D"
    return 200, {"markets": [mk(len(urls) * 1000 + i) for i in range(1000)], "cursor": "c%d" % len(urls)}, "D"
s = m.Stream(m.BUDGET, fetch=fake, clock=lambda: 0.0, sleep=lambda d: None)
d = tempfile.mkdtemp()
cov = m.poll(s, 1.0e9 + 3600, d)
print(json.dumps({"calls": s.calls, "cov": cov, "books": sum("/orderbook" in u for u in urls), "trades": sum("/trades" in u for u in urls), "lists": sum("/markets?" in u for u in urls), "files": sorted(os.listdir(d)),
  "q": len(open(os.path.join(d, "quotes.csv")).read().splitlines())}))`);
  assert.ok(out.calls <= c.budget);
  assert.strictEqual(out.lists, c.pages);
  assert.strictEqual(out.books, c.books);
  assert.strictEqual(out.trades, 0, 'no trade reads (Nov 13, 2026)');
  assert.strictEqual(out.q - 1, c.rows, 'quote rows are capped');
  assert.deepStrictEqual(out.files, ['books.csv', 'quotes.csv']);
};

// CB7: any combo with a posted bid or ask at any price on the yes or the no side, or any volume, is kept (widened Nov 12, 2026); an empty side (bid 0, ask 1.0000) is not a price; the order is
// tightest yes spread first, then volume, then ticker.
gates.CB7 = () => {
  const out = py(`
mk = lambda t, b, a, v="0.00", nb=None, na=None: dict({"ticker": t, "yes_bid_dollars": b, "yes_ask_dollars": a, "volume_fp": v}, **({"no_bid_dollars": nb} if nb is not None else {}), **({"no_ask_dollars": na} if na is not None else {}))
ms = [mk("CHEAP5", "0.0000", "0.0500"), mk("ONLYNOBID", "0.0000", "1.0000", "0.00", "0.6000", "1.0000"), mk("EMPTY", "0.0000", "1.0000", "0.00", "0.0000", "1.0000"), mk("TIGHT", "0.5000", "0.5100"),
      mk("WIDE", "0.1000", "0.9000"), mk("TRADED", "0.0000", "1.0000", "3.00"), mk("TIGHTVOL", "0.2000", "0.2100", "9.00"), mk("NOASK", "0.0000", "1.0000", "0.00", "0.0000", "0.4000"), {"yes_bid_dollars": "0.9"}, "junk"]
print(json.dumps([x["ticker"] for x in m.pick([x for x in ms if isinstance(x, dict)])]))`);
  assert.deepStrictEqual(out, ['TIGHTVOL', 'TIGHT', 'WIDE', 'TRADED', 'CHEAP5', 'NOASK', 'ONLYNOBID']);
};

// CB11: the widened filter admits a combo whose only price is a 5c yes ask, and a combo whose only price is a NO bid; it still drops a combo with nothing posted and no volume.
gates.CB11 = () => {
  const out = py(`
a = {"ticker": "A5C", "yes_bid_dollars": "0.0000", "yes_ask_dollars": "0.0500", "volume_fp": "0.00"}
b = {"ticker": "BNO", "yes_bid_dollars": "0.0000", "yes_ask_dollars": "1.0000", "no_bid_dollars": "0.7000", "no_ask_dollars": "1.0000", "volume_fp": "0.00"}
c = {"ticker": "CNONE", "yes_bid_dollars": "0.0000", "yes_ask_dollars": "1.0000", "no_bid_dollars": "0.0000", "no_ask_dollars": "1.0000", "volume_fp": "0.00"}
print(json.dumps([m.is_selected(a), m.is_selected(b), m.is_selected(c)]))`);
  assert.deepStrictEqual(out, [true, true, false]);
  assert.ok(!/HIGH_PRICE/.test(code), 'no price floor is left in the code');
};

// CB12: the book cap takes the tightest spreads first and is deterministic; the trade cap takes the most traded; no request count rises with the wider filter.
gates.CB12 = () => {
  const out = py(`
import tempfile
ms = [{"ticker": "T%03d" % i, "yes_bid_dollars": "0.1000", "yes_ask_dollars": "%.4f" % (0.11 + i * 0.001), "volume_fp": "%d.00" % (i % 7)} for i in range(200)]
urls = []
def fake(u):
    urls.append(u)
    if "/orderbook" in u: return 200, {"orderbook_fp": {"yes_dollars": [["0.1000", "5.00"]], "no_dollars": []}}, "D"
    if "/trades" in u: return 200, {"trades": []}, "D"
    return 200, {"markets": ms}, "D"
s = m.Stream(m.BUDGET, fetch=fake, clock=lambda: 0.0, sleep=lambda d: None)
m.poll(s, 1.0e9 + 3600, tempfile.mkdtemp())
books = [u.split("/markets/")[1].split("/")[0] for u in urls if "/orderbook" in u]
print(json.dumps({"books": books, "calls": s.calls, "trades": [u for u in urls if "/trades" in u]}))`);
  assert.deepStrictEqual(out.books, Array.from({ length: 40 }, (_, i) => 'T' + String(i).padStart(3, '0')), 'tightest spreads first');
  assert.strictEqual(out.trades.length, 0, 'no trade reads here (Nov 13, 2026)');
  assert.ok(out.calls <= 90);
};

// CB13: the quote rows carry the leg tickers (Nov 12, 2026) as a LAST column `leg_tickers` ("ticker:side" joined by "|"), read from the market object already listed: no extra request, every older column keeps its
// place, the string is bounded and says when it was cut, and only the first MAX_LEG_ROWS rows carry it (size).
gates.CB13 = () => {
  const out = py(`
import tempfile
leg = lambda t, s: {"event_ticker": "E", "market_ticker": t, "side": s}
mk = {"ticker": "KXMVE-A", "mve_selected_legs": [leg("KXA-1", "yes"), leg("KXB-2", "no"), "KXC-3", {"event_ticker": "E"}]}
long = {"ticker": "KXMVE-L", "mve_selected_legs": [leg("KXLONGLEGTICKER-%03d" % i, "yes") for i in range(60)]}
cols = m.QUOTE_COLS
short = m.quote_row(1, "D", mk); lng = m.quote_row(1, "D", long)
urls = []
def fake(u):
    urls.append(u)
    if "/orderbook" in u: return 200, {"orderbook_fp": {"yes_dollars": [["0.1000", "5.00"]], "no_dollars": []}}, "D"
    if "/trades" in u: return 200, {"trades": []}, "D"
    return 200, {"markets": [dict(mk, ticker="T%03d" % i, yes_bid_dollars="0.1000", yes_ask_dollars="%.4f" % (0.11 + i * 0.001)) for i in range(300)]}, "D"
s = m.Stream(m.BUDGET, fetch=fake, clock=lambda: 0.0, sleep=lambda d: None)
d = tempfile.mkdtemp(); m.poll(s, 1.0e9 + 3600, d)
import csv, os
rows = list(csv.reader(open(os.path.join(d, "quotes.csv"))))
print(json.dumps({"cols": cols, "short": short[-2:], "n": len(short), "long": lng[-2:], "nolegs": m.quote_row(1, "D", {"ticker": "X"})[-2:], "off": m.quote_row(1, "D", mk, False)[-2:],
  "filled": sum(1 for r in rows[1:] if r[-1]), "rows": len(rows) - 1, "hdr": rows[0][-2:], "calls": s.calls, "cap": m.LEGS_MAX_CHARS, "legrows": m.MAX_LEG_ROWS, "marker": m.LEGS_MARKER}))`);
  assert.deepStrictEqual(out.cols.slice(0, 18), ['t_send_ms', 't_recv_ms', 'server_date_header', 'ticker', 'event_ticker', 'exchange_index', 'open_time', 'close_time', 'yes_bid', 'yes_ask', 'no_bid', 'no_ask', 'yes_bid_size', 'yes_ask_size', 'last_price', 'volume', 'open_interest', 'legs'], 'older columns keep their order');
  assert.strictEqual(out.cols[18], 'leg_tickers');
  assert.strictEqual(out.cols.length, 19, 'the new column is the last');
  assert.deepStrictEqual(out.short, [4, 'KXA-1:yes|KXB-2:no|KXC-3'], 'the true count stays; a leg with no ticker is skipped');
  assert.ok(out.long[1].length <= out.cap && out.long[1].endsWith(out.marker) && out.long[0] === 60, 'bounded, marked, true count kept');
  assert.ok(/^(KXLONGLEGTICKER-\d{3}:yes\|)+\.\.\.$/.test(out.long[1].replace(/\|\.\.\.$/, '|...')) || /:yes\|\.\.\.$/.test(out.long[1]), 'cut at a whole leg');
  assert.deepStrictEqual(out.nolegs, ['', ''], 'no legs list: both empty, never zero');
  assert.strictEqual(out.off[1], '');
  assert.strictEqual(out.filled, out.rows, 'every quote row carries its leg tickers (Nov 13, 2026; it was the first 100)');
  assert.strictEqual(out.legrows, 400);
  assert.deepStrictEqual(out.hdr, ['legs', 'leg_tickers']);
  assert.ok(out.cap <= 600 && out.legrows <= 400);
  assert.strictEqual(out.calls, 1 + 40 + 0, 'no request was added for the legs: one list page and the 40 books');
  assert.ok(!/mve_selected_legs[^\n]*(Stream|\.get\()/.test(code), 'the legs are read from the listing, never asked for');
};

// CB8: rows are as the exchange returns them; a missing field is empty, never zero; an empty book is no row; levels run best first.
gates.CB8 = () => {
  const out = py(`
mk = {"ticker": "KXMVE-A", "event_ticker": "KXMVE-S", "exchange_index": 1, "open_time": "o", "close_time": "c", "yes_bid_dollars": "0.4000", "yes_ask_dollars": "0.4500", "no_bid_dollars": "0.5500", "yes_bid_size_fp": "12.00", "mve_selected_legs": [1, 2, 3]}
book = {"orderbook_fp": {"yes_dollars": [["0.3800", "1.00"], ["0.4000", "12.00"]], "no_dollars": [["0.5500", "9.00"]]}}
print(json.dumps({"q": m.quote_row(7, "D", mk), "cols": len(m.QUOTE_COLS), "none": [m.quote_row(1, "D", {}), m.quote_row(1, "D", None)], "b": m.book_row(7, "D", mk, book), "bcols": len(m.BOOK_COLS),
  "nob": [m.book_row(1, "D", mk, {"orderbook_fp": {"yes_dollars": [], "no_dollars": []}}), m.book_row(1, "D", mk, []), m.book_row(1, "D", mk, {"orderbook_fp": []})],
  "r": m.result_row(9, {"ticker": "T", "result": "no", "volume_fp": "4.00"}), "rnone": [m.result_row(9, {"ticker": "T", "result": "", "volume_fp": "4.00"}), m.result_row(9, {"ticker": "T", "result": "no", "volume_fp": "0.00"})]}))`);
  assert.strictEqual(out.q.length, out.cols);
  assert.deepStrictEqual(out.q.slice(8, 18), ['0.4000', '0.4500', '0.5500', '', '12.00', '', '', '', '', 3], 'missing fields are empty');
  assert.deepStrictEqual(out.none, [null, null]);
  assert.strictEqual(out.b.length, out.bcols);
  assert.deepStrictEqual(out.b.slice(4, 6), ['0.4000', '0.3800'], 'best YES bid first');
  assert.deepStrictEqual(out.b.slice(9, 11), ['12.00', '1.00']);
  assert.strictEqual(out.b[14], '0.5500');
  assert.deepStrictEqual(out.nob, [null, null, null]);
  assert.deepStrictEqual(out.r.slice(1), ['T', '', '', 'no', '', '4.00'].slice(0, 6));
  assert.deepStrictEqual(out.rnone, [null, null]);
};

// CB9: size cap: a worst case run's raw output stays small, so a day is about a megabyte gzipped, and the doc states the figures.
gates.CB9 = () => {
  const c = py('print(json.dumps({"rows": m.MAX_QUOTE_ROWS, "books": m.MAX_BOOKS, "qc": len(m.QUOTE_COLS), "bc": len(m.BOOK_COLS)}))');
  const rawBytes = c.rows * 220 + c.books * 260 + 15 * 100 * 120; // quote rows, book rows, a full trades page each
  assert.ok(rawBytes * 48 / 1e6 < 60, 'under 60 MB a day raw at the caps, gzip is several times smaller: ' + (rawBytes * 48 / 1e6).toFixed(1));
  const doc = fs.readFileSync(path.join(root, 'docs', 'COMBO_RECORDER.md'), 'utf8');
  for (const need of ['requests per minute', 'requests per day', 'MB per day', 'runner minutes', 'combo-data', '2027-01-31']) assert.ok(doc.toLowerCase().includes(need.toLowerCase()), need);
};

// CB10: the repo's other rules hold for the new files: no em dash, no live account figures.
gates.CB10 = () => {
  for (const f of [scriptPath, path.join(root, '.github', 'workflows', 'record-combo.yml'), path.join(root, 'docs', 'COMBO_RECORDER.md'), __filename]) assert.ok(!new RegExp(String.fromCharCode(8212)).test(fs.readFileSync(f, 'utf8')), 'no em dash in ' + path.basename(f));
};

// CB14: self-chaining (Nov 12, 2026): the last step runs after a failed poll, sleeps to :11 or :41 at least 25 minutes after the start, checks the end date before and after, dispatches only this workflow on main; cron stays.
gates.CB14 = () => {
  const chain = wf.split(/\n      - name: /).pop();
  assert.ok(/^Chain the next run/.test(chain));
  assert.ok(/if: "!cancelled\(\) && steps\.gate\.outputs\.go == 'true' && steps\.fresh\.outputs\.poll == 'true'"/.test(chain), 'never from a skipped or past-end run');
  assert.ok(/2027-01-31T23:59:00Z/.test(chain) && (chain.match(/not chaining/g) || []).length >= 2, 'end date before and after the sleep');
  assert.ok(chain.indexOf('sleep $((') > -1 && chain.indexOf('sleep $((') < chain.indexOf('gh workflow run'));
  assert.ok(/START \+ 1500/.test(chain) && /660/.test(chain) && /1800/.test(chain), 'at least 25 minutes after the start, on :11 or :41');
  assert.ok(/RUN_START: \$\{\{ steps\.gate\.outputs\.start \}\}/.test(chain) && !/github\.run_started_at/.test(wf.replace(/#[^\n]*/g, '').replace(/\([^)]*run_started_at[^)]*\)/g, '')), 'start time from the first step');
  assert.deepStrictEqual([...wf.matchAll(/gh workflow run ([^\n]+)/g)].map((x) => x[1].trim()), ['record-combo.yml --ref main'], 'only this workflow, only on main');
  assert.deepStrictEqual([...wf.matchAll(/cron:\s*"([^"]+)"/g)].map((x) => x[1]), ['11,41 * * * *'], 'cron stays as the restart path');
  assert.ok(/steps\.fresh\.outputs\.poll == 'true'/.test(wf.split('- name: One poll')[1].split('- name:')[0]), 'a skipped poll does not poll');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
