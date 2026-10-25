import math, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import search5k as S

# rules: exactly 5,000, all distinct, pairs only across different features, fixed seed reproduces
conds, _ = S.make_conditions([{"series": s, **{f: float(i) for f in S.NUMERIC}, **{f: 0 for f in S.CATEGORICAL}} for s in ("BTC", "ETH") for i in range(8)], [{"series": s, **{f: float(i) for f in S.NUMERIC}, **{f: 0 for f in S.CATEGORICAL}} for s in ("BTC", "ETH") for i in range(8)])
rules = S.make_rules(conds)
assert len(rules) == S.N_RULES == len(set(rules)), (len(rules), len(set(rules)))
assert all(len(r) == 1 or conds[r[0]][1] != conds[r[1]][1] for r in rules)
assert rules == S.make_rules(conds)

# screen: a planted effect is found; pure noise stays inside the shuffled-maximum distribution
rng = np.random.default_rng(1)
N, R = 3000, 400
M = (rng.random((R, N)) < 0.3).astype(np.float32)
x = rng.normal(0, 0.2, N)
d, z = S.screen(M, x, 100)
groups = [np.arange(i, min(N, i + 50)) for i in range(0, N, 50)]
mx = S.null_max(M, x, groups, 60, 100, 5)
crit = np.percentile(mx, 95)
assert (np.nanmax(z) <= crit * 1.25), "noise should not sit far above its own null"
x2 = x + 0.1 * M[7]                       # rule 7's group earns 0.1 more
d2, z2 = S.screen(M, x2, 100)
assert np.nanargmax(z2) == 7 and z2[7] > crit * 1.5
# a group that is too small or covers everything is not scored
M3 = np.zeros((2, N), dtype=np.float32); M3[0, :50] = 1; M3[1] = 1
d3, z3 = S.screen(M3, x, 100)
assert np.isnan(z3).all()

# no lookahead: perp features at decision t may read only the bar stamped t - 60 and earlier
class FakeCon:
    def execute(self, sql, args):
        class R:
            def __init__(s, rows): s.rows = rows
            def fetchall(s): return s.rows
        cur = args[0]
        T0 = 1_700_000_000_000
        n = 2000
        if "from bar" in sql: return R([(T0 + 60_000 * i, 100.0, 100.5, 99.5, 100.0 + 0.01 * (i % 3) + (0.0 if i < 1651 else 1000.0), 5.0) for i in range(n)])
        if "from dv" in sql: return R([(T0 + 60_000 * i, 50.0) for i in range(n)])
        return R([(T0 + 3_600_000 * i, 1e-6) for i in range(60)])
P = S.Perp(FakeCon(), "BTC"); Q = S.Perp(FakeCon(), "ETH")
t = (P.t0 + 1650) * 60 + 60           # the bar stamped t - 60 is index 1650: price 100; later bars (index >= 1700) are 1100
f = S.perp_features(P, Q, t, t - 900, 1)
assert f is not None and abs(f["ret1"]) < 0.01 and abs(f["ret60"]) < 0.01, f   # a one-bar lookahead would read the 1000 jump
print("search5k tests ok")
