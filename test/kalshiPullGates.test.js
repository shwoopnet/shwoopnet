'use strict';
// kalshi-pull (Nov 12, 2026, the owner waived reading Kalshi's terms; see CLAUDE.md): a MANUAL workflow that pulls Kalshi's PUBLIC market data for research. These gates state the consequence:
// nothing starts it by itself, it can only ask one host for public data, at most once a second, it stops when told no three times, it holds no key, and what it fetches never reaches main or the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'kalshi_pull.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'kalshi-pull.yml'), 'utf8');
const jobDir = path.join(root, 'kalshi-scalper', 'workers', 'kalshi_pull_jobs');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '').replace(/^(DENY_PATH|DENY_PARAM) = .*$/gm, '');
const wfCode = wf.replace(/^\s*#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, os, tempfile
spec = importlib.util.spec_from_file_location('kp', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8' }));
const jobs = fs.readdirSync(jobDir).filter((f) => /^[A-Z0-9_]+\.json$/.test(f) && f !== 'NOSIDE1_CUTS.json');

// KP1: only a person can start it. No schedule, push, pull request or any other trigger; a dry run is the default.
gates.KP1 = () => {
  const on = wfCode.match(/^on:\n((?:[ ]+.*\n|\n)+?)(?=\S)/m)[1];
  assert.ok(/^ {2}workflow_dispatch:/m.test(on));
  assert.deepStrictEqual([...on.matchAll(/^ {2}(\w+):/gm)].map((x) => x[1]), ['workflow_dispatch'], 'workflow_dispatch is the only trigger');
  assert.ok(!/schedule|cron|pull_request|push:|workflow_run|repository_dispatch/.test(on));
  assert.ok(/dry_run:[\s\S]*?default: "true"/.test(wf), 'the default is a dry run');
};

// KP2: the token can write the repo and nothing else; the built-in token is the only secret; no input or secret is pasted into a shell line.
gates.KP2 = () => {
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf));
  const runLines = wfCode.split('\n').filter((l) => /^\s+(run:|\S)/.test(l));
  const runBlocks = [...wfCode.matchAll(/run: \|\n((?: {10}.*\n?)+)/g)].map((x) => x[1]).join('\n');
  assert.ok(runBlocks.length > 100, 'run blocks found');
  assert.ok(!/\$\{\{/.test(runBlocks), 'no ${{ }} expression inside a run: block (inputs and the token go through env:)');
  assert.ok(!/github\.event|pull_request_target/.test(wfCode));
  assert.ok(runLines.length > 0);
};

// KP3: actions pinned by full commit hash, only checkout, nothing installed or downloaded.
gates.KP3 = () => {
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length === 1 && /^actions\/checkout@[0-9a-f]{40}$/.test(uses[0]));
  assert.ok(!/pip install|npm install|curl |wget /.test(wfCode));
  assert.ok(!/^\s*(from|import)\s+(?!argparse|calendar|gzip|hashlib|json|os|re|sys|time|urllib)/m.test(code), 'the script imports only the standard library it needs');
};

// KP4 (Nov 12, 2026, the owner): the job id is a free string, so a pull request that only adds a job file never edits the workflow. The consequence: a bad id, or an id with no job file on main, stops the run before anything is sent, and the id never reaches a shell as code.
gates.KP4 = () => {
  const job = wfCode.match(/^ {6}job:\n((?: {8}.*\n)+)/m)[1];
  assert.ok(/^ {8}type: string$/m.test(job) && !/options:|type: choice/.test(job), 'the job input is a plain string with no choice list');
  assert.ok(!/case "\$JOB"/.test(wfCode), 'no hard-coded list of job names in a case guard');
  assert.ok(/JOB: \$\{\{ inputs\.job \}\}/.test(wf) && /DRY_RUN: \$\{\{ inputs\.dry_run \}\}/.test(wf), 'both inputs reach the steps only through env');
  assert.strictEqual((wfCode.match(/inputs\.job/g) || []).length, 1, 'inputs.job appears once, as the env assignment');
  const bodies = [...wfCode.matchAll(/run: \|\n((?: {10}.*\n?)+)/g)].map((x) => x[1]).join('\n');
  assert.ok(!/inputs\./.test(bodies) && !/\$\{\{/.test(bodies), 'no expression is interpolated into any run: script');
  assert.ok(wfCode.includes('[[ "$JOB" =~ ^[A-Z][A-Z0-9_]{2,60}$ ]] || { echo "bad job id"; exit 1; }'), 'the exact id pattern is checked in the first step, through env');
  assert.ok(wfCode.indexOf('bad job id') < wfCode.indexOf('uses: actions/checkout'), 'the id is validated before anything is checked out');
  const ex = wfCode.indexOf('test -f "code/kalshi-scalper/workers/kalshi_pull_jobs/$JOB.json"');
  assert.ok(ex > wfCode.indexOf('uses: actions/checkout') && ex < wfCode.indexOf('kalshi_pull.py'), 'the job file is required in the checkout of main, before the runner is called');
  assert.ok(/ref: main\n\s+path: code/.test(wfCode) && (wfCode.match(/ref:/g) || []).length === 1, 'the only checkout is of main, so a job cannot run from another branch');
  assert.ok(!/\.\.|\*/.test(wfCode.slice(ex, ex + 160).split('\n')[0]), 'no globbing and no .. in the existence test');
  // the pattern itself, as bash reads it: a newline, a path, a lowercase or a short id is refused
  const ok = (v) => { try { execFileSync('bash', ['-c', '[[ "$JOB" =~ ^[A-Z][A-Z0-9_]{2,60}$ ]]'], { env: { JOB: v } }); return true; } catch (e) { return false; } };
  assert.deepStrictEqual(['SPREADLISTS', 'AB', 'abc', 'A../B', 'ABC\nx', 'ABC DEF', 'A' + 'B'.repeat(60), 'A' + 'B'.repeat(61)].map(ok), [true, false, false, false, false, false, true, false]);
  // every job file's id fits the pattern, so none is locked out
  for (const f of jobs) assert.ok(/^[A-Z][A-Z0-9_]{2,60}$/.test(f.replace('.json', '')), f + ': the id fits the workflow pattern');
};

// KP5: one host, pinned in code, https only, no other URL anywhere in the script.
gates.KP5 = () => {
  assert.ok(!/https?:\/\/[A-Za-z0-9]/.test(code), 'no host is written out anywhere but the HOST constant');
  assert.ok(/HOST = "api\.elections\.kalshi\.com"/.test(code) && /BASE_PATH = "\/trade-api\/v2"/.test(code));
  assert.ok(/PERPS_HOST = "external-api\.kalshi\.com"/.test(code) && /PERPS_BASE_PATH = "\/trade-api\/v2\/margin"/.test(code));
  assert.ok(!/http:\/\//.test(code));
  const hosts = py('print(json.dumps([m.build_url({}, "/markets", {"series_ticker": "KXA"}), m.build_url({}, "/markets", {}, "abc=")]))');
  assert.deepStrictEqual(hosts, ['https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXA', 'https://api.elections.kalshi.com/trade-api/v2/markets?cursor=abc%3D']);
  for (const f of jobs) { const jj = JSON.parse(fs.readFileSync(path.join(jobDir, f), 'utf8')); if (jj.route) assert.ok(!('host' in jj) && !('base_path' in jj), f + ': a routed job carries no host'); else assert.strictEqual(jj.host, 'api.elections.kalshi.com', f); }
  const bad = py(`
def t(j):
    try: m.check_job(j); return "ok"
    except m.Refused: return "refused"
j = json.load(open(os.path.join(m.JOB_DIR, "COMBO1_OPENBOOK.json")))
j["status"] = "active"
print(json.dumps([t(j), t(dict(j, host="example.com")), t(dict(j, base_path="/other"))]))`);
  assert.deepStrictEqual(bad, ['ok', 'refused', 'refused']);
};

// KP6: GET only, no key, no auth header, no cookie, no body, no proxy, no address switching.
gates.KP6 = () => {
  assert.ok(!/POST|PUT|PATCH|DELETE|method\s*=|data\s*=|\.add_header|Authorization|Cookie|Bearer|X-Api|signature|private_key/i.test(code), 'no write method, body, auth or signing');
  assert.ok(!/os\.environ\[?[^\n]*(KEY|TOKEN|SECRET)/i.test(code) && !/getenv\([^)]*(KEY|TOKEN|SECRET)/i.test(code), 'it reads no key-like environment variable');
  assert.ok(!/ProxyHandler|proxies|socks|X-Forwarded|source_address|bind\(|rotate|getaddrinfo|HTTP_PROXY|HTTPS_PROXY|requests\.|httpx|aiohttp|threading|asyncio|multiprocessing|concurrent/i.test(code), 'one stream, no proxy, no address switching, no threads');
  assert.ok(!/portfolio|\/orders\b|firebase|firestore/.test(code.replace(/DENY_PATH = [^\n]*/, '')), 'no account or order path outside the deny list');
  const denied = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "COMBO1_OPENBOOK.json")))
j["status"] = "active"
def t(path, params):
    j2 = json.loads(json.dumps(j)); j2["allowed_endpoints"].append({"name": "x", "method": "GET", "path_pattern": ".*", "params_allowed": ["series_ticker", "api_key", "status", "limit"]})
    j2["requests"][0] = {"id": "X", "path": path, "params": params}
    try: m.check_job(j2); return "ok"
    except m.Refused: return "refused"
print(json.dumps([t("/portfolio/balance", {}), t("/markets", {"api_key": "x"}), t("/markets", {"series_ticker": "KXMVENBASINGLEGAME", "limit": 5}), t("/exchange/status", {})]))`);
  assert.deepStrictEqual(denied, ['refused', 'refused', 'ok', 'refused']);
};

// KP7: an honest, generic User-Agent, not a browser's and with no personal details.
gates.KP7 = () => {
  const ua = py('print(json.dumps(m.UA))');
  assert.deepStrictEqual(ua, { 'User-Agent': 'shwoopnet-research-pull', Accept: 'application/json' });
  assert.ok(!/Mozilla|Chrome|Safari|Firefox|AppleWebKit|Gecko|Edge|Opera/i.test(JSON.stringify(ua)) && !/@|mailto|http/.test(ua['User-Agent']));
};

// KP8: a redirect is never followed (a mocked 302 to a second server is read as a failed request and the target is never asked).
gates.KP8 = () => {
  assert.ok(/_NoRedirect/.test(code) && /_NoRedirect\(\)/.test(code) && !/build_opener/.test(code) && !/urlopen/.test(code));
  const r = py(`
import threading, http.server
hit = []
class T(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/a":
            self.send_response(302); self.send_header("Location", "http://127.0.0.1:%d/b" % self.server.other); self.end_headers()
        else:
            hit.append(1); self.send_response(200); self.end_headers(); self.wfile.write(b'{"x":"INTERNAL"}')
b = http.server.HTTPServer(("127.0.0.1", 0), T); b.other = 0
a = http.server.HTTPServer(("127.0.0.1", 0), T); a.other = b.server_address[1]
for srv in (a, b): threading.Thread(target=srv.serve_forever, daemon=True).start()
st, body, date, trunc = m.http_get("http://127.0.0.1:%d/a" % a.server_address[1])
print(json.dumps({"status": st, "body": len(body), "target_hit": len(hit)}))`);
  assert.deepStrictEqual(r, { status: 302, body: 0, target_hit: 0 });
};

// KP9: never faster than one request a second, in the constant, in the job check and in a mocked run; a job can only slow it.
gates.KP9 = () => {
  assert.deepStrictEqual(py('print(json.dumps([m.GAP_S, m.MAX_429_IN_ROW, m.HARD_MAX_REQUESTS]))'), [1.0, 3, 1200]);
  const out = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "COMBO1_OPENBOOK.json")))
j["status"] = "active"
try: m.check_job(dict(j, pacing_seconds=0.5)); fast = "ok"
except m.Refused: fast = "refused"
clock = [1000.0]; starts = []
def sl(d): clock[0] += d
def ck(): return clock[0]
def fetch(url):
    starts.append(clock[0]); clock[0] += 0.05
    return 200, b'{"markets": []}', "D", False
d = tempfile.mkdtemp()
st = m.run(j, os.path.join(d, "o"), fetch=fetch, clock=ck, sleep=sl, out=lambda *a: None)
gaps = [round(b - a, 3) for a, b in zip(starts, starts[1:])]
print(json.dumps({"fast": fast, "st": st, "n": len(starts), "mingap": min(gaps)}))`);
  assert.strictEqual(out.fast, 'refused');
  assert.deepStrictEqual(out.st, ['complete', 0]);
  assert.strictEqual(out.n, 3);
  assert.ok(out.mingap >= 1.0, 'at least a second between request starts');
};

// KP10: a 429 backs off with doubling waits and asks the same request again; THREE in a row end the run and what was fetched is still written; one success resets the count; nothing retries around a refusal.
gates.KP10 = () => {
  const out = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "ROLLOFF_PROXY.json")))
def go(script):
    clock = [1000.0]; slept = []; seen = []
    def sl(d): slept.append(d); clock[0] += d
    def fetch(url):
        seen.append(url); clock[0] += 0.05
        code = script.pop(0) if script else 200
        return code, (b'{"markets": []}' if code == 200 else b""), "D", False
    d = tempfile.mkdtemp(); o = os.path.join(d, "o")
    st = m.run(j, o, fetch=fetch, clock=lambda: clock[0], sleep=sl, out=lambda *a: None)
    man = json.load(open(os.path.join(o, "manifest.json")))
    return {"st": st, "n": len(seen), "slept": [s for s in slept if s >= 5], "distinct": len(set(seen)), "files": sorted(os.listdir(o)), "status_file": open(os.path.join(o, "STATUS")).read().strip(), "rows": len(man["rows"])}
print(json.dumps({"three": go([200, 429, 429, 429]), "two": go([429, 429, 200]), "reset": go([429, 429, 200, 429, 429, 200, 200])}))`);
  assert.deepStrictEqual(out.three.st, ['stopped_429', 2]);
  assert.strictEqual(out.three.n, 4, 'the first answer, then exactly three refusals, then nothing more is sent');
  assert.deepStrictEqual(out.three.slept, [5, 10], 'doubling pause between the refusals');
  assert.ok(out.three.files.includes('0001.json.gz') && out.three.files.includes('manifest.json'), 'what was fetched is kept');
  assert.strictEqual(out.three.status_file, 'stopped_429');
  assert.deepStrictEqual(out.two.st, ['complete', 0]);
  assert.deepStrictEqual(out.two.slept, [5, 10]);
  assert.strictEqual(out.reset.st[0], 'complete', 'a success resets the run of refusals');
  assert.ok(/backoff = min\(BACKOFF_MAX_S, backoff \* 2\)/.test(code));
};

// KP11: the cap ends the run (pages count), a 404 is an answer, three other failures in a row end the run.
gates.KP11 = () => {
  const out = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "ROLLOFF_PROXY.json")))
def go(job, fn):
    clock = [1000.0]
    seen = []
    def fetch(url):
        seen.append(url); clock[0] += 0.05
        return fn(len(seen), url)
    d = tempfile.mkdtemp()
    st = m.run(job, os.path.join(d, "o"), fetch=fetch, clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s), out=lambda *a: None)
    return st[0], len(seen)
pages = lambda n, u: (200, json.dumps({"markets": [], "cursor": "next%d" % n}).encode(), "D", False)
capped = go(dict(j, max_requests=3, requests=j["requests"][:2]), pages)
full = go(j, pages)
nf = go(j, lambda n, u: (404, b"", "", False))
bad = go(j, lambda n, u: (500, b"", "", False))
print(json.dumps({"capped": capped, "full": full, "notfound": nf, "bad": bad}))`);
  assert.deepStrictEqual(out.capped, ['stopped_at_cap', 3], 'pages count against the cap');
  assert.deepStrictEqual(out.full, ['complete', 9], 'six requests, nine pages, under the cap of 12 (the two series reads have no cursor page limit beyond max_pages)');
  assert.deepStrictEqual(out.notfound, ['complete', 6]);
  assert.deepStrictEqual(out.bad, ['stopped_failures', 3]);
};

