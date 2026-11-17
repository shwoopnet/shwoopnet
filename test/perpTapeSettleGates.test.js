'use strict';
// PLT1 to PLT8: the perps live recorder's tape, settlement window and daily funding steps (Nov 17, 2026, Forensics' spec, research only). Public GET only, bounded, and the script behaves on fixtures with no network.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const root = path.join(__dirname, '..');
const py = fs.readFileSync(path.join(root, 'scripts', 'record_perps_live.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-perps-live.yml'), 'utf8');
const code = py.split('\n').filter((l) => !/^\s*#/.test(l)).join('\n');

// PLT1: only the Kalshi external host and the margin paths: list, orderbooks, trades, funding history. Nothing else is ever requested.
assert.ok(/BASE = "https:\/\/external-api\.kalshi\.com\/trade-api\/v2\/margin"/.test(code), 'PLT1 one host');
const gpaths = [...code.matchAll(/"(\/(?:markets|trades|funding_rates)[^"?]*)/g)].map((m) => m[1]);
assert.deepStrictEqual([...new Set(gpaths)].sort(), ['/funding_rates/historical', '/markets', '/markets/orderbooks', '/trades'].sort(), 'PLT1 only the four public paths');
assert.ok(!/ticker=/.test(code.split('def tape_poll')[1].split('def in_settle_window')[0]), 'PLT1 the tape is read with no ticker (the whole perps tape)');
assert.ok(/assert url\.startswith\("https:\/\/external-api\.kalshi\.com\/"\)/.test(code), 'PLT1 the one request function refuses any other host');
console.log('ok   PLT1 hosts and paths');

