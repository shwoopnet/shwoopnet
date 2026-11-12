'use strict';
// Politics shadow recorder (Nov 11, 2026, research only): quotes of open politics markets that settle within 14 days, results after they settle, a daily count of what the hold cap (30 days since Nov 11, 2026, 14 before) left out.
// It reads public data, holds no secret, places no order, writes no Firestore, writes only to its own data branch, is not published with the site and stops by itself on 2027-02-28.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_politics.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-politics.yml'), 'utf8');
const listPath = path.join(root, 'kalshi-scalper', 'workers', 'POLREC_SERIES.json');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('pr', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// PR1: it can never trade or sign anything, and the one host is Kalshi's public market data.
gates.PR1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)], ['https://external-api.kalshi.com'], 'the only host is Kalshi public market data');
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2/.test(code));
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code), 'no account or order endpoint');
  assert.ok(!/firebase|firestore|admin\.initializeApp/i.test(code), 'no Firestore');
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  assert.deepStrictEqual(fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_politics|record-politics|polrec/.test(fs.readFileSync(path.join(fnDir, f), 'utf8'))), [], 'nothing in functions/ mentions it');
  assert.ok(!/record_politics|record-politics|polrec/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8').replace(/<li>[^\n]*<\/li>/g, '')), 'the page code does not use it (only the changelog line may name it)');
};

// PR2: a redirect is never followed, the User-Agent is generic (no personal contact), and urlopen is gone.
gates.PR2 = () => {
  assert.ok(!/urlopen/.test(code) && /_NoRedirect/.test(code) && /build_opener\(_NoRedirect\)/.test(code) && /_OPENER\.open\(/.test(code));
  assert.deepStrictEqual(py('print(json.dumps(m.UA))'), { 'User-Agent': 'shwoopnet-research-recorder' });
  assert.ok(!/@|mailto/.test(script.match(/UA = .*/)[0]), 'no email or contact in the User-Agent');
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
print(json.dumps({"status": st, "body": body is not None}))`);
  assert.deepStrictEqual(r, { status: 302, body: false }, 'the 3xx answer is the failed read, nothing from the target is read');
};

// PR3: the workflow pushes only its own data branch with the built-in token, never main, never quote-data, and is not published with the site.
gates.PR3 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin pol-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf));
  assert.ok(!/quote-data|nc-data/.test(wf.replace(/#[^\n]*/g, '')), 'it never touches the other data branches');
  assert.ok(/git fetch -q --depth 1 origin pol-data; then git checkout -q -b pol-data FETCH_HEAD; else git checkout -q --orphan pol-data/.test(wf), 'the first run creates pol-data as an orphan branch');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['polrec']);
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n\s*actions: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and actions write (the chain dispatch) and nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-politics\s*\n\s*cancel-in-progress: false/.test(wf), 'a running job is never cancelled');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'every action pinned by commit SHA');
  assert.ok(!/pip install|npm install|curl |wget /.test(wf) && !/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  assert.ok(/ref: main/.test(wf) && /record_politics\.py "data\/polrec\/\$STAMP"/.test(wf));
  assert.ok(/STAMP="\$\(date -u \+%Y-%m-%d\/%H%M\)-\$\{GITHUB_RUN_ID\}-\$\{GITHUB_RUN_ATTEMPT\}"/.test(wf), 'folder names carry the run id and attempt: two runs never write the same file');
  assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin pol-data/.test(wf) && /git pull -q --rebase origin pol-data/.test(wf), 'the six-try push loop');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- kalshi-scalper/.test(cfg), 'workflow, script and series list are not published with the site');
};

// PR4: it stops by itself on 2027-02-28, in the workflow and in the script.
gates.PR4 = () => {
  const out = py('print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH)]))');
  assert.deepStrictEqual(out, ['2027-02-28T23:59:00Z', false, true]);
  assert.ok(/date -u -d '2027-02-28T23:59:00Z' \+%s/.test(wf) && /go=false/.test(wf));
  const steps = wf.split(/\n      - name: /).slice(2);
  assert.ok(steps.length === 6 && steps.every((s) => /if: (always\(\) && )?steps\.gate\.outputs\.go == 'true'/.test(s)), 'every later step is skipped after the end date');
  assert.ok(/if past_end\(time\.time\(\)\):\s*\n\s*print\([^\n]*\)\s*\n\s*return 0/.test(code) && /if past_end\(now\):\s*\n\s*break/.test(code), 'the script exits at once, and no poll starts after it');
};

// PR5: the 14 day cap: a market that closes in 3 days is recorded, a 20 day one is skipped, a long span is skipped even if it closes soon, no close time fails closed.
gates.PR5 = () => {
  const out = py(`
now = m.epoch_of("2026-11-11T00:00:00Z")
import time
iso = lambda d: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + d * 86400))
mk = lambda o, c: {"open_time": iso(o), "close_time": iso(c)}
print(json.dumps({"three": m.within_cap(mk(-4, 3), now), "twenty": m.within_cap(mk(-1, 20), now), "longspan": m.within_cap(mk(-30, 2), now), "edge": m.within_cap(mk(0, 14), now), "spanover": m.within_cap(mk(-1, 14), now),
  "noclose": m.within_cap({"open_time": iso(0)}, now), "junk": [m.within_cap(None, now), m.within_cap("x", now), m.within_cap({"close_time": "soon"}, now)], "noopen": m.within_cap({"close_time": iso(5)}, now),
  "frac": m.within_cap({"close_time": "2026-11-15T14:59:00.123Z"}, now)}))`);
  assert.deepStrictEqual(out, { three: true, twenty: false, longspan: false, edge: true, spanover: false, noclose: false, junk: [false, false, false], noopen: true, frac: true });
};

// PR6: the series list comes from the committed JSON, is capped, and a bad list is refused.
gates.PR6 = () => {
  const cfg = JSON.parse(fs.readFileSync(listPath, 'utf8'));
  assert.ok(cfg.series.length >= 17 && cfg.series.length <= 60 && cfg.max_series <= 60 && cfg.max_requests_per_run > 0 && cfg.cap_days === 30);
  assert.ok(cfg.series.every((s) => /^[A-Z0-9]{2,40}$/.test(s)) && new Set(cfg.series).size === cfg.series.length);
  for (const must of ['KXTRUMPAPPROVE', 'KXVHGCB', 'KXTRUMPACT', 'KXHORMUZWEEKLY', 'KXTRUTHSOCIAL', 'KXACTBLUETOP', 'KXBABELMANDEBWEEKLY', 'KXHORMUZPEAK', 'KXTRUMPENDORSEMENTS', 'KXAPRPOTUS', 'KXAPRPOTUSD', 'KXGENERICBALLOTVOTEHUB', 'KXVOTEHUBTRUMPUPDOWN']) assert.ok(cfg.series.includes(must), must);
  assert.strictEqual(cfg.series.length, 45, 'Nov 12, 2026: 42 series plus the three Refinement additions');
  assert.ok(!cfg.series.includes('KXGENERICBALLOT'), 'one event in all history: left out on purpose');
  assert.ok(!cfg.series.some((s) => cfg.later_only.includes(s)), 'a later-only series is not recorded');
  assert.ok(!/KX[A-Z0-9]{3,}/.test(code), 'no series name is hard coded in the script');
  assert.deepStrictEqual(py('print(json.dumps(m.load_series()[0]))'), cfg.series, 'the script reads the file');
  const bad = py(`
