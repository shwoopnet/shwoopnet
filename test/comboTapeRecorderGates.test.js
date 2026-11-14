'use strict';
// Combo trade-tape recorder (Nov 13, 2026, the owner: "Yes, nonstop recorder"; Idea Desk C's CROWDLEG and NOTAKER cards, paper only). Research only: public Kalshi market data, no key,
// no order, no Firestore; its own combotape-data branch; stops by itself on 2027-01-31. CT1 checks the code against the hand case committed before the code (test/handcases/comboTapeHandCase.json).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_combo_tape.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wfPath = path.join(root, '.github', 'workflows', 'record-combo-tape.yml');
const wf = fs.readFileSync(wfPath, 'utf8');
const handPath = path.join(root, 'test', 'handcases', 'comboTapeHandCase.json');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('ct', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// CT1: the hand case (written before the code): five cycles of a fake exchange give exactly the trade rows, legs rows, coverage rows, URLs and final mark worked out by hand.
gates.CT1 = () => {
  const hand = JSON.parse(fs.readFileSync(handPath, 'utf8'));
  const out = py(`
hand = json.load(open(${JSON.stringify(handPath)}))
for k, v in hand["constants"].items(): assert getattr(m, k) == v, (k, getattr(m, k), v)
T0 = hand["T0"]
cycles = hand["cycles"]
g = [{"status": 200, "body": {"trades": [{"trade_id": "g%d" % n, "ticker": "KXMVE-D", "created_time": "2027-01-15T08:02:%02dZ" % (50 - n), "yes_price_dollars": "0.6000", "count_fp": "1.00", "taker_outcome_side": "yes"}], "cursor": "more"}} for n in range(1, 11)]
script = {1: (cycles[0]["tape"], cycles[0]["legs"]), 2: (cycles[1]["tape"], cycles[1]["legs"]), 3: (cycles[2]["tape"], []), 4: (g, []), 5: (cycles[4]["tape"], cycles[4]["legs"])}
state = {"c": 1, "ti": 0, "li": 0}
urls = []
def fake(u):
    urls.append((state["c"], u))
    tape, legs = script[state["c"]]
    if "/markets/trades?" in u:
        a = tape[state["ti"]]; state["ti"] += 1
    else:
        a = legs[state["li"]]; state["li"] += 1
    return a["status"], a["body"]
clock = [float(T0)]
def sl(d): clock[0] += d
s = m.Stream(fetch=fake, clock=lambda: clock[0], sleep=sl)
rec = m.Recorder(s, T0, hand["since"])
trades, legs, cov = [], [], []
for c in range(1, 6):
    state.update({"c": c, "ti": 0, "li": 0})
    r, l, cv = rec.cycle(T0 + 60 * (c - 1))
    trades += r; legs += l; cov.append(cv)
print(json.dumps({"trades": [t[1:] for t in trades], "legs": [x[1:] for x in legs], "cov": [c[:16] for c in cov], "mark": rec.mark, "end": rec.end(),
  "u1": [u.split("?")[1] for c, u in urls if c == 1 and "/trades?" in u], "lu": [u.split("?")[1] for c, u in urls if "tickers=" in u]}))`);
  const ex = hand.expected;
  const g = Array.from({ length: 10 }, (_, i) => ['KXMVE-D', `2027-01-15T08:02:${String(49 - i).padStart(2, '0')}Z`, '0.6000', '1.00', 'yes', 'g' + (i + 1)]);
  assert.deepStrictEqual(out.trades, ex.trades.slice(0, 4).concat(g), 'trade rows');
  assert.deepStrictEqual(out.legs, ex.legs, 'legs rows');
  assert.deepStrictEqual(out.cov, ex.coverage, 'coverage rows');
  assert.strictEqual(out.mark, ex.last_mark);
  assert.strictEqual(out.end, ex.legs_missing_at_end);
  assert.deepStrictEqual(out.u1, ex.tape_urls_cycle1);
  assert.deepStrictEqual(out.lu, ex.legs_urls);
};

// CT2: it can never trade or sign anything; one host, Kalshi's public market data; GET only; /markets endpoints only; nothing in functions/ or the page names it.
gates.CT2 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)], ['https://external-api.kalshi.com']);
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE|PATCH)|data\s*=\s*b?["']|os\.environ|getenv/i.test(code), 'no key, no auth header, no signing, no write call, no environment secret');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|batched/.test(code));
  assert.ok(!/firebase|firestore/i.test(code) && !/^\s*(from|import)\s+[^\n]*functions/m.test(script));
  const urls = [...code.matchAll(/"(%s\/[^"]*)"/g)].map((x) => x[1]);
  assert.ok(urls.length === 2 && urls.every((u) => /^%s\/markets(\/trades)?\?/.test(u)), urls.join(' | '));
  for (const f of fs.readdirSync(path.join(root, 'functions')).filter((f) => f.endsWith('.js'))) assert.ok(!/record_combo_tape|record-combo-tape|combotape-data/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')), f);
  assert.ok(!/record_combo_tape|record-combo-tape|combotape-data/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8').replace(/<li>[^\n]*<\/li>/g, '')), 'only the changelog line may name it');
};

// CT3: no redirect is followed; a plain User-Agent with no contact.
gates.CT3 = () => {
  assert.ok(!/urlopen/.test(code) && /build_opener\(_NoRedirect\)/.test(code) && /_OPENER\.open\(/.test(code));
  assert.deepStrictEqual(py('print(json.dumps(m.UA))'), { 'User-Agent': 'shwoopnet-research-recorder' });
  const r = py(`
import threading, http.server
class T(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(302); self.send_header("Location", "http://127.0.0.1:1/x"); self.end_headers()
a = http.server.HTTPServer(("127.0.0.1", 0), T)
threading.Thread(target=a.serve_forever, daemon=True).start()
st, body = m.http_get("http://127.0.0.1:%d/a" % a.server_address[1])
print(json.dumps([st, body is None]))`);
  assert.deepStrictEqual(r, [302, true]);
};

// CT4: rate. At least 6 s between calls (at most 10 a minute), a 429 doubles its wait up to 60 s, a cycle sends at most 10 requests and reads at most 10 pages, 2 legs look-ups of 40.
gates.CT4 = () => {
  const c = py('print(json.dumps({"gap": m.GAP_S, "bo": [m.BACKOFF_S, m.BACKOFF_MAX_S], "req": m.MAX_REQ_CYCLE, "pages": m.MAX_PAGES_CYCLE, "lk": m.LEG_LOOKUPS_CYCLE, "batch": m.LEG_BATCH, "cyc": m.CYCLE_S, "c429": m.MAX_CONSEC_429}))');
  assert.ok(c.gap >= 6 && 60 / c.gap <= 10 && c.bo[0] >= 5 && c.bo[1] <= 60);
  assert.ok(c.req <= 10 && c.pages <= c.req && c.lk <= 2 && c.batch <= 40 && c.cyc === 60 && c.c429 === 3);
  const out = py(`
clock = [0.0]; slept = []
def sl(d): slept.append(round(d, 3)); clock[0] += d
s = m.Stream(fetch=lambda u: (200, {"trades": [], "cursor": "x"}), clock=lambda: clock[0], sleep=sl)
rec = m.Recorder(s, 1000, None)
_r, _l, cov = rec.cycle(1000)
s2 = m.Stream(fetch=lambda u: (429, None), clock=lambda: clock[0], sleep=sl)
for _ in range(4): s2.get("u")
print(json.dumps({"req": cov[15], "pages": cov[3], "capped": cov[5], "slept": slept[:9], "bo": slept[9:12]}))`);
  assert.strictEqual(out.req, 10);
  assert.strictEqual(out.pages, 10);
  assert.strictEqual(out.capped, 1);
  assert.ok(out.slept.every((d) => d >= 6), 'every call waits at least 6 s after the last: ' + out.slept);
  assert.deepStrictEqual(out.bo, [5, 10, 20], 'a refusal doubles the wait');
};

// CT5: only combo tickers of a safe shape, end to end; the cursor is percent-encoded; a trade without a usable id is dropped; a failed read moves no mark.
gates.CT5 = () => {
  const out = py(`
safe = [m.is_combo(t) for t in ("KXMVE-A1", "KXMVE-A1\\n", "KXMVE-A B", "KXBTC-1", "KXMVE-" + "A" * 121, None, 5)]
enc = m.tape_url(1, 2, "a&ticker=X/..")
s = m.Stream(fetch=lambda u: (200, {"trades": [{"ticker": "KXMVE-A", "trade_id": None}, {"ticker": "KXMVE-A", "trade_id": ["x"]}, {"ticker": "KXMVE-A", "trade_id": ""}, "junk"], "cursor": ""}), clock=lambda: 0.0, sleep=lambda d: None)
rec = m.Recorder(s, 1000, None)
r, l, cov = rec.cycle(1000)
s2 = m.Stream(fetch=lambda u: (500, None), clock=lambda: 0.0, sleep=lambda d: None)
rec2 = m.Recorder(s2, 1000, 900)
mark0 = rec2.mark
r2, l2, cov2 = rec2.cycle(1060)
print(json.dumps({"safe": safe, "enc": enc, "rows": len(r), "tape_rows": cov[7], "mark": [mark0, rec2.mark], "cov2": [cov2[3], cov2[4], cov2[5], cov2[11]]}))`);
  assert.deepStrictEqual(out.safe, [true, false, false, false, false, false, false]);
  assert.strictEqual(out.enc, 'https://external-api.kalshi.com/trade-api/v2/markets/trades?min_ts=1&max_ts=2&limit=1000&cursor=a%26ticker%3DX%2F..');
  assert.deepStrictEqual([out.rows, out.tape_rows], [0, 4]);
  assert.deepStrictEqual(out.mark, [900, 900], 'a failed read leaves the mark');
  assert.deepStrictEqual(out.cov2, [0, 0, 0, 0], 'no page, not complete, not capped, no legs look-up after a failed tape read');
};

// CT6: the first window: the previous job's mark clamped to 1 minute to 2 hours back, 5 minutes when unknown or junk.
gates.CT6 = () => {
  const out = py('print(json.dumps([m.first_mark(100000, x) for x in (None, 0, 100000 - 30, 100000 - 600, 100000 - 99999, 100000 + 5, True, "99000")]))');
  assert.deepStrictEqual(out, [99700, 99700, 99940, 99400, 92800, 99700, 99700, 99700]);
};

// CT7: the run loop: cycles every 60 s to the stop, never after the end date, an overrun skips ticks instead of bursting, the rows and mark.txt are written after every cycle.
gates.CT7 = () => {
  const out = py(`
import tempfile, os
clock = [5000.0]
def sl(d): clock[0] += d
def fake(u):
    clock[0] += 0.5
    return 200, {"trades": [], "cursor": ""}
s = m.Stream(fetch=fake, clock=lambda: clock[0], sleep=sl)
d = tempfile.mkdtemp()
rec = m.run(d, s, 5000, 5000 + 300, None, clock=lambda: clock[0], sleep=sl)
cov = open(os.path.join(d, "coverage.csv")).read().splitlines()
mk = open(os.path.join(d, "mark.txt")).read().strip()
e = rec.end()
d2 = tempfile.mkdtemp()
rec2 = m.run(d2, m.Stream(fetch=fake, clock=lambda: clock[0], sleep=sl), m.END_EPOCH - 90, m.END_EPOCH + 600, None, clock=lambda: clock[0], sleep=sl)
print(json.dumps({"n": rec.n, "cov": len(cov) - 1, "hdr": cov[0], "mark": mk, "files": sorted(os.listdir(d)), "n2": rec2.n, "end": e}))`);
  assert.strictEqual(out.n, 5, 'one cycle a minute for 5 minutes');
  assert.strictEqual(out.cov, 5);
  assert.strictEqual(out.mark, '5240');
  assert.deepStrictEqual(out.files, ['coverage.csv', 'end.txt', 'legs.csv', 'mark.txt', 'trades.csv']);
  assert.ok(out.n2 <= 2, 'no cycle starts at or after the end date');
  assert.ok(/mark\.txt[\s\S]*tick \+= CYCLE_S/.test(script.split('def run(')[1]), 'mark.txt is written inside the loop, after every cycle');
  assert.ok(/while tick < clock\(\) - CYCLE_S:/.test(script), 'an overrun skips ticks');
};

// CT8: the workflow: its own data branch, never main or another data branch, built-in token only, minimal permissions, pinned checkout, never-cancelling concurrency, the six-try push,
// the previous job's mark passed as digits only through env, the end date in the workflow and the script, not published with the site.
gates.CT8 = () => {
  const bare = wf.replace(/#[^\n]*/g, '');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf));
  assert.ok(/git push -q origin combotape-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf));
  assert.ok(!/quote-data|nc-data|pol-data|perp-data|sports-data|combo-data|kalshi-pull-data/.test(bare), 'it never touches another data branch');
  assert.ok(/git fetch -q --depth 1 origin combotape-data; then git checkout -q -b combotape-data FETCH_HEAD; else git checkout -q --orphan combotape-data/.test(wf));
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['tape']);
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write only');
  assert.ok(/concurrency:\s*\n\s*group: record-combo-tape\s*\n\s*cancel-in-progress: false/.test(wf));
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)));
  assert.ok(!/pip install|npm install|curl |wget /.test(wf) && !/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin combotape-data && exit 0/.test(wf), 'the six-try push loop');
  const rec = wf.split('- name: Record the combo tape')[1].split('- name:')[0];
  assert.ok(/SINCE: \$\{\{ steps\.mark\.outputs\.since \}\}/.test(rec) && /case "\$SINCE" in ''\|\*\[!0-9\]\*\) SINCE=0 ;; esac/.test(rec) && /--since "\$SINCE"/.test(rec));
  assert.ok(!/\$\{\{ steps\.mark\.outputs\.since \}\}/.test(rec.split('run: |')[1]), 'the mark reaches the shell through env, never pasted into the script');
  assert.ok(/tr -cd '0-9'/.test(wf), 'mark.txt is reduced to digits before it is passed on');
  assert.ok(/ref: main/.test(wf) && /timeout-minutes: (\d+)/.test(wf) && Number(wf.match(/timeout-minutes: (\d+)/)[1]) <= 330);
  assert.ok(/date -u -d '2027-01-31T23:59:00Z' \+%s/.test(wf));
  assert.deepStrictEqual(py('print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH)]))'), ['2027-01-31T23:59:00Z', false, true]);
  assert.ok(/if past_end\(now\):\s*\n\s*print\([^\n]*\)\s*\n\s*return 0/.test(code));
  const steps = wf.split(/\n      - name: /).slice(2);
  assert.ok(steps.every((s) => /if: (always\(\) && )?steps\.gate\.outputs\.go == 'true'/.test(s)), 'every step after the gate checks it');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- docs/.test(cfg), 'not published with the site');
};

