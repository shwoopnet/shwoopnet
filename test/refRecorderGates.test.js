'use strict';
// The reference-value recorder (Nov 3, 2026, research only, RECREF): public GET only, no secret, writes only to the quote-data branch under ref/, driven by a watchlist file, not published with the site.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const script = read('scripts', 'record_ref.py');
const adapters = read('scripts', 'ref_adapters.py');
const wf = read('.github', 'workflows', 'record-ref.yml');
const watch = JSON.parse(read('kalshi-scalper', 'workers', 'RECREF_WATCHLIST.json'));
const strip = (s) => s.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
const gates = {};
const py = (code) => execFileSync('python3', ['-I', '-c', `
import sys, json
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import record_ref as m
${code}`], { encoding: 'utf8' });

// R1: it can never trade or sign anything, whatever it is changed into.
gates.R1 = () => {
  for (const [name, src] of [['record_ref.py', script], ['ref_adapters.py', adapters]]) {
    const code = strip(src);
    assert.ok(!/PRIVATE|SECRET|Authorization|ACCESS[-_]?KEY|SIGNATURE|method\s*=|data\s*=\s*b?["'{]|Cookie/i.test(code) && !/\b(POST|PUT|DELETE)\b/.test(code), name + ': no key, no signing, no write call (urlopen of a bare Request is a GET)');
    assert.ok(!/\/portfolio|\/orders\b|order_id|create_order/.test(code), name + ': no account or order endpoint');
    assert.ok(!/os\.environ|getenv/.test(code), name + ': reads no environment variable, so no secret');
  }
  assert.ok(/external-api\.kalshi\.com\/trade-api\/v2\/markets|BASE = "https:\/\/external-api\.kalshi\.com\/trade-api\/v2"/.test(script), 'it reads Kalshi public market data');
  assert.ok(/User-Agent/.test(script) && /UA = "shwoopnet-research-recorder/.test(adapters), 'a descriptive User-Agent');
};

// R2: the workflow pushes only the data branch, uses only the built-in token, cannot overlap itself, runs every 2 hours.
gates.R2 = () => {
  assert.ok(/cron: "\d+ \*\/2 \* \* \*"/.test(wf), 'every 2 hours');
  assert.ok(/timeout-minutes: 20/.test(wf), 'a run is short');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wf), 'the only secret it touches is the built-in token');
  assert.ok(/git push -q origin quote-data/.test(wf) && !/git push[^\n]*\bmain\b/.test(wf), 'it pushes the data branch only, never main');
  assert.ok(/git add ref\b/.test(wf) && !/git add (-A|\.)/.test(wf), 'it stages only ref/');
  assert.ok(/permissions:\s*\n\s*contents: write/.test(wf), 'contents write and nothing wider');
  assert.ok(/cancel-in-progress: false/.test(wf), 'two runs never overlap');
  assert.ok(/workflow_dispatch/.test(wf), 'it can be started by hand');
  assert.ok(/ref: main/.test(wf), 'it runs the reviewed script from main');
  const cfg = read('_config.yml');
  assert.ok(/- \.github/.test(cfg) && /- scripts/.test(cfg) && /- kalshi-scalper/.test(cfg), 'none of it is published with the site');
};

// R3: what is polled comes from the watchlist alone: no ticker in the code, 8 to 12 series, no live 15 minute series, every reference used.
gates.R3 = () => {
  for (const src of [script, adapters]) assert.ok(!/KX[A-Z0-9]{2,}/.test(strip(src)), 'the code names no Kalshi ticker');
  assert.ok(watch.series.length >= 8 && watch.series.length <= 12, 'between 8 and 12 series');
  for (const e of watch.series) {
    assert.ok(!/15M$/.test(e.series), e.series + ' is a 15 minute series (the live bot and the other recorders cover those)');
    assert.ok(e.rule_source && e.refs.length > 0, e.series + ' names its settlement source and its references');
  }
  const ids = new Set(watch.refs.map((r) => r.id));
  const used = new Set(watch.series.flatMap((e) => e.refs));
  assert.deepStrictEqual([...ids].sort(), [...used].sort());
};

// R4: every reference is a fixed public https page or derived from the open markets, on a short list of hosts.
gates.R4 = () => {
  const hosts = new Set();
  for (const r of watch.refs) {
    const u = (r.params && r.params.url) || (r.per_event && r.per_event.url);
    if (u) { assert.ok(u.startsWith('https://'), r.id); hosts.add(u.split('/')[2]); }
  }
  for (const h of hosts) assert.ok(['kworb.net', 'www.billboard.com', 'store.steampowered.com', 'www.rottentomatoes.com', 'www.metacritic.com'].includes(h), h);
  assert.ok(/XT = "https:\/\/xtracker\.polymarket\.com\/api"/.test(adapters));
  const code = strip(script + adapters);
  const urls = new Set((code.match(/https?:\/\/[a-z0-9.-]+/g) || []).map((x) => x.split('//')[1]));
  for (const h of urls) assert.ok(['external-api.kalshi.com', 'xtracker.polymarket.com'].includes(h), 'no other host is named in the code: ' + h);
};

// R5: rows have one value per column; a market is kept only inside its window; a re-run of a slot is idempotent; slot is 2 hours.
gates.R5 = () => {
  const out = JSON.parse(py(`
now = 1_800_000_000
mk = lambda c: {"ticker": "A", "event_ticker": "E", "close_time": m.iso(c), "yes_bid_dollars": "0.9"}
row = m.quote_row(now, now, "d", {"series": "S", "family": "f"}, dict(mk(now + 3600), status="active", open_time="o"), "k")
print(json.dumps({"n": len(m.QUOTE_COLS), "row": len(row), "in": m.wanted(mk(now + 100 * 3600), 168, now), "far": m.wanted(mk(now + 200 * 3600), 168, now),
  "past": m.wanted(mk(now - 3600), 168, now), "mins": row[11], "slot": [m.slot_of(now) == m.slot_of(now + 7199 - now % 7200), m.slot_of(now + 7200) - m.slot_of(now)],
  "refcols": len(m.REF_COLS), "runcols": len(m.RUN_COLS)}))`));
  assert.strictEqual(out.n, out.row);
  assert.strictEqual(out.in, true); assert.strictEqual(out.far, false); assert.strictEqual(out.past, false);
  assert.strictEqual(out.mins, 60);
  assert.strictEqual(out.slot[1], 7200);
  assert.ok(/"ref", "quotes", day, hhmm/.test(script) && /"ref", "refvals", day, hhmm/.test(script), 'files are named for the slot');
};

// R6: politeness: one request a second per host, a refused read is counted and retried only with a pause, never a crash and never a made-up value.
gates.R6 = () => {
  assert.ok(/HOST_GAP_S = 1\.0/.test(script), 'one request per second per host');
  const out = JSON.parse(py(`
m._sleep = lambda x: None
m.http_get = lambda url: (429, None, "")
ms, calls, n429, bad, date = m.list_markets("S", "open")
rows, c, n, failed = m.poll_target({"id": "x", "adapter": "mc"}, "", "https://www.metacritic.com/game/x/", 1, 1)
print(json.dumps([ms, calls, n429, bad, rows, failed]))`));
  assert.deepStrictEqual(out, [[], 3, 3, true, [], true]);
};

// R9 (RECPATCH1): a Rotten Tomatoes page with no score yet is "no_score_yet", not a parse failure; an unreadable page is still a failure; a page with a score is unchanged.
gates.R9 = () => {
  const out = JSON.parse(py(`
import ref_adapters as ad
noscore = '<script id="media-hero-json" type="application/json">{}</script><rt-text>Tomatometer</rt-text>'
scored = '"aggregateRating":{"@type":"AggregateRating","name":"Tomatometer","ratingCount":67,"ratingValue":"90","reviewCount":67}'
print(json.dumps([ad.rt_parse({}, [noscore]), ad.rt_parse({}, ["<html>blocked</html>"]), ad.rt_parse({}, [scored])]))`));
  assert.deepStrictEqual(out, [[[1, 'tomatometer', null, null, 'no_score_yet']], [], [[1, 'tomatometer', 90, 67, 'percent;critic_reviews']]]);
  const out2 = JSON.parse(py(`
m._sleep = lambda x: None
page = '<script id="media-hero-json" type="application/json">{}</script><rt-text>Tomatometer</rt-text>'
m.http_get = lambda url: (200, page, "")
rows, c, n, failed = m.poll_target({"id": "rt_page", "adapter": "rt"}, "k", "https://www.rottentomatoes.com/m/k", 1, 1)
print(json.dumps([len(rows), failed, rows[0][8], rows[0][10]]))`));
  assert.deepStrictEqual(out2, [1, false, '', 'no_score_yet']);
};

// R10 (RECBUILD1): the Yahoo 1 minute adapter keeps bars with a close, drops what is already on file, and returns [] for a body that is not a chart (a counted failure, never a made-up value).
const YAHOO = JSON.stringify({ chart: { result: [{ meta: { symbol: 'CL=F' }, timestamp: [1000, 1060, 1120, 1180], indicators: { quote: [{ open: [70, 71, null, 73], high: [71, 72, null, 74], low: [69, 70, null, 72], close: [70.5, 71.5, null, 73.5], volume: [10, null, null, 5] }] } }], error: null } });
gates.R10 = () => {
  const out = JSON.parse(py(`
import ref_adapters as ad
body = ${JSON.stringify(YAHOO)}
print(json.dumps({"all": ad.yahoo1m_parse({}, [body]), "after": ad.yahoo1m_parse({"after_ts": 1060}, [body]), "bad": [ad.yahoo1m_parse({}, ["<html>"]), ad.yahoo1m_parse({}, ['{"chart":{"result":null}}']), ad.yahoo1m_parse({}, ['{"chart":{"result":[{"meta":{"symbol":"X"}}]}}'])],
  "url": ad.yahoo1m_url("EURUSD=X", "7d"), "hosts": list(ad.YH_HOSTS), "reg": "yahoo1m" in ad.ADAPTERS}))`));
  assert.deepStrictEqual(out.all, [[1000, 'CL=F', 70.5, 10, 'o=70;h=71;l=69'], [1060, 'CL=F', 71.5, '', 'o=71;h=72;l=70'], [1180, 'CL=F', 73.5, 5, 'o=73;h=74;l=72']]);
  assert.deepStrictEqual(out.after.map((r) => r[0]), [1180], 'bars at or before the mark are dropped; a null close is skipped');
  assert.deepStrictEqual(out.bad, [[], [], []]);
  assert.strictEqual(out.url, 'https://query2.finance.yahoo.com/v8/finance/chart/EURUSD%3DX?interval=1m&range=7d&includePrePost=false');
  assert.deepStrictEqual(out.hosts, ['query2.finance.yahoo.com', 'query1.finance.yahoo.com']); assert.strictEqual(out.reg, true);
  assert.ok(/YH_HOSTS = \("query2\.finance\.yahoo\.com", "query1\.finance\.yahoo\.com"\)/.test(adapters), 'only the two public Yahoo chart hosts');
};

// R11 (RECBUILD1): the standalone Yahoo reference: the first run is a 7 day backfill, later runs ask for 1 day and add only newer bars, a gap over 20 hours backfills again, a failed symbol keeps its mark,
// a 429 on one Yahoo host falls back once to the other (the User-Agent is never changed), and a run with nothing standalone is unchanged.
gates.R11 = () => {
  const out = JSON.parse(py(`
import ref_adapters as ad
m._sleep = lambda x: None
urls = []
body = ${JSON.stringify(YAHOO)}
def get(url):
    urls.append(url)
    if "SI%3DF" in url: return 500, None, ""
    if "query2" in url and "NG%3DF" in url: return 429, None, ""
    return 200, body, ""
m.http_get = get
ref = {"id": "yahoo_1m", "adapter": "yahoo1m", "params": {"symbols": ["CL=F", "NG=F", "SI=F"], "range": "1d", "backfill_range": "7d"}}
state = {}
rows, calls, n429, fails = m.run_standalone(ref, "x", 7200, 2000, state)
first_urls = list(urls); urls.clear()
rows2, c2, n2, f2 = m.run_standalone(ref, "x", 7200, 2060, state)      # 60 s later, nothing newer than the high-water mark
second = list(urls); urls.clear()
state["CL=F"] = 100
m.run_standalone(ref, "x", 7200, 100 + 21 * 3600, state)
gap = [u for u in urls if "CL%3DF" in u][0]; urls.clear()
state["CL=F"] = 1000
m.run_standalone(ref, "x", 7200, 1000 + 3600, state)
recent = [u for u in urls if "CL%3DF" in u][0]
print(json.dumps({"n": len(rows), "r0": rows[0], "state": state, "fails": fails, "n429": n429, "first_rng": ["range=7d" in u for u in first_urls], "hosts": sorted({u.split("/")[2] for u in first_urls}),
  "n2": len(rows2), "f2": f2, "second_rng": ["range=1d" in u for u in second][:1], "gap7": "range=7d" in gap, "recent1": "range=1d" in recent, "refvals": len(m.REF_COLS) == len(rows[0]),
  "standalone": m.load_standalone(${JSON.stringify(path.join(root, 'kalshi-scalper', 'workers', 'RECREF_WATCHLIST.json'))})[0]["params"]["symbols"]}))`));
  assert.strictEqual(out.n, 6, 'CL=F and NG=F gave 3 bars each; SI=F failed');
  assert.strictEqual(out.r0[2], 'yahoo_1m:CL=F'); assert.strictEqual(out.r0[6], 1000); assert.strictEqual(out.r0[7], 'CL=F');
  assert.strictEqual(out.state['CL=F'], 1180); assert.strictEqual(out.state['NG=F'], 1180); assert.ok(!('SI=F' in out.state), 'a failed symbol keeps no mark, so the next run backfills it');
  assert.strictEqual(out.fails, 1); assert.ok(out.n429 >= 1, 'the 429 is counted');
  assert.strictEqual(out.first_rng.every(Boolean), true, 'the first run is a 7 day backfill');
  assert.ok(out.hosts.includes('query1.finance.yahoo.com') && out.hosts.includes('query2.finance.yahoo.com'), 'one fallback to the other host');
  assert.strictEqual(out.n2, 0, 'no duplicate bars'); assert.strictEqual(out.f2, 1);
  assert.deepStrictEqual(out.second_rng, [true]); assert.strictEqual(out.gap7, true); assert.strictEqual(out.recent1, true); assert.strictEqual(out.refvals, true);
  assert.deepStrictEqual(out.standalone, ['EURUSD=X', 'GBPUSD=X', 'JPY=X', 'AUDUSD=X', 'CAD=X', 'CL=F', 'NG=F', 'SI=F']);
  const code = strip(script + adapters);
  assert.ok(!/Mozilla|Chrome|Safari|spoof/i.test(code), 'no browser User-Agent');
  assert.ok(/"ref", "bars", day, "%s\.csv\.gz" % int\(now\)/.test(script), 'standalone bars go to a file named for the poll second, never overwritten by a re-run of the slot');
};

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }
