'use strict';
// External-signal shadow logger (Nov 11, 2026, research only). A registered public signal is logged next to the Kalshi quote. It reads only allowlisted public hosts, holds no key,
// places no order, writes only to the quote-data branch, is not published with the site, stops by itself and fits the 250 runner minute limit.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scriptPath = path.join(root, 'scripts', 'record_signals.py');
const script = fs.readFileSync(scriptPath, 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'record-signals.yml'), 'utf8');
const regPath = path.join(root, 'kalshi-scalper', 'signals', 'REGISTRY.json');
const code = script.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json
spec = importlib.util.spec_from_file_location('sg', ${JSON.stringify(scriptPath)}); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
good = {"id":"WXHIGH1","readme":"kalshi-scalper/README.md#wxhigh1","url":"https://api.weather.gov/gridpoints/OKX/33,37/forecast","parse":{"type":"json","path":["properties","updated"]},"kalshi":{"series":"KXHIGHNY"},"cadence":"run","stopDate":"2026-12-31","enabled":True}
${src}`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));

// SG1: the host allowlist is enforced, and a registry edit cannot widen it.
gates.SG1 = () => {
  const r = py(`
def v(**kw):
    e = dict(good); e.update(kw); return m.validate_entry(e)
print(json.dumps({"good": v(), "binance": v(url="https://api.binance.com/x"), "http": v(url="http://api.weather.gov/x"), "userinfo": v(url="https://a:b@api.weather.gov/x"),
  "port": v(url="https://api.weather.gov:8443/x"), "lookalike": v(url="https://api.weather.gov.evil.com/x"), "allow": sorted(m.ALLOWLIST)}))`);
  assert.strictEqual(r.good, '');
  for (const k of ['binance', 'http', 'userinfo', 'port', 'lookalike']) assert.notStrictEqual(r[k], '', k + ' is rejected');
  assert.ok(!r.allow.includes('api.binance.com'), 'binance is not allowed');
  for (const h of ['api.weather.gov', 'www.okx.com', 'www.deribit.com', 'api.coinbase.com', 'api.kraken.com']) assert.ok(r.allow.includes(h), h);
  const hosts = [...code.matchAll(/https?:\/\/[^"'\s/%]+/g)].map((x) => x[0]);
  assert.deepStrictEqual([...new Set(hosts)].filter((h) => h !== 'https://github.com').sort(), ['https://external-api.kalshi.com'], 'the only literal host in the code is the Kalshi quote host; signal hosts come from the allowlist');
};

// SG2: no eval, no exec, no shell, no key, no write call, no order endpoint, no regex taken from the registry.
gates.SG2 = () => {
  assert.ok(!/\b(eval|exec|__import__|subprocess|os\.system|popen|pickle|importlib|shlex)\b/.test(code), 'no eval, exec or shell');
  assert.ok(!/PRIVATE|SECRET|Authorization|Bearer|API[-_]?KEY|PASSPHRASE|TOKEN|SIGNATURE|method\s*=\s*["'](POST|PUT|DELETE)|data\s*=\s*b?["']/i.test(code), 'no key, auth header or write call');
  assert.ok(!/\/portfolio|\/orders\b|order_id|create_order|placeOrder/.test(code), 'no order endpoint or word');
  assert.ok(!/re\.(compile|match|search|findall|sub)\(\s*(e|entry|spec|ps|k)\b/.test(code), 'no regex built from the registry');
  assert.ok((code.match(/os\.environ\.get\(/g) || []).length === 1 && /GITHUB_REPOSITORY/.test(code) && !/os\.environ\[|getenv/.test(code), 'the only environment variable is the repository name');
  assert.ok(!/^\s*(from|import)\s+[^\n]*functions/m.test(script), 'imports nothing from functions/');
};

// SG3: the validator rejects bad entries: id, missing stopDate, late stopDate, oversized fields, bad parse, bad cadence.
gates.SG3 = () => {
  const r = py(`
def v(**kw):
    e = dict(good); e.update(kw); return m.validate_entry(e)
