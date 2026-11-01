'use strict';
// The SPORTS-PRE recorder (Oct 31, 2026, research only): it reads public data (Kalshi market data, ESPN public JSON), holds no secret, places no order, writes only to the quote-data branch, is not
// published with the site, has a built-in stop date, and sends every request through one paced, backed-off helper that never raises.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_sportspre.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-sportspre.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, io, os, sys, urllib.error
spec = importlib.util.spec_from_file_location('sp', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));

// SR1: it can never trade or sign anything, whatever it is changed into; three public hosts only; only the four moneyline series.
gates.SR1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)].sort(), ['https://external-api.kalshi.com', 'https://site.api.espn.com', 'https://sports.core.api.espn.com'], 'Kalshi public market data and ESPN public JSON, nothing else');
  assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|API[-_]?KEY|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|os\.environ|getenv/.test(code), 'no account or order endpoint, and it reads no environment variable (no secret can reach it)');
  const series = [...new Set([...code.matchAll(/KX[A-Z0-9]+/g)].map((x) => x[0]))].sort();
  assert.deepStrictEqual(series, ['KXMLBGAME', 'KXNBAGAME', 'KXNCAAFGAME', 'KXNFLGAME'], 'exactly the four moneyline series: no 15 minute ticker, nothing the live bot trades');
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  const mentions = fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_sportspre|record-sportspre|sportspre/.test(fs.readFileSync(path.join(fnDir, f), 'utf8')));
  assert.deepStrictEqual(mentions, [], 'nothing in functions/ mentions it');
  assert.ok(!/record_sportspre|record-sportspre|sportspre/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
};

// SR2: the workflow pushes only the data branch, uses only the built-in token, adds only its own folder, and each job fits inside the 6 hour limit.
gates.SR2 = () => {
  assert.ok(/cron: "50 3,7,11,15,19,23 \* \* \*"/.test(wf) && /cron: "20 \* \* \* \*"/.test(wf) && /--cycle-hours 4/.test(wf), 'six 4 hour jobs a day plus an hourly trigger behind them');
  assert.ok(/timeout-minutes: 330/.test(wf), 'a job fits inside the 6 hour limit');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['sportspre'], 'it adds its own folder and nothing wider');
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-sportspre\s*\n\s*cancel-in-progress: false/.test(wf), 'one group, a running job is never cancelled, so runs never overlap');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'every action pinned by commit SHA');
  assert.ok(!/pip install|npm install|curl |wget /.test(wf), 'installs nothing: the script uses the standard library only');
  assert.ok(/ref: main/.test(wf) && /python3 code\/scripts\/record_sportspre\.py "data\/sportspre\/\$STAMP"/.test(wf));
  assert.ok(!/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither the workflow nor the script is published with the site');
};

// SR3: a built-in stop date that is in the future and matches the workflow; nothing is tracked after it and nothing runs after the end.
gates.SR3 = () => {
  const o = py(`print(json.dumps({"stop": m.STOP_TRACK, "end": m.STOP_ALL, "stop_iso": m.STOP_TRACK_ISO, "end_iso": m.STOP_ALL_ISO}))`);
  assert.strictEqual(o.stop_iso, '2026-12-31T00:00:00Z');
  assert.strictEqual(o.end_iso, '2027-01-01T06:00:00Z');
  assert.ok(o.stop > Date.now() / 1000, 'the stop date is in the future (this gate fails on purpose after the recorder is finished)');
  assert.ok(o.end > o.stop, 'results are collected after the last tracked game');
  assert.ok(wf.includes("2027-01-01T06:00:00Z"), 'the workflow gate uses the same end date');
  const done = py(`
import tempfile
m._now = lambda: m.STOP_ALL + 5
d = tempfile.mkdtemp()
import contextlib
with contextlib.redirect_stdout(io.StringIO()):
    rc = m.main([os.path.join(d, "x")])
print(json.dumps({"rc": rc, "made": os.path.exists(os.path.join(d, "x"))}))`);
  assert.deepStrictEqual(done, { rc: 0, made: false }, 'past the end date it exits at once and records nothing');
  const late = py(`
sched = {"a": {"id": "1", "series": "KXNBAGAME", "start": m.STOP_TRACK + 3600, "state": "pre"}, "b": {"id": "2", "series": "KXNBAGAME", "start": m.STOP_TRACK - 3600, "state": "pre"}}
print(json.dumps([g["id"] for g in m.window_games(sched, m.STOP_TRACK - 3600 - 4000)] + [g["id"] for g in m.window_games(sched, m.STOP_TRACK + 3600 - 4000)]))`);
  assert.deepStrictEqual(late, ['2'], 'a game that starts on or after the stop date is never tracked');
};

