'use strict';
// Recorder OKLQ (Nov 10, 2026, research only, DRAFT, not active): OKX's public Bitcoin swap liquidation feed. It reads one public host, holds no secret, places no order, sends no
// auth header, writes only to a data branch, is not published with the site and stops by itself on 2026-12-31.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_oklq.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-oklq.yml'), 'utf8');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('ol', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
${src}`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));

// OL1: it can never trade or sign anything: one public host, GET only, no auth, no order word, no account endpoint.
gates.OL1 = () => {
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)].filter((h) => h !== 'https://github.com').sort(), ['https://www.okx.com'], 'the only host it requests is OKX public data');
  assert.ok(/public\/liquidation-orders/.test(code) && !/\/trade\/|\/account\/|\/asset\//.test(code), 'only the public liquidation endpoint');
  assert.ok(!/PRIVATE|SECRET|Authorization|Bearer|ACCESS[-_]?KEY|SIGNATURE|API[-_]?KEY|PASSPHRASE|TOKEN|OK-ACCESS|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, no auth header, no signing, no write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|placeOrder|ordId/.test(code), 'no order endpoint or word');
  assert.ok(!/os\.environ\[|getenv/.test(code) && (code.match(/os\.environ\.get\(/g) || []).length === 1 && /GITHUB_REPOSITORY/.test(code), 'the only environment variable is the repository name, for the User-Agent');
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
  const fnDir = path.join(root, 'functions');
  const mentions = fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_oklq|record-oklq|oklq/i.test(fs.readFileSync(path.join(fnDir, f), 'utf8')));
  assert.deepStrictEqual(mentions, [], 'nothing in functions/ mentions it');
  assert.ok(!/record_oklq|record-oklq|oklq/i.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
};

// OL2: the workflow pushes only the data branch, touches only the built-in token, has no inputs, never cancels a running job, is pinned and says it is a draft.
gates.OL2 = () => {
  assert.ok(/^# DRAFT, NOT ACTIVE: lives on claude\/refine-live only; schedules run only from the default branch, merge needs the owner and a security review/.test(wf), 'draft header');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['oklq'], 'it adds its own folder and nothing wider');
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(/concurrency:\s*\n\s*group: record-oklq\s*\n\s*cancel-in-progress: false/.test(wf), 'one group, a running job is never cancelled');
  assert.ok(/workflow_dispatch: \{\}/.test(wf) && !/inputs:/.test(wf), 'the manual trigger takes no inputs');
  assert.ok(/timeout-minutes: 15/.test(wf), 'a short job');
  const uses = [...wf.matchAll(/uses:\s*([^\s#]+)/g)].map((x) => x[1]);
  assert.ok(uses.length && uses.every((u) => /@[0-9a-f]{40}$/.test(u)), 'every action pinned by commit SHA');
  assert.ok(!/pip install|npm install|curl |wget /.test(wf), 'installs nothing: the script uses the standard library only');
  assert.ok(/ref: main/.test(wf) && /python3 code\/scripts\/record_oklq\.py "data\/oklq\/\$STAMP" --seen data\/oklq/.test(wf), 'the script comes from main, the data goes under oklq/');
  assert.ok(!/pull_request_target|github\.event\.(issue|pull_request|comment|head_commit)/.test(wf));
  assert.ok(/cron: "7 \*\/2 \* \* \*"/.test(wf) && /cron: "37 1-23\/2 \* \* \*"/.test(wf), 'two interleaved two hourly sets, far inside the 17 hour history');
};

// OL3: neither the workflow nor the script is published with the site.
gates.OL3 = () => {
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg), 'neither is published with the site');
};

// OL4: the stop date exists, is in the future, and the script and the workflow agree on it.
gates.OL4 = () => {
  const o = py('print(json.dumps({"end": m.END_UTC, "e": m.END_EPOCH, "before": m.past_end(m.END_EPOCH - 1), "at": m.past_end(m.END_EPOCH)}))');
  assert.strictEqual(o.end, '2026-12-31T23:59:00Z');
  assert.ok(o.e * 1000 > Date.now(), 'the stop date is in the future (if this fails, the recorder has already stopped: extend it on purpose)');
  assert.deepStrictEqual([o.before, o.at], [false, true]);
  assert.ok(/2026-12-31T23:59:00Z/.test(wf), 'the workflow gate carries the same end date');
};

// OL5: every request goes through the backoff helper; a 429 or 5xx waits 2 s, doubling to a cap, tried 4 times, never raises; the gap holds; the horizon fits OKX's history.
gates.OL5 = () => {
  assert.strictEqual((code.match(/urlopen\(/g) || []).length, 1, 'one network call in the file');
  assert.ok(/def http_get[\s\S]*?urlopen\(/.test(code) && !/urlopen\(/.test(code.replace(/def http_get[\s\S]*?(?=\nclass Stream)/, '')), 'it is inside http_get');
  assert.strictEqual([...code.matchAll(/\bhttp_get\(/g)].length, 2, 'http_get is defined once and called only by the Stream transport');
  assert.ok([...code.matchAll(/\bstream\.get\(/g)].length >= 1, 'the fetch code asks through a Stream');
  const o = py(`
