"""FUT1 scorer (workers/FUT1_PROTOCOL.md). Development only: the last third of each market's dates is never loaded here.

Data: EIA daily futures settlements (data/fut/RCLC1..4.xls, RNGC1..4.xls). Research only, no orders.
Usage: python3 -I src/scalper/fut1.py score        (dev windows W1/W2, prints the table and verdicts)
       python3 -I src/scalper/fut1.py selftest     (synthetic checks)
"""
import math, os, random, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "fut")
MARKETS = {  # multiplier (units per contract), tick value in dollars
    "CL": dict(prefix="RCLC", mult=1000.0, tick=10.0),
    "NG": dict(prefix="RNGC", mult=10000.0, tick=10.0),
}
FEE = 2.50          # dollars per contract per side (commission + exchange)
SLIP_TICKS = 1.0    # ticks per side
DEADBAND = 0.002    # carry deadband and roll spread floor, fraction of price
LOOKBACKS = [20, 60, 120, 250]
COMBO_L = [60, 120, 250]
BOOT = 2000
SEED = 90901


def load(m):
    dfs = []
    for k in range(1, 5):
        x = pd.read_excel(os.path.join(DATA, "%s%d.xls" % (MARKETS[m]["prefix"], k)), sheet_name=1, skiprows=2)
        x.columns = ["date", "c%d" % k]
        dfs.append(x.dropna().set_index("date"))
    d = pd.concat(dfs, axis=1, join="inner").dropna()
    d = d[(d > 0).all(axis=1)]
    return d.sort_index()


ROLL_WINDOW = {"CL": (17, 27, 0), "NG": (24, 31, 5)}  # (first day, last day, shift days); at most ONE roll per month


def roll_returns(d, m="CL"):
    """Per-unit roll-adjusted daily price change and a roll-day flag (Amendment 2: one roll per calendar
    month, inside the market's expiry window; the first version flagged 28% of days and was wrong)."""
    c1, c2 = d["c1"].values, d["c2"].values
    n = len(d)
    ret = np.zeros(n)
    roll = np.zeros(n, dtype=bool)
    lo, hi, shift = ROLL_WINDOW[m]
    best = {}
    for t in range(1, n):
        same = abs(c1[t] - c1[t - 1])
        sw = abs(c1[t] - c2[t - 1])
        wide = abs(c2[t - 1] - c1[t - 1]) > DEADBAND * c1[t - 1]
        ts = d.index[t] + pd.Timedelta(days=shift)
        day = ts.day if shift == 0 else d.index[t].day
        in_win = (lo <= d.index[t].day <= hi) if shift == 0 else (d.index[t].day >= lo or d.index[t].day <= 4)
        gain = same - sw
        if wide and in_win and gain > 0:
            key = (ts.year, ts.month)
            if key not in best or gain > best[key][0]:
                best[key] = (gain, t)
    for _, t in best.values():
        roll[t] = True
    for t in range(1, n):
        ret[t] = (c1[t] - c2[t - 1]) if roll[t] else (c1[t] - c1[t - 1])
    return ret, roll


def signals(d, ret, name):
    """Position decided at day t from data up to t (it earns day t+1)."""
    n = len(d)
    cs = np.cumsum(ret)
    kind = name.split(":")[0]
    long_only = name.endswith(":LO")
    base = name.replace(":LO", "")
    parts = base.split(":")
    pos = np.zeros(n)

    def tsm(L):
        s = np.zeros(n)
        for t in range(L, n):
            v = cs[t] - cs[t - L]
            s[t] = 1.0 if v > 0 else (-1.0 if v < 0 else 0.0)
        return s

    def carry():
        s = np.zeros(n)
        spr = (d["c1"].values - d["c2"].values) / d["c1"].values
        s[spr > DEADBAND] = 1.0
        s[spr < -DEADBAND] = -1.0
        return s

    if parts[0] == "TSMOM":
        pos = tsm(int(parts[1]))
    elif parts[0] == "CARRY":
        pos = carry()
    elif parts[0] == "TC":
        a, b = tsm(int(parts[1])), carry()
        pos = np.where(a == b, a, 0.0)
    if long_only:
        pos = np.where(pos > 0, 1.0, 0.0)
    return pos


def variants():
    v = ["TSMOM:%d" % L for L in LOOKBACKS] + ["CARRY"] + ["TC:%d" % L for L in COMBO_L]
    return v + [x + ":LO" for x in v if x.startswith(("TSMOM", "CARRY"))] + ["TC:%d:LO" % COMBO_L[0]]


def pnl(d, ret, roll, pos, m, cost_mult=1.0):
    mult, tick = MARKETS[m]["mult"], MARKETS[m]["tick"]
    side = (FEE + SLIP_TICKS * tick) * cost_mult
    n = len(d)
    out = np.zeros(n)
    for t in range(1, n):
        p_prev = pos[t - 1]            # decided at t-1, earns day t
        p_prev2 = pos[t - 2] if t >= 2 else 0.0
        gross = p_prev * ret[t] * mult
        sides = abs(p_prev - p_prev2) + (1.0 if (roll[t] and p_prev != 0) else 0.0)
        out[t] = gross - sides * side
    return out