// SR4: every request goes through the one helper (pacing, backoff, never raises).
gates.SR4 = () => {
  assert.strictEqual((code.match(/_open\(/g) || []).length, 1, 'the network is opened in exactly one place');
  assert.strictEqual((code.match(/urlopen/g) || []).length, 1);
  assert.strictEqual((code.match(/urllib\.request\.Request\(/g) || []).length, 1);
  const body = code.slice(code.indexOf('def http_get'), code.indexOf('# ---', code.indexOf('def http_get')));
  assert.ok(/_open\(/.test(body) && /Request\(/.test(body), 'and that place is http_get');
  const others = [...code.matchAll(/http_get\(/g)].length;
  assert.ok(others >= 8, 'the callers all use it');
  const o = py(`
import urllib.error
sleeps, calls = [], []
m._sleep = lambda s: sleeps.append(round(s, 2))
class R:
    status = 200
    headers = {"Date": "D"}
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return b'{"a": 1}'
def http_err(code):
    return urllib.error.HTTPError("u", code, "x", {"Retry-After": "7"} if code == 429 else {}, io.BytesIO(b""))
def mk(seq):
    it = iter(seq)
    def _o(req, timeout=0):
        calls.append(1)
        x = next(it)
        if isinstance(x, Exception): raise x
        return x
    return _o
class J(R):
    def read(self, *a): return b'{"a": 1}'
import json as _j
class RJ(R):
    def __init__(self): self._b = io.BytesIO(b'{"a": 1}')
    def read(self, n=-1): return self._b.read(n)
res = {}
m._open = mk([http_err(429), http_err(503), RJ()]); res["recovers"] = list(m.http_get("https://x/", "kalshi")[:3]); res["sleeps_recover"] = [s for s in sleeps if s >= 2]
sleeps.clear(); calls.clear()
m._open = mk([http_err(429)] * 10); r = m.http_get("https://x/", "espn"); res["exhausted"] = [r[0], r[1], len(calls)]
sleeps.clear(); calls.clear()
m._open = mk([http_err(400)]); r = m.http_get("https://x/", "espn"); res["fourhundred"] = [r[0], len(calls), [s for s in sleeps if s >= 2]]
sleeps.clear(); calls.clear()
m._open = mk([OSError("boom")] * 10); r = m.http_get("https://x/", "espn"); res["oserror"] = [r[0], r[1], len(calls)]
res["stats_failed"] = m.STATS["failed"]
print(_j.dumps(res))`);
  assert.deepStrictEqual(o.recovers, [200, { a: 1 }, 'D'], 'a 429 then a 503 are retried and the third answer is returned');
  assert.deepStrictEqual(o.sleeps_recover, [7, 4], 'backoff honours Retry-After on a 429 and doubles on the next');
  assert.deepStrictEqual(o.exhausted, [429, null, 4], 'retries are bounded (4 tries), then the status is returned, never an exception');
  assert.deepStrictEqual(o.fourhundred, [400, 1, []], 'a 400 (no predictor for the game) is not retried');
  assert.deepStrictEqual(o.oserror, [0, null, 4], 'a dead network is a status 0, never an exception');
  assert.ok(o.stats_failed >= 1);
};

// SR5: ESPN's probability is read the way the registration says: both sides when present, the NBA away-only shape completed from teamChanceLoss, junk is nothing.
gates.SR5 = () => {
  const o = py(`
st = lambda gp=None, loss=None: {"statistics": [x for x in ([{"name": "gameProjection", "value": gp}] if gp is not None else []) + ([{"name": "teamChanceLoss", "value": loss}] if loss is not None else [])]}
fb = {"lastModified": "2026-10-31T11:00Z", "homeTeam": st(81.76, 18.24), "awayTeam": st(18.24, 81.76)}
nba = {"homeTeam": {"team": {}}, "awayTeam": st(59.423, 40.577)}
print(json.dumps({"fb": m.predictor_probs(fb), "nba": m.predictor_probs(nba), "junk": [m.predictor_probs(None), m.predictor_probs({}), m.predictor_probs("x")]}))`);
  assert.deepStrictEqual(o.fb, [81.76, 18.24]);
  assert.deepStrictEqual(o.nba, [40.577, 59.423], 'NBA: the home figure is the away team chance of loss');
  assert.deepStrictEqual(o.junk, [[null, null], [null, null], [null, null]]);
};

// SR6: a Kalshi event is paired with the ESPN game by date and both team names; ambiguity and a wrong day are dropped, never guessed.
gates.SR6 = () => {
  const o = py(`
team = lambda i, ab, loc, name: {"id": i, "abbr": ab, "loc": loc, "name": name, "disp": loc + " " + name, "short": name}
game = {"id": "9", "series": "KXNBAGAME", "start": m.parse_iso("2026-11-02T01:00Z"), "home": team("13", "LAL", "Los Angeles", "Lakers"), "away": team("14", "MIA", "Miami", "Heat")}
mk = lambda t, sub: {"ticker": t, "yes_sub_title": sub}
ev = {"KXNBAGAME-26NOV01MIALAL": [mk("KXNBAGAME-26NOV01MIALAL-MIA", "Miami"), mk("KXNBAGAME-26NOV01MIALAL-LAL", "Los Angeles L")],
      "KXNBAGAME-26NOV01LACGSW": [mk("KXNBAGAME-26NOV01LACGSW-LAC", "Los Angeles C"), mk("KXNBAGAME-26NOV01LACGSW-GSW", "Golden State")],
      "KXNBAGAME-26NOV09MIALAL": [mk("KXNBAGAME-26NOV09MIALAL-MIA", "Miami"), mk("KXNBAGAME-26NOV09MIALAL-LAL", "Los Angeles L")]}
e, hm, am, st = m.match_game(game, ev)
none = m.match_game(game, {"KXNBAGAME-26NOV01LACGSW": ev["KXNBAGAME-26NOV01LACGSW"]})
dup = dict(ev); dup["KXNBAGAME-26NOV01MIALAL"] = ev["KXNBAGAME-26NOV01MIALAL"]; dup["KXNBAGAME-26NOV01MIALAL2"] = ev["KXNBAGAME-26NOV01MIALAL"]
amb = m.match_game(game, {k: v for k, v in dup.items() if "09" not in k})
print(json.dumps({"ok": [e, hm["ticker"], am["ticker"], st], "none": [none[0], none[3]], "amb": [amb[0], amb[3]], "date": [str(m.ticker_date("KXMLBGAME-26APR011305NYYBOS")), m.ticker_date("junk")]}))`);
  assert.deepStrictEqual(o.ok, ['KXNBAGAME-26NOV01MIALAL', 'KXNBAGAME-26NOV01MIALAL-LAL', 'KXNBAGAME-26NOV01MIALAL-MIA', 'ok'], 'Los Angeles L is the Lakers; the home market is the home team');
  assert.deepStrictEqual(o.none, ['', 'none']);
  assert.deepStrictEqual(o.amb, ['', 'ambiguous'], 'two equally good events are dropped, not guessed');
  assert.deepStrictEqual(o.date, ['2026-04-01', null]);
};

// SR7: the look window is 120 down to 30 minutes before the start, only for games that have not started.
gates.SR7 = () => {
  const o = py(`
mk = lambda i, off, state="pre": {"id": i, "series": "KXNFLGAME", "start": 1000000 + off, "state": state}
sched = {i: mk(i, off, st) for i, off, st in [("a", 7200, "pre"), ("b", 7201, "pre"), ("c", 1800, "pre"), ("d", 1799, "pre"), ("e", 3600, "in"), ("f", 3600, "post"), ("g", 3600, "pre")]}
print(json.dumps(sorted(g["id"] for g in m.window_games(sched, 1000000))))`);
  assert.deepStrictEqual(o, ['a', 'c', 'g'], 'both edges inclusive; started or finished games never');
};

// SR8: one poll writes both team markets with the Kalshi Date header, the RAW ESPN responses with the recorder's own receive time, and a game ESPN has no figure for is probed once and then left alone.
gates.SR8 = () => {
  const o = py(`
import tempfile, gzip
d = tempfile.mkdtemp(); out = m.Out(d)
team = lambda i, ab, loc, name: {"id": i, "abbr": ab, "loc": loc, "name": name, "disp": loc + " " + name, "short": name}
mkg = lambda i: {"id": i, "series": "KXNBAGAME", "start": m.parse_iso("2026-11-01T02:00Z"), "state": "pre", "home": team("30", "CHA", "Charlotte", "Hornets"), "away": team("20", "PHI", "Philadelphia", "76ers")}
mkm = lambda t, sub, b, a: {"ticker": t, "event_ticker": "KXNBAGAME-26OCT31PHICHA", "yes_sub_title": sub, "yes_bid_dollars": b, "yes_ask_dollars": a, "yes_bid_size_fp": "100.00", "yes_ask_size_fp": "50.00", "status": "active"}
mkts = [mkm("KXNBAGAME-26OCT31PHICHA-CHA", "Charlotte", "0.4900", "0.5000"), mkm("KXNBAGAME-26OCT31PHICHA-PHI", "Philadelphia", "0.5100", "0.5200")]
pred = {"lastModified": "2026-10-31T22:00Z", "homeTeam": {"team": {}}, "awayTeam": {"statistics": [{"name": "gameProjection", "value": 59.423}, {"name": "teamChanceLoss", "value": 40.577}]}}
seen = []
def fake(url, host):
    seen.append(url)
    if "/markets?series_ticker=" in url: return 200, {"markets": mkts, "cursor": ""}, "Sat, 31 Oct 2026 20:00:00 GMT", 1111
    if url.endswith("/predictor"): return (200, pred, "Sat, 31 Oct 2026 20:00:01 GMT", 2222) if "/2001/" in url else (400, None, "", 3333)
    if "/summary?event=2001" in url: return 200, {"predictor": {"homeTeam": {"gameProjection": "40.6"}, "awayTeam": {"gameProjection": "59.4"}}, "header": {"competitions": [{"status": {"type": {"state": "pre"}}}]}}, "D2", 4444
    return 200, {"header": {"competitions": [{"status": {"type": {"state": "pre"}}}]}}, "D3", 5555
m.http_get = fake
matched, written, nopred = {}, set(), set()
m.poll_cycle(out, [mkg("2001"), mkg("2002")], matched, written, 99, nopred)
n_first = len(seen)
m.poll_cycle(out, [mkg("2001"), mkg("2002")], matched, written, 99, nopred)
out.close()
rd = lambda n: [l.split(",") for l in open(os.path.join(d, n)).read().strip().split("\\n")]
raw = [json.loads(l) for l in open(os.path.join(d, "espn_raw.jsonl"))]
q = rd("quotes.csv")
second_reqs = len(seen) - n_first
print(json.dumps({"quote_rows_2001": [r for r in q if "2001" in r], "n_quotes": len(q) - 1, "kinds": [(r["kind"], r["espn_id"], r["recv_ms"], r["http"]) for r in raw], "nopred": sorted(nopred),
  "games_rows": len(rd("games.csv")) - 1, "pred": rd("predictor.csv"), "second_reqs": second_reqs, "raw_body": raw[0]["body"]["lastModified"], "date": raw[0]["date_header"]}))`);
  assert.strictEqual(o.n_quotes, 4 + 2, 'first poll: two markets for each of two games; second poll: two for the game still probed');
  assert.ok(o.quote_rows_2001.every((r) => r[1].includes('Sat'), 'the server Date header is on every quote row'));
  assert.deepStrictEqual(o.kinds.slice(0, 2), [['core_predictor', '2001', 2222, 200], ['summary_predictor', '2001', 4444, 200]], 'raw ESPN bodies carry the recorder receive time');
  assert.strictEqual(o.raw_body, '2026-10-31T22:00Z', 'the raw body is stored as returned (its lastModified is kept)');
  assert.deepStrictEqual(o.nopred, ['KXNBAGAME2002'], 'a game with no ESPN figure is marked');
  assert.strictEqual(o.games_rows, 2, 'one games row per game per job');
  assert.deepStrictEqual(o.pred[1].slice(3, 8), ['core_predictor', '200', '2026-10-31T22:00Z', '40.577', '59.423']);
  assert.strictEqual(o.second_reqs, 1 + 2, 'the second poll: one Kalshi read and two ESPN reads for the one game still probed; the no-figure game costs nothing');
};

// SR9: results are written once per game, only when both Kalshi markets have a result (or after 72 hours, marked unresolved), with the core predictor read again after the game for the audit.
gates.SR9 = () => {
  const o = py(`
import tempfile, csv
root = tempfile.mkdtemp(); jd = os.path.join(root, "2026-11-01", "0000"); os.makedirs(jd)
out = m.Out(jd)
now = 10000000
out.write("games", [[1, "KXNBAGAME", "77", m.iso(now - 4 * 3600), "30", "CHA", "Hornets", "20", "PHI", "76ers", "EV", "EV-CHA", "EV-PHI", "ok"],
                    [1, "KXNBAGAME", "78", m.iso(now - 3600), "30", "CHA", "Hornets", "20", "PHI", "76ers", "EV2", "EV2-CHA", "EV2-PHI", "ok"],
                    [1, "KXNBAGAME", "79", m.iso(now - 5 * 86400), "30", "CHA", "Hornets", "20", "PHI", "76ers", "EV3", "EV3-CHA", "EV3-PHI", "ok"]])
out.flush()
settled = {"EV-CHA": "yes", "EV-PHI": "no", "EV3-CHA": "", "EV3-PHI": ""}
def fake(url, host):
    if "/markets/" in url: return 200, {"market": {"result": settled.get(url.rsplit("/", 1)[1], "")}}, "", 1
    if url.endswith("/predictor"): return 200, {"lastModified": "x"}, "D", 9
    return 200, {"header": {"competitions": [{"status": {"type": {"state": "post", "completed": True}}, "competitors": [{"homeAway": "home", "score": "101"}, {"homeAway": "away", "score": "99"}]}]}}, "D", 5
m.http_get = fake
tried = {}
n1 = m.results_pass(out, root, now, tried)
n2 = m.results_pass(out, root, now + 4000, tried)
out.close()
rows = list(csv.DictReader(open(os.path.join(jd, "results.csv"))))
raw = [json.loads(l)["kind"] for l in open(os.path.join(jd, "espn_raw.jsonl"))]
print(json.dumps({"n": [n1, n2], "rows": [[r["espn_id"], r["home_result"], r["away_result"], r["home_score"], r["away_score"], r["resolved"]] for r in rows], "raw": raw}))`);
  assert.deepStrictEqual(o.n, [2, 0], 'game 78 is too young; game 77 is final; game 79 is given up on; nothing is written twice');
  assert.deepStrictEqual(o.rows, [['79', '', '', '101', '99', '0'], ['77', 'yes', 'no', '101', '99', '1']], 'oldest first');
  assert.deepStrictEqual(o.raw, ['core_predictor_post'], 'the predictor is re-read once, after a final result');
};

// SR10: back to back jobs leave no gap (the same stop rule as the other recorders).
gates.SR10 = () => {
  const o = py(`print(json.dumps([m.cycle_stop_time(14400 * 5 + 1000, 14400), m.cycle_stop_time(14400 * 5 + 13000, 14400)]))`);
  assert.deepStrictEqual(o, [14400 * 6 + 60, 14400 * 7 + 60]);
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }
