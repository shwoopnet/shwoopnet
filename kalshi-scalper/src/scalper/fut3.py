"""FUT3 scorer (workers/FUT3_PROTOCOL.md and Amendment 1): diversified futures trend, carry and cross-sectional momentum, development only.
Data: Databento GLBX.MDP3 ohlcv-1d, volume-roll continuous .v.0 (front) and .v.1 (second), unadjusted, data/fut/db3 (git-ignored).
The last third of dates is cut BEFORE any signal is computed. Research only.
Usage: python3 -I src/scalper/fut3.py selftest | score
"""
import glob, math, os, random, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB3 = os.path.join(HERE, "..", "..", "data", "fut", "db3")
SPEC = {  # point value (dollars per 1.0 of price), tick value in dollars
    "ES": (50, 12.5), "NQ": (20, 5), "RTY": (50, 5), "YM": (5, 5), "GC": (100, 10), "SI": (5000, 25), "HG": (25000, 12.5), "PL": (50, 5),
    "CL": (1000, 10), "NG": (10000, 10), "HO": (42000, 4.2), "RB": (42000, 4.2), "ZN": (1000, 15.625), "ZB": (1000, 31.25), "ZF": (1000, 7.8125),
    "6E": (125000, 6.25), "6J": (12500000, 6.25), "6B": (62500, 6.25), "6A": (100000, 10), "ZC": (50, 12.5), "ZS": (50, 12.5), "ZW": (50, 12.5),
}
ROOTS = list(SPEC)
FEE = 2.50
DEAD = 0.002
TARGET_VOL = 0.10
VOLWIN = 60
CAP = 3.0
BOOT, BOOT_HI = 2000, 20000
N_PRIOR = 165          # futures ledger before the scoring run (160 + 5 variants); sensitivity re-costings add 5 inside score()
SEED = 90903


def load_rank(rank):
    files = sorted(glob.glob(os.path.join(DB3, "r%d__*.csv.zst" % rank)))
    if not files:
        raise SystemExit("no files for rank %d in %s" % (rank, DB3))
    d = pd.concat([pd.read_csv(f, usecols=["ts_event", "instrument_id", "close", "symbol"]) for f in files])
    d["date"] = pd.to_datetime(d["ts_event"], utc=True).dt.tz_localize(None).dt.normalize()
    d["root"] = d["symbol"].str.split(".").str[0]
    return d


def build():
    d0, d1 = load_rank(0), load_rank(1)
    out = {}
    for r in ROOTS:
        a = d0[d0.root == r].drop_duplicates("date").set_index("date")[["close", "instrument_id"]].rename(columns={"close": "c0", "instrument_id": "i0"})
        b = d1[d1.root == r].drop_duplicates("date").set_index("date")[["close", "instrument_id"]].rename(columns={"close": "c1", "instrument_id": "i1"})
        x = a.join(b, how="inner").dropna().sort_index()
        x = x[(x.c0 > 0) & (x.c1 > 0)]
        if len(x) > 300:
            out[r] = x
    return out


def returns(x):
    """Percentage return of the held contract by identity. A day on which the front instrument is yesterday's second instrument is a roll:
    return = c0[t] / c1[t-1] - 1 and one extra side is paid; a day on which the front changed to something else books zero."""
    c0, c1, i0, i1 = x.c0.values, x.c1.values, x.i0.values, x.i1.values
    n = len(x)
    ret = np.zeros(n)
    roll = np.zeros(n, bool)
    for t in range(1, n):
        if i0[t] == i0[t - 1]:
            ret[t] = c0[t] / c0[t - 1] - 1.0
        elif i0[t] == i1[t - 1]:
            ret[t] = c0[t] / c1[t - 1] - 1.0
            roll[t] = True
        else:
            ret[t] = 0.0
            roll[t] = True
    return pd.Series(ret, index=x.index), pd.Series(roll, index=x.index)


def side_pct(x, root, stress=1.0):
    pv, tick = SPEC[root]
    return (FEE + tick) * stress / (x.c0 * pv)       # one side, fraction of notional (fee 2.50 + 1 tick)


