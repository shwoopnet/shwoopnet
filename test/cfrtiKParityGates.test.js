'use strict';
// CFRTI-K, the pure decision (functions/kalshiCfrtiKLib.js). Consequence: the bot decides exactly as the research desk's frozen scorer decided on the same inputs, so a probation fill is a fill of the
// tested rule and not of a re-implementation that drifted. The 20 vectors are Idea Desk A's (development windows and constructed missing-input cases, inputs and decisions only, no outcome).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const L = require('../functions/kalshiCfrtiKLib');
const V = require('./fixtures/cfrtiKParityVectors.json');
const gates = {};
const run = (v) => L.cfrtiKDecide({ floorStrike: v.floor_strike, yesBid: v.yes_bid, yesAsk: v.yes_ask, marks: v.marks.map((m) => m.price), openMark: v.open_mark ? v.open_mark.price : null });

gates['PV1 all 20 desk vectors: the same decision and the same reason, and the numbers agree to 1e-9'] = () => {
  assert.strictEqual(V.vectors.length, 20);
  for (const v of V.vectors) {
    const r = run(v);
    assert.strictEqual(r.trade, v.decision !== 'no order', v.case);
    assert.strictEqual(r.reason, v.reason, v.case);
    if (v.decision === 'BUY YES') assert.strictEqual(r.side, 'yes', v.case);
    if (v.decision === 'BUY NO') assert.strictEqual(r.side, 'no', v.case);
    for (const [mine, theirs] of [['edge', 'edge'], ['modelYes', 'model_yes'], ['sideChance', 'side_chance'], ['sidePrice', 'side_price']]) {
      if (typeof v[theirs] === 'number' && r[mine] !== null) assert.ok(Math.abs(r[mine] - v[theirs]) < 1e-9, v.case + ' ' + mine + ' ' + r[mine] + ' vs ' + v[theirs]);
    }
    if (r.sd !== null && typeof v.sd === 'number') assert.ok(Math.abs(r.sd - v.sd) < 1e-9, v.case + ' sd');
    if (r.trade && typeof v.index === 'number') assert.ok(Math.abs(r.index - v.index) < 1e-6, v.case + ' index');
    if (typeof v.n_changes === 'number' && r.nChanges !== null) assert.strictEqual(r.nChanges, v.n_changes, v.case + ' changes');
  }
};
gates['PV2 the vectors cover every refusal the rule has, and fire both sides'] = () => {
  const seen = new Set(V.vectors.map((v) => v.reason));
  for (const r of ['trade', 'no edge', 'not cheap', 'spread over 3c or crossed', 'no decision candle', 'under 6 changes', 'no opening minute', 'no volatility']) assert.ok(seen.has(r), 'a vector for ' + r);
  assert.ok(V.vectors.some((v) => v.decision === 'BUY YES') && V.vectors.some((v) => v.decision === 'BUY NO'));
};
gates['PV3 the edge line and the band edges are inclusive within 1e-9, and 6 changes fire while 5 do not'] = () => {
  const v = (i) => V.vectors[i];
  assert.strictEqual(run(v(14)).trade, true, 'edge 0.05005 fires'); assert.strictEqual(run(v(13)).trade, false, 'edge 0.0494 does not');
  assert.strictEqual(run(v(2)).trade, true, 'a YES ask of exactly 0.05'); assert.strictEqual(run(v(15)).reason, 'no edge', 'a side price of exactly 0.30 is inside the band (it is judged on edge)');
  assert.strictEqual(run(v(16)).trade, true, 'exactly 6 changes'); assert.strictEqual(run(v(17)).reason, 'under 6 changes', 'exactly 5');
};
gates['PV4 a missing or zero input is no order: no quote, no strike, no opening mark, no decision mark; nothing is guessed'] = () => {
  const base = run(V.vectors[0]); assert.strictEqual(base.trade, true);
  const in0 = (o) => L.cfrtiKDecide(Object.assign({ floorStrike: V.vectors[0].floor_strike, yesBid: V.vectors[0].yes_bid, yesAsk: V.vectors[0].yes_ask, marks: V.vectors[0].marks.map((m) => m.price), openMark: V.vectors[0].open_mark.price }, o));
  assert.strictEqual(in0({ yesBid: null }).trade, false); assert.strictEqual(in0({ yesAsk: undefined }).trade, false); assert.strictEqual(in0({ floorStrike: null }).trade, false);
  assert.strictEqual(in0({ openMark: null }).trade, false); assert.strictEqual(in0({ openMark: 0 }).trade, false); assert.strictEqual(in0({ marks: [] }).trade, false);
  assert.strictEqual(in0({ marks: V.vectors[0].marks.map((m, i) => (i === 0 ? null : m.price)) }).trade, false, 'no decision-minute mark');
  assert.strictEqual(in0({ marks: V.vectors[0].marks.map(() => 100) }).trade, false, 'no movement means no volatility, no order');
  assert.strictEqual(L.cfrtiKDecide().trade, false); assert.strictEqual(L.cfrtiKDecide(null).trade, false);
};
gates['PV5 the perp candle reader keys on the END of the minute, takes bid and ask closes, and treats a missing side or a zero as no mark'] = () => {
  const c = (sec, b, a) => ({ end_period_ts: sec, bid: { close: b }, ask: { close: a } });
  const cs = [c(1000 - 120, '99', '101'), c(1000 - 180, '0', '101'), c(1000 - 240, '99', null), c(1000 - 900, '50', '52'), c(1000 - 119, '1', '1'), { end_period_ts: 1000 - 300 }];
  const r = L.perpMarks(cs, 1000);
  assert.strictEqual(r.marks[0], 100, 'mid of 99 and 101 at the decision minute'); assert.strictEqual(r.marks[1], null, 'a zero side is missing'); assert.strictEqual(r.marks[2], null, 'a null side is missing');
  assert.strictEqual(r.openMark, 51); assert.strictEqual(r.decisionPresent, true); assert.strictEqual(r.marks[3], null, 'no candle for that minute: null, never a neighbour');
  assert.strictEqual(r.newestEndSec, 1000 - 119);
  assert.strictEqual(L.perpMarks(cs.slice(1), 1000).decisionPresent, false, 'without the decision candle it is absent; an older candle is not substituted');
  assert.strictEqual(L.perpMarks(null, 1000).decisionPresent, false);
};
gates['PV6 the normal distribution is accurate to 1e-12 in the body and the tails'] = () => {
  const ref = [[0, 0.5], [1, 0.8413447460685429], [-1, 0.15865525393145707], [1.96, 0.9750021048517795], [3, 0.9986501019683699], [-3, 0.0013498980316301035], [-6, 9.865876450376946e-10], [6, 0.9999999990134123]];
  for (const [x, p] of ref) assert.ok(Math.abs(L.phi(x) - p) < 1e-12, x + ': ' + L.phi(x));
  assert.ok(L.phi(40) === 1 && L.phi(-40) === 0 && L.phi(-8) > 0);
};
gates['PV7 the library is pure: no network, no store, no clock, no randomness, no environment, no require of anything'] = () => {
  const c = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiCfrtiKLib.js'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
  assert.ok(!/require\(|fetch|firebase|Date\.now|new Date|Math\.random|process\.env|setTimeout|setInterval|performance|https?:/.test(c));
};
(async () => { let failed = 0; for (const [n, f] of Object.entries(gates)) { try { await f(); console.log('ok   ' + n); } catch (e) { failed++; console.log('FAIL ' + n + ': ' + (e && e.stack ? e.stack.split('\n').slice(0, 5).join(' | ') : e)); } } process.exit(failed ? 1 : 0); })();