// KP12: an answer over 5 MB is cut and marked, a body that is not an object is stored and never read for a cursor, and a bad cursor is never followed.
gates.KP12 = () => {
  const out = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "ROLLOFF_PROXY.json")))
def go(body, trunc=False):
    clock = [1000.0]
    d = tempfile.mkdtemp(); o = os.path.join(d, "o")
    job = dict(j, requests=j["requests"][:1])
    m.run(job, o, fetch=lambda u: (200, body, "D", trunc), clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s), out=lambda *a: None)
    man = json.load(open(os.path.join(o, "manifest.json")))
    return [man["requests_sent"], man["rows"][0]["body_kind"], man["rows"][0]["truncated"]]
print(json.dumps({"list": go(b"[1,2,3]"), "text": go(b"not json"), "null": go(b"null"), "trunc": go(b'{"cursor":"abc"', True), "badcursor": go(b'{"cursor":"../../x?y=1"}'), "limits": [m.MAX_BODY_BYTES, m.MAX_RUN_BYTES]}))`);
  assert.deepStrictEqual(out.list, [1, 'not_object', false]);
  assert.deepStrictEqual(out.text, [1, 'not_object', false]);
  assert.deepStrictEqual(out.null, [1, 'not_object', false]);
  assert.deepStrictEqual(out.trunc, [1, 'not_object', true]);
  assert.deepStrictEqual(out.badcursor, [1, 'object', false], 'a cursor with a slash or a query is not followed');
  assert.deepStrictEqual(out.limits, [5000000, 200000000]);
  assert.ok(/r\.read\(MAX_BODY_BYTES \+ 1\)/.test(code), 'the read itself is bounded');
};

// KP13: a job file cannot carry a path outside its patterns, a traversal or an injected parameter; none of those sends a request.
gates.KP13 = () => {
  const out = py(`
base = json.load(open(os.path.join(m.JOB_DIR, "COMBO1_OPENBOOK.json")))
base["status"] = "active"   # COMBO1_OPENBOOK is retired; these checks use its shape as a known-good plan
def t(req=None, **top):
    j = json.loads(json.dumps(base)); j.update(top)
    if req is not None: j["requests"] = [req]
    try: m.check_job(j); return "ok"
    except m.Refused: return "refused"