t = [0.0]; slept = []
def clock(): return t[0]
def sleep(s): slept.append(round(s, 3)); t[0] += s
seq = iter([429, 429, 503, 200]); calls = []
def fetch(u): calls.append(u); st = next(seq); return st, ({"ok": 1} if st == 200 else None)
s = m.Stream(1.0, {}, fetch=fetch, clock=clock, sleep=sleep); r = s.get("u1")
bad = m.Stream(1.5, {}, fetch=lambda u: (429, None), clock=clock, sleep=sleep); r2 = bad.get("u2")
print(json.dumps({"r": r[0], "slept": slept[:4], "n429": s.n429, "n5xx": s.n5xx, "bad": r2[0], "badreq": bad.requests, "horizon": m.HORIZON_S, "pages": m.PAGE_LIMIT}))`);
  assert.strictEqual(o.r, 200);
  assert.deepStrictEqual(o.slept.slice(0, 3), [2, 4, 8], 'backoff waits 2, 4, 8 s');
  assert.deepStrictEqual([o.n429, o.n5xx], [2, 1]);
  assert.deepStrictEqual([o.bad, o.badreq], [429, 4], 'gives up after four tries and returns a status');
  assert.ok(o.horizon <= 16 * 3600, 'a pass never asks for rows near the 17 hour edge');
  assert.ok(o.pages >= 32, 'the page limit covers 16 hours of BTC-USDT at about 200 rows an hour');
  assert.throws(() => py('m.Stream(0.5, {})'), 'a gap under one second is refused');
};

// OL6: paging, de-duplication across overlapping passes, coverage and the hole flag, against a fake exchange.
gates.OL6 = () => {
  const o = py(`
import tempfile, os, csv
NOW = 1_800_000_000
def mk(ts, i): return {"ts": str(ts), "time": ts, "side": "sell", "posSide": "long", "sz": "1.%d" % i, "bkPx": "70000", "bkLoss": "0", "ccy": ""}
allrows = [mk((NOW - 60 * i) * 1000, i) for i in range(250)]   # newest first, 250 rows over 250 minutes
def fake(url):
    after = int(url.split("after=")[1]) if "after=" in url else None
    rows = [r for r in allrows if after is None or int(r["ts"]) < after][:100]
    uly = "BTC-USDT" if "uly=BTC-USDT" in url else "BTC-USD"
    data = [{"instId": uly + "-SWAP", "uly": uly, "details": rows if uly == "BTC-USDT" else []}]
    return 200, {"code": "0", "data": data}
t = [0.0]
def clock(): return t[0]
def sleep(s): t[0] += s
d = tempfile.mkdtemp()
s1 = m.Stream(1.0, {}, fetch=fake, clock=clock, sleep=sleep)
out = m.Out(os.path.join(d, "2027-01-01", "0000")); c1 = m.run_pass(s1, out, None, now=NOW); out.close()
# second pass, ten minutes later, with the first pass's folder as --seen (as the workflow passes it)
seen_root = os.path.join(d, "seen"); os.makedirs(seen_root)
today = __import__("time").strftime("%Y-%m-%d", __import__("time").gmtime(NOW))
os.makedirs(os.path.join(seen_root, today, "0000"))
import shutil; shutil.copy(os.path.join(d, "2027-01-01", "0000", "liquidations.csv"), os.path.join(seen_root, today, "0000", "liquidations.csv"))
s2 = m.Stream(1.0, {}, fetch=fake, clock=clock, sleep=sleep)
out2 = m.Out(os.path.join(d, "p2")); c2 = m.run_pass(s2, out2, seen_root, now=NOW + 600); out2.close()
rows1 = list(csv.DictReader(open(os.path.join(d, "2027-01-01", "0000", "liquidations.csv"))))
rows2 = list(csv.DictReader(open(os.path.join(d, "p2", "liquidations.csv"))))
cov1 = list(csv.DictReader(open(os.path.join(d, "2027-01-01", "0000", "coverage.csv"))))
# a pass whose exchange keeps failing marks a hole and still returns
bad = m.Stream(1.0, {}, fetch=lambda u: (500, None), clock=clock, sleep=sleep)
out3 = m.Out(os.path.join(d, "p3")); c3 = m.run_pass(bad, out3, None, now=NOW); out3.close()
cov3 = list(csv.DictReader(open(os.path.join(d, "p3", "coverage.csv"))))
print(json.dumps({"n1": len(rows1), "keys1": len({(r["inst_id"], r["ts_ms"], r["sz"]) for r in rows1}), "n2": len(rows2), "c1": c1, "c2": c2, "cov1": [r["stop_reason"] for r in cov1],
                  "cov3": [r["stop_reason"] for r in cov3], "note3": cov3[0]["note"], "cols": list(rows1[0].keys())}))`);
  assert.strictEqual(o.n1, 250, 'all 250 rows read over three pages');
  assert.strictEqual(o.keys1, 250, 'no duplicates inside a pass');
  assert.strictEqual(o.n2, 0, 'an overlapping second pass adds nothing already on the data branch');
  assert.deepStrictEqual(o.cov1, ['history_end', 'history_end'], 'the coverage row says why each underlying stopped');
  assert.deepStrictEqual(o.cov3, ['read_failed', 'read_failed']);
  assert.ok(/possible hole/.test(o.note3), 'a failed read is flagged as a possible hole');
  assert.deepStrictEqual(o.cols, ['t_recv_ms', 'inst_id', 'uly', 'ts_ms', 'side', 'pos_side', 'sz', 'bk_px', 'bk_loss', 'ccy']);
};

// OL7: the script exits 0 even when the network is unreachable (a failed read never fails the job).
gates.OL7 = () => {
  const o = py(`
import tempfile, os
orig = m.Stream.__init__
m.Stream.__init__ = lambda self, gap, h, fetch=None, clock=None, sleep=None: orig(self, gap, h, fetch=lambda u: (0, None), clock=__import__("time").time, sleep=lambda x: None)
import io, contextlib
d = tempfile.mkdtemp()
with contextlib.redirect_stdout(io.StringIO()):
    rc = m.main([d, "--seen", os.path.join(d, "none")])
print(json.dumps({"rc": rc}))`);
  assert.strictEqual(o.rc, 0);
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
if (failed) process.exit(1);
