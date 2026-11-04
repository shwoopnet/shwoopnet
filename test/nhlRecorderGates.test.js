'use strict';
// The NHL pre-puck-drop ladder recorder (Nov 4, 2026, RECBUILD1, research only): public GET only, no secret, writes only to the quote-data branch under nhl/, not published with the site.
// Offline: ESPN and Kalshi are replaced by trimmed copies of real responses (test/fixtures/nhl), so no gate touches the network.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const script = read('scripts', 'record_nhl.py');
const wf = read('.github', 'workflows', 'record-nhl.yml');
const strip = (s) => s.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const FX = path.join(root, 'test', 'fixtures', 'nhl');
const gates = {};
// A fake network: ESPN scoreboard and summary and the three Kalshi series come from the fixtures; `fail` lists URL fragments answered 500.
const prelude = `
import importlib.util, json, os, sys, tempfile, gzip, glob, io, urllib.error
spec = importlib.util.spec_from_file_location('rn', ${JSON.stringify(path.join(root, 'scripts', 'record_nhl.py'))}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
FX = ${JSON.stringify(FX)}
fx = lambda n: open(os.path.join(FX, n)).read()
class R:
    def __init__(self, body, status=200): self.b, self.status, self.headers = body.encode(), status, {"Date": "Wed, 04 Nov 2026 14:00:00 GMT"}
    def read(self, *a): return self.b
    def __enter__(self): return self
    def __exit__(self, *a): return False
CALLS = []
FAIL = []
def fake_open(req, timeout=0):
    u = req.full_url
    CALLS.append(u)
    if any(f in u for f in FAIL): raise urllib.error.HTTPError(u, 500, "x", {}, None)
    if "scoreboard" in u: return R(fx("espn_scoreboard.json"))
    if "/summary" in u: return R(fx("espn_summary.json"))
    for s in ("KXNHLGOAL", "KXNHLAST", "KXNHLPTS"):
        if "series_ticker=" + s in u: return R(fx("kalshi_%s.json" % s))
    raise urllib.error.HTTPError(u, 404, "x", {}, None)
m._open = fake_open
m._sleep = lambda x: None
T = [1_793_000_000.0]
m._now = lambda: T[0]
START = m.parse_iso("2026-11-05T00:30Z")
tmp = tempfile.mkdtemp()
`;
const py = (code) => execFileSync('python3', ['-I', '-c', prelude + code], { encoding: 'utf8' });

// N1: it can never trade or sign anything, and it names exactly the two public hosts.
gates.N1 = () => {
  const code = strip(script);
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|Cookie|method\s*=|data\s*=\s*b?["'{]|\b(POST|PUT|DELETE)\b/i.test(code), 'no key, no signing, no write call (urlopen of a bare Request is a GET)');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|\/exchange\//.test(code), 'no account or order endpoint');
  assert.ok(!/os\.environ|getenv/.test(code), 'reads no environment variable, so no secret');
  assert.deepStrictEqual([...new Set(code.match(/https:\/\/[a-z0-9.-]+/g))].sort(), ['https://external-api.kalshi.com', 'https://site.api.espn.com']);
  assert.ok(/UA = \{"User-Agent": "shwoopnet-research-recorder/.test(script) && !/Mozilla|Chrome|Safari/i.test(code), 'an honest User-Agent, never a browser one');
  assert.ok(/MIN_GAP = \{"kalshi": 1\.0, "espn": 1\.0\}/.test(script), 'one request a second per host');
  assert.ok(!/KX[A-Z0-9]*15M|L1_SERIES/.test(code), 'no live 15 minute series');
};

// N2: the workflow: three scheduled starts (the same times the script is told), only the built-in token, pushes the data branch only, six push tries, an end date, cannot overlap itself.
gates.N2 = () => {
  assert.deepStrictEqual([...wf.matchAll(/- cron: "(\d+) (\d+) \* \* \*"/g)].map((x) => x[2] + ':' + x[1]).sort(), ['14:45', '1:30', '21:30'], 'three starts a day');
  assert.ok(/record_nhl\.py data\/nhl --anchors 14:45,21:30,01:30/.test(wf) && /DEFAULT_ANCHORS = "14:45,21:30,01:30"/.test(script), 'the job and the script agree on the start times');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/git add nhl\b/.test(wf) && !/git add (-A|\.)/.test(wf), 'it stages only nhl/');
  assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin quote-data/.test(wf), 'six push tries (RECPATCH1)');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
  assert.ok(/cancel-in-progress: false/.test(wf) && /group: record-nhl/.test(wf), 'two jobs never overlap, the next queues');
  assert.ok(/workflow_dispatch/.test(wf) && /ref: main/.test(wf), 'startable by hand; it runs the reviewed script from main');
  assert.ok(/timeout-minutes: 330/.test(wf) && /2027-02-01T06:00:00Z/.test(wf) && /STOP_ALL_ISO = "2027-02-01T06:00:00Z"/.test(script), 'a job is bounded and nothing runs after the end date');
  const cfg = read('_config.yml');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- kalshi-scalper/.test(cfg) && /- test/.test(cfg), 'none of it is published with the site');
};

// N3: the ESPN scoreboard is read into games, and each game is matched to its Kalshi event by the two team codes (either spelling), within a day, never when ambiguous.
gates.N3 = () => {
  const out = JSON.parse(py(`
games = m.parse_scoreboard(json.loads(fx("espn_scoreboard.json")))
ev = {e: [] for e in ("KXNHLGOAL-26NOV04OTTBUF", "KXNHLGOAL-26NOV04CHIFLA")}
g = {g["id"]: g for g in games}
tb = {"start": START, "home": {"abbr": "TB"}, "away": {"abbr": "NJ"}}
print(json.dumps({
  "n": len(games), "ids": [x["id"] for x in games], "start": games[0]["start"] == START, "state": games[0]["state"], "away": games[0]["away"]["abbr"],
  "ott": m.match_event(g["401892644"], ev), "chi": m.match_event(g["401892645"], ev),
  "alias": m.match_event(tb, {"KXNHLGOAL-26NOV04NJDTBL": [], "KXNHLGOAL-26NOV04BOSTOR": []}), "alias2": m.match_event(tb, {"KXNHLGOAL-26NOV04NJTB": []}),
  "wrong_day": m.match_event(tb, {"KXNHLGOAL-26NOV09NJTB": []}), "next_day": m.match_event(tb, {"KXNHLGOAL-26NOV05NJTB": []}),
  "ambiguous": m.match_event(tb, {"KXNHLGOAL-26NOV04NJTB": [], "KXNHLGOAL-26NOV04NJDTBL": []}), "none": m.match_event(tb, {}),
  "bad": m.parse_scoreboard({"events": [{"id": "1", "date": "x"}, {"nope": 1}]}), "empty": m.parse_scoreboard(None), "dates": m.schedule_dates(1_793_000_000)}))`));
  assert.strictEqual(out.n, 2); assert.deepStrictEqual(out.ids, ['401892644', '401892645']); assert.strictEqual(out.start, true);
  assert.strictEqual(out.state, 'pre'); assert.strictEqual(out.away, 'OTT');
  assert.strictEqual(out.ott, 'KXNHLGOAL-26NOV04OTTBUF'); assert.strictEqual(out.chi, 'KXNHLGOAL-26NOV04CHIFLA');
  assert.strictEqual(out.alias, 'KXNHLGOAL-26NOV04NJDTBL'); assert.strictEqual(out.alias2, 'KXNHLGOAL-26NOV04NJTB');
  assert.strictEqual(out.wrong_day, ''); assert.strictEqual(out.next_day, 'KXNHLGOAL-26NOV05NJTB'); assert.strictEqual(out.ambiguous, ''); assert.strictEqual(out.none, '');
  assert.deepStrictEqual(out.bad, []); assert.deepStrictEqual(out.empty, []); assert.ok(out.dates.length >= 1);
};

// N4: a look is due from its target (start minus 120, 90, 60, 30 or 5 minutes) for its slack, never before, never once taken, never after the start, never for a game that has started.
gates.N4 = () => {
  const out = JSON.parse(py(`
g = {"id": "G", "start": START, "state": "pre", "home": {}, "away": {}}
at = lambda mins_before: m.due_looks({"G": g}, set(), START - mins_before * 60)
lk = lambda d: [x[1] for x in d]
res = {"before": lk(at(121)), "t120": lk(at(120)), "t120late": lk(at(120 - 11)), "gap": lk(at(105)), "t90": lk(at(90)), "t60": lk(at(60)), "t30": lk(at(30)), "t5": lk(at(5)), "t5late": lk(at(1.5)),
       "t5over": lk(at(0.5)), "started": lk(at(-1)),
       "taken": lk(m.due_looks({"G": g}, {("G", 60)}, START - 3600)), "live": lk(m.due_looks({"G": dict(g, state="in")}, set(), START - 3600)),
       "next": m.next_target({"G": g}, set(), START - 7300) == START - 7200, "next_none": m.next_target({"G": dict(g, state="post")}, set(), START - 7300),
       "looks": list(m.LOOKS_MIN), "slack": m.LOOK_SLACK_S}
print(json.dumps(res))`));
  assert.deepStrictEqual(out.looks, [120, 90, 60, 30, 5]);
  assert.deepStrictEqual(out.before, []); assert.deepStrictEqual(out.t120, [120]); assert.deepStrictEqual(out.t120late, [120]); assert.deepStrictEqual(out.gap, []);
  assert.deepStrictEqual(out.t90, [90]); assert.deepStrictEqual(out.t60, [60]); assert.deepStrictEqual(out.t30, [30]); assert.deepStrictEqual(out.t5, [5]); assert.deepStrictEqual(out.t5late, [5]);
  assert.deepStrictEqual(out.t5over, []); assert.deepStrictEqual(out.started, []); assert.deepStrictEqual(out.taken, []); assert.deepStrictEqual(out.live, []);
  assert.strictEqual(out.next, true); assert.strictEqual(out.next_none, null);
};

// N5: a look writes EVERY rung of the matched events with bid, ask, both sizes and the volume at that moment, for all three series; a game with no open ladder is a zero, not a gap; nothing is filtered.
gates.N5 = () => {
  const out = JSON.parse(py(`
games = m.parse_scoreboard(json.loads(fx("espn_scoreboard.json")))
sched = {g["id"]: g for g in games}
T[0] = START - 3600 + 5
taken, matched, written = set(), {}, set()
due = m.due_looks(sched, taken, T[0])
cap, n = m.take_looks(tmp, due, taken, matched, written)
quotes = [l.split(",") for l in gzip.open(glob.glob(tmp + "/quotes/*/*.csv.gz")[0], "rt").read().strip().split("\\n")]
looks = open(glob.glob(tmp + "/looks/*.csv")[0]).read().strip().split("\\n")
import csv
qr = list(csv.DictReader(io.StringIO("\\n".join(",".join(r) if False else l for l in gzip.open(glob.glob(tmp + "/quotes/*/*.csv.gz")[0], "rt").read().strip().split("\\n")))))
lr = list(csv.DictReader(open(glob.glob(tmp + "/looks/*.csv")[0])))
gr = list(csv.DictReader(open(glob.glob(tmp + "/games/*.csv")[0])))
print(json.dumps({"cap": cap, "n": n, "nq": len(qr), "cols": list(qr[0].keys()) == m.QUOTE_COLS, "series": sorted({r["series"] for r in qr}), "games": sorted({r["espn_id"] for r in qr}),
  "looks": len(lr), "lcols": list(lr[0].keys()) == m.LOOK_COLS, "lookmin": sorted({r["look_min"] for r in qr}), "taken": sorted(list(taken)), "mins": float(qr[0]["mins_to_start"]),
  "vol_col": all("volume" in r and r["volume"] != "" for r in qr), "bid_ask": all(r["yes_ask"] != "" for r in qr), "sizes": all(r["yes_ask_size"] != "" for r in qr), "date": qr[0]["server_date_header"][:3],
  "player": qr[0]["player"] != "", "ev_ok": all(r["event_ticker"].endswith("OTTBUF") for r in qr if r["espn_id"] == "401892644"),
  "no_other": all(r["event_ticker"].endswith(("OTTBUF", "CHIFLA")) for r in qr), "game_rows": [r["match"] for r in gr], "n_markets": sorted({int(r["n_markets"]) for r in lr})[:3]}))`));
  assert.strictEqual(out.cap, 2); assert.ok(out.n > 0 && out.nq === out.n);
  assert.strictEqual(out.cols, true); assert.strictEqual(out.lcols, true);
  assert.deepStrictEqual(out.series, ['KXNHLAST', 'KXNHLGOAL', 'KXNHLPTS']); assert.deepStrictEqual(out.games, ['401892644', '401892645']);
  assert.strictEqual(out.looks, 6); assert.deepStrictEqual(out.lookmin, ['60']); assert.ok(Math.abs(out.mins - 59.9) < 0.2);
  assert.strictEqual(out.vol_col, true, 'volume is stored on every rung at the look'); assert.strictEqual(out.bid_ask, true); assert.strictEqual(out.sizes, true);
  assert.strictEqual(out.date, 'Wed'); assert.strictEqual(out.player, true); assert.strictEqual(out.ev_ok, true); assert.strictEqual(out.no_other, true);
  assert.deepStrictEqual(out.game_rows, ['ok', 'ok']);
  // a game with no listed event: a zero row per series, the look is still taken (so "no ladder yet" differs from "not captured")
  const z = JSON.parse(py(`
g = {"id": "X", "start": START, "state": "pre", "home": {"abbr": "AAA", "id": "1", "name": "a"}, "away": {"abbr": "BBB", "id": "2", "name": "b"}}
T[0] = START - 7200 + 3
taken, matched, written = set(), {}, set()
cap, n = m.take_looks(tmp, m.due_looks({"X": g}, taken, T[0]), taken, matched, written)
import csv
lr = list(csv.DictReader(open(glob.glob(tmp + "/looks/*.csv")[0])))
gr = list(csv.DictReader(open(glob.glob(tmp + "/games/*.csv")[0])))
print(json.dumps({"cap": cap, "n": n, "looks": [(r["series"], r["n_markets"], r["read_ok"], r["event_ticker"]) for r in lr], "match": gr[0]["match"], "glob": glob.glob(tmp + "/quotes/*/*.csv.gz")}))`));
  assert.strictEqual(z.cap, 1); assert.strictEqual(z.n, 0); assert.strictEqual(z.looks.length, 3);
  for (const l of z.looks) { assert.strictEqual(l[1], '0'); assert.strictEqual(l[2], '1'); assert.strictEqual(l[3], ''); }
  assert.strictEqual(z.match, 'no_event_yet');
};