ok = lambda **p: {"id": "A", "path": "/markets", "params": dict({"series_ticker": "KXMVENBASINGLEGAME"}, **p)}
print(json.dumps({
 "base": t(), "trav": t({"id": "A", "path": "/markets/../portfolio/balance", "params": {}}), "enc": t({"id": "A", "path": "/markets%2f..", "params": {}}),
 "amp": t(ok(status="open&limit=9")), "q": t(ok(status="open?x=1")), "hash": t(ok(status="open#y")), "crlf": t(ok(status="open\\r\\nHost: evil")), "eq": t(ok(status="a=b")),
 "series": t({"id": "A", "path": "/markets", "params": {"series_ticker": "KXNOTLISTED"}}), "unknownparam": t(ok(foo="1")), "url": t({"id": "A", "path": "/markets", "params": {}, "url": "https://evil.example/"}),
 "unknownkey": t(extra="x"), "owner": t(owner="SOMEONE"), "noheld": t(heldout=""), "reg": t(registration="../etc/passwd"), "inactive": t(status="inactive"),
 "cap": t(max_requests=1201), "overcap": t(max_requests=2), "nonascii": "n/a", "dupe": "n/a"}))`);
  const expectRefused = ['trav', 'enc', 'amp', 'q', 'hash', 'crlf', 'eq', 'series', 'unknownparam', 'url', 'unknownkey', 'owner', 'noheld', 'reg', 'inactive', 'cap', 'overcap'];
  assert.strictEqual(out.base, 'ok');
  for (const k of expectRefused) assert.strictEqual(out[k], 'refused', k);
};

// KP14: every job file has a cap, an owner, a registration and an allowlist; the first jobs are in the owner's rank order with the stated counts; ECONLAG and BALLOTNO are not here.
gates.KP14 = () => {
  const j = {};
  for (const f of jobs) j[f.replace('.json', '')] = JSON.parse(fs.readFileSync(path.join(jobDir, f), 'utf8'));
  assert.deepStrictEqual(Object.keys(j).sort(), ['CENSUS_LISTING', 'CFRTI_K_CANDLES', 'CFRTI_K_LISTS', 'CFRTI_K_PROBE', 'CFRTI_K_R6SLICE', 'COMBO1_OPENBOOK', 'ECONLAG_CALENDAR', 'ESOCTIE_CANDLES_P1', 'ESOCTIE_CANDLES_P2', 'ESOCTIE_CANDLES_P3', 'ESOCTIE_CANDLES_P4', 'ESOCTIE_LISTS', 'HOURLYTEMP_LISTS', 'INGAMELAG_M1', 'INGAMELAG_M1A', 'INGAMELAG_M1B', 'INPLAYJUMP_LISTS', 'MAPBREAK_CANDLES', 'MAPBREAK_CANDLES_REST', 'MAPBREAK_LISTS', 'NHLOT_CANDLES', 'NHLOT_LISTS', 'NOSIDE1_CANDLES', 'NOSIDE1_CANDLES_P1', 'NOSIDE1_CANDLES_P2', 'NOSIDE1_CANDLES_P3', 'NOSIDE1_LISTS', 'PERPBTC1M', 'PERPETH1M', 'POLAPPR1_CANDLES', 'POLAPPR1_CANDLES_P2', 'POLAPPR1_CANDLES_P3', 'REMATCH_STAGE1_CANDLES', 'ROLLOFF_PROXY', 'SOCDERIV_LISTS', 'SPREADCELL1', 'SPREADCELL1_REST', 'SPREADLISTS', 'TESTING_LISTS_BUNDLE', 'TIE3_CANDLES', 'WHEEL0_LISTS']);
  assert.ok(!jobs.some((f) => /BALLOTNO|ECONLAG_CANDLES/i.test(f)), 'BALLOTNO and the not-yet-built candle stages are not included');
  for (const [id, job] of Object.entries(j)) {
    assert.strictEqual(job.job_id, id);
    assert.ok(Number.isInteger(job.max_requests) && job.max_requests >= 1 && job.max_requests <= 1200, id + ': cap');
    assert.ok(job.pacing_seconds >= 1.0 && job.stop_rules.stop_after_consecutive_429 <= 3, id + ': pace and 429 rule');
    assert.ok(job.registration && job.heldout && job.owner, id + ': registration, heldout, owner');
    assert.ok(Array.isArray(job.allowed_endpoints) && Array.isArray(job.series_allowlist) && Array.isArray(job.ticker_allowlist), id + ': allowlists');
    assert.ok(job.requests.length <= job.max_requests, id + ': requests within the cap');
  }
  // rank 1: the approval NO-side candle pull (the lists stage is retired: the universe is frozen), rank 2: the spread cell
  assert.strictEqual(j.NOSIDE1_LISTS.status, 'retired');
  assert.strictEqual(j.NOSIDE1_CANDLES.max_requests, 1034);
  assert.strictEqual(j.NOSIDE1_CANDLES.requests.length, 1034);
  assert.strictEqual(j.SPREADCELL1.max_requests, 274);
  assert.strictEqual(j.SPREADCELL1.requests.length, 274);
  assert.strictEqual(j.SPREADCELL1_REST.max_requests, 36);
  assert.strictEqual(j.SPREADCELL1_REST.requests.length, 36);
  assert.deepStrictEqual(['NOSIDE1_CANDLES_P1', 'NOSIDE1_CANDLES_P2', 'NOSIDE1_CANDLES_P3'].map((n) => j[n].requests.length), [345, 345, 344]);
  assert.strictEqual(j.SPREADLISTS.max_requests, 11);
  assert.strictEqual(j.SPREADLISTS.requests.length, 11);
  assert.strictEqual(j.ROLLOFF_PROXY.max_requests, 12);
  assert.strictEqual(j.COMBO1_OPENBOOK.max_requests, 3);
  assert.strictEqual(j.COMBO1_OPENBOOK.status, 'retired');
  // jobs v3 (Nov 12): the counts each job was registered with
  const v3 = { CFRTI_K_LISTS: [2, 30], CFRTI_K_PROBE: [1, 1], CFRTI_K_R6SLICE: [20, 20], ECONLAG_CALENDAR: [10, 10], NHLOT_LISTS: [4, 10], INGAMELAG_M1A: [108, 123], INGAMELAG_M1B: [107, 122] };
  for (const [id, [n, cap]] of Object.entries(v3)) { assert.strictEqual(j[id].status, 'active', id); assert.strictEqual(j[id].requests.length, n, id + ': requests'); assert.strictEqual(j[id].max_requests, cap, id + ': cap'); }
  // INGAMELAG_M1 (one 215 request job) is retired: it risked the 200 MB a run cap, so the same fixed list runs as M1A and M1B
  assert.strictEqual(j.INGAMELAG_M1.status, 'retired');
  assert.ok(/INGAMELAG_M1A/.test(j.INGAMELAG_M1.notes) && /INGAMELAG_M1B/.test(j.INGAMELAG_M1.notes), 'the retired job points to M1A and M1B');
  // development dates only: the CFRTI-K lists stop before the 2026-11-05 held-out cutoff (max_close_ts 1793836800)
  assert.ok(j.CFRTI_K_LISTS.requests.some((r) => r.params && r.params.max_close_ts === 1793836800), 'CFRTI_K_LISTS live list bounded at the cutoff');
  // the runner refuses a retired job (a job that is not active never runs) and passes the rest
  const verdicts = py(`
out = {}
for n in ("NOSIDE1_LISTS", "COMBO1_OPENBOOK", "NOSIDE1_CANDLES", "NOSIDE1_CANDLES_P1", "NOSIDE1_CANDLES_P2", "NOSIDE1_CANDLES_P3", "SPREADCELL1", "SPREADCELL1_REST", "SPREADLISTS", "ROLLOFF_PROXY", "PERPBTC1M", "PERPETH1M", "CFRTI_K_LISTS", "CFRTI_K_PROBE", "CFRTI_K_R6SLICE", "ECONLAG_CALENDAR", "NHLOT_LISTS", "INGAMELAG_M1", "INGAMELAG_M1A", "INGAMELAG_M1B", "INPLAYJUMP_LISTS", "CENSUS_LISTING", "POLAPPR1_CANDLES", "POLAPPR1_CANDLES_P2", "POLAPPR1_CANDLES_P3", "CFRTI_K_CANDLES", "HOURLYTEMP_LISTS", "TESTING_LISTS_BUNDLE", "SOCDERIV_LISTS", "MAPBREAK_CANDLES", "MAPBREAK_LISTS", "ESOCTIE_LISTS", "TIE3_CANDLES", "WHEEL0_LISTS", "MAPBREAK_CANDLES_REST", "ESOCTIE_CANDLES_P1", "ESOCTIE_CANDLES_P2", "ESOCTIE_CANDLES_P3", "ESOCTIE_CANDLES_P4", "NHLOT_CANDLES", "REMATCH_STAGE1_CANDLES"):
    try: m.check_job(json.load(open(os.path.join(m.JOB_DIR, n + ".json")))); out[n] = "ok"
    except m.Refused as e: out[n] = "refused"
