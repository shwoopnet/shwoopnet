import sys, numpy as np, pandas as pd
R = pd.read_pickle(sys.argv[1]); rng = np.random.default_rng(20261112)
R["r60"] = R["e"] - R["m60"]
R["paid"] = np.where(R["s"] > 0, R["yes_price_dollars"], 1 - R["yes_price_dollars"])
def boot(g, col="r60"):
    g = g.dropna(subset=[col]); u, inv = np.unique(g["tk"].to_numpy(), return_inverse=True)
    num = np.bincount(inv, g[col].to_numpy(float)); den = np.bincount(inv); bs = []
    for _ in range(300):
        i = rng.integers(0, len(u), len(u)); bs.append(num[i].sum() / den[i].sum())
    return "%+.2f (%+.2f,%+.2f) n=%d w=%d" % (100 * num.sum() / den.sum(), 100 * np.percentile(bs, 2.5), 100 * np.percentile(bs, 97.5), len(g), len(u))
print("trades", len(R), "windows", R["tk"].nunique())
for s, g in R.groupby("series"):
    print(s, "| all", boot(g), "| e %.2f m60 %.2f" % (100 * g["e"].mean(), 100 * g["m60"].mean()), "| whole", boot(g[~g["frac"]]), "| frac", boot(g[g["frac"]]),
          "| diff %+.2f" % (100 * (g.loc[g["frac"], "r60"].mean() - g.loc[~g["frac"], "r60"].mean())),
          "| paid .70-.90", boot(g[(g["paid"] >= .7) & (g["paid"] < .9)]), "| paid .10-.30", boot(g[(g["paid"] >= .1) & (g["paid"] < .3)]), "| paid .30-.70", boot(g[(g["paid"] >= .3) & (g["paid"] < .7)]))
