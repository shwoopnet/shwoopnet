"""IDEAS20 (README, Pre-registration: IDEAS20): twenty new Bitcoin 15 minute rules built on volume, open interest, spread, candle shape and
statistics of the price path. Discovery on the first two thirds of the days, confirmation on the last third. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.ideas20 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import math
import sqlite3
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR

# ---- fixed in the README before any of these rules was scored ----
SERIES, SOURCES, BAND = "KXBTC15M", ("l1b", "book", "e3b", "alts2", "fresh"), L.L1["band"]
DISC_FRAC = 2 / 3
MIN_N_DISC, MIN_N_CONF = 200, 100
DISC_C, DISC_Z, CONF_C, CONF_Z, PF_BAR, FALSIFY_C, FALSIFY_Z = 0.015, 2.5, 0.010, 1.65, 1.3, 0.005, 1.0
RESULT = DATA_DIR / "ideas20_result.txt"
Q = ("end", "bid", "ask", "bid_h", "bid_l", "ask_h", "ask_l", "vol", "oi", "last")


def load_btc(series: str = SERIES) -> dict[str, dict]:
    """ticker -> {close, result, strike, c: [candle dict sorted by end]} for settled Bitcoin markets with quotes, three sources, first seen wins."""
    out: dict[str, dict] = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        by: dict = defaultdict(list)
        for tk, end, bc, ac, bh, bl, ah, al, vol, oi, last in db.execute(
                "SELECT c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.bid_l, c.ask_h, c.ask_l, c.volume, c.oi, c.price_c FROM candle c WHERE c.series = ? ORDER BY c.ticker, c.end_ts", (series,)):
            if bc is not None and ac is not None:
                by[tk].append(dict(zip(Q, (end, bc, ac, bh, bl, ah, al, vol or 0.0, oi or 0.0, last))))
        for tk, close_ts, res, strike in db.execute("SELECT ticker, close_ts, result, strike FROM market WHERE series = ?", (series,)):
            if tk in by and tk not in out and res in ("yes", "no"):
                out[tk] = {"close": close_ts, "res": res, "strike": strike, "c": by[tk]}
    return out


def spread(c: dict) -> float:
    return c["ask"] - c["bid"]


def at(m: dict, left: int):
    """(index, candle) of the candle ending exactly `left` seconds before the close, and the candles strictly before it."""
    t = m["close"] - left
    for i, c in enumerate(m["c"]):
        if c["end"] == t:
            return c, m["c"][:i]
    return None, []


def mid_side(c: dict, side: str) -> float:
    return (c["bid"] + c["ask"]) / 2 if side == "yes" else 1 - (c["bid"] + c["ask"]) / 2


def ask_side(c: dict, side: str) -> float:
    return c["ask"] if side == "yes" else round(1 - c["bid"], 4)


def fav(c: dict):
    return L.favorite(c["bid"], c["ask"], BAND)


def mean_or(v: list[float], d: float = 0.0) -> float:
    return st.mean(v) if v else d


# each rule: (name, left seconds, function(market, decision candle, earlier candles, prior_strike) -> (side, price) or None)
def r01(m, c, e, ps):   # SURGE: decision-minute volume at least 2x the earlier mean
    f = fav(c)
    return f if f and len(e) >= 3 and c["vol"] >= 2 * mean_or([x["vol"] for x in e]) else None


def r02(m, c, e, ps):   # QUIET: decision-minute volume at most 0.5x the earlier mean
    f = fav(c)
    return f if f and len(e) >= 3 and c["vol"] <= 0.5 * mean_or([x["vol"] for x in e]) else None


def r03(m, c, e, ps):   # OIBUILD: open interest at least 25% above three minutes earlier
    f = fav(c)
    p = next((x for x in e if x["end"] == c["end"] - 180), None)
    return f if f and p and p["oi"] > 0 and c["oi"] / p["oi"] >= 1.25 else None


def r04(m, c, e, ps):   # OIFLAT: open interest up by at most 10% over three minutes
    f = fav(c)
    p = next((x for x in e if x["end"] == c["end"] - 180), None)
    return f if f and p and p["oi"] > 0 and c["oi"] / p["oi"] <= 1.10 else None


def _move(c, e, k):
    p = next((x for x in e if x["end"] == c["end"] - 60 * k), None)
    return None if p is None else ((c["bid"] + c["ask"]) / 2 - (p["bid"] + p["ask"]) / 2)


def r05(m, c, e, ps):   # SURGE_FOLLOW (8 minutes left): volume >= 1.8x earlier mean and a 4c move in 2 minutes, buy the side that moved at 0.55 to 0.85
    d = _move(c, e, 2)
    if d is None or abs(d) < 0.04 or len(e) < 3 or c["vol"] < 1.8 * mean_or([x["vol"] for x in e]):
        return None
    side = "yes" if d > 0 else "no"
    p = ask_side(c, side)
    return (side, p) if 0.55 <= p <= 0.85 else None


def r06(m, c, e, ps):   # SURGE_FADE: same trigger, buy the other side at 0.15 to 0.45
    d = _move(c, e, 2)
    if d is None or abs(d) < 0.04 or len(e) < 3 or c["vol"] < 1.8 * mean_or([x["vol"] for x in e]):
        return None
    side = "no" if d > 0 else "yes"
    p = ask_side(c, side)
    return (side, p) if 0.15 <= p <= 0.45 else None


def r07(m, c, e, ps):   # ABSORB: previous minute volume >= 1.5x the one before it while the mid moved under 3c
    f = fav(c)
    if not f or len(e) < 2 or e[-1]["end"] != c["end"] - 60 or e[-2]["end"] != c["end"] - 120:
        return None
    mv = abs((e[-1]["bid"] + e[-1]["ask"]) / 2 - (e[-2]["bid"] + e[-2]["ask"]) / 2)
    return f if e[-2]["vol"] > 0 and e[-1]["vol"] >= 1.5 * e[-2]["vol"] and mv < 0.03 else None


def r08(m, c, e, ps):   # TIGHT: spread at most 1c now and a minute earlier
    f = fav(c)
    return f if f and e and e[-1]["end"] == c["end"] - 60 and spread(c) <= 0.0101 and spread(e[-1]) <= 0.0101 else None


def r09(m, c, e, ps):   # WIDENING: spread at least 1.5x the earlier mean and at least 2c
    f = fav(c)
    return f if f and len(e) >= 3 and spread(c) >= 0.02 and spread(c) >= 1.5 * mean_or([spread(x) for x in e]) else None


def r10(m, c, e, ps):   # SPREADCOLLAPSE: spread now at most half of the widest of the last three minutes, which was at least 1.5c
    f = fav(c)
    w = max((spread(x) for x in e[-3:]), default=0.0)
    return f if f and w >= 0.015 and spread(c) <= 0.5 * w else None


def r11(m, c, e, ps):   # RANGE: the decision minute's ask range is at least 4c
    f = fav(c)
    return f if f and c["ask_h"] is not None and c["ask_l"] is not None and c["ask_h"] - c["ask_l"] >= 0.04 else None


def r12(m, c, e, ps):   # LIFTING: the last trade printed at the ask of the side we buy
    f = fav(c)
    if not f or c["last"] is None:
        return None
    return f if (f[0] == "yes" and c["last"] >= c["ask"] - 0.001) or (f[0] == "no" and c["last"] <= c["bid"] + 0.001) else None


def r13(m, c, e, ps):   # PRIORMOVE: the strike moved at least 0.15% from the previous window's strike (a big 15 minute spot move)
    f = fav(c)
    return f if f and ps and m["strike"] and abs(m["strike"] / ps - 1) >= 0.0015 else None


def _changes(e):
    mids = [(x["bid"] + x["ask"]) / 2 for x in e]
    return [b - a for a, b in zip(mids, mids[1:])]


def r14(m, c, e, ps):   # CHOPPY: lag-1 autocorrelation of the minute mid changes is at most -0.3 (at least 6 changes)
    f = fav(c)
    d = _changes(e)
    if not f or len(d) < 6 or st.pstdev(d) == 0:
        return None
    mu = st.mean(d)
    ac = sum((a - mu) * (b - mu) for a, b in zip(d, d[1:])) / sum((a - mu) ** 2 for a in d)
    return f if ac <= -0.3 else None


def r15(m, c, e, ps):   # TREND: the earlier mids fit a line with R^2 >= 0.8 and the favourite is on the side the line is heading to
    f = fav(c)
    mids = [(x["bid"] + x["ask"]) / 2 for x in e]
    n = len(mids)
    if not f or n < 6:
        return None
    xs = list(range(n))
    mx, my = st.mean(xs), st.mean(mids)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in mids)
    if syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, mids))
    r2 = sxy * sxy / (sxx * syy)
    return f if r2 >= 0.8 and ((sxy > 0) == (f[0] == "yes")) else None


def r16(m, c, e, ps):   # ROUND: the strike is within 0.05% of a multiple of 1000
    f = fav(c)
    if not f or not m["strike"]:
        return None
    return f if abs(m["strike"] - round(m["strike"] / 1000) * 1000) <= 0.0005 * m["strike"] else None


def r17(m, c, e, ps):   # MOM_FOLLOW (7 minutes left): the mid moved at least 6c in 3 minutes, buy that side at 0.60 to 0.85
    d = _move(c, e, 3)
    if d is None or abs(d) < 0.06:
        return None
    side = "yes" if d > 0 else "no"
    p = ask_side(c, side)
    return (side, p) if 0.60 <= p <= 0.85 else None


def r18(m, c, e, ps):   # MOM_FADE: same move, buy the other side at 0.15 to 0.40
    d = _move(c, e, 3)
    if d is None or abs(d) < 0.06:
        return None
    side = "no" if d > 0 else "yes"
    p = ask_side(c, side)
    return (side, p) if 0.15 <= p <= 0.40 else None


def r19(m, c, e, ps):   # THIN: the previous minute's volume was at most half the earlier mean
    f = fav(c)
    return f if f and len(e) >= 4 and e[-1]["end"] == c["end"] - 60 and e[-1]["vol"] <= 0.5 * mean_or([x["vol"] for x in e[:-1]]) else None


def r20(m, c, e, ps):   # ARRIVED: the favourite side's ask was under 0.80 two minutes earlier and is in the band now
    f = fav(c)
    p = next((x for x in e if x["end"] == c["end"] - 120), None)
    return f if f and p and ask_side(p, f[0]) < 0.80 else None


RULES = [("SURGE", 360, r01), ("QUIET", 360, r02), ("OIBUILD", 360, r03), ("OIFLAT", 360, r04), ("SURGE_FOLLOW", 480, r05), ("SURGE_FADE", 480, r06),
         ("ABSORB", 360, r07), ("TIGHT", 360, r08), ("WIDENING", 360, r09), ("SPREADCOLLAPSE", 360, r10), ("RANGE", 360, r11), ("LIFTING", 360, r12),
         ("PRIORMOVE", 360, r13), ("CHOPPY", 360, r14), ("TREND", 360, r15), ("ROUND", 360, r16), ("MOM_FOLLOW", 420, r17), ("MOM_FADE", 420, r18),
         ("THIN", 360, r19), ("ARRIVED", 360, r20)]


def entries(markets: dict[str, dict], left: int, fn) -> list[dict]:
    by_close = {m["close"]: m for m in markets.values()}
    out = []
    for tk, m in markets.items():
        c, e = at(m, left)
        if c is None:
            continue
        prior = by_close.get(m["close"] - 900)
        pick = fn(m, c, e, prior["strike"] if prior else None)
        if pick is None:
            continue
        side, price = pick
        yes = m["res"] == "yes"
        out.append({"day": datetime.fromtimestamp(m["close"], timezone.utc).strftime("%Y-%m-%d"), "close_ts": m["close"],
                    "net": L.net(side, price, yes), "stress": L.net(side, price, yes, L.STRESS)})
    return out


def pf(rows: list[dict]) -> float:
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    return w / l if l > 0 else float("inf")


def stat(rows: list[dict]):
    if len(rows) < 2:
        return 0.0, 0.0
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    return m, z


def judge(rows: list[dict], cut_day: str, pf_rows: list[dict] | None = None) -> dict:
    d = [r for r in rows if r["day"] < cut_day]
    c = [r for r in rows if r["day"] >= cut_day]
    dm, dz = stat(d)
    cm, cz = stat(c)
    am, az = stat(rows)
    p = pf(pf_rows if pf_rows is not None else rows) if rows else 0.0
    if len(d) < MIN_N_DISC or len(c) < MIN_N_CONF:
        v = "NOT_ENOUGH_DATA"
    elif dm >= DISC_C and dz >= DISC_Z and cm >= CONF_C and cz >= CONF_Z and p >= PF_BAR and sum(r["stress"] for r in d) > 0 and sum(r["stress"] for r in c) > 0:
        v = "NOT_YET_FALSIFIED"
    else:
        v = "FALSIFIED" if (am < FALSIFY_C or az < FALSIFY_Z) else "NOT_ENOUGH_DATA"
    return {"verdict": v, "nd": len(d), "nc": len(c), "dm": dm, "dz": dz, "cm": cm, "cz": cz, "am": am, "az": az, "pf": p}


def cut_day(markets: dict[str, dict]) -> str:
    days = sorted({datetime.fromtimestamp(m["close"], timezone.utc).strftime("%Y-%m-%d") for m in markets.values()})
    return days[int(len(days) * DISC_FRAC)]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = load_btc()
    cut = cut_day(mk)
    out = [f"IDEAS20: {len(mk)} Bitcoin markets, discovery before {cut}, confirmation from {cut}"]
    for name, left, fn in RULES:
        j = judge(entries(mk, left, fn), cut)
        out.append(f"{name:15s} {j['verdict']:18s} disc n={j['nd']:5d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:5d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f} PF {j['pf']:.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
