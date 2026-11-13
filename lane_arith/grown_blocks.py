# Arithmetic only, no market data. [design]
# How often a rule clears its FIRST block (and the 30 signal confirmation) under ROTATION_LANE.md section 4
# items (a) to (o): blocks grow until 60 signals, 7 different days and 10 of the rarer outcome all hold;
# a block not complete within 21 days expires unread; whole cents; halves; the 30 percent day rule.
# "No edge" = wins exactly as often as its price says, so it loses one fee an order.
import numpy as np, math, sys
rng = np.random.default_rng(20261113)
C = 10
def fee_c(pc): return math.ceil(0.07 * C * (pc / 100) * (1 - pc / 100) * 100 - 1e-9)      # cents, pc = price in whole cents
def q_for(pc, t):                                                                        # win rate giving cash PF t
    f = fee_c(pc); a = C * (100 - pc) - f; b = C * pc + f; return t * b / (a + t * b)
def trial(prices, rate, edge):
    # one rule: signals at Poisson rate per day for 60 days; returns outcome code
    n = rng.poisson(rate * 60)
    if n < 90: return "expired", 0
    t = np.sort(rng.random(n) * 60.0)
    pc = rng.choice(prices, n)
    f = np.array([fee_c(x) for x in pc])
    q = np.array([q_for(x, edge) for x in pc]) if edge else pc / 100.0
    win = rng.random(n) < q
    cash = np.where(win, C * (100 - pc) - f, -(C * pc + f)).astype(np.int64)
    need_w = prices.min() <= 50; need_l = prices.max() > 50
    day = np.floor(t).astype(int)
    cw = np.cumsum(win); cl = np.cumsum(~win)
    # distinct days so far
    newday = np.r_[True, day[1:] != day[:-1]]; cd = np.cumsum(newday)
    idx = np.arange(1, n + 1)
    ok = (idx >= 60) & (cd >= 7)
    if need_w: ok &= cw >= 10
    if need_l: ok &= cl >= 10
    if not ok.any(): return "expired", 0
    e = int(np.argmax(ok))                       # block is signals 0..e
    if t[e] - t[0] > 21: return "expired", e + 1
    b = cash[: e + 1]; m = (e + 1) // 2
    def passes(x, num, den):
        W = int(x[x > 0].sum()); L = int(-x[x < 0].sum()); return W > 0 and den * W >= num * L
    if not (passes(b, 13, 10) and passes(b[:m], 1, 1) and passes(b[m:], 1, 1)): return "failed", e + 1
    net = int(b.sum()); d = day[: e + 1]
    for dd in np.unique(d):
        if 100 * int(b[d == dd].sum()) > 30 * net: return "failed", e + 1
    c = cash[e + 1 : e + 31]
    if len(c) < 30 or t[e + 30] - t[e] > 21: return "cleared_conf_expired", e + 1
    return ("qualified" if passes(c, 1, 1) else "cleared_conf_failed"), e + 1
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
cells = [("20c", np.array([20])), ("50c", np.array([50])), ("85c", np.array([85])), ("mixed 11c to 87c", np.arange(11, 88))]
for edge, name in ((0, "no edge"), (1.3, "true 1.3")):
    for rate in (4, 9, 15):
        for lab, prices in cells:
            out = {}; sizes = []
            for _ in range(N):
                o, s = trial(prices, rate, edge); out[o] = out.get(o, 0) + 1
                if o != "expired": sizes.append(s)
            cl = sum(v for k, v in out.items() if k.startswith("cleared") or k == "qualified")
            print(f"{name:8s} | {rate:2d} a day | {lab:16s} | clears first block {100*cl/N:5.1f}% | qualified {100*out.get('qualified',0)/N:5.1f}% | expired {100*out.get('expired',0)/N:5.1f}% | median block {int(np.median(sizes)) if sizes else 0}")