// N6: politeness and failure: one request a second per host, 429 and 5xx backed off with a pause (Retry-After honoured, capped), a dead host is a status never a raise; a failed series is tried
// again while time is left in the look's slack and written with read_ok 0 only at the end of the slack.
gates.N6 = () => {
  const out = JSON.parse(py(`
sleeps = []
m._sleep = lambda x: sleeps.append(x)
FAIL.append("scoreboard")
st, body, d, rv = m.http_get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=1", "espn")
five_xx = [st, body, m.STATS["n5xx"], m.STATS["failed"], len(CALLS), max(sleeps) <= 60]
FAIL.clear(); sleeps.clear(); CALLS.clear()
m.http_get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=1", "espn")
m.http_get("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=2", "espn")
paced = sleeps[0] > 0.9 if sleeps else False
def boom(req, timeout=0): raise OSError("dead")
m._open = boom
st2 = m.http_get("https://external-api.kalshi.com/x", "kalshi")[:2]
m._open = fake_open
games = m.parse_scoreboard(json.loads(fx("espn_scoreboard.json")))
sched = {g["id"]: g for g in games}
FAIL.append("series_ticker=KXNHLAST")
T[0] = START - 3600 + 5
taken, matched, written = set(), {}, set()
early = m.take_looks(tmp, m.due_looks(sched, taken, T[0]), taken, matched, written)
T[0] = START - 3600 + 720 - 30
late = m.take_looks(tmp, m.due_looks(sched, taken, T[0]), taken, matched, written)
import csv
lr = list(csv.DictReader(open(glob.glob(tmp + "/looks/*.csv")[0])))
print(json.dumps({"five_xx": five_xx, "paced": paced, "dead": st2, "early": early, "late_cap": late[0], "ok_flags": sorted({(r["series"], r["read_ok"]) for r in lr}), "taken": len(taken)}))`));
  assert.deepStrictEqual(out.five_xx, [500, null, 4, 1, 4, true]);
  assert.strictEqual(out.paced, true); assert.deepStrictEqual(out.dead, [0, null]);
  assert.deepStrictEqual(out.early, [0, 0], 'a look with one failed series is not written while time is left');
  assert.strictEqual(out.late_cap, 2);
  assert.deepStrictEqual(out.ok_flags, [['KXNHLAST', '0'], ['KXNHLGOAL', '1'], ['KXNHLPTS', '1']]);
};

// N7: a job stops a few minutes past the next start time at least an hour away, and ends early when no look is due before then (no billed idling); the run row counts looks and misses.
gates.N7 = () => {
  const out = JSON.parse(py(`
an = m.anchors_of(m.DEFAULT_ANCHORS)
day = 1_793_000_000 - 1_793_000_000 % 86400
hm = lambda h, mi=0: day + h * 3600 + mi * 60
stops = {"at1500": m.stop_time(hm(15), an) - hm(21, 30), "at2200": m.stop_time(hm(22), an) - hm(25, 30), "at0130": m.stop_time(hm(25, 30), an) - hm(38, 45),
         "at2129": m.stop_time(hm(21, 29), an) - hm(25, 30), "late": m.stop_time(hm(14, 52), an) - hm(21, 30)}
# a weekday job at 14:45 with only the 00:30Z games (first look 22:30Z): nothing is due before its stop (21:35), so it ends at once
T[0] = hm(14, 45)
t0 = T[0]
sleeps = []
m._sleep = lambda x: (sleeps.append(x), T.__setitem__(0, T[0] + x))
m.run(tmp, m.stop_time(T[0], an))
runs = open(glob.glob(tmp + "/runs/*.csv")[0]).read().strip().split("\\n")
print(json.dumps({"stops": stops, "idle_loops": len(sleeps), "ended_early": T[0] - t0 < 600, "runs": runs[1].split(","), "hdr": runs[0].split(",") == m.RUN_COLS}))`));
  assert.deepStrictEqual(out.stops, { at1500: 300, at2200: 300, at0130: 300, at2129: 300, late: 300 });
  assert.strictEqual(out.ended_early, true, 'no look is due before the next start, so the job does not sit idle');
  assert.strictEqual(out.hdr, true); assert.strictEqual(out.runs.length, 14);
};