// CT10 (Auditor B F1, Nov 13): the mark comes from the newest job folder that HAS a mark.txt with digits, so a job that died before its first cycle (folder, no mark) or wrote junk does not
// send the next job back to the 5 minute default and lose the gap silently. Hand case: three folders, the newest without a mark, the middle with junk, the oldest with 1800000240.
gates.CT10 = () => {
  const os = require('os');
  const step = wf.split('- name: Find where the previous job\'s tape ended')[1].split('run: |')[1].split('\n      - name:')[0];
  const body = step.split('\n').map((l) => l.replace(/^          /, '')).join('\n');
  const run = (layout) => {
    const d = fs.mkdtempSync(path.join(os.tmpdir(), 'ct10-'));
    for (const [folder, mark] of layout) {
      fs.mkdirSync(path.join(d, 'data', 'tape', folder), { recursive: true });
      if (mark !== null) fs.writeFileSync(path.join(d, 'data', 'tape', folder, 'mark.txt'), mark);
    }
    const outFile = path.join(d, 'out');
    execFileSync('bash', ['-c', body], { cwd: d, env: { PATH: process.env.PATH, GITHUB_OUTPUT: outFile } });
    return fs.readFileSync(outFile, 'utf8').trim();
  };
  assert.strictEqual(run([['2027-01-15/0800', '1800000240\n'], ['2027-01-15/1200', 'junk\n'], ['2027-01-15/1600', null]]), 'since=1800000240', 'skips a folder with no mark and one with no digits');
  assert.strictEqual(run([['2027-01-15/0800', '1800000240\n'], ['2027-01-15/1200', '1800014400\n']]), 'since=1800014400', 'the newest good mark wins');
  assert.strictEqual(run([['2027-01-15/0800', null]]), 'since=0', 'no mark anywhere: the 5 minute default');
  assert.strictEqual(run([]), 'since=0', 'a new branch: the 5 minute default');
  assert.strictEqual(run([['2027-01-15/0800', '1800000240; rm -rf /\n']]), 'since=1800000240', 'anything but digits is stripped');
};

