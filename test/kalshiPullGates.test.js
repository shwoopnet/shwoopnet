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

// KP4: the job id is a fixed choice, double checked in the first step, and every choice has a job file.
gates.KP4 = () => {
  const options = [...wf.match(/job:[\s\S]*?options:\n((?:\s+- \w+\n)+)/)[1].matchAll(/- (\w+)/g)].map((x) => x[1]);
  // NOSIDE1_LISTS is retired (the universe is frozen) and has no choice; every other job file, retired COMBO1_OPENBOOK included, keeps one.
  assert.deepStrictEqual(options.sort(), jobs.map((f) => f.replace('.json', '')).filter((n) => n !== 'NOSIDE1_LISTS').sort(), 'the choices are the job files except the retired lists job');
  assert.ok(/case "\$JOB" in NOSIDE1_CANDLES\|SPREADCELL1\|ROLLOFF_PROXY\|COMBO1_OPENBOOK\)/.test(wf));
  assert.ok(/JOB: \$\{\{ inputs\.job \}\}/.test(wf) && /DRY_RUN: \$\{\{ inputs\.dry_run \}\}/.test(wf));
};

// KP5: one host, pinned in code, https only, no other URL anywhere in the script.
gates.KP5 = () => {
  assert.ok(!/https?:\/\/[A-Za-z0-9]/.test(code), 'no host is written out anywhere but the HOST constant');
  assert.ok(/HOST = "api\.elections\.kalshi\.com"/.test(code) && /BASE_PATH = "\/trade-api\/v2"/.test(code));
  assert.ok(!/http:\/\//.test(code));
  const hosts = py('print(json.dumps([m.build_url({}, "/markets", {"series_ticker": "KXA"}), m.build_url({}, "/markets", {}, "abc=")]))');
  assert.deepStrictEqual(hosts, ['https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXA', 'https://api.elections.kalshi.com/trade-api/v2/markets?cursor=abc%3D']);
  for (const f of jobs) assert.strictEqual(JSON.parse(fs.readFileSync(path.join(jobDir, f), 'utf8')).host, 'api.elections.kalshi.com', f);
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
  assert.deepStrictEqual(Object.keys(j).sort(), ['COMBO1_OPENBOOK', 'NOSIDE1_CANDLES', 'NOSIDE1_LISTS', 'ROLLOFF_PROXY', 'SPREADCELL1']);
  assert.ok(!jobs.some((f) => /ECONLAG|BALLOTNO/i.test(f)), 'ECONLAG and BALLOTNO are not included');
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
  assert.strictEqual(j.ROLLOFF_PROXY.max_requests, 12);
  assert.strictEqual(j.COMBO1_OPENBOOK.max_requests, 3);
  assert.strictEqual(j.COMBO1_OPENBOOK.status, 'retired');
  // the runner refuses a retired job (a job that is not active never runs) and passes the rest
  const verdicts = py(`
out = {}
for n in ("NOSIDE1_LISTS", "COMBO1_OPENBOOK", "NOSIDE1_CANDLES", "SPREADCELL1", "ROLLOFF_PROXY"):
    try: m.check_job(json.load(open(os.path.join(m.JOB_DIR, n + ".json")))); out[n] = "ok"
    except m.Refused as e: out[n] = "refused"
print(json.dumps(out))`);
  assert.deepStrictEqual(verdicts, { NOSIDE1_LISTS: 'refused', COMBO1_OPENBOOK: 'refused', NOSIDE1_CANDLES: 'ok', SPREADCELL1: 'ok', ROLLOFF_PROXY: 'ok' });
  for (const id of ['NOSIDE1_CANDLES', 'SPREADCELL1', 'ROLLOFF_PROXY']) assert.doesNotThrow(() => execFileSync('python3', ['-I', scriptPath, id, '--dry-run'], { encoding: 'utf8' }), id + ' passes its own check');
  // the held-out third is not in the stage 2 universe: the builder only takes thirds 0 and 1
};

// KP14b: every ACTIVE job's requests all match its own allowed endpoints and ticker or series allowlist, none is a denied path, and the count equals the cap (at most 1,200).
gates.KP14b = () => {
  for (const f of jobs) {
    const job = JSON.parse(fs.readFileSync(path.join(jobDir, f), 'utf8'));
    if (job.status !== 'active') continue;
    // a job with paged requests (ROLLOFF_PROXY) is capped by its page budget; one without must use its cap exactly
    const budget = job.requests.reduce((n, r) => n + (r.max_pages || 1), 0);
    assert.ok(job.max_requests <= 1200 && budget <= job.max_requests, job.job_id + ': page budget within the cap, cap within 1,200');
    if (job.requests.every((r) => !r.max_pages || r.max_pages === 1)) assert.strictEqual(job.requests.length, job.max_requests, job.job_id + ': count equals the cap');
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
      if (p.series_ticker) assert.ok(sr.has(p.series_ticker), job.job_id + ': series allowlisted');
      const m = /\/historical\/markets\/([^/]+)\/candlesticks$/.exec(r.path);
      if (m) assert.ok(tk.has(m[1]), job.job_id + ': ticker allowlisted ' + m[1]);
    }
  }
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
  assert.strictEqual(steps.length, 6);
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

// KP18: it stops by itself on 2027-02-28, in the workflow and in the script, and a real run is limited to 6 a UTC day.
gates.KP18 = () => {
  assert.deepStrictEqual(py('print(json.dumps([m.END_UTC, m.past_end(m.END_EPOCH - 1), m.past_end(m.END_EPOCH)]))'), ['2027-02-28T23:59:00Z', false, true]);
  assert.ok(/date -u -d '2027-02-28T23:59:00Z' \+%s/.test(wf) && /go=false/.test(wf));
  const day = py(`
d = tempfile.mkdtemp(); now = 1790000000.0
import time
day = time.strftime("%Y-%m-%d", time.gmtime(now))
for i in range(5): os.makedirs(os.path.join(d, "pull", "JOB_A", day + "T0%d00Z_1" % i))
os.makedirs(os.path.join(d, "pull", "JOB_B", day + "T0900Z_1")); os.makedirs(os.path.join(d, "pull", "JOB_B", "2020-01-01T0900Z_1"))
print(json.dumps([m.runs_today(d, "JOB_A", now), m.MAX_RUNS_PER_DAY]))`);
  assert.deepStrictEqual(day, [6, 6], 'runs of every job count toward the day cap');
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

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