def make(universe, dates, kind):
    R = pd.DataFrame({r: returns(x)[0] for r, x in universe.items()}).reindex(dates)
    ROLL = pd.DataFrame({r: returns(x)[1] for r, x in universe.items()}).reindex(dates).fillna(False)
    C0 = pd.DataFrame({r: x.c0 for r, x in universe.items()}).reindex(dates)
    C1 = pd.DataFrame({r: x.c1 for r, x in universe.items()}).reindex(dates)
    return R.fillna(0.0), ROLL.astype(bool), C0, C1, R.notna()


def signals(kind, R, C0, C1, valid):
    cs = R.cumsum()
    if kind.startswith("TSMOM"):
        L = int(kind.split(":")[1])
        s = np.sign(cs - cs.shift(L)).where(valid & valid.shift(L).fillna(False), 0.0)
    elif kind == "CARRY":
        spr = (C0 - C1) / C0
        s = pd.DataFrame(np.where(spr > DEAD, 1.0, np.where(spr < -DEAD, -1.0, 0.0)), index=R.index, columns=R.columns).where(valid, 0.0)
    elif kind == "XSMOM:120":
        m = (cs - cs.shift(120)).where(valid & valid.shift(120).fillna(False))
        rk = m.rank(axis=1, method="first")
        n = m.notna().sum(axis=1)
        s = pd.DataFrame(0.0, index=R.index, columns=R.columns)
        top = rk.ge(n.sub(6), axis=0) & m.notna()
        bot = rk.le(7) & m.notna()
        s = s.mask(top, 1.0).mask(bot, -1.0)
    elif kind == "LONG":
        s = pd.DataFrame(1.0, index=R.index, columns=R.columns).where(valid, 0.0)
    else:
        raise ValueError(kind)
    return s


def portfolio(kind, R, ROLL, C0, C1, valid, universe, mode="primary", stress=1.0):
    s = signals(kind, R, C0, C1, valid)
    vol = R.rolling(VOLWIN).std().shift(0)               # known at the close of t
    nact = (s != 0).sum(axis=1).clip(lower=1)
    w = s * (TARGET_VOL / math.sqrt(252.0)) / vol.replace(0, np.nan)
    w = w.div(np.sqrt(nact), axis=0).clip(-CAP, CAP).fillna(0.0)
    held = w.shift(1).fillna(0.0)                          # decided at t-1, earns day t
    gross = (held * R).sum(axis=1)
    turn = (w.shift(1).fillna(0.0) - w.shift(2).fillna(0.0)).abs()
    if mode == "primary":
        sp = pd.DataFrame({r: side_pct(universe[r], r, stress).reindex(R.index).ffill() for r in R.columns})
        cost = (turn * sp).sum(axis=1) + (held.abs() * ROLL * sp).sum(axis=1)
    else:  # perp sensitivity: 12 bps a side on traded notional, 2 bps a day funding on gross notional
        cost = turn.sum(axis=1) * 0.0012 + held.abs().sum(axis=1) * 0.0002
    return (gross - cost)


def stats(x):
    n = len(x)
    if n < 2:
        return dict(n=n, mean=0.0, sharpe=0.0, pf=0.0)
    sd = x.std(ddof=1)
    w, l = x[x > 0].sum(), -x[x < 0].sum()
    return dict(n=n, mean=float(x.mean()), sharpe=float(x.mean() / sd * math.sqrt(252)) if sd > 0 else 0.0, pf=float(w / l) if l > 0 else (99.0 if w > 0 else 0.0))


def boot_p(x, months, rng, boot):
    obs = x.mean()
    cen = x - obs
    groups = {}
    for v, mo in zip(cen, months):
        groups.setdefault(mo, []).append(v)
    arrs = [np.array(g) for g in groups.values()]
    cnt = 0
    for _ in range(boot):
        tot = np.concatenate([arrs[rng.randrange(len(arrs))] for _ in range(len(arrs))])
        if tot.mean() >= obs:
            cnt += 1
    return (cnt + 1) / (boot + 1)


VARIANTS = ["TSMOM:60", "TSMOM:120", "TSMOM:250", "CARRY", "XSMOM:120"]


def score():
    uni = build()
    dates = sorted(set().union(*[set(x.index) for x in uni.values()]))
    dates = pd.DatetimeIndex(dates)
    cut = (2 * len(dates)) // 3
    dev_dates = dates[:cut]                    # last third is cut before any signal is computed
    print("roots loaded %d of %d: %s" % (len(uni), len(ROOTS), ",".join(uni)))
    print("dates %s to %s; development %s to %s (%d days), holdout %d days UNREAD" % (dates[0].date(), dates[-1].date(), dev_dates[0].date(), dev_dates[-1].date(), len(dev_dates), len(dates) - cut))
    uni = {r: x[x.index <= dev_dates[-1]] for r, x in uni.items()}
    R, ROLL, C0, C1, valid = make(uni, dev_dates, None)
    half = len(dev_dates) // 2
    N = N_PRIOR + 5
    bar = 0.05 / N
    print("futures ledger N = %d, p bar %.5f" % (N, bar))
    mon = np.array([str(d)[:7] for d in dev_dates])
    rng = random.Random(SEED)
    print("%-11s %-8s %7s %6s %5s | %7s %6s %5s | %6s %7s | %s" % ("variant", "costs", "W1mean", "W1shp", "W1pf", "W2mean", "W2shp", "W2pf", "x2shp", "p", "verdict"))
    surv = []
    for kind in VARIANTS + ["LONG"]:
        for mode in ("primary", "perp"):
            x = portfolio(kind, R, ROLL, C0, C1, valid, uni, mode).values
            x2 = portfolio(kind, R, ROLL, C0, C1, valid, uni, mode, stress=2.0).values if mode == "primary" else x
            w1, w2, s2 = stats(x[:half]), stats(x[half:]), stats(x2)
            ok0 = w1["sharpe"] >= 0.5 and w2["sharpe"] >= 0.5 and w1["pf"] >= 1.5 and w2["pf"] >= 1.5 and kind != "LONG"
            p = boot_p(x, mon, rng, BOOT_HI if ok0 else BOOT)
            ok = ok0 and p < bar
            if ok:
                surv.append((kind, mode))
            print("%-11s %-8s %7.4f %6.2f %5.2f | %7.4f %6.2f %5.2f | %6.2f %7.4f | %s" % (kind, mode, w1["mean"] * 1e2, w1["sharpe"], w1["pf"], w2["mean"] * 1e2, w2["sharpe"], w2["pf"], s2["sharpe"], p, "SURVIVOR?" if ok else ("control" if kind == "LONG" else "falsified")))
    print("(means in percent per day)\nSURVIVORS (dev, all conditions):", surv if surv else "none")


def selftest():
    idx = pd.date_range("2020-01-01", periods=400)
    rng = np.random.default_rng(3)
    # one root, deterministic trend: up 0.1% a day; contract identity constant
    c = 100 * (1.001 ** np.arange(400))
    x = pd.DataFrame({"c0": c, "c1": c * 1.01, "i0": 1, "i1": 2}, index=idx)
    r, roll = returns(x)
    assert abs(r.iloc[5] - 0.001) < 1e-9 and not roll.any()
    # a roll: front becomes yesterday's second instrument; return uses the previous second price
    y = x.copy()
    y.loc[idx[200]:, "i0"] = 2
    y.loc[idx[200]:, "i1"] = 3
    y.loc[idx[200]:, "c0"] = x.c1.iloc[199] * 1.001 ** np.arange(1, 201)
    r2, roll2 = returns(y)
    assert roll2.iloc[200] and abs(r2.iloc[200] - 0.001) < 1e-6, r2.iloc[200]
    # trend signal on the constant uptrend is long and the portfolio makes money before costs; no lookahead: change the last 50 days
    uni = {"ES": x.copy()}
    R, ROLL, C0, C1, valid = make(uni, idx, None)
    p1 = portfolio("TSMOM:60", R, ROLL, C0, C1, valid, uni)
    x_b = x.copy()
    x_b.iloc[350:, x_b.columns.get_loc("c0")] *= 0.5
    uni_b = {"ES": x_b}
    Rb, ROLLb, C0b, C1b, validb = make(uni_b, idx, None)
    p2 = portfolio("TSMOM:60", Rb, ROLLb, C0b, C1b, validb, uni_b)
    assert np.allclose(p1.iloc[:349].values, p2.iloc[:349].values), "lookahead"
    assert p1.iloc[100:300].mean() > 0
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    else:
        score()
