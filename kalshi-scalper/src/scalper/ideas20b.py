"""IDEAS20B (README, Pre-registration: IDEAS20B): a second twenty Bitcoin 15 minute rules, built on the multi-window path (an hour of strikes and results), the window's
position in the hour, the opening gap, the closing shape of the minute, activity relative to the previous window and open-interest turnover. Research only.
Same data, split, bars and verdict words as IDEAS20 (imported, not copied). Nothing here means trade.
Usage: python -m scalper.ideas20b run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import ideas20 as I
from .paths import DATA_DIR

RESULT = DATA_DIR / "ideas20b_result.txt"
WIN = 900


def ctx(m, c, e, ps, mk):
    """Context from other windows: the markets closing 15, 30, ... minutes earlier (strike and result), and the previous window's candle at the same elapsed time."""
    prior = [mk.get(m["close"] - WIN * k) for k in range(1, 9)]
    return prior


def _ret(a, b):
    return b / a - 1 if a and b else None


def _cum(mm, end):
    return sum(x["vol"] for x in mm["c"] if x["end"] <= end) if mm else None


def make(mk_by_close):
    P = lambda m, k: mk_by_close.get(m["close"] - WIN * k)

    def hourclose(m, c, e, ps):
        f = I.fav(c)
        return f if f and datetime.fromtimestamp(m["close"], timezone.utc).minute == 0 else None

    def halfclose(m, c, e, ps):
        f = I.fav(c)
        return f if f and datetime.fromtimestamp(m["close"], timezone.utc).minute == 30 else None

    def _trend4(m):
        p4 = P(m, 4)
        return _ret(p4["strike"], m["strike"]) if p4 else None

    def trend4(m, c, e, ps):
        f, r = I.fav(c), _trend4(m)
        return f if f and r is not None and abs(r) >= 0.003 and ((r > 0) == (f[0] == "yes")) else None

    def trend4_opp(m, c, e, ps):
        f, r = I.fav(c), _trend4(m)
        return f if f and r is not None and abs(r) >= 0.003 and ((r > 0) != (f[0] == "yes")) else None

    def _vol8(m):
        ks = [P(m, k) for k in range(0, 9)] if False else [m] + [P(m, k) for k in range(1, 9)]
        if any(x is None or not x["strike"] for x in ks):
            return None
        rets = [ks[i]["strike"] / ks[i + 1]["strike"] - 1 for i in range(8)]
        return st.pstdev(rets)

    def highreg(m, c, e, ps):
        f, v = I.fav(c), _vol8(m)
        return f if f and v is not None and v >= 0.0012 else None

    def lowreg(m, c, e, ps):
        f, v = I.fav(c), _vol8(m)
        return f if f and v is not None and v <= 0.0006 else None

    def _streak(m):
        rs = [P(m, k) for k in range(1, 4)]
        if any(x is None for x in rs) or len({x["res"] for x in rs}) != 1:
            return None
        return rs[0]["res"]

    def streak(m, c, e, ps):
        f, s = I.fav(c), _streak(m)
        return f if f and s and f[0] == s else None

    def streak_opp(m, c, e, ps):
        f, s = I.fav(c), _streak(m)
        return f if f and s and f[0] != s else None

    def round500(m, c, e, ps):
        f = I.fav(c)
        return f if f and m["strike"] and abs(m["strike"] - round(m["strike"] / 500) * 500) <= 0.0004 * m["strike"] else None

    def _gap(m):
        c0 = m["c"][0]
        return (c0["bid"] + c0["ask"]) / 2 - 0.5

    def gapopen(m, c, e, ps):
        f, g = I.fav(c), _gap(m)
        return f if f and abs(g) >= 0.10 and ((g > 0) == (f[0] == "yes")) else None

    def gapopen_opp(m, c, e, ps):
        f, g = I.fav(c), _gap(m)
        return f if f and abs(g) >= 0.10 and ((g > 0) != (f[0] == "yes")) else None

    def closehigh(m, c, e, ps):
        f = I.fav(c)
        if not f or c["ask_h"] is None or c["ask_l"] is None or c["ask_h"] - c["ask_l"] < 0.02:
            return None
        return f if (f[0] == "yes" and c["ask"] >= c["ask_h"] - 0.001) or (f[0] == "no" and c["bid"] <= c["bid_l"] + 0.001) else None

    def closelow(m, c, e, ps):
        f = I.fav(c)
        if not f or c["ask_h"] is None or c["ask_l"] is None or c["ask_h"] - c["ask_l"] < 0.02:
            return None
        return f if (f[0] == "yes" and c["ask"] <= c["ask_l"] + 0.001) or (f[0] == "no" and c["bid"] >= c["bid_h"] - 0.001) else None

    def biddrop(m, c, e, ps):
        f = I.fav(c)
        return f if f and c["bid_h"] is not None and c["bid_h"] - c["bid"] >= 0.03 else None

    def _act(m, c):
        p1 = P(m, 1)
        if not p1:
            return None
        elapsed = c["end"] - (m["close"] - WIN)
        a, b = _cum(m, c["end"]), _cum(p1, (p1["close"] - WIN) + elapsed)
        return a / b if a and b else None

    def active(m, c, e, ps):
        f, r = I.fav(c), _act(m, c)
        return f if f and r is not None and r >= 1.3 else None

    def inactive(m, c, e, ps):
        f, r = I.fav(c), _act(m, c)
        return f if f and r is not None and r <= 0.8 else None

    def turnover(m, c, e, ps):
        f = I.fav(c)
        cv = _cum(m, c["end"])
        return f if f and c["oi"] > 0 and cv / c["oi"] >= 3 else None

    def oilevel(m, c, e, ps):
        f, p1 = I.fav(c), P(m, 1)
        if not f or not p1:
            return None
        elapsed = c["end"] - (m["close"] - WIN)
        pc = next((x for x in p1["c"] if x["end"] == (p1["close"] - WIN) + elapsed), None)
        return f if pc and pc["oi"] > 0 and c["oi"] / pc["oi"] >= 1.3 else None

    def decayed(m, c, e, ps):
        f = I.fav(c)
        p = next((x for x in e if x["end"] == c["end"] - 120), None)
        return f if f and p and I.ask_side(p, f[0]) >= 0.95 else None

    def fadedtop(m, c, e, ps):
        f = I.fav(c)
        return f if f and I.ask_side(c, f[0]) <= 0.93 and any(I.mid_side(x, f[0]) >= 0.97 for x in e) else None

    def calmopen(m, c, e, ps):
        f = I.fav(c)
        first = m["c"][:3]
        return f if f and len(first) == 3 and all(0.40 <= (x["bid"] + x["ask"]) / 2 <= 0.60 for x in first) else None

    return [("HOURCLOSE", 360, hourclose), ("HALFCLOSE", 360, halfclose), ("TREND4", 360, trend4), ("TREND4_OPP", 360, trend4_opp),
            ("HIGHREG", 360, highreg), ("LOWREG", 360, lowreg), ("STREAK3", 360, streak), ("STREAK3_OPP", 360, streak_opp), ("ROUND500", 360, round500),
            ("GAPOPEN", 360, gapopen), ("GAPOPEN_OPP", 360, gapopen_opp), ("CLOSEHIGH", 360, closehigh), ("CLOSELOW", 360, closelow), ("BIDDROP", 360, biddrop),
            ("ACTIVE", 360, active), ("INACTIVE", 360, inactive), ("TURNOVER", 360, turnover), ("OILEVEL", 360, oilevel), ("DECAYED", 360, decayed), ("CALMOPEN", 360, calmopen)]


def rules(mk):
    return make({m["close"]: m for m in mk.values()})


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = I.load_btc()
    cut = I.cut_day(mk)
    out = [f"IDEAS20B: {len(mk)} Bitcoin markets, discovery before {cut}, confirmation from {cut}"]
    for name, left, fn in rules(mk):
        j = I.judge(I.entries(mk, left, fn), cut)
        out.append(f"{name:15s} {j['verdict']:18s} disc n={j['nd']:5d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:5d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f} PF {j['pf']:.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