def stats(x):
    n = len(x)
    if n < 2:
        return dict(n=n, mean=0.0, sharpe=0.0, pf=0.0)
    sd = x.std(ddof=1)
    w, l = x[x > 0].sum(), -x[x < 0].sum()
    return dict(n=n, mean=x.mean(), sharpe=(x.mean() / sd * math.sqrt(252)) if sd > 0 else 0.0,
                pf=(w / l) if l > 0 else (99.0 if w > 0 else 0.0))


def month_boot_p(x, months, rng):
    """One-sided p that the mean is above 0: centre, resample whole months."""
    obs = x.mean()
    cen = x - obs
    groups = {}
    for v, mo in zip(cen, months):
        groups.setdefault(mo, []).append(v)
    keys = list(groups)
    arrs = [np.array(groups[k]) for k in keys]
    cnt = 0
    for _ in range(BOOT):
        pick = [arrs[rng.randrange(len(arrs))] for _ in range(len(arrs))]
        tot = np.concatenate(pick)
        if tot.mean() >= obs:
            cnt += 1
    return (cnt + 1) / (BOOT + 1)


def score():
    names = variants()
    N = 2 * (len(MARKETS) * len(names) + len(MARKETS))  # Amendment 2: the invalid first run counts too
    bar_p = 0.05 / N
    print("N (futures ledger) = %d, p bar %.5f" % (N, bar_p))
    rng = random.Random(SEED)
    allpnl = {}
    for m in MARKETS:
        d = load(m)
        ret, roll = roll_returns(d, m)
        n = len(d)
        dev_end = (2 * n) // 3        # last third is never touched here
        half = dev_end // 2
        print("\n%s: %d days %s to %s; dev %s to %s (holdout unread); rolls %d" % (
            m, n, d.index[0].date(), d.index[-1].date(), d.index[0].date(), d.index[dev_end - 1].date(), roll[:dev_end].sum()))
        print("%-12s %7s %7s %6s | %7s %7s %6s | %7s %7s %6s | %8s" % (
            "variant", "W1mean", "W1shp", "W1pf", "W2mean", "W2shp", "W2pf", "x2shp", "p", "", "verdict"))
        mon = np.array(["%d-%02d" % (a.year, a.month) for a in d.index[:dev_end]])
        for name in names:
            pos = signals(d, ret, name)
            x = pnl(d, ret, roll, pos, m)[:dev_end]
            x2 = pnl(d, ret, roll, pos, m, 2.0)[:dev_end]
            w1, w2 = stats(x[:half]), stats(x[half:])
            s2 = stats(x2)
            p = month_boot_p(x[1:], mon[1:], rng)
            ok = (w1["n"] >= 1000 and w2["n"] >= 1000 and w1["sharpe"] >= 0.5 and w2["sharpe"] >= 0.5
                  and w1["pf"] >= 1.5 and w2["pf"] >= 1.5 and p < bar_p)
            v = "SURVIVOR?" if ok else "falsified"
            allpnl[(m, name)] = (w1, w2, p, ok)
            print("%-12s %7.0f %7.2f %6.2f | %7.0f %7.2f %6.2f | %7.2f %7.4f %6s | %s" % (
                name, w1["mean"], w1["sharpe"], w1["pf"], w2["mean"], w2["sharpe"], w2["pf"], s2["sharpe"], p, "", v))
    surv = [k for k, v in allpnl.items() if v[3]]
    print("\nSURVIVORS (dev, all conditions):", surv if surv else "none")
    if surv:
        print("Survivors must still beat their long-only control and be read once on the holdout.")
    return allpnl


def selftest():
    # 1) roll detection: build two contracts; C1 expires and the old C2 becomes C1.
    n = 60
    base = np.linspace(50, 50, n)
    c1 = np.full(n, 50.0)
    c2 = np.full(n, 52.0)
    c1[30:] = 52.0  # after expiry the old C2 (52) is today's C1
    c2[30:] = 54.0
    d = pd.DataFrame({"c1": c1, "c2": c2, "c3": c2, "c4": c2}, index=pd.date_range("2020-01-18", periods=n))
    ret, roll = roll_returns(d, 'CL')
    assert roll[30] and roll.sum() == 1, (roll.sum(), np.where(roll))
    assert abs(ret[30]) < 1e-9, ret[30]          # no fake +2 jump
    # 2) costs: flat position costs nothing; a flip costs two sides.
    pos = np.zeros(n)
    pos[10:] = 1.0
    x = pnl(d, ret, roll, pos, "CL")
    side = FEE + SLIP_TICKS * 10
    assert abs(x[11] + side) < 1e-6, x[11]       # entry cost on the first day earned
    # 3) no lookahead: a signal built only from the past gives the same position if the future is changed.
    rng = np.random.default_rng(1)
    c = 50 + np.cumsum(rng.normal(0, 1, 400))
    d1 = pd.DataFrame({"c1": c, "c2": c + 0.5, "c3": c + 1, "c4": c + 1.5}, index=pd.date_range("2020-01-01", periods=400))
    r1, _ = roll_returns(d1, 'CL')
    p1 = signals(d1, r1, "TSMOM:60")
    d2 = d1.copy()
    d2.iloc[300:] *= 1.5
    r2, _ = roll_returns(d2, 'CL')
    p2 = signals(d2, r2, "TSMOM:60")
    assert np.array_equal(p1[:299], p2[:299])
    # 4) stats sanity
    s = stats(np.array([2.0, -1.0, 2.0, -1.0]))
    assert abs(s["pf"] - 2.0) < 1e-9
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    else:
        score()
