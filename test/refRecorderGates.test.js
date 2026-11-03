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

for (const [name, fn] of Object.entries(gates)) { fn(); console.log('ok   ' + name); }
