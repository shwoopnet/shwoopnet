'use strict';
// Rolling shadow record in the nightly report (Nov 12, 2026). Each gate states the consequence: the flag cannot flip because the report was read more often or the rows came in a different order, a rule
// with too little data never gets a verdict, and the replay reads nothing from Kalshi and writes nothing.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sh = require('../functions/kalshiShadowLib.js');
const rep = require('../functions/kalshiReportLib.js');
const gates = {};
const NOW = Date.parse('2026-11-30T00:00:00Z'), DAY = 86400000;
const R = { id: 'RULEX' };
const mk = (n, f) => Array.from({ length: n }, (_, i) => ({ rule: 'RULEX', atMs: Date.parse('2026-11-01T00:00:00Z') + i * 3 * 3600000, settled: true, wouldFill: true, pnl: f(i) }));
const good = (i) => (i % 10 === 9 ? -0.5 : 0.12);
const shuffle = (a) => { const b = a.slice(); let s = 7; for (let i = b.length - 1; i > 0; i--) { s = (s * 1103515245 + 12345) % 2147483648; const j = s % (i + 1); [b[i], b[j]] = [b[j], b[i]]; } return b; };

gates.RR1 = () => {
  const rows = mk(75, (i) => (i % 3 === 0 ? -0.2 : 0.09));
  const a = sh.shadowRolling(R, rows), b = sh.shadowRolling(R, shuffle(rows));
  assert.deepStrictEqual(a, b, 'row order cannot change the record');
  assert.deepStrictEqual(a, sh.shadowRolling(R, rows), 'reading twice gives the same answer');
};
gates.RR2 = () => {
  const r = sh.shadowRolling(R, mk(59, good));
  assert.strictEqual(r.status, 'collecting'); assert.strictEqual(r.flag, null);
  assert.strictEqual(r.pf, undefined, 'no figures before 60 fillable signals');
  // unfillable or unsettled rows never count toward the 60
  const half = mk(70, good).map((d, i) => (i % 2 ? Object.assign({}, d, { wouldFill: false }) : d));
  assert.strictEqual(sh.shadowRolling(R, half).status, 'collecting');
};
gates.RR3 = () => {
  // checkpoints: 64 and 69 signals are evaluated at the 60th, so more rows inside the same step change nothing
  const base = mk(70, good);
  const at60 = sh.shadowRolling(R, base.slice(0, 60)), at69 = sh.shadowRolling(R, base.slice(0, 69));
  assert.strictEqual(at69.checkpoint, 60); assert.deepStrictEqual(at60, Object.assign({}, at69, { fillable: 60 }));
  assert.strictEqual(sh.shadowRolling(R, base).checkpoint, 70);
  const w = sh.shadowRolling(R, base);
  assert.strictEqual(w.label, 'proposed, not a rule'); assert.strictEqual(w.flag, 'in');
  assert.ok(w.pf >= 1.3 && w.rarerOutcomeCount === 6 && w.daysSpanned > 0 && w.topDayShareOfNet > 0 && w.topDayShareOfNet <= 1);
};
gates.RR4 = () => {
  // a bad stretch flips it out; a middling one afterwards keeps it out (hysteresis), it does not flip back by itself
  const bad = mk(60, (i) => (i % 3 === 2 ? -0.9 : 0.12));
  assert.strictEqual(sh.shadowRolling(R, bad).flag, 'out');
  const mid = mk(60, (i) => (i % 4 === 3 ? -0.5 : 0.2));          // PF 1.2: between the lines
  assert.strictEqual(sh.shadowRolling(R, mid).flag, 'undecided');
  const strong = mk(60, (i) => (i % 10 === 9 ? -0.5 : 0.12)).concat(mk(10, (i) => (i % 4 === 3 ? -0.5 : 0.2)).map((d, i) => Object.assign({}, d, { atMs: d.atMs + 200 * DAY + i })));
  assert.strictEqual(sh.shadowRolling(R, strong).flag, 'in', 'between the lines keeps the last state');
};
gates.RR5 = () => {
  const rows = mk(70, good).concat([{ rule: 'OTHER', atMs: 1, settled: true, wouldFill: true, pnl: -9 }]);
  const ex = sh.shadowReport([R], rows, NOW)[0];
  assert.ok(!('rolling' in ex), 'shadowReport fields are unchanged');
  assert.strictEqual(sh.shadowRolling(R, rows).fillable, 70, "another rule's rows do not count");
};
gates.RR6 = () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiShadowLib.js'), 'utf8');
  const body = src.slice(src.indexOf('function shadowRolling'), src.indexOf('// The gold RETURN rule'));
  assert.ok(!/fetch|request|update\(|\.set\(|\.create\(|Date\.now|Math\.random/.test(body), 'pure replay: no request, no write, no clock');
  const rl = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiReportLib.js'), 'utf8');
  assert.ok(/shadowRolling/.test(rl));
};
let failed = 0;
for (const [k, f] of Object.entries(gates)) { try { f(); console.log('ok ' + k); } catch (e) { failed++; console.log('FAIL ' + k + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
