import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import crypto1 as M
# MOM signal at hour i uses only bars up to i: a jump in a LATER bar must not change an earlier signal
n = 400
c = 100 + np.cumsum(np.ones(n) * 0.1); o = c.copy(); h = c + 0.2; l = c - 0.2
rv = np.full(n, np.nan)
s1 = M.signals("MOM", 24, o, h, l, c, rv, rv)
c2 = c.copy(); c2[300:] *= 0.5
s2 = M.signals("MOM", 24, o, c2 + 0.2, c2 - 0.2, c2, rv, rv)
assert (s1[:300] == s2[:300]).all()
assert (s1[24:] == 1).all()                      # a steady rise is always long
# BRK: a close above the previous L-bar high goes long, below the low goes short
c3 = np.r_[np.full(30, 100.0), 105.0, np.full(10, 100.0)]; h3 = c3 + 0.1; l3 = c3 - 0.1
sb = M.signals("BRK", 24, c3, h3, l3, c3, rv[:len(c3)], rv[:len(c3)])
assert sb[30] == 1
# trades: enter at the open of the next hour, exit H hours later, costs and funding subtracted, spot ignores shorts
ts = np.arange(100) * 3600
o4 = np.arange(100, 200, dtype=float)
sig = np.zeros(100, dtype=int); sig[5] = 1
tr = M.run_strategy(sig, ts, o4, {}, 4, "perp", 0.0, 0.001)
assert len(tr) == 1 and abs(tr[0][1] - ((o4[10] / o4[6] - 1.0) - 0.001)) < 1e-12 and tr[0][0] == int(ts[10])
sig2 = np.zeros(100, dtype=int); sig2[5] = -1
assert M.run_strategy(sig2, ts, o4, {}, 4, "spot", 0.0, 0.006) == []
shortperp = M.run_strategy(sig2, ts, o4, {}, 4, "perp", 0.0, 0.001)
assert abs(shortperp[0][1] - (-(o4[10] / o4[6] - 1.0) - 0.001)) < 1e-12
fund = {int(ts[j]): 0.0001 for j in range(6, 10)}
lf = M.run_strategy(sig, ts, o4, fund, 4, "perp", 0.0, 0.0)
assert abs(lf[0][1] - ((o4[10] / o4[6] - 1.0) - 0.0004)) < 1e-12      # a long pays positive funding
print("crypto1 tests ok")
