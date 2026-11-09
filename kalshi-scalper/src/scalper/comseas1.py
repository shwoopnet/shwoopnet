"""COMSEAS1: calendar-month seasonality in crude oil and natural gas futures (workers/COMSEAS1_PROTOCOL.md). Development years only until the shortlist is frozen.
Uses the EIA contract series and the roll-adjusted daily returns of fut1.py. `python3 -I src/scalper/comseas1.py score`"""
import math, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fut1
from statistics import NormalDist
N_PRIOR = 170 + 48      # futures ledger (170) plus 48 cells (long and short)


def tcrit(df, alpha):
    # two-sided Student t critical value via normal approximation with the Cornish-Fisher correction (df >= 15)
    z = NormalDist().inv_cdf(1 - alpha / 2.0)
    return z + (z ** 3 + z) / (4.0 * df)


def monthly(m):
    d = fut1.load(m)
    ret, roll = fut1.roll_returns(d, m)
    spec = fut1.MARKETS[m]
    side = fut1.cost_side(spec)
    s = pd.Series(ret * spec["mult"], index=d.index)
    rl = pd.Series(roll, index=d.index)
    g = s.groupby([d.index.year, d.index.month]).sum()
    # one round trip per month (two sides) plus one extra side if the month contains a roll
    nroll = rl.groupby([d.index.year, d.index.month]).sum().clip(upper=1)
    net_long = g - 2 * side - nroll * side
    net_short = -g - 2 * side - nroll * side
    return net_long, net_short


def score():
    N = N_PRIOR
    alpha = 0.05 / N
    print("N = %d, per-cell two-sided alpha %.5f" % (N, alpha))
    short = []
    for m in ("CL", "NG"):
        nl, ns = monthly(m)
        years = sorted({y for y, _ in nl.index})
        cut = years[(2 * len(years)) // 3]
        dev = [y for y in years if y < cut]
        print("\n%s: years %d to %d, development %d to %d (%d years), holdout %d to %d UNREAD" % (m, years[0], years[-1], dev[0], dev[-1], len(dev), cut, years[-1]))
        print("%-5s %-5s %8s %8s %6s %s" % ("month", "side", "mean$", "t", "n", "verdict"))
        for mo in range(1, 13):
            for nm, ser in (("long", nl), ("short", ns)):
                v = np.array([ser.get((y, mo)) for y in dev if (y, mo) in ser.index], dtype=float)
                if len(v) < 10:
                    continue
                mean, sd = v.mean(), v.std(ddof=1)
                t = mean / (sd / math.sqrt(len(v))) if sd > 0 else 0.0
                ok = mean > 0 and t >= tcrit(len(v) - 1, alpha * 2)    # one-sided on the chosen direction, both directions counted in N
                if ok:
                    short.append((m, mo, nm, mean, t, len(v)))
                if t >= 1.5:
                    print("%-5d %-5s %8.0f %8.2f %6d %s" % (mo, nm, mean, t, len(v), "SHORTLIST" if ok else "below bar"))
    print("\nSHORTLIST:", short if short else "none")


if __name__ == "__main__":
    score()