import tempfile, os
def trial(d):
    p = os.path.join(tempfile.mkdtemp(), "s.json"); open(p, "w").write(json.dumps(d))
    try: m.load_series(p); return "ok"
    except ValueError: return "refused"
print(json.dumps([trial({"max_series": 2, "series": ["KXA", "KXB", "KXC"]}), trial({"series": ["KXA", "KXA"]}), trial({"series": ["kx/../a"]}), trial({"series": []}),
  trial({"max_series": 500, "series": ["KX%d" % i for i in range(61)]}), trial({"series": ["KXA", "KXB"]})]))`);
  assert.deepStrictEqual(bad, ['refused', 'refused', 'refused', 'refused', 'refused', 'ok']);
};

// PR7: rows parse from a market object as Kalshi returns it (fields seen on the live API on Nov 11, 2026); a missing field is empty, never zero; results only once there is one.
gates.PR7 = () => {
  const out = py(`
mk = {"ticker": "KXTRUTHSOCIAL-26NOV14-T60", "event_ticker": "KXTRUTHSOCIAL-26NOV14", "open_time": "2026-11-08T15:00:00Z", "close_time": "2026-11-15T14:59:00Z", "yes_bid_dollars": "0.0800",
  "yes_ask_dollars": "0.1000", "no_bid_dollars": "0.9000", "no_ask_dollars": "0.9200", "yes_bid_size_fp": "100.00", "last_price_dollars": "0.0900", "volume_fp": "5234.00", "open_interest_fp": "18466.66", "result": ""}
settled = dict(mk, result="no", expiration_value="55")
print(json.dumps({"q": m.quote_row(1, 2, "Wed, 11 Nov 2026 12:00:00 GMT", "KXTRUTHSOCIAL", mk), "cols": len(m.QUOTE_COLS), "none": [m.quote_row(1, 2, "d", "S", {}), m.quote_row(1, 2, "d", "S", None)],
  "r": m.result_row(9, "KXTRUTHSOCIAL", settled), "rnone": [m.result_row(9, "S", mk), m.result_row(9, "S", {"ticker": "T"})], "rcols": len(m.RESULT_COLS)}))`);
  assert.strictEqual(out.q.length, out.cols);
  assert.deepStrictEqual(out.q.slice(3, 5), ['KXTRUTHSOCIAL', 'KXTRUTHSOCIAL-26NOV14-T60']);
  assert.deepStrictEqual(out.q.slice(8, 17), ['0.0800', '0.1000', '0.9000', '0.9200', '100.00', '', '0.0900', '5234.00', '18466.66'], 'prices as returned, a missing ask size empty');
  assert.deepStrictEqual(out.none, [null, null]);
  assert.strictEqual(out.r.length, out.rcols);
  assert.deepStrictEqual(out.r.slice(5, 7), ['no', '55']);
  assert.deepStrictEqual(out.rnone, [null, null], 'no result yet is no row');
};

// PR8: a 429 backs off (doubling, capped) and is asked again; a non-object body is no answer and never aborts the run; paging follows the cursor to the end; the request budget is hard.
gates.PR8 = () => {
  const out = py(`
clock = [1000.0]; slept = []
def sl(d): slept.append(d); clock[0] += d
seq = [(429, None, ""), (429, None, ""), (200, {"markets": [{"ticker": "A"}], "cursor": "c1"}, "D"), (200, {"markets": [{"ticker": "B"}, "junk", 5], "cursor": ""}, "D")]
urls = []
def fake(u): urls.append(u); return seq.pop(0)
s = m.Stream(50, fetch=fake, clock=lambda: clock[0], sleep=sl)
mk, date, ts, tr, ok = m.read_series(s, "KXA", "open")
bad = []
for body in (["list"], "text", None, {"markets": "nope"}, {"markets": None}):
    s2 = m.Stream(50, fetch=lambda u, b=body: (200, b, ""), clock=lambda: clock[0], sleep=sl)
    bad.append(m.read_series(s2, "KXA", "open")[4])
rows = []; s3 = m.Stream(50, fetch=lambda u: (200, ["not", "an", "object"], ""), clock=lambda: clock[0], sleep=sl)
failed = m.poll_quotes(s3, ["KXA", "KXB"], 0, 14, rows, {})
s4 = m.Stream(2, fetch=lambda u: (200, {"markets": [], "cursor": ""}, ""), clock=lambda: clock[0], sleep=sl)
st = [s4.get("u")[0], s4.get("u")[0], s4.get("u")[0]]
print(json.dumps({"tick": [x["ticker"] for x in mk], "ok": ok, "n429": s.n429, "slept": slept[:2], "urls": urls, "bad": bad, "failed": failed, "rows": rows, "st": st, "gap": m.GAP_S, "backoff": [m.BACKOFF_S, m.BACKOFF_MAX_S]}))`);
  assert.deepStrictEqual(out.tick, ['A', 'B'], 'junk entries inside a good list are skipped');
  assert.strictEqual(out.ok, true);
  assert.strictEqual(out.n429, 2);
  assert.deepStrictEqual(out.slept, [5, 10], 'the first 429 waits 5 s, the second 10 s: it doubles');
  assert.ok(/cursor=c1$/.test(out.urls[3]) && /status=open&limit=1000$/.test(out.urls[0]), 'a refused page is asked again; the cursor is followed to the end');
  assert.deepStrictEqual(out.bad, [false, false, false, false, false], 'a non-object body is no answer');
  assert.deepStrictEqual(out.failed, ['KXA', 'KXB'], 'and the poll goes on to the next series instead of aborting');
  assert.deepStrictEqual(out.rows, []);
  assert.deepStrictEqual(out.st, [200, 200, -1], 'the request budget is hard');
  assert.ok(out.gap >= 5 && out.backoff[0] >= 5 && out.backoff[1] <= 60, 'at most 12 requests a minute');
};

// PR9: one poll writes quotes only for markets inside the cap, and counts the skipped ones for the daily file.
gates.PR9 = () => {
  const out = py(`
now = m.epoch_of("2026-11-11T00:00:00Z")
body = {"markets": [
  {"ticker": "SOON", "open_time": "2026-11-09T00:00:00Z", "close_time": "2026-11-14T00:00:00Z"},
  {"ticker": "FAR", "open_time": "2026-11-01T00:00:00Z", "close_time": "2026-12-14T00:00:00Z"},
  {"ticker": "NOCLOSE"}], "cursor": ""}
s = m.Stream(10, fetch=lambda u: (200, body, "D"), clock=lambda: 0.0, sleep=lambda d: None)
rows = []; daily = {}
failed = m.poll_quotes(s, ["KXA"], now, 14, rows, daily)
print(json.dumps({"failed": failed, "t": [r[4] for r in rows], "daily": daily, "d": m.daily_rows("2026-11-12", daily, ["KXA", "KXB"]), "cols": m.DAILY_COLS}))`);
  assert.deepStrictEqual(out.t, ['SOON']);
  assert.deepStrictEqual(out.daily.KXA, [3, 1, 1, 1]);
  assert.deepStrictEqual(out.d, [['2026-11-12', 'KXA', 3, 1, 1, 1], ['2026-11-12', 'KXB', 0, 0, 0, 0]]);
  assert.strictEqual(out.cols.length, 6);
  assert.ok(/if time\.gmtime\(now\)\.tm_hour == 0:\s*\n\s*write_csv\([^\n]*daily\.csv/.test(code), 'the skipped list is written once a day');
};

// PR10: cadence and request estimate (Nov 12, 2026): GitHub dropped most hourly starts, so starts come at minutes 7, 22, 37 and 52, each run does ONE poll, and a freshness step keeps it to about one poll per 30 minutes.
gates.PR10 = () => {
  const out = py('print(json.dumps([m.POLL_EVERY_S, m.GAP_S, len(m.load_series()[0]), m.load_series()[1]]))');
  assert.strictEqual(out[0], 1800);
  const [, gap, n, budget] = out;
  const perRun = 2 * n; // one quote poll and at most one result read, one request a series (paging adds a few)
  assert.ok(perRun * 2 < budget, 'the per-run budget covers a run with room for paging and retries');
  assert.ok(60 / gap <= 12, 'never more than 12 requests a minute');
  const cron = [...wf.matchAll(/cron:\s*"([^"]+)"/g)].map((x) => x[1]);
  assert.deepStrictEqual(cron, ['7,22,37,52 * * * *'], 'four staggered starts an hour, under the one never-cancelling group');
  assert.ok(/--minutes 0/.test(wf), 'a run is one poll, not two');
  assert.ok(/-lt 1500/.test(wf) && /steps\.fresh\.outputs\.poll == 'true'/.test(wf), 'a poll under 25 minutes after the last one is skipped, so the rate stays near one poll per 30 minutes');
  const polls = 24 * 60 / 30; // at most about this many polls a day
  assert.ok(polls * perRun / 1440 <= 4, 'about 4 requests a minute on average at the very most');
  assert.ok(/tm_min < 20/.test(code), 'the results read is hourly, not every run');
};

// PR11: self-chaining (Nov 12, 2026): the last step runs even after a failed poll, sleeps, checks the end date, dispatches only this workflow on main, and the cron stays as the restart path.
gates.PR11 = () => {
  const chain = wf.split(/\n      - name: /).pop();
  assert.ok(/^Chain the next run/.test(chain));
  assert.ok(/if: always\(\) && steps\.gate\.outputs\.go == 'true' && steps\.fresh\.outputs\.poll == 'true'/.test(chain), 'chains after a failed poll, never from a skipped or past-end run');
  assert.ok(/2027-02-28T23:59:00Z/.test(chain) && (chain.match(/not chaining/g) || []).length >= 2, 'the end date is checked before and after the sleep');
  assert.ok(chain.indexOf('sleep $((') > -1 && chain.indexOf('sleep $((') < chain.indexOf('gh workflow run'), 'it sleeps before it dispatches');
  assert.ok(/START \+ 1200/.test(chain) && /1800/.test(chain), 'at least 20 minutes after the start, on a half hour');
  const disp = [...wf.matchAll(/gh workflow run ([^\n]+)/g)].map((x) => x[1].trim());
  assert.deepStrictEqual(disp, ['record-politics.yml --ref main'], 'only this workflow, only on main');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf));
  assert.deepStrictEqual([...wf.matchAll(/cron:\s*"([^"]+)"/g)].map((x) => x[1]), ['7,22,37,52 * * * *'], 'cron stays as the restart path');
  assert.ok(/timeout-minutes: 60/.test(wf) && /cancel-in-progress: false/.test(wf));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
