'use strict';
// SM1 to SM5: a shadow trade with an M60 exit and no sellable mark is scored at settlement and counted, never dropped (Nov 17, 2026, the Head of R&D and Desk A: dropping it hides total losses and overstates every forward profit factor).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const root = path.join(__dirname, '..');
const prog = `
import sys, json
sys.path.insert(0, ${JSON.stringify(path.join(root, 'scripts'))})
sys.path.insert(0, ${JSON.stringify(path.join(root, 'kalshi-scalper', 'workers', 'desk_a_verify'))})
import shadow_runner as R
import engine1_core as K
C = 100000
def entry(path_, result="no", entry_end=C - 400, side="yes"):
    return {"id": "e", "close_ts": C, "day": "2026-11-17", "series": "KXAAA15M", "side": side, "ask": 0.90, "n": 10, "entry_end": entry_end, "result": result, "path": path_}
out = {}
# 1: no candle ends at close-60: the core says None "no mark"; the runner scores it held to settlement (a loss when the side loses), flag 1
e1 = entry([[C - 300, 0.88, 0.90], [C - 120, 0.40, 0.42]])
out["core1"] = K.score(e1, "M60", 0.01, 10)[1]
x1, x2, h = R.score_both(K, e1, "M60")
out["s1"] = [x1, x2, h, K.score(e1, "H", 0.01, 10)[0], K.score(e1, "H", 0.02, 10)[0]]
# 2: a two-sided mark at close-60 exists: the core's own M60 score, flag 0
e2 = entry([[C - 60, 0.60, 0.62]])
y1, y2, hh = R.score_both(K, e2, "M60")
out["s2"] = [y1, y2, hh, K.score(e2, "M60", 0.01, 10)[0]]
# 3: a collapsed side (bid 0 at the mark: not sellable): held, a total loss, never skipped
e3 = entry([[C - 60, 0.0, 0.03]])
z1, z2, hz = R.score_both(K, e3, "M60")
out["s3"] = [z1, z2, hz, K.score(e3, "M60", 0.01, 10)[1]]
# 4: the entry candle is after the mark: "too late" is held too
e4 = entry([[C - 30, 0.80, 0.82]], entry_end=C - 45)
w1, w2, hw = R.score_both(K, e4, "M60")
out["s4"] = [w1 is not None, hw, K.score(e4, "M60", 0.01, 10)[1]]
# 5: exits other than the time marks are untouched (held flag 0), and a winning held trade pays out
e5 = entry([[C - 300, 0.88, 0.90]], result="yes")
q1, q2, hq = R.score_both(K, e5, "H")
out["s5"] = [q1, hq]
e6 = entry([[C - 60, 0.97, 0.98]], result="yes")
r1, r2, hr = R.score_both(K, e6, "M60")
out["s5b"] = [r1 == K.score(e6, "M60", 0.01, 10)[0] and r1 is not None, hr]
# aggregate counts them
mods = {"engine1_core": K}
seq = [[x1, x2, 0, 1], [y1, y2, 0, 0], [-1.0, -1.0, 0]]
a = R.aggregate(mods, seq, 2, 0, 86400)
out["agg"] = [a["n"], a["scored_at_settlement"]]
print(json.dumps(out))
`;
const r = spawnSync('python3', ['-I', '-c', prog], { encoding: 'utf8' });
assert.strictEqual(r.status, 0, 'python failed: ' + r.stderr);
const o = JSON.parse(r.stdout.trim().split('\n').pop());

// SM1
assert.strictEqual(o.core1, 'no mark', 'SM1 the core itself drops this trade (None, no mark)');
assert.ok(o.s1[0] !== null && o.s1[1] !== null && o.s1[2] === 1, 'SM1 the runner scores it and flags it');
assert.strictEqual(o.s1[0], o.s1[3], 'SM1 at 1c it equals the core hold-to-settlement result');
assert.strictEqual(o.s1[1], o.s1[4], 'SM1 at 2c it equals the core hold-to-settlement result');
assert.ok(o.s1[0] < 0, 'SM1 a losing side loses its whole cost (the total loss that used to drop out)');
console.log('ok   SM1 no mark: held to settlement, counted, flagged');
// SM2
assert.strictEqual(o.s2[2], 0, 'SM2 a trade with a two-sided mark is not flagged');
assert.strictEqual(o.s2[0], o.s2[3], 'SM2 and keeps the core M60 score');
console.log('ok   SM2 a sellable mark keeps the core score');
// SM3
assert.strictEqual(o.s3[3], 'no mark');
assert.strictEqual(o.s3[2], 1, 'SM3 a collapsed side (bid 0) is held, not dropped');
assert.ok(o.s3[0] < 0, 'SM3 it counts as the loss it is');
console.log('ok   SM3 collapsed side counted as a loss');
// SM4
assert.deepStrictEqual(o.s4, [true, 1, 'too late'], 'SM4 an entry after the mark is held too');
console.log('ok   SM4 too late is held');
// SM5
assert.strictEqual(o.s5[1], 0, 'SM5 other exits are not flagged');
assert.deepStrictEqual(o.s5b, [true, 0], 'SM5 a normal M60 trade with a sellable mark is scored by the core, not flagged');
assert.deepStrictEqual(o.agg, [3, 1], 'SM5 the aggregate counts the held trades');
const v1 = fs.readFileSync(path.join(root, 'scripts', 'shadow_runner.py'), 'utf8');
const v4 = fs.readFileSync(path.join(root, 'scripts', 'shadow_runner_v4.py'), 'utf8');
assert.ok(/score_both\(K, core, spec\["exit"\]\)/.test(v1) && /R\.score_both\(K, core, spec\["exit"\]\)/.test(v4), 'SM5 both runners (V1, and V2 to V4) use it');
assert.ok(!/K\.score\(core, spec\["exit"\], 0\.01/.test(v1.replace(/def score_both[\s\S]*?return x1, x2, 0/, '')) && !/K\.score\(core, spec\["exit"\]/.test(v4), 'SM5 no runner calls the core directly any more');
assert.ok(/"scored_at_settlement": a\["scored_at_settlement"\]/.test(v1) && /"scored_at_settlement": a\["scored_at_settlement"\]/.test(v4), 'SM5 the counts file carries scored_at_settlement');
console.log('ok   SM5 both runners, counts file');
