'use strict';
// The generic forward shadow runner (Nov 16, 2026). Each gate states the consequence. SR1 runs the hand case first (test/shadowRunnerHandCase.py, worked on paper before the code ran).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const gates = {};
const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, f))).digest('hex');
const py = (src) => JSON.parse(execFileSync('python3', ['-c', `
import sys, json, os
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
import shadow_runner as R
${src}`], { encoding: 'utf8' }).trim().split('\n').pop());
const runnerSrc = fs.readFileSync(path.join(root, 'scripts', 'shadow_runner.py'), 'utf8');
const code = runnerSrc.replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');

gates.SR1 = () => {
  const o = JSON.parse(execFileSync('python3', [path.join(__dirname, 'shadowRunnerHandCase.py')], { encoding: 'utf8' }).trim().split('\n').pop());
  assert.ok(o.match, JSON.stringify(o.got) + ' vs ' + JSON.stringify(o.want));
  assert.ok(o.all_get && o.min_close_is_start, 'every request goes to the elections host and the first pull starts at the written start constant');
  assert.strictEqual(o.pulled_until, o.max_close + 1, 'the pull cursor moves to just after the last settled close it read');
  assert.ok(o.second_run_same_n && o.second_run_new_requests === 1, 'a second run reads one list page and no candles, and no trade is counted twice');
};
gates.SR2 = () => {
  // Consequence: nothing runs on an input that is not the pinned one: a changed module, list or cuts file stops the run before any read; the real config pins the real files.
  const cfg = JSON.parse(fs.readFileSync(path.join(root, 'kalshi-scalper', 'workers', 'shadow', 'SHADOW_RUNNER_CONFIG.json'), 'utf8'));
  assert.strictEqual(cfg.list_sha256, sha('kalshi-scalper/workers/SHADOW_LIST_V1.json'));
  assert.strictEqual(cfg.cuts_sha256, sha('kalshi-scalper/workers/SHADOW_SPREAD_CUTS_V1.json'));
  for (const [n, h] of Object.entries(cfg.modules)) assert.strictEqual(sha('kalshi-scalper/workers/desk_a_verify/' + n + '.py'), h, n);
  assert.strictEqual(cfg.start_utc, 1794873600, 'the start is the written constant 2026-11-17T00:00:00Z');
  assert.strictEqual(cfg.modules.engine1_core, '53317e4b56a8328fb616d460d5cb4597af13a2b9020d73aefaa37717439694bf');
  assert.strictEqual(cfg.modules.engine1_driver, '1281ce0a1dc0bce7875bbafc4774358f557e45d0897b8099f5615c33cf12640b');
  const r = py(`
import tempfile, shutil
d = tempfile.mkdtemp()
for n in ("engine1_core", "engine1_enum", "engine1_split", "engine1_driver"): shutil.copy(os.path.join(${JSON.stringify(root)}, "kalshi-scalper", "workers", "desk_a_verify", n + ".py"), d)
pins = ${JSON.stringify(cfg.modules)}
ok = "ok"
try: R.load_modules(d, pins)
except R.Refused: ok = "refused"
open(os.path.join(d, "engine1_core.py"), "a").write("# changed")
try: R.load_modules(d, pins); bad = "ok"
except R.Refused: bad = "refused"
print(json.dumps([ok, bad]))`);
  assert.deepStrictEqual(r, ['ok', 'refused']);
};
gates.SR3 = () => {
  // Consequence: the puller can only ask the one public host with plain GETs, never follows a redirect, and stops for good after three 429s in a row (it never retries around a refusal).
  const r = py(`
calls = []
def g429(url): calls.append(url); return 429, None
p = R.Puller(get=g429, sleep=lambda s: None)
try: p.read("/markets", {"a": 1}); a = "no stop"
except R.Refused: a = "stopped"
seq = iter([429, 200]); ans = []
def g2(url): s = next(seq); return s, ({"markets": []} if s == 200 else None)
p2 = R.Puller(get=g2, sleep=lambda s: None); b = p2.read("/markets", {"a": 1})
print(json.dumps({"a": a, "n429": len(calls), "b": b, "host": R.HOST}))`);
  assert.deepStrictEqual([r.a, r.n429, r.b, r.host], ['stopped', 3, { markets: [] }, 'https://api.elections.kalshi.com/trade-api/v2']);
  assert.ok(/NoRedirect/.test(runnerSrc) && /return None/.test(runnerSrc.slice(runnerSrc.indexOf('class NoRedirect'), runnerSrc.indexOf('class NoRedirect') + 200)), 'redirects are refused');
  assert.ok(!/\b(POST|PUT|DELETE)\b/.test(code) && !/authorization|secret|token|private|\/orders|\/portfolio|firestore|firebase/i.test(code), 'no write call, no key, no order or account path, no Firestore');
};
gates.SR4 = () => {
  // Consequence: the Head's status rules, exactly. CANDIDATE needs 100 signals, PF 1.3 at 1c, 1.0 at 2c and both halves 1.0; DROPPED is PF under 1.0 at 1c after 60; the days to 100 are None under 5 signals, 0 at 100, else the ceiling at the observed rate.
  const r = py(`
base = {"n": 100, "pf_1c": 1.31, "no_losses_1c": False, "pf_2c": 1.0, "no_losses_2c": False, "pf_half1_1c": 1.0, "no_losses_half1_1c": False, "pf_half2_1c": 1.2, "no_losses_half2_1c": False, "days": 10.0}
s = lambda **k: R.status_of(dict(base, **k))
print(json.dumps({"cand": s(), "n99": s(n=99), "pf129": s(pf_1c=1.29), "pf2": s(pf_2c=0.99), "h1": s(pf_half1_1c=0.99), "h2": s(pf_half2_1c=0.5), "nolosses": s(pf_1c=None, no_losses_1c=True),
  "drop": s(n=60, pf_1c=0.99), "no_drop59": s(n=59, pf_1c=0.5), "keep": s(n=60, pf_1c=1.0),
  "d": [R.days_to_100({"n": 4, "days": 4.0}), R.days_to_100({"n": 100, "days": 9.0}), R.days_to_100({"n": 20, "days": 10.0}), R.days_to_100({"n": 7, "days": 3.0})]}))`);
  assert.deepStrictEqual([r.cand, r.n99, r.pf129, r.pf2, r.h1, r.h2, r.nolosses], ['CANDIDATE', 'collecting', 'collecting', 'collecting', 'collecting', 'collecting', 'CANDIDATE']);
  assert.deepStrictEqual([r.drop, r.no_drop59, r.keep], ['DROPPED', 'collecting', 'collecting']);
  assert.deepStrictEqual(r.d, [null, 0, 40, 40], 'n 20 in 10 days is 2 a day, 80 more is 40 days; n 7 in 3 days is 2.33 a day, 93 more is 39.86 days, rounded up to 40');
};
gates.SR5 = () => {
  // Consequence (S1): the published files carry per-spec aggregates only: no ticker, no per-trade amount, no per-day table, and the two labels are on the results file.
  const o = JSON.parse(execFileSync('python3', [path.join(__dirname, 'shadowRunnerHandCase.py')], { encoding: 'utf8' }).trim().split('\n').pop());
  const text = JSON.stringify(o.counts);
  assert.ok(!/KXTEST|x1|x2|"c":|"d":/.test(text) && Object.keys(o.counts).sort().join() === ['as_of_utc', 'expected_days_to_100', 'id', 'settled', 'signals', 'start_utc', 'status', 'target', 'voids', 'wins'].join());
  assert.deepStrictEqual(o.labels, ['forward', 'paper']);
  const r = py(`print(json.dumps([R.LABEL_PAPER, R.LABEL_FWD]))`);
  assert.ok(/validate-window income, upward biased, not a forecast/.test(r[0]) && /calendar days, weekends included/.test(r[1]));
  assert.ok(!/state/.test(JSON.stringify(Object.keys(o.counts))), 'no state in the counts file');
};
gates.SR6 = () => {
  // Consequence (Auditor B, S1 state): the private state is only ordered net amounts plus a day counter; building it day by day gives the IDENTICAL ordered sequence as a rebuild from scratch (ties on close broken by ticker), so a lost cache loses nothing; the cache key moves with the runner, list and holds.
  const o = JSON.parse(execFileSync('python3', [path.join(__dirname, 'shadowRunnerStateCase.py')], { encoding: 'utf8' }).trim().split('\n').pop());
  assert.ok(o.seq_equal && o.days_equal && o.agg_equal && o.n === 12, JSON.stringify(o));
  assert.ok(o.no_identifiers, 'no ticker, time or price in the per-spec state');
  assert.deepStrictEqual(o.state_keys, ['last_day', 'n_days', 'seq']);
  assert.deepStrictEqual(o.first_two.map((t) => t[0]), [8.2, 8.2, -1.8], 'the tie at one close is ordered by ticker (TB before TC)');
  assert.ok(/def cache_key/.test(runnerSrc) && /list_sha256/.test(runnerSrc.slice(runnerSrc.indexOf('def cache_key'), runnerSrc.indexOf('def cache_key') + 500)) && /HOLDS\.json/.test(runnerSrc.slice(runnerSrc.indexOf('def cache_key'), runnerSrc.indexOf('def cache_key') + 500)));
};
gates.SR8 = () => {
  // Consequence: a cache miss is visible: the counts file says rebuilt_from_scratch true when the run started with no state, false when it had one.
  const o = JSON.parse(execFileSync('python3', [path.join(__dirname, 'shadowRunnerStateCase.py')], { encoding: 'utf8' }).trim().split('\n').pop());
  assert.deepStrictEqual(o.rebuilt, [true, false]);
};
gates.SR7 = () => {
  // Consequence (Auditor B S1 state): the daily workflow keeps the private state only in the Actions cache (never uploaded, committed or printed), pushes only the two aggregate files to its own shadow-data branch, never main, and stops by itself.
  const wf = fs.readFileSync(path.join(root, '.github', 'workflows', 'shadow-forward.yml'), 'utf8');
  const steps = wf.replace(/^#.*$/gm, '');
  assert.ok(/actions\/cache\/restore@/.test(steps) && /actions\/cache\/save@/.test(steps) && !/upload-artifact/.test(steps), 'state in the cache only, no artifact');
  assert.ok(/--print-key/.test(steps) && /restore-keys/.test(steps));
  assert.ok(/git add shadow_results\.json shadow_counts\.json/.test(steps) && !/git add (-A|\.)/.test(steps) && !/state\//.test(steps.slice(steps.indexOf('git add'))), 'only the two aggregate files are added');
  assert.ok(/git push -q origin shadow-data/.test(steps) && !/git push[^\n]*\bmain\b/.test(steps));
  assert.ok(/ref: main/.test(steps) && /persist-credentials: false/.test(steps) && /2027-01-31T23:59:00Z/.test(steps));
  assert.ok(!/\bcat\b[^\n]*state|echo[^\n]*state\/|ls[^\n]*state/.test(steps), 'the state is never printed');
  assert.ok(!/pull_request/.test(steps) && /schedule:/.test(steps) && /workflow_dispatch/.test(steps), 'only the schedule and a hand dispatch run it, never a pull request (nothing can read or poison the cache)');
  assert.ok(/unexpected path in the commit/.test(steps), 'the commit fails if any other path changed');
  assert.ok(/python3 -I code\/scripts\/shadow_runner\.py/.test(steps) && !/secrets\.(?!GITHUB_TOKEN)/.test(steps), 'no secret but the built-in token');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message.split('\n')[0]); } }
process.exit(failed ? 1 : 0);