print(json.dumps(out))`);
  assert.deepStrictEqual(verdicts, { NOSIDE1_LISTS: 'refused', COMBO1_OPENBOOK: 'refused', NOSIDE1_CANDLES: 'ok', NOSIDE1_CANDLES_P1: 'ok', NOSIDE1_CANDLES_P2: 'ok', NOSIDE1_CANDLES_P3: 'ok', SPREADCELL1: 'ok', SPREADCELL1_REST: 'ok', SPREADLISTS: 'ok', ROLLOFF_PROXY: 'ok', PERPBTC1M: 'ok', PERPETH1M: 'refused', CFRTI_K_LISTS: 'ok', CFRTI_K_PROBE: 'ok', CFRTI_K_R6SLICE: 'ok', ECONLAG_CALENDAR: 'ok', NHLOT_LISTS: 'ok', INGAMELAG_M1: 'refused', INGAMELAG_M1A: 'ok', INGAMELAG_M1B: 'ok', INPLAYJUMP_LISTS: 'ok', CENSUS_LISTING: 'ok', POLAPPR1_CANDLES: 'ok', POLAPPR1_CANDLES_P2: 'ok', POLAPPR1_CANDLES_P3: 'ok', CFRTI_K_CANDLES: 'ok', HOURLYTEMP_LISTS: 'ok', TESTING_LISTS_BUNDLE: 'ok', SOCDERIV_LISTS: 'ok', MAPBREAK_CANDLES: 'ok', MAPBREAK_LISTS: 'ok', ESOCTIE_LISTS: 'ok', TIE3_CANDLES: 'ok', WHEEL0_LISTS: 'ok', MAPBREAK_CANDLES_REST: 'ok', ESOCTIE_CANDLES_P1: 'ok', ESOCTIE_CANDLES_P2: 'ok', ESOCTIE_CANDLES_P3: 'ok', ESOCTIE_CANDLES_P4: 'ok', NHLOT_CANDLES: 'ok', REMATCH_STAGE1_CANDLES: 'ok' });
  for (const id of ['NOSIDE1_CANDLES', 'NOSIDE1_CANDLES_P1', 'NOSIDE1_CANDLES_P2', 'NOSIDE1_CANDLES_P3', 'SPREADCELL1', 'SPREADCELL1_REST', 'SPREADLISTS', 'ROLLOFF_PROXY', 'PERPBTC1M', 'CFRTI_K_LISTS', 'CFRTI_K_PROBE', 'CFRTI_K_R6SLICE', 'ECONLAG_CALENDAR', 'NHLOT_LISTS', 'INGAMELAG_M1A', 'INGAMELAG_M1B', 'INPLAYJUMP_LISTS', 'CENSUS_LISTING', 'POLAPPR1_CANDLES', 'POLAPPR1_CANDLES_P2', 'POLAPPR1_CANDLES_P3', 'CFRTI_K_CANDLES', 'HOURLYTEMP_LISTS', 'TESTING_LISTS_BUNDLE', 'SOCDERIV_LISTS', 'MAPBREAK_CANDLES', 'MAPBREAK_LISTS', 'ESOCTIE_LISTS', 'TIE3_CANDLES', 'WHEEL0_LISTS', 'MAPBREAK_CANDLES_REST', 'ESOCTIE_CANDLES_P1', 'ESOCTIE_CANDLES_P2', 'ESOCTIE_CANDLES_P3', 'ESOCTIE_CANDLES_P4', 'NHLOT_CANDLES', 'REMATCH_STAGE1_CANDLES']) assert.doesNotThrow(() => execFileSync('python3', ['-I', scriptPath, id, '--dry-run'], { encoding: 'utf8' }), id + ' passes its own check');
  // the held-out third is not in the stage 2 universe: the builder only takes thirds 0 and 1
};

// KP14c: SPREADCELL1_REST is exactly the 36 requests run 43249300663 did not reach (b119_0 to b136_1), equal to the matching SPREADCELL1 entries (no id asked twice across the two jobs, none dropped), and
// the three NOSIDE1_CANDLES parts are exactly the original's 1,034 requests, in order, no overlap and no gap, each at most 400. The 200 MB cap is not raised for either.
// KP26: the three politics approval candle jobs (W-POL-APPR1 full pull, Nov 12, 2026): 1,006 requests each, 3,018 in all, one historical single-market candle request per market and no market asked twice
// across the parts. Each request is one ticker inside its own allowlist and its own safe-character pattern, the window is the registered 8.5 days plus 1 hour at hourly bars, the only endpoint shapes are
// the two allowlisted ones, the host is the elections host, and the three request lists are disjoint (a market pulled twice would spend the budget and double-count in the scorer).
gates.KP26 = () => {
  const names = ['POLAPPR1_CANDLES', 'POLAPPR1_CANDLES_P2', 'POLAPPR1_CANDLES_P3'];
  const seen = new Set();
  for (const n of names) {
    const job = JSON.parse(fs.readFileSync(path.join(jobDir, n + '.json'), 'utf8'));
    assert.strictEqual(job.status, 'active', n + ': active');
    assert.strictEqual(job.host, 'api.elections.kalshi.com'); assert.strictEqual(job.base_path, '/trade-api/v2');
    assert.strictEqual(job.max_requests, 1006, n + ': cap'); assert.strictEqual(job.requests.length, 1006, n + ': requests');
    assert.deepStrictEqual(job.allowed_endpoints.map((e) => e.name).sort(), ['hist_market_candlesticks', 'markets_candlesticks_batch']);
    assert.ok(job.requests.every((r) => /^\/historical\/markets\/[A-Z0-9][A-Z0-9._-]{0,63}\/candlesticks$/.test(r.path)), n + ': only the single-market historical candle shape is requested');
    assert.ok(job.ticker_allowlist.every((t) => /^[A-Z0-9][A-Z0-9._-]{0,63}$/.test(t)) && new Set(job.ticker_allowlist).size === 1006, n + ': allowlist is safe and has no repeats');
    const allow = new Set(job.ticker_allowlist);
    for (const r of job.requests) {
      const t = /^\/historical\/markets\/([^/]+)\/candlesticks$/.exec(r.path)[1];
      assert.ok(allow.has(t), n + ': ticker inside its allowlist ' + t);
      assert.ok(!seen.has(t), 'a market is asked for in only one part ' + t); seen.add(t);
      assert.deepStrictEqual(Object.keys(r.params).sort(), ['end_ts', 'period_interval', 'start_ts']);
      assert.strictEqual(r.params.period_interval, 60);
      assert.strictEqual(r.params.end_ts - r.params.start_ts, 8.5 * 86400 + 3600, n + ': window is 8.5 days plus 1 hour');
    }
    assert.strictEqual(new Set(job.requests.map((r) => r.id)).size, 1006, n + ': request ids unique');
  }
  assert.strictEqual(seen.size, 3018, 'the three parts are disjoint and cover 3,018 markets');
  // every URL the runner would build is the elections host, https, a single historical candle read (the runner's own build_url), and the dry run passes (it prints only the first 10)
  const urls = py(`
out = []
for n in ${JSON.stringify(names)}:
    job = json.load(open(os.path.join(m.JOB_DIR, n + ".json"))); m.check_job(job)
    out += [m.build_url(job, r["path"], r.get("params", {})) for r in job["requests"]]