d = dict(good); del d["stopDate"]
print(json.dumps({"id": v(id="x"), "id2": v(id="TOOLONGID12345"), "nostop": m.validate_entry(d), "late": v(stopDate="2027-03-01"), "bigreadme": v(readme="x"*121),
  "bigurl": v(url="https://api.weather.gov/" + "a"*300), "deep": v(parse={"type":"json","path":list("abcdefghi")}), "longkey": v(parse={"type":"json","path":["k"*41]}),
  "regex": v(parse={"type":"regex","pattern":".*"}), "extra": v(parse={"type":"json","path":["a"],"eval":"1"}), "col": v(parse={"type":"csv","column":99,"row":"last"}),
  "cad": v(cadence="1s"), "tick": v(kalshi={"series":"bad ticker!"}), "both": v(kalshi={"series":"KXA","ticker":"KXB"}), "en": v(enabled="yes"), "notobj": m.validate_entry("x"),
  "csvok": v(parse={"type":"csv","column":2,"row":"last"})}))`);
  for (const [k, why] of Object.entries(r)) if (k === 'csvok') assert.strictEqual(why, ''); else assert.notStrictEqual(why, '', k + ' is rejected');
  const bad = py(`
import tempfile, os
p = os.path.join(tempfile.mkdtemp(), "r.json"); open(p, "w").write(json.dumps({"entries": [good, dict(good), dict(good, id="BAD1", url="https://evil.example/x")]}))
ok, b = m.load_registry(p); print(json.dumps({"ok": [e["id"] for e in ok], "bad": b, "missing": m.load_registry("/nonexistent")}))`);
  assert.deepStrictEqual(bad.ok, ['WXHIGH1']);
  assert.strictEqual(bad.bad.length, 2, 'a duplicate id and a bad host are both reported');
  assert.deepStrictEqual(bad.missing[0], [], 'an unreadable registry gives no entries');
};

// SG4: extraction is declarative and bounded: JSON path, CSV cell, over-long or structured values refused, formula characters neutralised.
gates.SG4 = () => {
  const r = py(`
j = {"type":"json","path":["a",1,"b"]}
print(json.dumps({"num": m.extract(j, b'{"a":[0,{"b":12.5}]}'), "str": m.extract(j, b'{"a":[0,{"b":"clear"}]}'), "miss": m.extract(j, b'{"a":[]}'), "obj": m.extract(j, b'{"a":[0,{"b":{"c":1}}]}'),
  "bool": m.extract(j, b'{"a":[0,{"b":true}]}'), "long": m.extract(j, ('{"a":[0,{"b":"' + "x"*41 + '"}]}').encode()), "bad": m.extract(j, b'not json'),
  "formula": m.extract(j, b'{"a":[0,{"b":"=1+1"}]}'), "neg": m.extract(j, b'{"a":[0,{"b":-3}]}'),
  "csvlast": m.extract({"type":"csv","column":1,"row":"last"}, b"t,v\\n1,5\\n2,7\\n"), "csvfirst": m.extract({"type":"csv","column":0,"row":"first"}, b"t,v\\n1,5\\n"), "csvoob": m.extract({"type":"csv","column":9,"row":"last"}, b"a,b\\n")}))`);
  assert.strictEqual(r.num, '12.5'); assert.strictEqual(r.str, 'clear'); assert.strictEqual(r.neg, '-3');
  for (const k of ['miss', 'obj', 'bool', 'long', 'bad', 'csvoob']) assert.strictEqual(r[k], null, k);
  assert.strictEqual(r.formula, "'=1+1"); assert.strictEqual(r.csvlast, '7'); assert.strictEqual(r.csvfirst, 't');
};

// SG5: stop dates and the example are honoured: a stopped, disabled or past-the-end entry is never due, a 'day' entry is due only at the first start of the UTC day.
gates.SG5 = () => {
  const r = py(`