// PLT2 and PLT3: no key or auth header, no POST, redirects refused (the old gates scan the whole script, so they cover the new code too).
assert.ok(!/Authorization|KALSHI-ACCESS|method=|data=|\.post\(|POST|portfolio|orders\/|api_key|secret|os\.environ/i.test(code.replace(/"orderbooks"|\/markets\/orderbooks/g, '')), 'PLT2 no auth, no POST, no account path');
assert.ok(/class NoRedirect/.test(code) && /return None/.test(code), 'PLT3 redirects refused');
console.log('ok   PLT2 PLT3 no key, redirects refused');

const t = fs.mkdtempSync(path.join(os.tmpdir(), 'ptape-'));
const prog = `
import sys, os, json, csv, io, time, calendar
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import record_perps_live as R
class Boom:
    def open(self, *a, **k): raise AssertionError("network used")
R.OPENER = Boom()
out = {}
def mk(n, base_s, tid0):
    # n trades newest first, one second apart ending at base_s
    rows = []
    for i in range(n):
        s_ = base_s - i
        iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(s_)) + ".500000Z"
        rows.append({"trade_id": "T%d" % (tid0 - i), "ticker": "KXAAAPERP", "count": "2.00", "price": "10.0100", "created_time": iso, "taker_side": "ask", "is_block_trade": False})
    return rows

# PLT4: three 429s in a row end the tape STEP (it returns, never raises), the wait doubles 2 s, 4 s and stays under 30 s.
buf, bufc = io.StringIO(), io.StringIO()
wt, wtc = csv.writer(buf), csv.writer(bufc)
waits = []
st = {"min_s": 1000, "seen": set()}
calls = []
def g429(p):
    calls.append(p); return 429, None, "", 1, 2
R.tape_poll(st, wt, wtc, g429, 10 ** 12, sleep=lambda s_: waits.append(s_), clock=time.time)
out["p4_calls"] = len(calls); out["p4_waits"] = waits; out["p4_cover"] = list(csv.reader(io.StringIO(bufc.getvalue())))[0]

# PLT5: time bound. A fake clock moves 8 s a page: the step stops by 20 s (3 pages), says truncated and names the window it did not reach; and it never starts a page inside the last second before the deadline.
class Clk:
    def __init__(self): self.t = 100000.0
    def __call__(self): return self.t
clk = Clk()
def gpage(p):
    clk.t += 8.0
    return 200, {"trades": mk(1000, 1700000000 - 2000 * len(calls5), 5000 - 1000 * len(calls5)), "cursor": "abc"}, "Date", 1, 2
calls5 = []
def gpage2(p):
    calls5.append(p); return gpage(p)
buf, bufc = io.StringIO(), io.StringIO(); wt, wtc = csv.writer(buf), csv.writer(bufc)
st = {"min_s": 1699990000, "seen": set()}
R.tape_poll(st, wt, wtc, gpage2, clk.t + 1000, sleep=lambda s_: None, clock=clk)
c = list(csv.reader(io.StringIO(bufc.getvalue())))[0]
out["p5_pages"] = int(c[1]); out["p5_trunc"] = c[7]; out["p5_lost_lo"] = c[8]; out["p5_lost_hi"] = c[9]; out["p5_note"] = c[10]
out["p5_paths"] = calls5[:1]; out["p5_has_cursor_second"] = "cursor=abc" in calls5[1]
clk2 = Clk(); n6 = []
def gnone(p):
    n6.append(p); return 200, {"trades": [], "cursor": None}, "D", 1, 2
buf, bufc = io.StringIO(), io.StringIO()
R.tape_poll({"min_s": 1, "seen": set()}, csv.writer(buf), csv.writer(bufc), gnone, clk2.t + 0.5, sleep=lambda s_: None, clock=clk2)
out["p5_deadline_pages"] = len(n6)
# five pages is the most
clk3 = Clk(); n7 = []
def gfive(p):
    n7.append(p); return 200, {"trades": mk(3, 1700000000 - 10 * len(n7), 90000 - 10 * len(n7)), "cursor": "k%d" % len(n7)}, "D", 1, 2
buf, bufc = io.StringIO(), io.StringIO()
R.tape_poll({"min_s": 1, "seen": set()}, csv.writer(buf), csv.writer(bufc), gfive, clk3.t + 100000, sleep=lambda s_: None, clock=clk3)
out["p5_max_pages"] = len(n7)

# PLT6: overlap is dropped by trade id inside a job; the next poll starts 60 s before the newest trade seen.
buf, bufc = io.StringIO(), io.StringIO(); wt, wtc = csv.writer(buf), csv.writer(bufc)
st = {"min_s": 1699999000, "seen": set()}
first = mk(5, 1700000000, 100)          # T100..T96, newest 1700000000.5
second = mk(5, 1700000003, 103)         # T103..T99: T99 T100 T101 T102 T103? ids 103,102,101,100,99
second = [dict(x) for x in second]
def g1(p): return 200, {"trades": first, "cursor": None}, "D", 1, 2
R.tape_poll(st, wt, wtc, g1, 10 ** 12, sleep=lambda s_: None, clock=time.time)
out["p6_min_after_first"] = st["min_s"]
def g2(p): return 200, {"trades": second, "cursor": None}, "D", 1, 2
R.tape_poll(st, wt, wtc, g2, 10 ** 12, sleep=lambda s_: None, clock=time.time)
rows = list(csv.reader(io.StringIO(buf.getvalue())))
out["p6_rows"] = len(rows); out["p6_cover2"] = list(csv.reader(io.StringIO(bufc.getvalue())))[1]
out["p6_tape_cols"] = R.TAPE_COLS
out["p6_no_trade_id_written"] = all("T1" not in ",".join(r) for r in rows)

# PLT7: the settlement window and the flagged rows (no extra request): 16:55:00 to 17:04:59 UTC.
def at(h, m, s_): return calendar.timegm((2026, 11, 17, h, m, s_))
out["p7"] = [R.in_settle_window(at(16, 54, 59)), R.in_settle_window(at(16, 55, 0)), R.in_settle_window(at(17, 4, 59)), R.in_settle_window(at(17, 5, 0)), R.in_settle_window(at(0, 0, 0))]
d = os.path.join(sys.argv[1], "settle"); os.makedirs(d)
R.MIN_GAP_S = 0.0; R.POLL_EVERY_S = 0.3; R.BACKOFF_S = 0.01; R.fast_window = lambda t_: False
mkts = [{"ticker": "KXAAAPERP", "asset_class": "Equities", "status": "active", "bid": "10.00", "ask": "10.02", "settlement_mark_price": {"price": "10.01"}}]
state = {"n": 0}
def fake(path):
    if path == "/markets":
        state["n"] += 1
        t1 = at(17, 0, 0) * 1000 if state["n"] == 1 else at(12, 0, 0) * 1000
        return 200, {"markets": mkts}, "D", t1 - 5, t1
    if path.startswith("/markets/orderbooks"): return 200, {"orderbooks": []}, "D", 1, 2
    raise AssertionError(path)
R.get = fake
R.TAPE_FIRST_BACK_S = 900
R.main([d, "--cycle-hours", "0.0006"])
sr = list(csv.reader(open(os.path.join(d, "settle.csv"))))
mr = list(csv.reader(open(os.path.join(d, "markets.csv"))))
out["p7_settle_rows"] = len(sr) - 1; out["p7_markets_rows"] = len(mr) - 1; out["p7_flag"] = sr[1][-1] if len(sr) > 1 else None; out["p7_cols"] = sr[0][-1]

# PLT8: daily funding read: one request, rows carry market_ticker, a failed read writes nothing and reports -1.
buf = io.StringIO(); wfd = csv.writer(buf)
seen_paths = []
def gf(p):
    seen_paths.append(p)
    return 200, {"funding_rates": [{"market_ticker": "KXBTCPERP", "funding_time": "2026-11-17T05:00:00Z", "funding_rate": "0.0001", "mark_price": "100.5"}, {"market_ticker": "KXETHPERP", "funding_time": "2026-11-17T05:00:00Z", "funding_rate": "-0.0002", "mark_price": "2.5"}]}, "D", 1, 2
n = R.funding_day_poll(at(0, 0, 0), wfd, gf)
out["p8_n"] = n; out["p8_reqs"] = len(seen_paths); out["p8_path"] = seen_paths[0]
out["p8_rows"] = list(csv.reader(io.StringIO(buf.getvalue())))
out["p8_fail"] = R.funding_day_poll(at(0, 0, 0), csv.writer(io.StringIO()), lambda p: (500, None, "", 1, 2))
out["p8_after"] = R.FUNDING_DAY_AFTER_S
print(json.dumps(out))
`;
const r = spawnSync('python3', ['-I', '-c', prog, t], { encoding: 'utf8' });
assert.strictEqual(r.status, 0, 'python failed: ' + r.stderr);
const o = JSON.parse(r.stdout.trim().split('\n').pop());

// PLT4
assert.strictEqual(o.p4_calls, 3, 'PLT4 three 429s end the tape step');
assert.deepStrictEqual(o.p4_waits, [2, 4], 'PLT4 the wait doubles from 2 s');
assert.ok(/three 429s in a row/.test(o.p4_cover[10]) && o.p4_cover[4] === '3', 'PLT4 the coverage row says so and counts the 429s');
assert.ok(/TAPE_BACKOFF_S, TAPE_BACKOFF_MAX_S = 2\.0, 30\.0/.test(code), 'PLT4 backoff 2 s doubling to 30 s');
console.log('ok   PLT4 429 backoff ends the step, not the job');

// PLT5
assert.strictEqual(o.p5_pages, 3, 'PLT5 stops by 20 seconds (8 s a page on the fake clock)');
assert.strictEqual(o.p5_trunc, '1');
assert.ok(o.p5_lost_lo !== '' && o.p5_lost_hi !== '', 'PLT5 a truncated poll names the window it did not read');
assert.strictEqual(o.p5_note, 'time bound');
assert.ok(/^\/trades\?limit=1000&min_ts=\d+$/.test(o.p5_paths[0]) && o.p5_has_cursor_second, 'PLT5 newest first, limit 1000, min_ts, then the cursor');
assert.strictEqual(o.p5_deadline_pages, 0, 'PLT5 no page starts inside the last second before the next list read');
assert.strictEqual(o.p5_max_pages, 5, 'PLT5 at most 5 pages');
assert.ok(/TAPE_BUDGET_S = 20\.0/.test(code) && /TAPE_MAX_PAGES = 5/.test(code) && /TAPE_EVERY_S = 60\.0/.test(code), 'PLT5 constants');
assert.ok(/deadline - now >= 5\.0/.test(code), 'PLT5 the tape step starts only with 5 seconds left before the next list read');
console.log('ok   PLT5 bounded: 20 s, 5 pages, never past the next list read');

// PLT6
assert.strictEqual(o.p6_rows, 8, 'PLT6 5 first-poll rows plus 3 new ones; the 2 overlapping trades are dropped');
assert.strictEqual(o.p6_cover2[3], '2', 'PLT6 duplicates dropped counted');
assert.strictEqual(o.p6_min_after_first, 1700000000 - 60, 'PLT6 the next poll starts 60 s before the newest trade seen');
assert.deepStrictEqual(o.p6_tape_cols, ['t_recv_ms', 'server_date_header', 'ticker', 'created_time', 'price', 'count', 'taker_side', 'is_block_trade'], 'PLT6 columns: no trade id is written');
assert.ok(o.p6_no_trade_id_written);
console.log('ok   PLT6 overlap deduplicated by trade id in memory, id not stored');

// PLT7
assert.deepStrictEqual(o.p7, [false, true, true, false, false], 'PLT7 window 16:55:00 to 17:04:59 UTC');
assert.strictEqual(o.p7_settle_rows, 1, 'PLT7 only the window poll is written to settle.csv');
assert.ok(o.p7_markets_rows > o.p7_settle_rows, 'PLT7 the normal list rows are all still written');
assert.strictEqual(o.p7_flag, '1');
assert.strictEqual(o.p7_cols, 'settle_window');
console.log('ok   PLT7 settle window rows flagged, no extra request');

// PLT8
assert.strictEqual(o.p8_n, 2); assert.strictEqual(o.p8_reqs, 1, 'PLT8 one request');
assert.ok(/^\/funding_rates\/historical\?start_ts=\d+&end_ts=\d+&limit=1000$/.test(o.p8_path) && !/ticker/.test(o.p8_path), 'PLT8 no ticker, a day window');
assert.deepStrictEqual(o.p8_rows[0], ['2', 'D', 'KXBTCPERP', '2026-11-17T05:00:00Z', '0.0001', '100.5'], 'PLT8 rows carry market_ticker, time, rate and mark');
assert.strictEqual(o.p8_fail, -1, 'PLT8 a failed read is -1 and writes nothing');
assert.strictEqual(o.p8_after, 21 * 3600 + 15 * 60, 'PLT8 after 21:15 UTC');
assert.ok(/2027-02-26T23:59:00Z/.test(py) && /2027-02-26T23:59:00Z/.test(wf), 'PLT8 the stop date is unchanged');
assert.ok(/gzip -9 -f data\/perplive\/\$STAMP\/\*\.csv/.test(wf), 'PLT8 the workflow already compresses every csv of the job folder, so the new files are gzipped and pushed with the rest');
console.log('ok   PLT8 daily funding read and the stop date');

// PLT9: the tape step ships OFF (the live test showed about 25 trades a second, which is far above the spec's size estimate and makes a 5 minute poll truncate every time); with it off no tape file is created and nothing is requested for it.
assert.ok(/^TAPE_ON = False/m.test(code), 'PLT9 the tape step is off by default');
assert.ok(/if TAPE_ON and now >= next_tape/.test(code) && /if TAPE_ON:\n\s+ft, ftc = open/.test(code), 'PLT9 the tape files and polls are behind the switch');
assert.ok(/TAPE_EVERY_S = 60\.0/.test(code), 'PLT9 once a minute when on');
console.log('ok   PLT9 tape step off by default');
