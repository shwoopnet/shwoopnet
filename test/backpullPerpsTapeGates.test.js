'use strict';
// BP1 to BP7: the one-time perps trade tape back-pull (Nov 17, 2026, research only). Public GET only, resumable, a day is written only when it is complete, and the script behaves on fixtures with no network.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const root = path.join(__dirname, '..');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'backpull-perps-tape.yml'), 'utf8');
const py = fs.readFileSync(path.join(root, 'scripts', 'backpull_perps_tape.py'), 'utf8');
const code = py.split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');
const wfcode = wf.split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');

// BP1: manual start only, own branch, never main, built-in token only, minimal permissions, pinned checkout, validated inputs, stops on 2027-02-26.
assert.ok(/on:\s+workflow_dispatch:/.test(wfcode) && !/schedule:|push:|pull_request/.test(wfcode), 'BP1 manual start only');
assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wfcode), 'BP1 no secret but the built-in token');
assert.ok(!/git push[^\n]*\bmain\b/.test(wfcode) && /git push -q origin perp-tape-data/.test(wfcode) && /--orphan perp-tape-data/.test(wfcode), 'BP1 its own orphan data branch, never main');
assert.ok(/permissions:\s+contents: write\s/.test(wfcode) && !/pull-requests|id-token|actions:/.test(wfcode), 'BP1 minimal permissions');
assert.ok(/actions\/checkout@[0-9a-f]{40}/.test(wfcode) && /ref: main/.test(wfcode), 'BP1 pinned checkout of main');
assert.ok(/concurrency:\s+group: backpull-perps-tape\s+cancel-in-progress: false/.test(wfcode), 'BP1 one concurrency group that never cancels');
assert.ok(/\^\[0-9\]\{4\}-\[0-9\]\{2\}-\[0-9\]\{2\}\$/.test(wfcode) && /2027-02-26T23:59:00Z/.test(wfcode) && /2027-02-26T23:59:00Z/.test(py), 'BP1 dates validated, stop date');
assert.ok(/python3 -I \.\.\/code\/scripts\/backpull_perps_tape\.py \./.test(wfcode) && /--filter=blob:none/.test(wfcode) && /git reset -q --mixed FETCH_HEAD/.test(wfcode), 'BP1 runs only its own script; the branch is opened without downloading its data');
assert.ok(/--max-days 5/.test(wfcode) && /\[ "\$RC" -eq 10 \] \|\| break/.test(wfcode), 'BP1 chunks of 5 days, pushed after each');
assert.ok(!/\$\{\{\s*inputs\./.test(wfcode.replace(/FROM_DATE: \$\{\{ inputs\.from_date \}\}|TO_DATE: \$\{\{ inputs\.to_date \}\}/g, '')), 'BP1 inputs reach the shell only through env vars');
console.log('ok   BP1 workflow');

// BP2: public GET only, one host, the trades path only, no ticker.
assert.ok(/BASE = "https:\/\/external-api\.kalshi\.com\/trade-api\/v2\/margin"/.test(code), 'BP2 one host');
assert.ok(!/Authorization|KALSHI-ACCESS|method=|data=|\.post\(|POST|portfolio|orders\/|api_key|secret|os\.environ/i.test(code), 'BP2 no auth, no POST, no account path');
assert.ok(/class NoRedirect/.test(code) && /return None/.test(code), 'BP2 redirects refused');
assert.ok(/UA = \{"User-Agent": "shwoopnet-research-recorder"\}/.test(code), 'BP2 generic user agent');
const paths = [...code.matchAll(/"(\/(?:markets|trades|funding_rates)[^"?]*)/g)].map((m) => m[1]);
assert.deepStrictEqual([...new Set(paths)], ['/trades'], 'BP2 only the trades path');
assert.ok(!/ticker=/.test(code), 'BP2 no ticker: the whole perps tape');
assert.ok(/GAP_S = 1\.2/.test(code) && /BACKOFF_S, BACKOFF_MAX_S, MAX_429_IN_ROW = 2\.0, 30\.0, 3/.test(code), 'BP2 pacing');
console.log('ok   BP2 public GET only');

const t = fs.mkdtempSync(path.join(os.tmpdir(), 'backpull-'));
const prog = `
import sys, os, json, csv, gzip, io, datetime as dt
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import backpull_perps_tape as B
class Boom:
    def open(self, *a, **k): raise AssertionError("network used")
B.OPENER = Boom()
out = {}
base = int(dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc).timestamp())
def trades(day_s, n, tid0):
    return [{"trade_id": "T%d" % (tid0 + i), "ticker": "KXAAAPERP", "count": "2.00", "price": "10.0100", "created_time": "2026-11-10T00:00:%02d.500000Z" % (i % 60), "taker_side": "ask", "is_block_trade": False} for i in range(n)]
calls = []
def fake(path):
    calls.append(path)
    if "cursor=c1" in path: return 200, {"trades": trades(base, 3, 100)[1:] + trades(base, 1, 500), "cursor": None}, "D", 7      # one repeat of T101 on the second page
    return 200, {"trades": trades(base, 3, 100), "cursor": "c1"}, "D", 7
d = os.path.join(sys.argv[1], "a"); os.makedirs(d)
rc = B.run(d, dt.date(2026, 11, 10), dt.date(2026, 11, 10), getter=fake, sleep=lambda s: None, today=dt.date(2026, 11, 17))
f = os.path.join(d, "tape", "2026-11-10.csv.gz")
rows = list(csv.reader(io.TextIOWrapper(gzip.open(f))))
out["bp3_rc"] = rc; out["bp3_cols"] = rows[0]; out["bp3_rows"] = len(rows) - 1; out["bp3_first"] = rows[1]
out["bp3_paths"] = calls
out["bp3_no_part_file"] = not os.path.exists(f + ".part")
# BP4: a day that stops writes nothing: three 429s in a row, a bad status, and the deadline.
waits = []
d2 = os.path.join(sys.argv[1], "b"); os.makedirs(d2)
rc = B.run(d2, dt.date(2026, 11, 10), dt.date(2026, 11, 10), getter=lambda p: (429, None, "", 1), sleep=lambda s: waits.append(s), today=dt.date(2026, 11, 17))
out["bp4_waits"] = [w for w in waits if w != B.GAP_S]; out["bp4_files"] = os.path.exists(os.path.join(d2, "tape"))
d3 = os.path.join(sys.argv[1], "c"); os.makedirs(d3)
B.run(d3, dt.date(2026, 11, 10), dt.date(2026, 11, 10), getter=lambda p: (500, None, "", 1), sleep=lambda s: None, today=dt.date(2026, 11, 17)); out["bp4_bad_status_files"] = os.path.exists(os.path.join(d3, "tape"))
d4 = os.path.join(sys.argv[1], "d"); os.makedirs(d4)
n = [0]
def endless(p):
    n[0] += 1; return 200, {"trades": trades(base, 2, 1000 * n[0]), "cursor": "k%d" % n[0]}, "D", 1
tick = [0.0]
def clk():
    tick[0] += 1.0; return tick[0]
B.run(d4, dt.date(2026, 11, 10), dt.date(2026, 11, 10), deadline_s=5, getter=endless, sleep=lambda s: None, clock=clk, today=dt.date(2026, 11, 17)); out["bp4_deadline_files"] = os.path.exists(os.path.join(d4, "tape")); out["bp4_deadline_pages"] = n[0]
# BP5: skip list, chunks, finished days only.
d5 = os.path.join(sys.argv[1], "e"); os.makedirs(d5); asked = []
def g5(p):
    asked.append(p); return 200, {"trades": trades(base, 1, len(asked)), "cursor": None}, "D", 1
rc5 = B.run(d5, dt.date(2026, 11, 8), dt.date(2026, 11, 12), skip={"2026-11-11"}, max_days=2, getter=g5, sleep=lambda s: None, today=dt.date(2026, 11, 17))
out["bp5_rc_chunk"] = rc5; out["bp5_files"] = sorted(os.listdir(os.path.join(d5, "tape")))
rc6 = B.run(d5, dt.date(2026, 11, 8), dt.date(2026, 11, 12), skip={"2026-11-11", "2026-11-12", "2026-11-10"}, max_days=9, getter=g5, sleep=lambda s: None, today=dt.date(2026, 11, 17))
out["bp5_rc_done"] = rc6; out["bp5_files2"] = sorted(os.listdir(os.path.join(d5, "tape")))
out["bp5_unfinished_day"] = B.run(d5, dt.date(2026, 11, 17), dt.date(2026, 11, 17), getter=g5, sleep=lambda s: None, today=dt.date(2026, 11, 17))
out["bp5_all_skipped"] = B.run(d5, dt.date(2026, 11, 8), dt.date(2026, 11, 8), skip={"2026-11-08"}, getter=g5, sleep=lambda s: None, today=dt.date(2026, 11, 17))
out["bp5_bad_dates"] = [B.main([d5, "--from", "2026-13-01x", "--to", "2026-11-10"]), B.main([d5, "--from", "2026-11-10", "--to", "2026-09-01"]), B.main([d5, "--from", "2026-01-01", "--to", "2026-11-10"])]
# BP7: the day's bounds in the request.
out["bp7_path"] = [p for p in calls if "cursor" not in p][0]
out["bp7_lo_hi"] = [base, base + 86400 - 1]
print(json.dumps(out))
`;
const r = spawnSync('python3', ['-I', '-c', prog, t], { encoding: 'utf8' });
assert.strictEqual(r.status, 0, 'python failed: ' + r.stderr);
const o = JSON.parse(r.stdout.trim().split('\n').pop());

// BP3
assert.strictEqual(o.bp3_rc, 0);
assert.deepStrictEqual(o.bp3_cols, ['t_recv_ms', 'server_date_header', 'ticker', 'created_time', 'price', 'count', 'taker_side', 'is_block_trade'], 'BP3 the live recorder tape.csv shape, no trade id');
assert.strictEqual(o.bp3_rows, 4, 'BP3 3 on page one, 1 new on page two (the repeated trade id is dropped)');
assert.strictEqual(o.bp3_first[2], 'KXAAAPERP');
assert.ok(o.bp3_paths[1].includes('cursor=c1') && o.bp3_no_part_file, 'BP3 follows the cursor, no partial file left');
console.log('ok   BP3 a finished day is written in the recorder shape');
// BP4
assert.deepStrictEqual(o.bp4_waits, [2, 4], 'BP4 429 waits 2 s then 4 s, three in a row end the run');
assert.strictEqual(o.bp4_files, false, 'BP4 three 429s write nothing for the day');
assert.strictEqual(o.bp4_bad_status_files, false, 'BP4 a bad answer writes nothing');
assert.strictEqual(o.bp4_deadline_files, false, 'BP4 the deadline writes nothing for an unfinished day');
assert.ok(o.bp4_deadline_pages < 10, 'BP4 the deadline stops the pages');
console.log('ok   BP4 an unfinished day is never written');
// BP5
assert.strictEqual(o.bp5_rc_chunk, 10, 'BP5 exit 10 while days remain');
assert.deepStrictEqual(o.bp5_files, ['2026-11-10.csv.gz', '2026-11-12.csv.gz'], 'BP5 newest first, the skipped day is not asked, a chunk of 2');
assert.strictEqual(o.bp5_rc_done, 0);
assert.deepStrictEqual(o.bp5_files2, ['2026-11-08.csv.gz', '2026-11-09.csv.gz', '2026-11-10.csv.gz', '2026-11-12.csv.gz'], 'BP5 the rest of the range, skip list honoured');
assert.strictEqual(o.bp5_unfinished_day, 1, 'BP5 a day that is not finished is refused');
assert.strictEqual(o.bp5_all_skipped, 0);
assert.deepStrictEqual(o.bp5_bad_dates, [1, 1, 1], 'BP5 bad dates and ranges are refused');
console.log('ok   BP5 resumable, chunked, finished days only');
// BP7
assert.strictEqual(o.bp7_path, '/trades?limit=1000&min_ts=' + o.bp7_lo_hi[0] + '&max_ts=' + o.bp7_lo_hi[1], 'BP7 one UTC day, limit 1000, newest first by default');
console.log('ok   BP7 the request brackets one UTC day');