import calendar, time
t = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
ex = json.load(open(${JSON.stringify(regPath)}))["entries"]
print(json.dumps({"on": m.is_due(good, t("2026-12-31T05:00:00Z")), "stopped": m.is_due(good, t("2027-01-01T05:00:00Z")), "off": m.is_due(dict(good, enabled=False), t("2026-12-01T05:00:00Z")),
  "day1": m.is_due(dict(good, cadence="day"), t("2026-12-01T01:11:00Z")), "day2": m.is_due(dict(good, cadence="day"), t("2026-12-01T05:11:00Z")),
  "end": m.is_due(dict(good, stopDate="2027-02-28"), t("2027-02-28T23:59:00Z")), "exvalid": [m.validate_entry(e) for e in ex], "exdue": [m.is_due(e, t("2026-12-01T01:11:00Z")) for e in ex],
  "exflag": [[e.get("example"), e.get("enabled")] for e in ex], "endutc": m.END_UTC}))`);
  assert.strictEqual(r.on, true); assert.strictEqual(r.stopped, false); assert.strictEqual(r.off, false); assert.strictEqual(r.day1, true); assert.strictEqual(r.day2, false); assert.strictEqual(r.end, false);
  assert.deepStrictEqual(r.exvalid, ['']); assert.deepStrictEqual(r.exdue, [false], 'the shipped example records nothing'); assert.deepStrictEqual(r.exflag, [[true, false]]);
  assert.ok(wf.includes("'" + r.endutc + "'"), 'the workflow enforces the same end date as the script');
  assert.ok(/steps\.gate\.outputs\.go == 'true'/.test(wf), 'every step is behind the end date gate');
};

// SG6: request caps: a fake fetch that always answers 429 never exceeds MAX_REQUESTS, requests are at least 1 s apart on a fake clock, and one failing source does not stop the next entry.
gates.SG6 = () => {
  const r = py(`
class C:
    def __init__(s): s.t = 1000.0; s.calls = []
    def clock(s): return s.t
    def sleep(s, d): s.t += d
c = C()
def fetch(url):
    c.calls.append((url, c.t)); return 429, None, ""
st = m.Stream(1.0, {}, fetch=fetch, clock=c.clock, sleep=c.sleep)
entries = [dict(good, id="E%d" % i) for i in range(10)]
rows = m.run(entries, st, 1796000000 - 90*86400, clock=c.clock)
gaps = [b[1] - a[1] for a, b in zip(c.calls, c.calls[1:])]
# a second run: the signal fails, the quote works
c2 = C()
def fetch2(url):
    if "kalshi" in url: return 200, json.dumps({"markets": [{"ticker": "KXHIGHNY-1", "close_time": "2026-12-01T00:00:00Z", "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.45", "yes_bid_size_fp": "10", "yes_ask_size_fp": "12"}, {"ticker": "KXHIGHNY-2", "close_time": "2026-12-02T00:00:00Z"}]}).encode(), "Tue"
    return 500, None, ""
st2 = m.Stream(1.0, {}, fetch=fetch2, clock=c2.clock, sleep=c2.sleep)
rows2 = m.run([dict(good, id="AA"), dict(good, id="BB")], st2, 1796000000 - 90*86400, clock=c2.clock)
print(json.dumps({"n": len(c.calls), "cap": m.MAX_REQUESTS, "mingap": min(gaps), "rows": len(rows), "capped": st.capped, "r2": rows2, "maxent": m.MAX_ENTRIES}))`);
  assert.ok(r.n <= r.cap, 'never more than MAX_REQUESTS requests (' + r.n + ')');
  assert.ok(r.mingap >= 1.0 - 1e-9, 'at least one second between requests');
  assert.ok(r.rows < 10, 'the request cap or the time budget stops new entries');
  assert.strictEqual(r.r2.length, 2, 'a failing signal source does not stop the next entry');
  assert.strictEqual(r.r2[0][0], 'AA'); assert.strictEqual(r.r2[1][0], 'BB');
  assert.ok(/signal_http_500/.test(r.r2[0][13]) && r.r2[0][5] === 'KXHIGHNY-1' && r.r2[0][6] === '0.4', 'the quote is kept, the signal failure is a flag, the soonest-closing market is chosen');
  assert.ok(r.maxent * 2 <= r.cap, 'entries times two reads fit under the request cap');
  assert.ok(/MAX_BYTES = \d+/.test(script) && /r\.read\(MAX_BYTES \+ 1\)/.test(script) && /timeout=15/.test(script), 'response size and time are bounded');
  assert.ok(/if past_end\(now\):[\s\S]*return 0/.test(script) && /^\s*sys\.exit\(main\(\)\)/m.test(script) && /except Exception as ex:/.test(script), 'always exits 0');
};

// SG7: the workflow pushes only the data branch, uses only the built-in token, has minimal permissions, is pinned and bounded, and the cron fits 250 billed minutes a month.
gates.SG7 = () => {
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'pushes quote-data only');
  assert.ok(/for i in 1 2 3 4 5 6; do git push -q origin quote-data && exit 0; \[ "\$i" -lt 6 \] \|\| break; sleep \$\(\(2 \*\* i\)\); git pull -q --rebase origin quote-data \|\| true; done/.test(wf), 'six try push loop');
  assert.deepStrictEqual([...wf.matchAll(/git add ([^\n]+)/g)].map((x) => x[1].trim()), ['signals'], 'adds its own folder only');
  assert.ok(/^permissions:\s*\n\s*contents: write\s*\n(?!\s+\w)/m.test(wf), 'contents write and nothing wider');
  assert.ok(/group: record-signals\s*\n\s*cancel-in-progress: false/.test(wf), 'one group that never cancels');
  assert.ok(/timeout-minutes: 15\b/.test(wf), '15 minute job timeout');
  assert.ok(/uses: actions\/checkout@[0-9a-f]{40}/.test(wf) && !/uses: [^\n]*@(v\d|main|master)\b/.test(wf), 'checkout is pinned to a commit');
  assert.ok(/ref: main/.test(wf), 'the script comes from main');
  assert.ok(!/inputs:/.test(wf), 'no manual inputs');
  const crons = [...wf.matchAll(/^\s*-\s*cron:\s*"([^"]+)"/gm)].map((x) => x[1]);
  assert.strictEqual(crons.length, 1);
  const f = crons[0].split(' ');
  const startsPerDay = f[1].split(',').length;
  assert.strictEqual(f[0].split(',').length, 1); assert.deepStrictEqual(f.slice(2), ['*', '*', '*']);
  const hours = f[1].split(',').map(Number);
  for (let i = 1; i < hours.length; i++) assert.ok(hours[i] - hours[i - 1] >= 3, 'starts are spaced');
  const minutesPerStart = 1, daysInMonth = 31;
  assert.ok(startsPerDay * minutesPerStart * daysInMonth <= 250, startsPerDay + ' starts x ' + minutesPerStart + ' min x 31 days = ' + startsPerDay * daysInMonth + ' is under 250');
  assert.ok(startsPerDay * 2 * daysInMonth <= 400, 'even at two billed minutes a start it stays bounded');
  const budget = Number(/TIME_BUDGET_S = (\d+)/.exec(script)[1]);
  assert.ok(budget <= 45, 'the time budget keeps a run near one billed minute');
};

// SG8: it touches nothing under functions/ or firestore.rules, the site and the page never mention it, and scripts, .github and kalshi-scalper are excluded from Pages.
gates.SG8 = () => {
  const changed = execFileSync('git', ['diff', '--name-only', 'origin/main'], { cwd: root, encoding: 'utf8' }).split('\n').filter(Boolean)
    .concat(execFileSync('git', ['ls-files', '--others', '--exclude-standard'], { cwd: root, encoding: 'utf8' }).split('\n').filter(Boolean));
  assert.deepStrictEqual(changed.filter((f) => f.startsWith('functions/') || f === 'firestore.rules'), [], 'functions/ and firestore.rules are untouched');
  const fnDir = path.join(root, 'functions');
  assert.deepStrictEqual(fs.readdirSync(fnDir).filter((f) => f.endsWith('.js')).filter((f) => /record_signals|record-signals/.test(fs.readFileSync(path.join(fnDir, f), 'utf8'))), [], 'nothing in functions/ mentions it');
  assert.ok(!/record_signals|record-signals/.test(fs.readFileSync(path.join(root, 'index.html'), 'utf8')), 'the page does not mention it');
  const cfg = fs.readFileSync(path.join(root, '_config.yml'), 'utf8');
  const excluded = new Set([...cfg.matchAll(/^\s*-\s+(\S+)\s*$/gm)].map((m) => m[1]));
  for (const d of ['scripts', '.github', 'kalshi-scalper']) assert.ok(excluded.has(d), d + ' is not served');
  assert.ok(fs.existsSync(regPath), 'the registry is under kalshi-scalper/, which is not served');
  assert.ok(!/signals\//.test(fs.readdirSync(root).join('\n')), 'no data folder in the repo tree; data lives on quote-data');
  const reg = JSON.parse(fs.readFileSync(regPath, 'utf8'));
  assert.ok(reg.entries.every((e) => e.enabled === false), 'the shipped registry enables nothing, so merging records nothing');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