// CT11 (the Head of R&D, Nov 13: a hard size stop). Hand case: the size step, run as written, on sparse files (no real disk used): 1.3 GB stops (ok=false, says why), exactly 1.2 GB stops,
// 1.0 GB and an empty or missing data/tape go on; the recording step needs ok == 'true'.
gates.CT11 = () => {
  const os = require('os');
  const step = wf.split('- name: Size stop')[1].split('run: |')[1].split('\n      - name:')[0];
  const body = step.split('\n').map((l) => l.replace(/^          /, '')).join('\n');
  const run = (sizes) => {
    const d = fs.mkdtempSync(path.join(os.tmpdir(), 'ct11-'));
    if (sizes !== null) {
      fs.mkdirSync(path.join(d, 'data', 'tape', '2027-01-15', '0800'), { recursive: true });
      sizes.forEach((n, i) => execFileSync('truncate', ['-s', String(n), path.join(d, 'data', 'tape', '2027-01-15', '0800', 'f' + i + '.csv.gz')]));
    }
    const outFile = path.join(d, 'out');
    const log = execFileSync('bash', ['-c', body], { cwd: d, env: { PATH: process.env.PATH, GITHUB_OUTPUT: outFile }, encoding: 'utf8' });
    return [fs.readFileSync(outFile, 'utf8').trim(), log];
  };
  const big = run([700000000, 600000000]);
  assert.strictEqual(big[0], 'ok=false');
  assert.ok(/size stop: data\/tape holds \d+ bytes, at or over 1200000000: nothing recorded/.test(big[1]), 'it logs why');
  assert.strictEqual(run([1200000000 - 4096, 4096])[0], 'ok=false', 'at the limit it stops');
  assert.strictEqual(run([1000000000])[0], 'ok=true');
  assert.strictEqual(run([])[0], 'ok=true');
  assert.strictEqual(run(null)[0], 'ok=true', 'a new branch goes on');
  assert.ok(/if: steps\.gate\.outputs\.go == 'true' && steps\.size\.outputs\.ok == 'true'/.test(wf.split('- name: Record the combo tape')[1].split('\n      - name:')[0]), 'recording needs the size check');
};

