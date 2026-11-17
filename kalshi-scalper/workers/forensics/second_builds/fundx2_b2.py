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
MAXGAP_NEXT = 5400


def two(r):
    return 0 < r[1] <= r[2]


def merge_funding(files):
    """files: list of (date, [(ticker,t,rate)]) read in DATE ORDER. Repeat same ticker,t, same rate kept once and
    counted; different rate keeps the first (earlier file), conflict counted."""
    seen, out, dup, conf = {}, [], 0, 0
    for _, f in sorted(files, key=lambda x: x[0]):
        for tk, t, r in f:
            k = (tk, t)
            if k in seen:
                if seen[k] == r:
                    dup += 1
                else:
                    conf += 1
                continue
            seen[k] = r
            out.append((tk, t, r))
    return out, dup, conf


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
    cnt = {"no_prior": 0, "no_after": 0, "open": 0, "no_exit": 0, "gap": 0, "one_sided": 0}
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
        if e[0] - before[-1][0] > MAXGAP_NEXT:
            cnt["gap"] += 1
            continue
        if not two(e):
            cnt["one_sided"] += 1
            continue
        long_ = (r < 0) if side == "fade" else (r > 0)
        tgt = e[0] + hold_h * 3600
        ex = next((x for x in rows if x[0] >= tgt), None)
        if ex is None or ex[0] - tgt > HOLD_TOL:
            cnt["no_exit"] += 1
            continue
        if not two(ex):
            cnt["one_sided"] += 1
            continue
        busy_until = ex[0]
        # Auditor B ruling: additive haircut on notional; touches unadjusted
        if long_:
            gross = ex[1] / e[2] - 1
        else:
            gross = 1 - ex[2] / e[1]
        fund = sum(rr for ft, rr in prints if e[0] < ft < ex[0])   # strictly between
        fund = fund if long_ else -fund
        net = gross - 2 * FEE - 2 * h - fund
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
    exp = (1 - 101.2 / 100.0) - 0.0024 + 0.0001   # short receives funding at ft=14h (strictly between)
    assert abs(tr[0]["net"] - exp) < 1e-12, (tr[0]["net"], exp)
    # follow = long: buys 100.2, sells 101.0, pays funding
    tr, _ = build_trades(pr, rows, c, "follow", 8, 0, 10**9, 0.0)
    exp = (101.0 / 100.2 - 1) - 0.0024 - 0.0001
    assert abs(tr[0]["net"] - exp) < 1e-12
    # additive haircut: exactly 2h lower
    tr2, _ = build_trades(pr, rows, c, "follow", 8, 0, 10**9, 0.0005)
    assert abs(tr2[0]["net"] - (tr[0]["net"] - 0.001)) < 1e-12
    # funding exactly at entry or exit is not booked
    tr3, _ = build_trades([(int(9.5 * H), 0.0003), (10 * H, 0.0005), (18 * H, 0.0005)], rows, c, "follow", 8, 0, 10**9, 0.0)
    assert abs(tr3[0]["net"] - ((101.0 / 100.2 - 1) - 0.0024)) < 1e-12, tr3
    # entry row too far (> 5400 s) and one-sided rows are skipped
    far = [(0, 99.9, 100.1), (4 * H, 99.9, 100.1)] + [(i * H, 99.9, 100.1) for i in range(5, 40)]
    assert build_trades([(1 * H, 0.0003)], far, c, "fade", 8, 0, 10**9, 0)[1]["gap"] == 1
    os_ = [(i * H, 99.9, 100.1) for i in range(40)]; os_[10] = (10 * H, 0.0, 100.2)
    assert build_trades([(int(9.5 * H), 0.0003)], os_, c, "fade", 8, 0, 10**9, 0)[1]["one_sided"] == 1
    m, d, cf = merge_funding([("2026-11-18", [("A", 5, 0.1), ("A", 6, 0.2)]), ("2026-11-17", [("A", 5, 0.1), ("A", 6, 0.3)])])
    assert d == 1 and cf == 1 and ("A", 6, 0.3) in m and ("A", 6, 0.2) not in m
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


# ---- FUNDX2-F forward layer (card FUNDX2F_CARD_NOV17 + Amendment 1) ----
import calendar, itertools
def _ep(y, m, d):
    return calendar.timegm((y, m, d, 0, 0, 0))
FWD_T0, FWD_T1 = _ep(2026, 11, 17), _ep(2026, 12, 15)      # prints and rows in [T0, T1)
GATE_D0, GATE_D1 = _ep(2026, 11, 17), _ep(2026, 11, 24)    # entry UTC date Nov 17..23 (7 days)
TICKERS = ["KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXDOGEPERP", "KXHYPEPERP"]
CELLS = [(q, side, hh) for q in (5, 10) for side in ("fade", "follow") for hh in (8, 24)]
RATE_MIN = 3.0


def cut_of(thr, ticker, q):
    """thr = parsed FUNDX2_THRESHOLDS.json. None when the name has no threshold."""
    c = thr["cuts"].get(ticker, {}).get(str(q))
    if not c or not c.get("has_threshold"):
        return None
    return {"lower": c["lower"], "upper": c["upper"]}


def gate(thr, prints_by, rows_by, h=0.0):
    """Counts only. prints_by/rows_by: ticker -> list. Returns per cell: pooled trades with entry in
    the gate window, rate a day, passes, plus skip counts pooled. Rows are cut to the window first."""
    out = {}
    for (q, side, hh) in CELLS:
        n, skips = 0, {"no_prior": 0, "no_after": 0, "open": 0, "no_exit": 0}
        for tk in TICKERS:
            c = cut_of(thr, tk, q)
            if c is None:
                continue
            rows = [x for x in rows_by.get(tk, []) if FWD_T0 <= x[0] < FWD_T1]
            pr = [x for x in prints_by.get(tk, []) if FWD_T0 <= x[0] < FWD_T1]
            tr, k = build_trades(pr, rows, c, side, hh, FWD_T0, FWD_T1, h)
            n += sum(1 for x in tr if GATE_D0 <= x["entry"] < GATE_D1)
            for a in skips:
                skips[a] += k[a]
        out["%d|%s|%d" % (q, side, hh)] = {"trades_gate_window": n, "rate_a_day": n / 7.0,
                                            "passes": n / 7.0 >= RATE_MIN, "skips": skips}
    return out


def selftest_fwd():
    H = 3600
    thr = {"cuts": {"KXBTCPERP": {"5": {"has_threshold": True, "lower": 0.0, "upper": 0.0002},
                                  "10": {"has_threshold": True, "lower": 0.0, "upper": 0.0001}},
                    "KXHYPEPERP": {"5": {"has_threshold": False}}}}
    rows = [(FWD_T0 + i * H, 99.9, 100.1) for i in range(0, 24 * 40)]
    prints = [(FWD_T0 + (24 * d + 21) * H, 0.0003) for d in range(0, 10)]
    g = gate(thr, {"KXBTCPERP": prints, "KXHYPEPERP": prints}, {"KXBTCPERP": rows, "KXHYPEPERP": rows})
    # 8h hold: prints at 21:00 each day, entry 22:00, exit 06:00 next day; 7 entries on Nov 17..23
    assert g["5|fade|8"]["trades_gate_window"] == 7 and abs(g["5|fade|8"]["rate_a_day"] - 1.0) < 1e-12
    assert g["5|fade|24"]["trades_gate_window"] == 4, g["5|fade|24"]   # exit 22:00 next day blocks the next print: every 2nd day
    assert not any(v["passes"] for v in g.values())                    # one name cannot reach 3 a day
    # HYPE has no threshold at q 5: excluded; at q 10 it is missing from thr: excluded too
    assert cut_of(thr, "KXHYPEPERP", 5) is None and cut_of(thr, "KXSOLPERP", 10) is None
    # a print before the window is never used; a print in the first hour has no prior row
    g2 = gate(thr, {"KXBTCPERP": [(FWD_T0 - 5, 0.0003), (FWD_T0, 0.0003)]}, {"KXBTCPERP": rows})
    assert g2["5|fade|8"]["trades_gate_window"] == 1 and g2["5|fade|8"]["skips"]["no_prior"] == 0
    g3 = gate(thr, {"KXBTCPERP": [(FWD_T0 - 1, 0.0003)]}, {"KXBTCPERP": rows[1:]})
    assert g3["5|fade|8"]["trades_gate_window"] == 0
    print("selftest_fwd OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        selftest()
        selftest_fwd()
    else:
        print("only selftest; no data is opened by this build")