print(json.dumps(out))`);
  assert.strictEqual(urls.length, 3018);
  assert.ok(urls.every((u) => u.startsWith('https://api.elections.kalshi.com/trade-api/v2/historical/markets/') && /\/candlesticks\?start_ts=\d+&end_ts=\d+&period_interval=60$/.test(u)), 'every URL is the elections host');
  for (const n of names) assert.ok(/plan: 1006 requests/.test(execFileSync('python3', ['-I', scriptPath, n, '--dry-run'], { encoding: 'utf8' })), n + ': dry run');
};

// KP29: CFRTI_K_CANDLES (Desk A, live mode, built from the CFRTI_K_LISTS answer) is development only and stays under the endpoint's 10,000 (minutes x tickers) limit: 215 requests, no ticker closes on or after 2026-11-05, each request at most 9,000 minutes x tickers, every ticker inside the allowlist.
gates.KP29 = () => {
  const c = JSON.parse(fs.readFileSync(path.join(jobDir, 'CFRTI_K_CANDLES.json'), 'utf8'));
  assert.strictEqual(c.requests.length, 215); assert.strictEqual(c.max_requests, 215); assert.strictEqual(c.status, 'active');
  const allow = new Set(c.ticker_allowlist);
  for (const r of c.requests) {
    const t = r.params.market_tickers.split(',');
    assert.ok(t.every((x) => allow.has(x) && /^[A-Z0-9][A-Z0-9._-]{0,63}$/.test(x)), r.id + ': tickers inside the allowlist');
    assert.ok(t.length * ((r.params.end_ts - r.params.start_ts) / 60) <= 9000, r.id + ': under the 10,000 limit with margin');
    assert.ok(r.params.end_ts <= 1793836800, r.id + ': nothing after the 2026-11-05 held-out cutoff');
    assert.strictEqual(r.params.period_interval, 1);
  }
};

// KP30: the Testing Desk and Desk B list jobs (SOCDERIV, HOURLYTEMP) are LISTINGS: only /markets, /historical/markets and /series/<ticker> reads, no candles, and each cap covers its page budget (the runner stops at the cap, so a cap under the budget would end a run early).
gates.KP30 = () => {
  for (const n of ['HOURLYTEMP_LISTS', 'SOCDERIV_LISTS', 'MAPBREAK_LISTS', 'INPLAYJUMP_LISTS', 'ESOCTIE_LISTS', 'WHEEL0_LISTS']) {
    const c = JSON.parse(fs.readFileSync(path.join(jobDir, n + '.json'), 'utf8'));
    assert.strictEqual(c.status, 'active', n);
    assert.ok(c.requests.every((r) => r.path === '/markets' || r.path === '/historical/markets' || /^\/series\/[A-Z0-9]{2,32}$/.test(r.path)), n + ': listing paths only');
    const budget = c.requests.reduce((a, r) => a + (r.max_pages || 1), 0);
    assert.ok(c.max_requests >= budget && c.max_requests <= 1200, n + ': cap covers the page budget');
  }
};

// KP33: WHEEL0_LISTS (Forensics, owner MAIN) lists four settled 15 minute series; rule (h): the Ethereum request is bounded before 2026-10-29 in the file itself, and Bitcoin is not requested at all.
gates.KP33 = () => {
  const c = JSON.parse(fs.readFileSync(path.join(jobDir, 'WHEEL0_LISTS.json'), 'utf8'));
  const eth = c.requests.filter((r) => r.params.series_ticker === 'KXETH15M');
  assert.strictEqual(eth.length, 1);
  assert.ok(eth[0].params.max_close_ts <= 1793231999, 'Ethereum bounded before Oct 29');
  assert.ok(!c.requests.some((r) => /^KXBTC/.test(r.params.series_ticker)), 'no Bitcoin');
};

// KP31: TIE3_CANDLES (Testing Desk, owner MAIN, with WXDAYEND_B riding in the same run) is 54 one-endpoint batched candle requests (50 TIE3 windows t3c_ and 4 WXDAYEND_B windows wxb_), cap 54, every ticker inside the allowlist, every request under the endpoint's 10,000 (minutes x tickers) limit, and nothing after 2026-11-12T23:59Z (the registered cutoff 2026-11-13T00:00Z is never requested).
gates.KP31 = () => {
  const c = JSON.parse(fs.readFileSync(path.join(jobDir, 'TIE3_CANDLES.json'), 'utf8'));
  assert.strictEqual(c.requests.length, 54); assert.strictEqual(c.max_requests, 54); assert.strictEqual(c.owner, 'MAIN'); assert.strictEqual(c.status, 'active');
  assert.ok(c.requests.every((r) => /^(t3c|wxb)_/.test(r.id)), 'ids carry the sub-job prefix');
  const allow = new Set(c.ticker_allowlist);
  for (const r of c.requests) {
    const t = r.params.market_tickers.split(',');
    assert.ok(t.every((x) => allow.has(x) && /^[A-Z0-9][A-Z0-9._-]{0,63}$/.test(x)), r.id + ': tickers inside the allowlist');
    assert.ok(t.length * ((r.params.end_ts - r.params.start_ts) / 60) <= 9000, r.id + ': under the 10,000 limit with margin');
    assert.ok(r.params.end_ts < 1794528000, r.id + ': nothing from 2026-11-13T00:00Z on');
    assert.strictEqual(r.params.period_interval, 1);
  }
};

// KP32: MAPBREAK_CANDLES (Testing Desk, owner MAIN) is single-page batched candle requests on one endpoint, cap equals the request count, every request under the endpoint's 10,000 minutes x tickers limit, every ticker in the allowlist, and every end_ts before the 2026-10-23 held-out cut.
gates.KP32 = () => {
  const c = JSON.parse(fs.readFileSync(path.join(jobDir, 'MAPBREAK_CANDLES.json'), 'utf8'));
  assert.strictEqual(c.status, 'active');
  assert.strictEqual(c.max_requests, c.requests.length);
  const allow = new Set(c.ticker_allowlist);
  for (const r of c.requests) {
    assert.strictEqual(r.path, '/markets/candlesticks');
    const t = r.params.market_tickers.split(',');
    assert.ok(t.every((x) => allow.has(x)), 'ticker in allowlist');
    assert.ok(t.length * ((r.params.end_ts - r.params.start_ts) / 60) <= 10000, 'under the batch limit');
    assert.ok(r.params.end_ts < 1792713600, 'before the held-out cut');
    assert.strictEqual(r.params.period_interval, 1);
  }
};

// KP27: the census listing is a read-only listing: series list and settled non-combo markets by hour, nothing else, and its answer size is estimated at about 120 MB (under the 200 MB cap).
gates.KP27 = () => {
  const c = JSON.parse(fs.readFileSync(path.join(jobDir, 'CENSUS_LISTING.json'), 'utf8'));
  assert.strictEqual(c.requests.length, 40); assert.strictEqual(c.max_requests, 100); assert.strictEqual(c.status, 'active');
  for (const r of c.requests) { assert.ok(r.path === '/series' || r.path === '/markets', r.id); assert.ok(!r.path.includes('candlesticks')); }
  assert.ok(c.requests.filter((r) => r.path === '/markets').every((r) => r.params.status === 'settled' && r.params.mve_filter === 'exclude' && (r.max_pages || 1) <= 3), 'markets: settled, no combos, at most 3 pages an hour');
};

// KP28: TESTING_LISTS_BUNDLE (Testing Desk, owner MAIN) carries three small jobs, TIE3_LISTS (32), WXDAYEND_A (22) and POLCOST (79: the OPEN-markets lists of the same 79 Politics series, status=open, no close-time bounds, which replaced the settled POL-i2 lists on the Head's ruling of Nov 12), in ONE file: 133 requests, 347 pages at most, cap 361 (the page budget plus 14 for 429 retries; UNRATE_LISTS left the bundle when the Head retired UNRATEROUND unread). SOCDERIV_LISTS stays its own job (the soccer lists are the heavy part and a size stop would cost a second run). The only candle requests are WXDAYEND_A's own 18 one-market windows; everything else is a listing. Ids carry a prefix (t3_ wx_ ur_ p2_) so each manifest row says its sub-job.
gates.KP28 = () => {
  const c = JSON.parse(fs.readFileSync(path.join(jobDir, 'TESTING_LISTS_BUNDLE.json'), 'utf8'));
  assert.strictEqual(c.requests.length, 133); assert.strictEqual(c.owner, 'MAIN'); assert.strictEqual(c.status, 'active');
  const budget = c.requests.reduce((a, r) => a + (r.max_pages || 1), 0);
  assert.strictEqual(budget, 347); assert.strictEqual(c.max_requests, 361); assert.ok(c.max_requests >= budget && c.max_requests <= 1200);
  assert.strictEqual(new Set(c.requests.map((r) => r.id)).size, 133, 'request ids are unique');
  assert.ok(c.requests.every((r) => /^(t3|wx|pc)_/.test(r.id)), 'every id carries its sub-job prefix, none is a soccer list');
  assert.ok(c.requests.filter((r) => r.id.startsWith('pc_')).every((r) => r.path === '/markets' && r.params.status === 'open' && !('min_close_ts' in r.params) && !('max_close_ts' in r.params)), 'POLCOST: open-market lists only, no close-time bounds');
  assert.strictEqual(c.requests.filter((r) => r.id.startsWith('pc_')).length, 79);
  const candles = c.requests.filter((r) => /candlesticks/.test(r.path));
  assert.strictEqual(candles.length, 18); assert.ok(candles.every((r) => r.id.startsWith('wx_') && !r.params.market_tickers.includes(',')), 'only WXDAYEND_A one-market candle windows');
  assert.ok(c.requests.filter((r) => !/candlesticks/.test(r.path)).every((r) => r.path === '/markets' || r.path === '/historical/markets' || /^\/series\/[A-Z0-9]{2,32}$/.test(r.path)), 'everything else is a listing');
};

gates.KP14c = () => {
  const rd = (n) => JSON.parse(fs.readFileSync(path.join(jobDir, n + '.json'), 'utf8'));
  const sc = rd('SPREADCELL1'), rest = rd('SPREADCELL1_REST');
  const missing = []; for (let b = 119; b <= 136; b++) { missing.push('b' + String(b).padStart(3, '0') + '_0', 'b' + String(b).padStart(3, '0') + '_1'); }
  assert.strictEqual(missing.length, 36);
  assert.deepStrictEqual(rest.requests.map((r) => r.id), missing, 'exactly the missing ids, in order');
  assert.deepStrictEqual(rest.requests, sc.requests.filter((r) => missing.includes(r.id)), 'equal to the SPREADCELL1 entries');
  for (const k of ['host', 'base_path', 'pacing_seconds', 'stop_rules', 'allowed_endpoints', 'series_allowlist', 'ticker_allowlist', 'owner', 'registration', 'heldout']) assert.deepStrictEqual(rest[k], sc[k], 'same ' + k);
  assert.strictEqual(rest.max_requests, 36);
  assert.ok(/completes SPREADCELL1/i.test(rest.notes) && /request id/.test(rest.notes));
  const whole = rd('NOSIDE1_CANDLES'), parts = [1, 2, 3].map((i) => rd('NOSIDE1_CANDLES_P' + i));
  assert.deepStrictEqual([].concat(...parts.map((p) => p.requests)), whole.requests, 'the parts are the original requests, in order, no gap, no overlap');
  for (const p of parts) { assert.ok(p.requests.length <= 400 && p.max_requests === p.requests.length, p.job_id + ': at most 400 and cap equals count'); assert.deepStrictEqual(p.stop_rules, whole.stop_rules); assert.strictEqual(p.host, whole.host); }
  assert.ok(whole.status === 'active' && whole.requests.length === 1034, 'the original stays intact');
};

// KP14b: every ACTIVE job's requests all match its own allowed endpoints and ticker or series allowlist, none is a denied path, and the count equals the cap (at most 1,200).
gates.KP14b = () => {
  for (const f of jobs) {
    const job = JSON.parse(fs.readFileSync(path.join(jobDir, f), 'utf8'));
    if (job.status !== 'active') continue;
    // a job with paged requests (ROLLOFF_PROXY) is capped by its page budget; one without must use its cap exactly
    const budget = job.requests.reduce((n, r) => n + (r.max_pages || 1), 0);
    assert.ok(job.max_requests <= 1200 && budget <= job.max_requests, job.job_id + ': page budget within the cap, cap within 1,200');
    // NHLOT_CANDLES (86 requests, cap 150) and REMATCH_STAGE1_CANDLES (120, cap 150) carry the cap their desk registered. INGAMELAG_M1 is registered with 20 requests of headroom for 429 retries (retries count against the cap): 215 requests, cap 235. Any other headroom is a failure.
    const headroom = { INGAMELAG_M1A: 15, INGAMELAG_M1B: 15, NHLOT_CANDLES: 64, REMATCH_STAGE1_CANDLES: 30 }[job.job_id] || 0;
    if (job.requests.every((r) => !r.max_pages || r.max_pages === 1)) assert.strictEqual(job.requests.length + headroom, job.max_requests, job.job_id + ': count equals the cap' + (headroom ? ' less its registered headroom' : ''));
    const eps = job.allowed_endpoints.map((e) => ({ rx: new RegExp('^(?:' + e.path_pattern.replace(/\(\?P</g, '(?<') + ')$'), params: new Set(e.params_allowed) }));
    const tk = new Set(job.ticker_allowlist);
    const sr = new Set(job.series_allowlist);
    for (const r of job.requests) {
      assert.ok(!/portfolio|account|\/orders|order_group|\/fills|\/positions|api_key|api-key|subaccount|communications|login|logout|\/rfq|\/quotes|\/margin|\/exchange/i.test(r.path), job.job_id + ': denied path ' + r.path);
      const ep = eps.find((e) => e.rx.test(r.path));
      assert.ok(ep, job.job_id + ': path matches an allowed endpoint ' + r.path);
      for (const k of Object.keys(r.params || {})) assert.ok(ep.params.has(k), job.job_id + ': param ' + k + ' allowed');
      const p = (r.params || {});
      if (p.market_tickers) for (const t of p.market_tickers.split(',')) assert.ok(tk.has(t), job.job_id + ': ticker allowlisted ' + t);
      // the runner checks market_tickers against the allowlist but not 'tickers', so this gate does
      if (p.tickers) for (const t of p.tickers.split(',')) assert.ok(tk.has(t), job.job_id + ': ticker allowlisted ' + t);
      if (p.series_ticker) assert.ok(sr.has(p.series_ticker), job.job_id + ': series allowlisted');
      const m = /\/historical\/markets\/([^/]+)\/candlesticks$/.exec(r.path);
      if (m) assert.ok(tk.has(m[1]), job.job_id + ': ticker allowlisted ' + m[1]);
    }
  }
};

// KP14c: the batched candle endpoint counts (window minutes x tickers) against a limit of 10,000 and answers HTTP 400 above it, so no batched request may exceed 9,000 minutes x tickers. The probe is 24 consecutive tickers in 1 request, the R6 slice is 20 requests covering all 407 windows once.
gates.KP14c = () => {
  for (const id of ['CFRTI_K_PROBE', 'CFRTI_K_R6SLICE']) {
    const job = JSON.parse(fs.readFileSync(path.join(jobDir, id + '.json'), 'utf8'));
    const seen = [];
    for (const r of job.requests) {
      const p = r.params, n = p.market_tickers.split(',').length, minutes = (p.end_ts - p.start_ts) / 60;
      assert.ok(minutes * n <= 9000, id + ' ' + r.id + ': minutes x tickers ' + minutes * n + ' is at most 9,000 (the endpoint refuses above 10,000)');
      seen.push(...p.market_tickers.split(','));
    }
    assert.strictEqual(new Set(seen).size, seen.length, id + ': no ticker requested twice');
    assert.strictEqual(seen.length, job.ticker_allowlist.length, id + ': every allowlisted ticker is requested once');
  }
  const probe = JSON.parse(fs.readFileSync(path.join(jobDir, 'CFRTI_K_PROBE.json'), 'utf8'));
  assert.strictEqual(probe.ticker_allowlist.length, 24);
  assert.strictEqual(probe.requests.length, 1);
  const slice = JSON.parse(fs.readFileSync(path.join(jobDir, 'CFRTI_K_R6SLICE.json'), 'utf8'));
  assert.strictEqual(slice.ticker_allowlist.length, 407);
  assert.strictEqual(slice.requests.length, 20);
  // the offline builder packs the same way: here 700 consecutive quarter hours, every batch within 9,000 (about 24 tickers a request, so the real lists come to about 216 requests in live mode and about 624 in all mode, each under the 1,200 cap)
  const out = JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location('b', ${JSON.stringify(path.join(jobDir, 'build_cfrti_k_candles.py'))}); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
import calendar, time
t0 = calendar.timegm(time.strptime("2026-10-01", "%Y-%m-%d"))
mk = [("KXBTC15M-%d" % i, t0 + 900 * i) for i in range(700)]
b.read_markets = lambda f: mk
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf): b.main("x", "all")
j = json.loads(buf.getvalue())
print(json.dumps([[len(r["params"]["market_tickers"].split(",")) * (r["params"]["end_ts"] - r["params"]["start_ts"]) / 60 for r in j["requests"]], j["max_requests"], len(j["ticker_allowlist"])]))`], { encoding: 'utf8' }));
  assert.ok(out[0].every((x) => x <= 9000), 'the builder never packs a batch above 9,000 minutes x tickers');
  assert.strictEqual(out[2], 700);
  assert.ok(out[1] >= 700 / 25 && out[1] <= 1200, 'about 24 tickers a request, far under the 1,200 cap');
};

// KP14d: INGAMELAG_M1A and M1B are ONE measurement of a fixed list of 215 games, split only for the 200 MB a run cap. Consequence if this breaks: a game read twice or not at all, or a run refused for a ticker its own file did not allow.
gates.KP14d = () => {
  const load = (n) => JSON.parse(fs.readFileSync(path.join(jobDir, n + '.json'), 'utf8'));
  const a = load('INGAMELAG_M1A'), b = load('INGAMELAG_M1B'), old = load('INGAMELAG_M1');
  const ids = (job) => job.requests.map((r) => r.id);
  const idsA = new Set(ids(a)), idsB = new Set(ids(b));
  assert.strictEqual(idsA.size, a.requests.length, 'M1A request ids are unique');
  assert.strictEqual(idsB.size, b.requests.length, 'M1B request ids are unique');
  assert.deepStrictEqual([...idsA].filter((i) => idsB.has(i)), [], 'M1A and M1B request ids are disjoint');
  assert.deepStrictEqual([...idsA, ...idsB].sort(), ids(old).sort(), 'together they are exactly the 215 games of the retired job');
  assert.strictEqual(a.requests.length + b.requests.length, 215);
  for (const job of [a, b]) {
    const used = job.requests.flatMap((r) => r.params.market_tickers.split(','));
    assert.deepStrictEqual([...job.ticker_allowlist].sort(), [...new Set(used)].sort(), job.job_id + ': the ticker allowlist is exactly its tickers');
    assert.strictEqual(new Set(used).size, used.length, job.job_id + ': no ticker is asked twice');
    assert.ok(job.max_requests >= job.requests.length, job.job_id + ': cap is not below its request count');
    assert.ok(used.every((t) => /^[A-Z0-9-]+$/.test(t)), job.job_id + ': safe ticker characters');
    assert.strictEqual(job.host, 'api.elections.kalshi.com');
    assert.deepStrictEqual(job.allowed_endpoints.map((e) => e.path_pattern), ['/markets/candlesticks']);
  }
  const ta = new Set(a.ticker_allowlist);
  assert.ok(b.ticker_allowlist.every((t) => !ta.has(t)), 'no ticker is in both jobs');
  assert.ok(a.max_requests >= a.requests.length && b.max_requests >= b.requests.length);
};

