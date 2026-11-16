'use strict';
// NC15 place counts (Nov 16, 2026, the owner: "Allow the host"). Each gate states the consequence.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'nc15-place-counts.yml'), 'utf8');
const wfCode = wf.replace(/^\s*#.*$/gm, '');
const gates = {};
const norm = new Function(html.slice(html.indexOf('  function kalshiCountsNorm('), html.indexOf('  function kalshiCountsEnsure(')) + '; return kalshiCountsNorm;')();
const good = { places: [{ id: 'WH-NC15-WTI', fill_checked_signals: 12, status: 'active', target: 60, start_utc: '2026-11-13T02:40:00Z', as_of_utc: '2026-11-16T18:00:00Z' }, { id: 'WH-NC15-SILVER', fill_checked_signals: 3, status: 'parked', target: 60, start_utc: '2026-11-13T02:40:00Z', as_of_utc: '2026-11-16T18:00:00Z' }] };

// NC1: the page makes exactly one request to that host: a read-only GET of the one counts file, with no credentials, and nothing else on the host is named anywhere.
gates.NC1 = () => {
  const urls = [...html.matchAll(/https?:\/\/raw\.githubusercontent\.com[^'"\s)]*/g)].map((m) => m[0]);
  assert.deepStrictEqual(urls, ['https://raw.githubusercontent.com/shwoopnet/shwoopnet/nc15-counts/nc15_place_counts.json'], 'one path on the host, and only the counts file');
  const ens = html.slice(html.indexOf('  function kalshiCountsEnsure('), html.indexOf("  // Gold's kill state: read once"));
  assert.ok(/fetch\(KAL_COUNTS_URL, \{ cache: 'no-cache', credentials: 'omit' \}\)/.test(ens) && !/method|POST|body|headers/.test(ens), 'a plain GET with no credentials, headers or body');
  assert.ok(!/setInterval|setTimeout/.test(ens), 'no timer: it is read when the page is drawn and again only after ten minutes');
};
// NC2: only counts reach the page: the validator keeps the id, the signal count, the status, the target and the as-of time, refuses a bad shape, and ignores every other field (a price or a dollar figure in the file would never be shown).
gates.NC2 = () => {
  const by = norm(good);
  assert.deepStrictEqual(by['WH-NC15-WTI'], { signals: 12, status: 'active', target: 60, asOf: '2026-11-16T18:00:00Z' });
  assert.strictEqual(by['WH-NC15-SILVER'].status, 'parked');
  assert.strictEqual(norm({ places: [{ id: 'bad', fill_checked_signals: 1 }] }), null, 'an id that is not a place id is refused');
  assert.strictEqual(norm({ places: [{ id: 'WH-NC15-WTI', fill_checked_signals: -1 }] }), null);
  assert.strictEqual(norm({ places: [{ id: 'WH-NC15-WTI', fill_checked_signals: 1.5 }] }), null);
  assert.strictEqual(norm({ nope: 1 }), null);
  const withMoney = norm({ places: [{ id: 'WH-NC15-WTI', fill_checked_signals: 4, pnl: 99, price: 0.5, status: 'active', target: 60 }] });
  assert.deepStrictEqual(Object.keys(withMoney['WH-NC15-WTI']).sort(), ['asOf', 'signals', 'status', 'target'], 'no other field is kept');
};
// NC3: the workflow keeps Auditor B's conditions: nc-data read-only and sparse, only the one wrapper command, the push touches only the counts file on its own branch, no secret and no Kalshi request, a stop date.
gates.NC3 = () => {
  assert.deepStrictEqual([...wfCode.matchAll(/python3 [^\n]*/g)].map((m) => m[0].trim()), ['python3 -I code/kalshi-scalper/workers/testing/nc15_place_counts.py nc nc15_place_counts.json "$(date -u +%Y-%m-%dT%H:%M:%SZ)"'], 'only the wrapper command runs on the book files');
  assert.ok(/ref: nc-data[\s\S]*?path: nc[\s\S]*?sparse-checkout: nc15[\s\S]*?persist-credentials: false/.test(wfCode), 'nc-data is checked out read only (no credentials kept) and only its nc15 folder');
  assert.ok(/git add nc15_place_counts\.json/.test(wfCode) && !/git add (-A|\.)/.test(wfCode) && /origin nc15-counts/.test(wfCode) && !/origin main|origin nc-data/.test(wfCode), 'the push touches only the counts file on nc15-counts');
  assert.ok(!/secrets\.(?!GITHUB_TOKEN)/.test(wfCode) && !/kalshi\.com|curl|wget/.test(wfCode), 'no secret and no Kalshi request');
  assert.ok(/2027-01-31T23:59:00Z/.test(wfCode) && /permissions:\s+contents: write\s+concurrency/.test(wfCode) && /cancel-in-progress: false/.test(wfCode), 'a stop date, contents write only, never cancelling');
  assert.ok(/actions\/checkout@[0-9a-f]{40}/.test(wfCode) && !/actions\/checkout@v/.test(wfCode), 'checkout is pinned by commit');
};
// NC4: the files the wrapper pins are on main with the hashes the allow line and the wrapper name.
gates.NC4 = () => {
  const sha = (f) => require('crypto').createHash('sha256').update(fs.readFileSync(path.join(root, f))).digest('hex');
  assert.strictEqual(sha('kalshi-scalper/workers/desk_a_held/nc15_wheel_counts.py'), '23f5932d7f3f2abd7e42a71ffacdf4accc31e6878312f8cccd41cee8a7f8f44c', 'the counting core is the pinned one');
  assert.strictEqual(sha('kalshi-scalper/workers/testing/nc15_place_counts.py'), '1a4f770af6abdc9519494ef80048be841dedf0543f088e8a0b675a6a32532733', 'the wrapper is the one Auditor B cleared');
};
// NC5: the page shows the depth cells as signals toward 60, and a parked place as parked (rate), not as a progress bar.
gates.NC5 = () => {
  assert.ok(/word: building \? 'BUILDING' : bkey === 'live' \? 'ON TRIAL' : parked \? 'PARKED \(RATE\)' : 'COLLECTING'/.test(html), 'a parked place says parked (rate)');
  assert.ok(/frac: !parked && tgt && have !== null/.test(html), 'a parked place draws no progress');
  const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8')).strategies.filter((r) => r.id.indexOf('WH-NC15-') === 0 && r.stage === 'Shadow');
  assert.strictEqual(reg.length, 7);
  for (const r of reg) assert.deepStrictEqual([r.roomTarget, r.roomWhat], [60, 'signals toward 60'], r.id);
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