// CT12 (the Head of R&D, Nov 13: push every 60 minutes inside a job). Hand case: the recording step, run as written, against a stub recorder (each chunk writes one csv and a mark one hour
// later than the last) and a real local bare repository as origin: five hourly chunks, each pushed in its own commit (so a lost runner loses at most the chunk in progress), each chunk's
// --since is the previous chunk's mark, every chunk gets --until (the boundary) and --max-minutes 60, and a chunk that fails is followed by the next.
gates.CT12 = () => {
  const os = require('os');
  const step = wf.split('- name: Record the combo tape')[1].split('run: |')[1].split('\n      - name:')[0];
  const body = step.split('\n').map((l) => l.replace(/^          /, '')).join('\n');
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'ct12-'));
  const git = (args, cwd) => execFileSync('git', args, { cwd, encoding: 'utf8', env: { PATH: process.env.PATH, HOME: d, GIT_CONFIG_NOSYSTEM: '1' } });
  git(['init', '-q', '--bare', 'origin.git'], d);
  fs.mkdirSync(path.join(d, 'data'));
  git(['init', '-q'], path.join(d, 'data'));
  git(['remote', 'add', 'origin', path.join(d, 'origin.git')], path.join(d, 'data'));
  git(['checkout', '-q', '--orphan', 'combotape-data'], path.join(d, 'data'));
  fs.mkdirSync(path.join(d, 'code', 'scripts'), { recursive: true });
  const log = path.join(d, 'calls.log');
  fs.writeFileSync(path.join(d, 'code', 'scripts', 'record_combo_tape.py'), `import sys, os, time
a = sys.argv[1:]
if "--boundary" in a:
    print(int(time.time()) + 100000); sys.exit(0)
out = a[0]; since = int(a[a.index("--since") + 1])
open(${JSON.stringify(log)}, "a").write(" ".join(a[1:]) + "\\n")
n = len(open(${JSON.stringify(log)}).read().splitlines())
open(os.path.join(out, "trades.csv"), "a").write("chunk%d\\n" % n)
if n == 3:
    sys.exit(1)   # a chunk that fails: no mark; the step must go on
open(os.path.join(out, "mark.txt"), "w").write("%d\\n" % (1800000000 + 3600 * n))
`);
  const env = { PATH: process.env.PATH, HOME: d, GIT_CONFIG_NOSYSTEM: '1', SINCE: '1799999000', GIT_AUTHOR_DATE: '2027-01-15T08:00:00Z', GIT_COMMITTER_DATE: '2027-01-15T08:00:00Z' };
  // the step sleeps 30 s after a failed chunk; replace only that sleep so the test is quick (the push loop's own sleeps never run: every push succeeds)
  execFileSync('bash', ['-c', body.replace('|| sleep 30', '|| true')], { cwd: d, env, encoding: 'utf8' });
  const calls = fs.readFileSync(log, 'utf8').trim().split('\n');
  const commits = git(['log', '--format=%s', 'combotape-data'], path.join(d, 'origin.git')).trim().split('\n');
  const files = git(['ls-tree', '-r', '--name-only', 'combotape-data'], path.join(d, 'origin.git')).trim().split('\n');
  assert.strictEqual(calls.length, 5, 'five hourly chunks at most');
  assert.deepStrictEqual(calls.map((c) => c.match(/--since (\d+)/)[1]), ['1799999000', '1800003600', '1800007200', '1800007200', '1800014400'], 'each chunk starts at the previous chunk mark; a failed chunk leaves it');
  assert.ok(calls.every((c) => /--until \d+ --max-minutes 60$/.test(c)), calls.join(' | '));
  assert.ok(files.every((f) => /^tape\/\d{4}-\d{2}-\d{2}\/\d{4}-[1-5]\/(trades\.csv\.gz|mark\.txt)$/.test(f)), 'gzipped data and marks under tape/: ' + files.join(' '));
  assert.strictEqual(files.filter((f) => f.endsWith('trades.csv.gz')).length, 5, 'every chunk keeps its own folder, even within one minute');
  assert.strictEqual(commits.length, 5, 'one push per chunk');
  assert.ok(/for i in 1 2 3 4 5 6; do git -C data push -q origin combotape-data && return 0; \[ "\$i" -lt 6 \] \|\| break; sleep \$\(\(2 \*\* i\)\); git -C data pull -q --rebase origin combotape-data \|\| true; done/.test(step), 'the six-try loop');
  assert.ok(/push \|\| echo "hourly push failed: the last step tries again"/.test(step), 'a failed hourly push does not end the job');
  assert.ok(/for k in 1 2 3 4 5; do/.test(step) && /\[ "\$NOW" -ge "\$STOPDATE" \]/.test(step), 'at most five chunks, and none after the end date');
};

// CT9: the docs state the figures; no em dash in the new files.
gates.CT9 = () => {
  const doc = fs.readFileSync(path.join(root, 'docs', 'COMBO_TAPE_RECORDER.md'), 'utf8');
  for (const need of ['requests per minute', 'requests per day', 'MB per day', 'runner minutes', 'combotape-data', '2027-01-31', 'held-out', 'complete', 'capped']) assert.ok(doc.toLowerCase().includes(need.toLowerCase()), need);
  for (const f of [scriptPath, wfPath, path.join(root, 'docs', 'COMBO_TAPE_RECORDER.md'), handPath, __filename]) assert.ok(!new RegExp(String.fromCharCode(8212)).test(fs.readFileSync(f, 'utf8')), 'no em dash in ' + path.basename(f));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