// KP15: the stage 2 builder takes development events only, round robin, never the held-out third, and never passes the registered total.
gates.KP15 = () => {
  const out = JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location('b', ${JSON.stringify(path.join(jobDir, 'build_noside1_candles.py'))}); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
cuts = {"series": {"KXA": {"events": [["EA1", 0], ["EA2", 1], ["EA3", 2]]}, "KXB": {"events": [["EB1", 0], ["EB2", 2]]}}}
mk = lambda t, e, c: {"ticker": t, "event_ticker": e, "close_time": c, "result": "yes"}
events = {"EA1": [mk("EA1-1", "EA1", "2026-01-01T00:00:00Z"), mk("EA1-2", "EA1", "2026-01-01T00:00:00Z")], "EA2": [mk("EA2-1", "EA2", "2026-10-01T00:00:00Z")], "EA3": [mk("EA3-1", "EA3", "2026-10-02T00:00:00Z")],
  "EB1": [mk("EB1-1", "EB1", "2026-02-01T00:00:00Z")], "EB2": [mk("EB2-1", "EB2", "2026-10-03T00:00:00Z")]}
reqs, tk, cap = b.build(cuts, events, 10, total_cap=1200)
small, _, cap2 = b.build(cuts, events, 10, total_cap=13)
print(json.dumps({"ids": [r["id"] for r in reqs], "paths": [r["path"] for r in reqs], "cap": cap, "small": len(small), "cap2": cap2}))`], { encoding: 'utf8' }));
  assert.deepStrictEqual(out.ids, ['EA1-1', 'EA1-2', 'EB1-1', 'EA2-1'], 'round robin by event, held-out thirds absent');
  assert.ok(!out.ids.some((i) => /EA3|EB2/.test(i)));
  assert.deepStrictEqual(out.paths.map((p) => p.startsWith('/historical/')), [true, true, true, false], 'before 2026-09-12 historical, after it the live series path');
  assert.strictEqual(out.cap, 1190);
  assert.strictEqual(out.small, 3, 'the total of both stages never passes the cap');
};

// KP16: the workflow pushes only its own data branch, with the six-try loop, never main or another data branch, and never cancels a running pull.
gates.KP16 = () => {
  assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin kalshi-pull-data && exit 0; \[ "\$i" -lt 6 \] \|\| break; sleep \$\(\(2 \*\* i\)\); git pull -q --rebase origin kalshi-pull-data \|\| true; done/.test(wf));
  assert.deepStrictEqual([...wfCode.matchAll(/git push[^\n]*/g)].length, 1, 'one push command');
  assert.ok(!/git push[^\n]*\bmain\b/.test(wfCode) && !/quote-data|pol-data|nc-data|perp-data|sports-data|gh-pages/.test(wfCode));
  assert.deepStrictEqual([...wfCode.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['pull']);
  assert.ok(/if git fetch -q --depth 1 origin kalshi-pull-data; then git checkout -q -b kalshi-pull-data FETCH_HEAD; else git checkout -q --orphan kalshi-pull-data; fi/.test(wf), 'the first real run creates an orphan branch');
  assert.ok(/concurrency:\s*\n\s*group: kalshi-pull\s*\n\s*cancel-in-progress: false/.test(wf));
  assert.ok(/if: always\(\) && steps\.gate\.outputs\.go == 'true' && env\.DRY_RUN == 'false'/.test(wf), 'the data is pushed even when the run stopped early, and never on a dry run');
  // every later step is skipped on a dry run except the dry run itself
  const steps = wf.split(/\n      - name: /).slice(1);
  assert.strictEqual(steps.length, 7);
  assert.strictEqual(steps.filter((x) => /env\.DRY_RUN == 'false'/.test(x)).length, 3, 'the open, pull and push steps are real-run only');
  assert.strictEqual(steps.filter((x) => /env\.DRY_RUN == 'true'/.test(x)).length, 1, 'one dry-run step');
};

// KP17: the answers are not published with the site and are never on main: the script, jobs and workflow sit in excluded folders, no symlink, and the data branch is not main.
gates.KP17 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  for (const must of ['.github', 'scripts', 'kalshi-scalper', 'docs', 'CLAUDE.md', 'test']) assert.ok(new RegExp('- ' + must.replace('.', '\\.') + '\\b').test(cfg), must + ' is excluded from the site');
  assert.ok(!/kalshi-pull-data/.test(cfg));
  const links = execFileSync('git', ['ls-files', '-s'], { cwd: root, encoding: 'utf8' }).split('\n').filter((l) => l.startsWith('120000'));
  assert.deepStrictEqual(links, []);
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8').replace(/<li>[^\n]*<\/li>/g, '');
  assert.ok(!/kalshi_pull|kalshi-pull/.test(html), 'the page code does not use it (only the changelog line names it)');
  const fnDir = path.join(root, 'functions');
  assert.deepStrictEqual(fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /kalshi_pull|kalshi-pull/.test(fs.readFileSync(path.join(fnDir, f), 'utf8'))), [], 'nothing in functions/ mentions it');
};

// KP18: it stops by itself on 2027-02-28, in the workflow and in the script, and a real run is limited to 20 a UTC day.
gates.KP18 = () => {
  assert.deepStrictEqual(py('print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH)]))'), ['2027-02-28T23:59:00Z', false, true]);
  assert.ok(/date -u -d '2027-02-28T23:59:00Z' \+%s/.test(wf) && /go=false/.test(wf));
  const day = py(`
d = tempfile.mkdtemp(); now = 1790000000.0
import time
day = time.strftime("%Y-%m-%d", time.gmtime(now))
for i in range(19): os.makedirs(os.path.join(d, "pull", "JOB_A", day + "T%02d00Z_1" % i))
os.makedirs(os.path.join(d, "pull", "JOB_B", day + "T0900Z_1")); os.makedirs(os.path.join(d, "pull", "JOB_B", "2020-01-01T0900Z_1"))
print(json.dumps([m.runs_today(d, "JOB_A", now), m.MAX_RUNS_PER_DAY]))`);
  assert.deepStrictEqual(day, [20, 20], 'runs of every job count toward the day cap (20 a UTC day since Nov 12, 2026)');
};

// KP18b: raising the day cap from 6 to 12 changed ONLY that number. Every per-run limit is still what it was.
gates.KP18b = () => {
  const out = py('print(json.dumps([m.GAP_S, m.BACKOFF_S, m.BACKOFF_MAX_S, m.MAX_429_IN_ROW, m.MAX_FAILS_IN_ROW, m.HARD_MAX_REQUESTS, m.MAX_BODY_BYTES, m.MAX_RUN_BYTES, m.MAX_RUN_SECONDS, m.MAX_JOB_BYTES, m.MAX_PAGES, m.END_UTC, sorted(m.ROUTES.keys()), [m.ROUTES[k][0] for k in sorted(m.ROUTES)]]))');
  assert.deepStrictEqual(out, [1.0, 5.0, 60.0, 3, 3, 1200, 5000000, 200000000, 2400, 2000000, 50, '2027-02-28T23:59:00Z', ['elections', 'perps'], ['api.elections.kalshi.com', 'external-api.kalshi.com']]);
  const src = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'kalshi_pull.py'), 'utf8');
  assert.ok(/^MAX_RUNS_PER_DAY = 20 /m.test(src), 'the day cap is 20');
  assert.ok(/5 MB an answer, 200 MB a run, 20 real runs a UTC day/.test(wf), 'the workflow header says 20');
};

// KP19: file names on the data branch are counters; a hostile request id or answer cannot create a path outside the run folder.
gates.KP19 = () => {
  const out = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "ROLLOFF_PROXY.json")))
d = tempfile.mkdtemp(); o = os.path.join(d, "o"); clock = [1000.0]
m.run(dict(j, requests=j["requests"][:2]), o, fetch=lambda u: (200, b'{"a":"../../x"}', "D", False), clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s), out=lambda *a: None)
print(json.dumps(sorted(os.listdir(o))))`);
  assert.deepStrictEqual(out, ['0001.json.gz', '0002.json.gz', 'STATUS', 'manifest.json']);
  assert.ok(/"%04d\.json\.gz" % sent/.test(code));
};