// N8: a full job on a fake clock takes every look of a game once (120, 90, 60, 30, 5), in order, with the run row counting 10 looks for two games.
gates.N8 = () => {
  const out = JSON.parse(py(`
an = m.anchors_of("21:30,01:30,14:45")
T[0] = START - 7500
def sl(x): T[0] += x
m._sleep = sl
m.run(tmp, START + 600)
import csv
lr = [r for f in sorted(glob.glob(tmp + "/looks/*.csv")) for r in csv.DictReader(open(f))]
runs = [r for f in sorted(glob.glob(tmp + "/runs/*.csv")) for r in csv.DictReader(open(f))]
goal = [r for r in lr if r["series"] == "KXNHLGOAL" and r["espn_id"] == "401892644"]
print(json.dumps({"looks": [r["look_min"] for r in goal], "mins": [float(r["mins_to_start"]) for r in goal], "run": runs[0], "all": len(lr)}))`));
  assert.deepStrictEqual(out.looks, ['120', '90', '60', '30', '5']);
  out.mins.forEach((v, i) => assert.ok(Math.abs(v - [120, 90, 60, 30, 5][i]) < 1.0, 'the look is taken at its target time: ' + v));
  assert.strictEqual(out.all, 30); assert.strictEqual(out.run.looks_captured, '10'); assert.strictEqual(out.run.looks_missed, '0'); assert.strictEqual(out.run.games_seen, '2');
};

// N9: box scores: goals and assists per skater, once per game, only when the game is over; the empty skaters group, goalies and repeated players are not counted twice.
gates.N9 = () => {
  const out = JSON.parse(py(`
body = json.loads(fx("espn_summary.json"))
rows = m.box_goals_assists(body)
games_dir = os.path.join(tmp, "games"); os.makedirs(games_dir)
open(os.path.join(games_dir, "2026-11-03.csv"), "w").write(",".join(m.GAME_COLS) + "\\n" + ",".join(["1", "777", "2026-11-04T00:00:00Z", "pre", "1", "H", "h", "2", "A", "a", "", "", "", "no_event_yet"]) + "\\n")
T[0] = m.parse_iso("2026-11-04T00:00:00Z") + 4 * 3600
tried = {}
w1 = m.results_pass(tmp, T[0], tried)
w2 = m.results_pass(tmp, T[0] + 3600, tried)
import csv
rr = list(csv.DictReader(open(glob.glob(tmp + "/results/*.csv")[0])))
tried2 = {}
body["header"]["competitions"][0]["status"]["type"]["state"] = "in"
print(json.dumps({"n": len(rows), "first": rows[0], "w1": w1, "w2": w2, "cols": list(rr[0].keys()) == m.RESULT_COLS, "rr": len(rr), "ids_unique": len({r["athlete_id"] for r in rr}) == len(rr), "bad": m.box_goals_assists({"x": 1})}))`));
  assert.ok(out.n > 0 && out.n <= 18); assert.strictEqual(out.w1, 1); assert.strictEqual(out.w2, 0, 'a game gets its result once');
  assert.strictEqual(out.cols, true); assert.strictEqual(out.rr, out.n); assert.strictEqual(out.ids_unique, true); assert.deepStrictEqual(out.bad, []);
  assert.strictEqual(out.first.length, 5);
};

// N10: the stop date: nothing runs after it, and the one job entry point never raises.
gates.N10 = () => {
  const out = JSON.parse(py(`
T[0] = m.STOP_ALL + 10
rc = m.main([tmp + "/n"])
T[0] = 1_793_000_000.0
m.run = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bug"))
rc2 = m.main([tmp + "/n2"])
print("RESULT" + json.dumps([rc, rc2, os.path.exists(tmp + "/n")]))`).split('\n').find((l) => l.startsWith('RESULT')).slice(6));
  assert.deepStrictEqual(out, [0, 0, false]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }
