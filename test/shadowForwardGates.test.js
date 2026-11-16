'use strict';
// The generic forward shadow scorer (Nov 16, 2026). Each gate states the consequence. HAND CASE FIRST (SH1): every figure below was worked on paper before the code ran.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const M = require('../scripts/shadow_forward.js');
const gates = {};
const SPEC = { id: 'T1', market: 'KXTEST15M', entry: { look: 600 }, exit: { holdToSettle: true }, side: 'cheap', startUtc: '2026-11-17T00:00:00Z', target: 60 };
const T0 = Date.parse('2026-11-17T00:00:00Z');
const sig = (i, side, price, result, o) => Object.assign({ specId: 'T1', ticker: 'KXTEST15M-' + i, side, price, tsMs: T0 + i * 1000, fillChecked: true, result }, o || {});

// Hand case: a 10c yes buy that wins, a 10c yes buy that loses, and a 50c no buy that wins.
// fee(0.10) = ceil(0.07 x 10 x 0.1 x 0.9 x 100) / 100 / 10 = ceil(6.3) / 1000 = 0.007; win = 1 - 0.10 - 0.007 = 0.893; loss = -(0.10 + 0.007) = -0.107.
// fee(0.50) = ceil(0.07 x 10 x 0.25 x 100) / 1000 = ceil(17.5) / 1000 = 0.018; win = 1 - 0.50 - 0.018 = 0.482.
// cash net = 0.893 - 0.107 + 0.482 = 1.268; gross win 1.375, gross loss 0.107, PF = 12.850 (1.375 / 0.107 = 12.85).
gates.SH1 = () => {
  const s = M.scoreSpecs([SPEC], [sig(1, 'yes', 0.10, 'yes'), sig(2, 'yes', 0.10, 'no'), sig(3, 'no', 0.50, 'no')], T0 + 1e6).T1;
  assert.deepStrictEqual([s.fillCheckedSignals, s.settled, s.wins, s.losses], [3, 3, 2, 1]);
  assert.strictEqual(s.slip.cash.net, 1.268);
  assert.strictEqual(s.slip.cash.pf, 12.85);
  // +1c: the 10c buys pay 11c (fee(0.11) = ceil(0.07 x 10 x 0.0979 x 100) / 1000 = ceil(6.853) / 1000 = 0.007) and the 50c buy pays 51c (fee 0.018): win 0.883, loss -0.117, win 0.472: net 1.238.
  assert.strictEqual(s.slip['+1c'].net, 1.238);
  assert.ok(s.slip['+2c'].net < s.slip['+1c'].net && s.slip['+1c'].net < s.slip.cash.net, 'a worse fill never earns more');
};

gates.SH2 = () => {
  // Consequence: only fill-checked signals at or after the spec's start count, one per ticker and side, and an unsettled signal counts as a signal but not as settled.
  const rows = [sig(1, 'yes', 0.10, 'yes'), sig(1, 'yes', 0.10, 'yes', { tsMs: T0 + 5000 }), sig(2, 'yes', 0.10, 'no', { fillChecked: false }), sig(3, 'yes', 0.10, 'no', { tsMs: T0 - 1 }), sig(4, 'yes', 0.10, null), sig(5, 'yes', 0.10, 'no', { specId: 'OTHER' })];
  const s = M.scoreSpecs([SPEC], rows, T0 + 1e6).T1;
  assert.deepStrictEqual([s.fillCheckedSignals, s.settled, s.wins], [2, 1, 1], JSON.stringify(s));
  assert.strictEqual(M.scoreSpecs([SPEC], [sig(1, 'yes', 0.10, 'yes', { tsMs: T0 + 9e9 })], T0 + 1e6).T1.fillCheckedSignals, 0, 'a signal from after the as-of time does not exist yet');
};

gates.SH3 = () => {
  // Consequence: no losses is said as no losses (pf null, noLosses true), never as an infinite or invented number; an empty spec has no figures.
  const s = M.scoreSpecs([SPEC], [sig(1, 'yes', 0.10, 'yes')], T0 + 1e6).T1.slip.cash;
  assert.deepStrictEqual([s.pf, s.noLosses], [null, true]);
  const e = M.scoreSpecs([SPEC], [], T0 + 1e6).T1.slip.cash;
  assert.deepStrictEqual([e.net, e.pf, e.noLosses], [0, null, false]);
};

gates.SH4 = () => {
  // Consequence: the spec list is frozen in shape: unknown or performance keys, duplicate ids, a bad side or time and an empty list are all refused, and a bad list scores nothing.
  assert.strictEqual(M.validateSpecs([SPEC]).ok, true);
  const bad = (o) => M.validateSpecs([Object.assign({}, SPEC, o)]).ok;
  assert.strictEqual(bad({ minPf: 1.3 }), false, 'no performance parameter');
  assert.strictEqual(bad({ promote: true }), false);
  assert.strictEqual(bad({ side: 'both' }), false);
  assert.strictEqual(bad({ startUtc: 'soon' }), false);
  assert.strictEqual(bad({ target: 0 }), false);
  assert.strictEqual(bad({ id: 'lower' }), false);
  assert.strictEqual(M.validateSpecs([SPEC, SPEC]).ok, false, 'duplicate id');
  assert.strictEqual(M.validateSpecs([]).ok, false);
  assert.throws(() => M.scoreSpecs([Object.assign({}, SPEC, { minPf: 2 })], [], T0));
};

gates.SH5 = () => {
  // Consequence: the counts feed carries counts and dates only. No price, dollar figure or profit factor can reach the Strategies page through it.
  const scores = M.scoreSpecs([SPEC], [sig(1, 'yes', 0.10, 'yes'), sig(2, 'yes', 0.10, 'no')], T0 + 1e6);
  const f = M.countsFeed([SPEC], scores, T0 + 1e6);
  assert.deepStrictEqual(f.specs[0], { id: 'T1', signals: 2, settled: 2, wins: 1, voids: 0, target: 60, start_utc: '2026-11-17T00:00:00Z', as_of_utc: new Date(T0 + 1e6).toISOString() });
  assert.ok(!/pnl|net|pf|price|slip|\$/i.test(JSON.stringify(f).replace(/start_utc|as_of_utc/g, '')), 'counts and dates only');
};

gates.SH6 = () => {
  // Consequence: the scorer is pure and cannot trade: it requires only the fee helper, names no network, file system, clock or order code, and has no promote word.
  const src = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'shadow_forward.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.deepStrictEqual([...src.matchAll(/require\(([^)]*)\)/g)].map((m) => m[1]), ["'../functions/kalshiShadowLib.js'"]);
  assert.ok(!/fetch|http|process\.|Date\.now|Math\.random|writeFile|fs\.|firebase|orders?\b|promote|PASS/.test(src), 'no network, clock, file, order or promote word');
};

gates.SH7 = () => {
  // Consequence (the Head of R&D's void ruling, Nov 16, 2026): a void is a settled trade at minus the entry fee (price refunded, fee kept), counted in `settled` and as a loss, and in its own `voids` count.
  // Hand case: a 10c yes buy that wins (+0.893), and a 10c yes buy that is void (fee(0.10) = 0.007, so -0.007): net 0.886, gross loss 0.007, PF 127.571 (0.893 / 0.007 = 127.571).
  const s = M.scoreSpecs([SPEC], [sig(1, 'yes', 0.10, 'yes'), sig(2, 'yes', 0.10, 'void')], T0 + 1e6).T1;
  assert.deepStrictEqual([s.settled, s.wins, s.losses, s.voids], [2, 1, 1, 1]);
  assert.strictEqual(s.slip.cash.net, 0.886);
  assert.strictEqual(s.slip.cash.pf, 127.571);
  assert.strictEqual(M.signalPnl(sig(3, 'no', 0.50, 'void'), 0), -0.018, 'a void on a 50c buy costs its 1.8c fee, not the price');
  assert.strictEqual(M.countsFeed([SPEC], M.scoreSpecs([SPEC], [sig(1, 'yes', 0.10, 'void')], T0 + 1e6), T0 + 1e6).specs[0].voids, 1, 'the counts feed carries the voids count');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
