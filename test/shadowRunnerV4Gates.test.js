'use strict';
// The forward shadow runner for SHADOW_LIST_V2, V3 and V4 (Nov 17, 2026). Each gate states the consequence. Data in test/shadowRunnerV4Check.py is invented; nothing here reads the network.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, f))).digest('hex');
const read = (f) => fs.readFileSync(path.join(root, f), 'utf8');
const cfg = JSON.parse(read('kalshi-scalper/workers/shadow/SHADOW_RUNNER_V4_CONFIG.json'));
const o = JSON.parse(execFileSync('python3', ['-I', path.join(__dirname, 'shadowRunnerV4Check.py')], { encoding: 'utf8' }).trim().split('\n').pop());
const gates = {};

gates.V4_1 = () => {
  // Consequence: nothing runs on a feature module, list or fixture that is not the pinned one, so the audited functions are the ones that score.
  assert.strictEqual(cfg.list_sha256, sha('kalshi-scalper/workers/SHADOW_LIST_V4.json'));
  assert.strictEqual(cfg.list_sha256, 'b8c4f727c38fa52c81800ef58319b15e74872f8359e3d3752468a9af41878cd2');
  assert.strictEqual(cfg.fixture_sha256, sha('kalshi-scalper/workers/V4_RUNNER_FIXTURE_NOV16.json'));
  assert.strictEqual(cfg.fixture_sha256, '38e875a2665c1e420a2c4fcb058b7c1e879c81e65abb01798c5e4e7f5dfbd461');
  for (const [n, h] of Object.entries(cfg.modules)) assert.strictEqual(sha('kalshi-scalper/workers/desk_a_verify/' + n + '.py'), h, n);
  assert.strictEqual(cfg.modules.engine1_batchc, 'ba77f70c7d86152539ad01cbd958d1056e3e78b40b3a568693f6ea444f77a279');
  assert.strictEqual(cfg.modules.engine1_batchb, '68a5ab435d8246be30681a703179d88608b0384ce2ca50f4f6bad458cea07f1e');
  assert.strictEqual(cfg.modules.engine1_enum, 'e42ee1a45f67b76e8560cd9cbefac352fce9a765c8300bc04d5ce05a27e4d5a7');
  assert.deepStrictEqual(o.loaded, ['engine1_batchb', 'engine1_batchc', 'engine1_core', 'engine1_driver', 'engine1_enum', 'engine1_split']);
};
gates.V4_2 = () => {
  // Consequence: the runner's feature value and class equal Desk A's hand arithmetic on every one of the 26 invented cases, missing candles included (a missing candle is no feature and no entry).
  assert.strictEqual(o.fixture_cases, 26);
  assert.deepStrictEqual(o.fixture_bad, []);
};
gates.V4_3 = () => {
  // Consequence: only the class a pick names enters: oiacc down enters, up does not, a null open interest does not; a market the held-out guard refuses is counted as refused and never scored; a market that closed before the start is not forward.
  assert.ok(o.band_found);
  assert.strictEqual(o.down_trades, 1);
  assert.strictEqual(o.up_trades, 0);
  assert.strictEqual(o.null_oi_trades, 0);
  assert.strictEqual(o.held_trades, 0);
  assert.strictEqual(o.held_refused, 1);
  assert.strictEqual(o.before_start_trades, 0);
};
gates.V4_4 = () => {
  // Consequence: ethmom3 reads the ETH market of the SAME close: up enters, down does not, a missing ETH candle or market gives no entry, and a held ETH market gives no entry (the other series is under the guard too).
  assert.strictEqual(o.eth_up_trades, 1);
  assert.strictEqual(o.eth_down_trades, 0);
  assert.strictEqual(o.eth_missing_trades, 0);
  assert.strictEqual(o.eth_absent_trades, 0);
  assert.strictEqual(o.eth_held_trades, 0);
};
gates.V4_5 = () => {
  // Consequence: the two Bitcoin picks do not log before 2026-11-21T00:00Z (H09) whatever the config start is; every other pick starts at the config start; the start is a written constant.
  assert.strictEqual(o.btc_start, Date.parse('2026-11-21T00:00:00Z') / 1000);
  assert.strictEqual(o.other_start, cfg.start_utc);
  assert.ok(Number.isInteger(cfg.start_utc) && cfg.start_utc >= Date.parse('2026-11-17T00:00:00Z') / 1000, 'never earlier than the list start');
  assert.ok(/^shadow-state-v234-71bc18fb-ecc64e55-b8c4f727-/.test(o.cache_key), 'its own state key, built from the three list shas');
};
gates.V4_6 = () => {
  // Consequence: V1 is untouched and keeps its own state and files; V4 cannot overwrite V1's results, and the runner holds no key and places no order.
  const v1 = read('scripts/shadow_runner.py');
  assert.ok(!/shadow_runner_v4|SHADOW_LIST_V4/.test(v1), 'V1 does not know V4');
  const v4 = read('scripts/shadow_runner_v4.py').replace(/"""[\s\S]*?"""/g, '').replace(/#.*$/gm, '');
  assert.ok(!/POST|Authorization|KALSHI_|\/orders|\/portfolio|requests\.post|firestore/i.test(v4));
  assert.ok(!/https?:\/\//.test(v4), 'no host named here: the only host is V1 Puller\'s elections host');
  assert.ok(/shadow_results_%s\.json/.test(v4) && /shadow_counts_%s\.json/.test(v4) && /v\.lower\(\)/.test(v4));
  assert.ok(!/"shadow_results\.json"|"shadow_counts\.json"/.test(v4));
  const wf = read('.github/workflows/shadow-forward-lists.yml');
  assert.ok(/group: shadow-forward-lists/.test(wf) && /cancel-in-progress: false/.test(wf));
  assert.ok(/shadow_runner_v4\.py/.test(wf) && !/shadow_runner\.py/.test(wf));
  assert.ok(/shadow_\(results\|counts\)_v\[234\]/.test(wf) && !/cp \.\.\/out\/shadow_results\.json/.test(wf));
  assert.ok(/2027-01-31T23:59:00Z/.test(wf), 'it stops by itself');
  assert.ok(/contents: write/.test(wf) && !/actions: write|id-token/.test(wf));
  const v1wf = read('.github/workflows/shadow-forward.yml');
  assert.ok(/group: shadow-forward$/m.test(v1wf) && /shadow_runner\.py/.test(v1wf), 'V1 workflow is as it was');
};

gates.V4_7 = () => {
  // Consequence: V2 reads the Bitcoin market of the SAME close (btcmom3): the matching class enters, the other does not, a missing Bitcoin candle or market gives no entry; Desk A's 17 case fixture passes; V2 starts no earlier than 2026-11-21.
  const c2 = JSON.parse(read('kalshi-scalper/workers/shadow/SHADOW_RUNNER_V2_CONFIG.json'));
  assert.strictEqual(c2.list_sha256, sha('kalshi-scalper/workers/SHADOW_LIST_V2.json'));
  assert.strictEqual(c2.list_sha256, '71bc18fb8200dcb48bd7e280' + c2.list_sha256.slice(24));
  assert.strictEqual(c2.fixture_sha256, sha('kalshi-scalper/workers/BTCMOM3_RUNNER_FIXTURE_NOV16.json'));
  for (const [n, h] of Object.entries(c2.modules)) assert.strictEqual(sha('kalshi-scalper/workers/desk_a_verify/' + n + '.py'), h, n);
  assert.strictEqual(o.btcmom3_fixture_cases, 17);
  assert.deepStrictEqual(o.btcmom3_fixture_bad, []);
  assert.strictEqual(o.v2_match_trades, 1);
  assert.strictEqual(o.v2_other_class_trades, 0);
  assert.strictEqual(o.v2_btc_absent_trades, 0);
  assert.strictEqual(o.v2_start, Date.parse('2026-11-21T00:00:00Z') / 1000);
};
gates.V4_8 = () => {
  // Consequence: V3's swid picks run on the audited function (a wider spread than 180 s earlier is up, a missing candle is no feature); V3's three vspike picks are NOT run, because their frozen cuts are not pinned, and a list that carries a vspike pick that is neither excluded nor given cuts refuses to run at all (no guessed cut).
  const c3 = JSON.parse(read('kalshi-scalper/workers/shadow/SHADOW_RUNNER_V3_CONFIG.json'));
  assert.strictEqual(c3.list_sha256, sha('kalshi-scalper/workers/SHADOW_LIST_V3.json'));
  assert.strictEqual(c3.modules.engine1_batchb2, sha('kalshi-scalper/workers/desk_a_verify/engine1_batchb2.py'));
  assert.strictEqual(c3.modules.engine1_batchb2, 'aa6e06824b2799f49812d201' + c3.modules.engine1_batchb2.slice(24));
  assert.deepStrictEqual(o.v3_excluded, o.v3_vspike_ids);
  assert.strictEqual(o.v3_excluded.length, 3);
  assert.strictEqual(o.v3_unexcluded_refused, true);
  assert.strictEqual(o.swid_up, 2);
  assert.strictEqual(o.swid_missing, null);
  assert.ok(!c3.vspike_cuts_file, 'no cuts file is pinned yet');
  // the vspike class code, on invented numbers and the real cuts shape: ratio 1.0 is mid (between 0.7 and 1.1), 0.5 is low, 2.0 is high; a null cut, a missing volume candle or a zero mean is no feature
  assert.deepStrictEqual([o.vspike_mid_ratio1, o.vspike_low, o.vspike_high, o.vspike_nullcut, o.vspike_missing, o.vspike_zero_mean], ['mid', 'low', 'high', null, null, null]);
};

let failed = 0;
for (const [n, f] of Object.entries(gates)) {
  try { f(); console.log('ok   ' + n); } catch (e) { failed++; console.log('FAIL ' + n + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
