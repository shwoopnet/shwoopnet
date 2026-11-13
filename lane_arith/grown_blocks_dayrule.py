# Arithmetic only, no market data. [design]
# The same first-block count as grown_blocks.py, split by how the "no single day more than 30 percent of the block's net"
# line is read, to show how much of the result that one line decides. Variants:
#   none     : the day rule left out (how the table in ROTATION_LANE.md section 4 was worked on Nov 12)
#   net30    : as written and as ruled in (h): 100 x day net > 30 x block net fails
#   net50    : the same at 50 percent (shown for scale only; not a proposal)
#   wins30   : a day's gross wins more than 30 percent of the block's gross wins fails (shown for scale only)
import numpy as np, math, sys
rng = np.random.default_rng(20261113)
C = 10
def fee_c(pc): return math.ceil(0.07 * C * (pc / 100) * (1 - pc / 100) * 100 - 1e-9)
def q_for(pc, t):
    f = fee_c(pc); a = C * (100 - pc) - f; b = C * pc + f; return t * b / (a + t * b)
def passes(x, num, den):
    W = int(x[x > 0].sum()); L = int(-x[x < 0].sum()); return W > 0 and den * W >= num * L
def trial(prices, rate, edge):
    n = rng.poisson(rate * 60)
    if n < 90: return None
    t = np.sort(rng.random(n) * 60.0); pc = rng.choice(prices, n)
    f = np.array([fee_c(x) for x in pc]); q = np.array([q_for(x, edge) for x in pc]) if edge else pc / 100.0
    win = rng.random(n) < q
    cash = np.where(win, C * (100 - pc) - f, -(C * pc + f)).astype(np.int64)
    day = np.floor(t).astype(int); cw = np.cumsum(win); cl = np.cumsum(~win)
    cd = np.cumsum(np.r_[True, day[1:] != day[:-1]]); idx = np.arange(1, n + 1)
    ok = (idx >= 60) & (cd >= 7)
    if prices.min() <= 50: ok &= cw >= 10
    if prices.max() > 50: ok &= cl >= 10
    if not ok.any(): return None
    e = int(np.argmax(ok))
    if t[e] - t[0] > 21: return None
    b = cash[: e + 1]; m = (e + 1) // 2
    if not (passes(b, 13, 10) and passes(b[:m], 1, 1) and passes(b[m:], 1, 1)): return {}
    net = int(b.sum()); d = day[: e + 1]; gw = int(b[b > 0].sum())
    dn = [int(b[d == dd].sum()) for dd in np.unique(d)]; dw = [int(b[(d == dd) & (b > 0)].sum()) for dd in np.unique(d)]
    c = cash[e + 1 : e + 31]; conf = len(c) == 30 and t[e + 30] - t[e] <= 21 and passes(c, 1, 1)
    r = {"none": True, "net30": all(100 * x <= 30 * net for x in dn), "net50": all(100 * x <= 50 * net for x in dn), "wins30": all(100 * x <= 30 * gw for x in dw)}
    return {k: (v, v and conf) for k, v in r.items()}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
for edge, name in ((0, "no edge"), (1.3, "true 1.3")):
    for rate in (4, 9, 15):
        for lab, prices in (("50c", np.array([50])), ("mixed 11c to 87c", np.arange(11, 88))):
            cnt = {k: [0, 0] for k in ("none", "net30", "net50", "wins30")}
            for _ in range(N):
                r = trial(prices, rate, edge)
                if not r: continue
                for k, (a, b) in r.items(): cnt[k][0] += a; cnt[k][1] += b
            print(f"{name:8s} | {rate:2d} a day | {lab:16s} | " + " | ".join(f"{k}: clears {100*v[0]/N:4.1f}% qualified {100*v[1]/N:4.1f}%" for k, v in cnt.items()))