// KP20: the docs and the CLAUDE.md section say the rate plainly and record the terms risk exactly; no live figures and no em dashes in anything added.
gates.KP20 = () => {
  const doc = fs.readFileSync(path.join(root, 'docs', 'KALSHI_PULL.md'), 'utf8');
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  const sec = claude.match(/^## kalshi-pull[^\n]*\n[\s\S]*?(?=\n## |(?![\s\S]))/m);
  assert.ok(sec && /^## kalshi-pull.*\(Nov 12, 2026/.test(sec[0]), 'dated CLAUDE.md section, Nov 12');
  for (const text of [doc, sec[0]]) {
    assert.ok(/OWNER-ACCEPTED TERMS RISK/.test(text));
    assert.ok(/[Tt]he owner waived reading Kalshi's Developer Agreement and Terms of Use on Nov 12, 2026/.test(text));
    assert.ok(/NOT read/.test(text) && /HTTP 429 to every fetch/.test(text) && /archive copy also unreachable/.test(text));
    assert.ok(/[Tt]his is NOT a finding that automated reads are allowed/.test(text));
    assert.ok(/[Ss]ame treatment as the Yahoo market strip/.test(text));
  }
  assert.ok(/at most 1 request a second/i.test(doc) && /1,200/.test(doc) && /5 MB/.test(doc) && /runner minutes/i.test(doc));
  const files = ['scripts/kalshi_pull.py', '.github/workflows/kalshi-pull.yml', 'docs/KALSHI_PULL.md', 'test/kalshiPullGates.test.js'].concat(fs.readdirSync(jobDir).filter((f) => /\.(json|py)$/.test(f)).map((f) => 'kalshi-scalper/workers/kalshi_pull_jobs/' + f));
  for (const f of files) assert.ok(!/\u2014/.test(fs.readFileSync(path.join(root, f), 'utf8')), f + ' has no em dash');
  assert.ok(!/\u2014/.test(sec[0]));
};

// KP21: the opener has no environment-proxy handler, so a proxy variable on a runner cannot send the requests through another address.
gates.KP21 = () => {
  const out = execFileSync('python3', ['-I', '-c', `
import sys, os, json
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:9"
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import kalshi_pull as m
print(json.dumps([type(h).__name__ for h in m._OPENER.handlers]))`], { encoding: 'utf8' });
  assert.ok(!/Proxy/.test(out), 'no proxy handler in the opener: ' + out);
};

// KP22: the destination is chosen from the constant ROUTES table by KEY only: exactly two pairs, a job that names a route cannot also carry a host or base path, an unknown key is refused, and the
// URL is built from the table (perps jobs reach external-api.kalshi.com/trade-api/v2/margin, older jobs still reach the elections pair).
gates.KP22 = () => {
  const r = py(`
print(json.dumps({"routes": m.ROUTES, "perps_url": m.build_url(json.load(open(os.path.join(m.JOB_DIR, "PERPBTC1M.json"))), "/markets/KXBTCPERP/candlesticks", {"period_interval": 1, "start_ts": 1780444800, "end_ts": 1780531200}),
 "old_url": m.build_url(json.load(open(os.path.join(m.JOB_DIR, "COMBO1_OPENBOOK.json"))), "/markets", {})}))`);
  assert.deepStrictEqual(r.routes, { elections: ['api.elections.kalshi.com', '/trade-api/v2'], perps: ['external-api.kalshi.com', '/trade-api/v2/margin'] });
  assert.strictEqual(r.perps_url, 'https://external-api.kalshi.com/trade-api/v2/margin/markets/KXBTCPERP/candlesticks?period_interval=1&start_ts=1780444800&end_ts=1780531200');
  assert.strictEqual(r.old_url, 'https://api.elections.kalshi.com/trade-api/v2/markets');
  const bad = py(`
def t(j):
    try: m.check_job(j); return "ok"
    except m.Refused: return "refused"
j = json.load(open(os.path.join(m.JOB_DIR, "PERPBTC1M.json")))
print(json.dumps([t(j), t(dict(j, host="example.com")), t(dict(j, base_path="/trade-api/v2/margin")), t(dict(j, host="external-api.kalshi.com", base_path="/trade-api/v2/margin")), t(dict(j, route="evil")), t(dict(j, route=["perps"]))]))`);
  assert.deepStrictEqual(bad, ['ok', 'refused', 'refused', 'refused', 'refused', 'refused'], 'a job cannot supply a host or base path of its own, and an unknown route key is refused');
};

// KP23: a perps job can read ONE thing: the 1 minute candlesticks of KXBTCPERP and KXETHPERP, one page, one UTC day at most. Lists, funding, other tickers, other series, cursors, wider windows and other intervals are refused.
gates.KP23 = () => {
  const out = py(`
base = json.load(open(os.path.join(m.JOB_DIR, "PERPBTC1M.json")))
def t(req=None, **top):
    j = json.loads(json.dumps(base)); j.update(top)
    if req is not None: j["requests"] = [req]
    try: m.check_job(j); return "ok"
    except m.Refused: return "refused"
c = lambda **p: {"id": "A", "path": "/markets/KXBTCPERP/candlesticks", "params": dict({"period_interval": 1, "start_ts": 1780444800, "end_ts": 1780531200}, **p)}
ep = lambda pat, pa=("period_interval", "start_ts", "end_ts"): [{"name": "x", "method": "GET", "path_pattern": pat, "params_allowed": list(pa)}]
print(json.dumps({"base": t(), "one": t(c()),
 "list": t({"id": "A", "path": "/markets", "params": {}}, allowed_endpoints=ep("/markets", ("limit",))),
 "funding": t({"id": "A", "path": "/funding_rates/historical", "params": {"ticker": "KXBTCPERP"}}, allowed_endpoints=ep("/funding_rates/historical", ("ticker",))),
 "othertk": t({"id": "A", "path": "/markets/KXSOLPERP/candlesticks", "params": c()["params"]}, ticker_allowlist=["KXBTCPERP", "KXSOLPERP"]),
 "unlisted": t({"id": "A", "path": "/markets/KXETHPERP/candlesticks", "params": c()["params"]}),
 "series": t(series_allowlist=["KXBTC"]), "wide": t(c(end_ts=1780531201)), "backwards": t(c(start_ts=1780531200, end_ts=1780444800)), "interval": t(c(period_interval=60)),
 "extra": t(c(limit=5)), "missing": t({"id": "A", "path": "/markets/KXBTCPERP/candlesticks", "params": {"start_ts": 1780444800, "end_ts": 1780531200}}),
 "pages": t(dict(c(), max_pages=2), allowed_endpoints=ep("/markets/(?P<ticker>KXBTCPERP|KXETHPERP)/candlesticks", ("period_interval", "start_ts", "end_ts", "cursor"))),
 "loosepattern": t(allowed_endpoints=ep("/markets/(?P<ticker>[A-Z]+)/candlesticks")),
 "denied": t({"id": "A", "path": "/portfolio/balance", "params": {}}), "marginpath": t({"id": "A", "path": "/margin/markets/KXBTCPERP/candlesticks", "params": c()["params"]}),
 "orders": t({"id": "A", "path": "/orders", "params": {}}, allowed_endpoints=ep("/orders", ()))}))`);
  assert.strictEqual(out.base, 'ok');
  assert.strictEqual(out.one, 'ok');
  for (const k of ['list', 'funding', 'othertk', 'unlisted', 'series', 'wide', 'backwards', 'interval', 'extra', 'missing', 'pages', 'loosepattern', 'denied', 'marginpath', 'orders']) assert.strictEqual(out[k], 'refused', k);
  const checks = py('print(json.dumps([sorted(m.PERPS_TICKERS), sorted(m.PERPS_PARAMS), m.PERPS_MAX_WINDOW_S]))');
  assert.deepStrictEqual(checks, [['KXBTCPERP', 'KXETHPERP'], ['end_ts', 'period_interval', 'start_ts'], 86400]);
};

// KP24: the two perps job files are exactly the explicit list the desk asked for: 163 UTC days, 2026-06-03 to 2026-11-12, one request per day per ticker, midnight to midnight, under the 1,200 cap, and pass their own dry run.
gates.KP24 = () => {
  for (const [id, tk] of [['PERPBTC1M', 'KXBTCPERP'], ['PERPETH1M', 'KXETHPERP']]) {
    const j = JSON.parse(fs.readFileSync(path.join(jobDir, id + '.json'), 'utf8'));
    assert.strictEqual(j.status, id === 'PERPETH1M' ? 'paused' : 'active'); assert.strictEqual(j.route, 'perps'); assert.deepStrictEqual(j.ticker_allowlist, [tk]);
    assert.strictEqual(j.requests.length, 163); assert.strictEqual(j.max_requests, 163);
    assert.strictEqual(j.requests[0].params.start_ts, Date.UTC(2026, 5, 3) / 1000);
    assert.strictEqual(j.requests[162].params.start_ts, Date.UTC(2026, 10, 12) / 1000);
    j.requests.forEach((r, i) => {
      assert.strictEqual(r.path, '/markets/' + tk + '/candlesticks');
      assert.strictEqual(r.params.start_ts, Date.UTC(2026, 5, 3) / 1000 + i * 86400);
      assert.strictEqual(r.params.end_ts - r.params.start_ts, 86400);
      assert.deepStrictEqual(Object.keys(r.params).sort(), ['end_ts', 'period_interval', 'start_ts']);
    });
    if (id === 'PERPETH1M') { assert.ok(/paused/i.test(j.notes) && /NOT be dispatched/.test(j.notes)); let r = ''; try { execFileSync('python3', ['-I', scriptPath, id, '--dry-run'], { encoding: 'utf8' }); } catch (e) { r = String(e.stdout); } assert.ok(/REFUSED/.test(r), 'the paused job is refused by the runner'); continue; }
    const dry = execFileSync('python3', ['-I', scriptPath, id, '--dry-run'], { encoding: 'utf8' });
    assert.ok(/plan: 163 requests/.test(dry) && dry.includes("https://external-api.kalshi.com/trade-api/v2/margin/markets/" + tk + "/candlesticks?") && /no request was sent/.test(dry));
  }
};

// KP25: a mocked perps run keeps the unchanged limits: a second between requests, three 429s end it with what was fetched kept, and only perps URLs are asked.
gates.KP25 = () => {
  const out = py(`
j = json.load(open(os.path.join(m.JOB_DIR, "PERPBTC1M.json")))
def go(script):
    clock = [1000.0]; urls = []; starts = []
    def sl(d): clock[0] += d
    def fetch(u):
        urls.append(u); starts.append(clock[0]); clock[0] += 0.05
        c = script.pop(0) if script else 200
        return c, (b'{"candlesticks": []}' if c == 200 else b""), "D", False
    d = tempfile.mkdtemp()
    st = m.run(dict(j, requests=j["requests"][:5]), os.path.join(d, "o"), fetch=fetch, clock=lambda: clock[0], sleep=sl, out=lambda *a: None)
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    return {"st": st, "n": len(urls), "hosts": sorted(set(u.split("/trade-api")[0] for u in urls)), "mingap": min(gaps) if gaps else 9}
print(json.dumps({"ok": go([]), "stop": go([200, 429, 429, 429])}))`);
  assert.deepStrictEqual(out.ok.st, ['complete', 0]); assert.strictEqual(out.ok.n, 5); assert.ok(out.ok.mingap >= 1.0);
  assert.deepStrictEqual(out.ok.hosts, ['https://external-api.kalshi.com']);
  assert.deepStrictEqual(out.stop.st, ['stopped_429', 2]); assert.strictEqual(out.stop.n, 4);
};


// KP14c: the runner holds a "tickers" list to the ticker allowlist the same as "market_tickers", so a job file cannot ask the markets list for a ticker it did not name up front.
gates.KP14c = () => {
  const out = py(`
base = json.load(open(os.path.join(m.JOB_DIR, "SPREADLISTS.json")))
ts = base["requests"][0]["params"]["tickers"].split(",")
def t(tickers, allow=None):
    j = json.loads(json.dumps(base)); j["requests"] = [{"id": "A", "path": "/markets", "params": {"tickers": tickers, "limit": 100}}]
    if allow is not None: j["ticker_allowlist"] = allow
    try: m.check_job(j); return "ok"
    except m.Refused: return "refused"
print(json.dumps({"listed": t(",".join(ts)), "unlisted": t(",".join(ts[:5] + ["KXNOTLISTED-1"])), "one_unlisted": t("KXNOTLISTED-1"), "over100": t(",".join(ts + base["ticker_allowlist"][100:101]) if len(ts) == 100 else ",".join(ts)), "empty_part": t(ts[0] + ",,") }))`);
  assert.strictEqual(out.listed, 'ok');
  for (const k of ['unlisted', 'one_unlisted', 'empty_part']) assert.strictEqual(out[k], 'refused', k);
  assert.strictEqual(out.over100, 'refused', 'more than 100 tickers is refused');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
