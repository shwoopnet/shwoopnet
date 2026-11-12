"""Cuts of the realized-spread table by the price the taker paid and by order class. usage: python3 -I mm_cuts.py R.pkl"""
import sys, numpy as np, pandas as pd
R = pd.read_pickle(sys.argv[1]); rng = np.random.default_rng(20261112)
R["r60"] = R["e"] - R["m60"]; R["r180"] = R["e"] - R["m180"]
R["paid"] = np.where(R["s"] > 0, R["yes_price_dollars"], 1 - R["yes_price_dollars"])
def boot(g, col, w=None):
    g = g.dropna(subset=[col])
    if len(g) < 500: return None
    u, inv = np.unique(g["tk"].to_numpy(), return_inverse=True)
    ww = g[w].to_numpy(float) if w else np.ones(len(g))
    num = np.bincount(inv, g[col].to_numpy(float) * ww); den = np.bincount(inv, ww); bs = []
    for _ in range(300):
        i = rng.integers(0, len(u), len(u)); bs.append(num[i].sum() / den[i].sum())
    return "%+.2f (%+.2f,%+.2f) n=%d w=%d" % (100 * num.sum() / den.sum(), 100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5), len(g), len(u))
B = [(0, .10), (.10, .30), (.30, .70), (.70, .90), (.90, 1.01)]
for s, g in R.groupby("series"):
    print("==", s)
    for lo, hi in B:
        h = g[(g["paid"] >= lo) & (g["paid"] < hi)]
        print("  paid %.2f-%.2f frac share ct %.2f | r60 all %s | frac %s | whole %s | r180 all %s | r60 per contract %s" % (lo, hi, h.loc[h["frac"], "count_fp"].sum() / max(h["count_fp"].sum(), 1), boot(h, "r60"), boot(h[h["frac"]], "r60"), boot(h[~h["frac"]], "r60"), boot(h, "r180"), boot(h, "r60", "count_fp")))
    for name, h in (("small<=10", g[g["count_fp"] <= 10]), ("10-100", g[(g["count_fp"] > 10) & (g["count_fp"] <= 100)]), (">100", g[g["count_fp"] > 100])):
        print("  size", name, "r60", boot(h, "r60"))
