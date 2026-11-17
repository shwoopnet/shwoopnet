#!/usr/bin/env python3
"""FUNDX2 blind second build (Forensics Desk), from the card and spec 0549b199 only.
Pure functions plus a selftest. Opens NO data file. Run: python3 -I fundx2_b2.py selftest
Readings (ask the History Miner to confirm): R1 extreme = rate>0 and rate>=upper, or rate<0 and rate<=lower
(cut 0 means any non-zero print of that sign). R2 signal row = last row t<=print; entry = first row t>print.
R3 exit = first row t>=entry+H*3600, within 30 min else trade skipped (no position held). R4 print strictly
before the exit instant of an open hold: no trade; print at the exit instant may signal. R5 funding booked on
prints with entry_t < ft <= exit_t, long pays rate, short receives rate, on entry notional. R6 haircut h is a
relative worsening of each fill (buy ask*(1+h), sell bid*(1-h)). R7 fee 0.0012 per side of notional.
R8 PF = gains / |losses| of net return fractions."""
import math, sys

FEE = 0.0012
HOLD_TOL = 1800


def cuts_from(rates, q, minn=120):
    n = len(rates)
    if n < minn:
        return None
    s = sorted(rates)
    k = math.ceil(q * n)
    return {"lower": s[k - 1], "upper": s[n - k]}


def is_extreme(rate, c):
    return (rate > 0 and rate >= c["upper"]) or (rate < 0 and rate <= c["lower"])


def build_trades(prints, rows, c, side, hold_h, t0, t1, h):
    """prints [(t,rate)], rows [(t,bid,ask)] sorted. Returns (trades, counts)."""
    cnt = {"no_prior": 0, "no_after": 0, "open": 0, "no_exit": 0}
    trades, busy_until, ri = [], None, 0
    for t, r in sorted(prints):
        if not (t0 <= t < t1) or not is_extreme(r, c):
            continue
        if busy_until is not None and t < busy_until:
            cnt["open"] += 1
            continue
        before = [x for x in rows if x[0] <= t]
        after = [x for x in rows if x[0] > t]
        if not before:
            cnt["no_prior"] += 1
            continue
        if not after:
            cnt["no_after"] += 1
            continue
        e = after[0]
        long_ = (r < 0) if side == "fade" else (r > 0)
        tgt = e[0] + hold_h * 3600
        ex = next((x for x in rows if x[0] >= tgt), None)
        if ex is None or ex[0] - tgt > HOLD_TOL:
            cnt["no_exit"] += 1
            continue
        busy_until = ex[0]
        if long_:
            ep, xp = e[2] * (1 + h), ex[1] * (1 - h)
            gross = xp / ep - 1
        else:
            ep, xp = e[1] * (1 - h), ex[2] * (1 + h)
            gross = 1 - xp / ep
        fund = sum(rr for ft, rr in prints if e[0] < ft <= ex[0])
        fund = -fund if long_ else fund
        net = gross - 2 * FEE + fund
        trades.append({"entry": e[0], "exit": ex[0], "long": long_, "net": net})
    return trades, cnt


def pf(trades):
    g = sum(x["net"] for x in trades if x["net"] > 0)
    l = -sum(x["net"] for x in trades if x["net"] < 0)
    return float("inf") if l == 0 and g > 0 else (g / l if l else None)


def gate_rate(trades, d0, d1):
    return sum(1 for x in trades if d0 <= x["entry"] < d1) / 7.0


def selftest():
    c = {"lower": -0.0001, "upper": 0.0002}
    assert is_extreme(0.0003, c) and is_extreme(-0.0001, c) and not is_extreme(0.0001, c)
    assert is_extreme(1e-9, {"lower": 0.0, "upper": 0.0}) and not is_extreme(0.0, {"lower": 0.0, "upper": 0.0})
    s = [i * 1e-6 for i in range(-60, 60)] * 2 + [0.0] * 10
    cu = cuts_from(s, 0.05)
    assert cu["lower"] == sorted(s)[math.ceil(0.05 * len(s)) - 1] and cuts_from(s[:100], 0.05) is None
    H = 3600
    rows = [(i * H, 99.9, 100.1) for i in range(0, 40)]
    rows[10] = (10 * H, 100.0, 100.2)       # entry row
    rows[18] = (18 * H, 101.0, 101.2)       # exit row (8h later)
    # case 1: print at 9.5h, rate +0.0003 (longs pay), fade -> short at bid of row 10, buy back at ask of row 18
    pr = [(int(9.5 * H), 0.0003), (14 * H, 0.0001)]
    tr, k = build_trades(pr, rows, c, "fade", 8, 0, 10**9, 0.0)
    assert len(tr) == 1 and not tr[0]["long"], tr
    exp = (1 - 101.2 / 100.0) - 0.0024 + 0.0001   # short receives funding at ft=14h
    assert abs(tr[0]["net"] - exp) < 1e-12, (tr[0]["net"], exp)
    # follow = long: buys 100.2, sells 101.0, pays funding
    tr, _ = build_trades(pr, rows, c, "follow", 8, 0, 10**9, 0.0)
    exp = (101.0 / 100.2 - 1) - 0.0024 - 0.0001
    assert abs(tr[0]["net"] - exp) < 1e-12
    # haircut worsens
    tr2, _ = build_trades(pr, rows, c, "follow", 8, 0, 10**9, 0.0005)
    assert tr2[0]["net"] < tr[0]["net"]
    # print exactly at a row: entry is the next row, never the print instant
    tr, _ = build_trades([(10 * H, 0.0003)], rows, c, "fade", 8, 0, 10**9, 0.0)
    assert tr[0]["entry"] == 11 * H
    # print inside open hold makes no trade; at exit instant it may signal
    tr, k = build_trades([(int(9.5 * H), 0.0003), (14 * H, 0.0004)], rows, c, "fade", 8, 0, 10**9, 0.0)
    assert len(tr) == 1 and k["open"] == 1
    tr, _ = build_trades([(int(9.5 * H), 0.0003), (18 * H, 0.0004)], rows, c, "fade", 8, 0, 10**9, 0.0)
    assert len(tr) == 2
    # no row after / no prior / no exit within 30 min
    assert build_trades([(39 * H, 0.0003)], rows, c, "fade", 8, 0, 10**9, 0)[1]["no_after"] == 1
    assert build_trades([(-5, 0.0003)], rows, c, "fade", 8, -10**9, 10**9, 0)[1]["no_prior"] == 1
    assert build_trades([(35 * H, 0.0003)], rows, c, "fade", 8, 0, 10**9, 0)[1]["no_exit"] == 1
    # window: print before t0 gives nothing
    assert build_trades(pr, rows, c, "fade", 8, 20 * H, 10**9, 0)[0] == []
    # PF and gate rate
    assert pf([{"net": 2.0}, {"net": -1.0}]) == 2.0 and pf([]) is None
    assert gate_rate([{"entry": 5}, {"entry": 99}], 0, 10) == 1 / 7
    print("selftest OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        selftest()
    else:
        print("only selftest; no data is opened by this build")
