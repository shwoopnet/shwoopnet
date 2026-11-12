#!/usr/bin/env python3
"""POL-i2 COUNT step, zero tries. Committed Nov 12, 2026, before any list or candle was
pulled. Registration: workers/pol_i2/POLI2_COUNT_REGISTRATION.md.

It COUNTS qualifying overnight gaps and the cost at the entry hour. For a gap morning it uses
the hourly closes at 22:00 ET the evening before and at 06:00 and 07:00 ET, and the volume of
the seven days before. It scores no trade, reads no price after 07:00 ET of that morning for
that gap, and never reads a result field.

Usage: python3 count_gaps.py <markets.json> <folder of the candle run> [<more runs>]
"""
import glob, gzip, json, os, sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
FIRST, LAST, SPLIT = date(2026, 9, 13), date(2026, 11, 12), date(2026, 10, 13)
GAP, BAND, STEADY, MIN_VOL, MIN_HALF, COST_BAR, FEE = 0.05, (0.10, 0.90), 0.01, 200.0, 40, 0.05, 0.07


def price(side):
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if v > 1.0 else v
    return None


def walk(node, found, hint=None):
    if isinstance(node, dict):
        tk = node.get("market_ticker") or node.get("ticker") or hint
        c = node.get("candlesticks")
        if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0]:
            if tk:
                found.setdefault(tk, []).extend(c)
        for v in node.values():
            walk(v, found, tk)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, hint)


def et(d, hour):
    return int(datetime(d.year, d.month, d.day, hour, tzinfo=ET).timestamp())


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else None


def main():
    markets = json.load(open(sys.argv[1]))
    cand = {}
    for run in sys.argv[2:]:
        for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
            try:
                walk(json.load(gzip.open(f, "rt")), cand)
            except (ValueError, OSError):
                continue
    days = [FIRST + timedelta(days=i) for i in range((LAST - FIRST).days + 1)]
    step = [0, 0, 0, 0, 0, 0]          # market-mornings alive, then passing conditions 1 to 5 in turn
    gaps, two_sided_markets = [], 0
    for m in markets:
        q, vol = {}, []
        for c in cand.get(m["ticker"], []):
            t = int(c["end_period_ts"])
            b, a = price(c.get("yes_bid")), price(c.get("yes_ask"))
            if b is not None and a is not None and 0 < b < a < 1:
                q[t] = (b, a)
            try:
                v = float(c.get("volume_fp", c.get("volume", 0)) or 0)
            except (TypeError, ValueError):
                v = 0.0
            vol.append((t, v))
        two_sided_markets += 1 if q else 0
        vol.sort()
        for d in days:
            t22, t06, t07 = et(d - timedelta(days=1), 22), et(d, 6), et(d, 7)
            if not (m["open_ts"] <= t22 and m["close_ts"] > t07):
                continue
            step[0] += 1
            if not (t22 in q and t06 in q and t07 in q):
                continue
            step[1] += 1
            move = (q[t07][0] + q[t07][1]) / 2 - (q[t22][0] + q[t22][1]) / 2
            if abs(move) < GAP - 1e-9:
                continue
            step[2] += 1
            up = move > 0
            ask07, bid07 = (q[t07][1], q[t07][0]) if up else (1 - q[t07][0], 1 - q[t07][1])
            ask06 = q[t06][1] if up else 1 - q[t06][0]
            if not (BAND[0] - 1e-9 <= ask07 <= BAND[1] + 1e-9 and abs(ask07 - ask06) <= STEADY + 1e-9):
                continue
            step[3] += 1
            if sum(v for t, v in vol if t22 - 7 * 86400 < t <= t22) < MIN_VOL:
                continue
            step[4] += 1
            if m["close_ts"] < t07 + 86400:
                continue
            step[5] += 1
            gaps.append({"market": m["ticker"], "series": m["series"], "day": d, "half": 1 if d < SPLIT else 2,
                         "spread": ask07 - bid07, "trip": (ask07 - bid07) + 2 * FEE * ask07 * (1 - ask07), "size": abs(move)})
    print("candle freshness measured on Bitcoin 15 minute only, not on politics; hourly closes, one instant an hour")
    print(f"markets in the fixed list {len(markets)} | series {len({m['series'] for m in markets})} | markets with any two-sided hourly candle {two_sided_markets}")
    names = ["market-mornings with the market open", "1 two-sided at 22:00, 06:00 and 07:00", "2 gap of 5c or more", "3 ask in 10c to 90c and steady for the last hour",
             "4 traded 200 or more in the 7 days before", "5 does not close within 24 hours"]
    for n, s in zip(names, step):
        print(f"  {n}: {s}")
    sm = {1: set(), 2: set()}
    for g in gaps:
        sm[g["half"]].add((g["series"], g["day"]))
    print(f"qualifying gaps {len(gaps)} | first half {sum(1 for g in gaps if g['half'] == 1)} | second half {sum(1 for g in gaps if g['half'] == 2)}"
          f" | distinct markets {len({g['market'] for g in gaps})} | distinct series {len({g['series'] for g in gaps})} | distinct mornings {len({g['day'] for g in gaps})}")
    print(f"independent count, series-mornings with a gap: first half {len(sm[1])} | second half {len(sm[2])}")
    f = lambda x: "n/a" if x is None else f"{100 * x:.1f}c"
    trip = med([g["trip"] for g in gaps])
    print(f"at the entry hour: median spread {f(med([g['spread'] for g in gaps]))} | median round trip {f(trip)} | median gap size {f(med([g['size'] for g in gaps]))}")
    if min(len(sm[1]), len(sm[2])) < MIN_HALF:
        print(f"VERDICT: CLOSED, not enough to test (fewer than {MIN_HALF} series-mornings with a qualifying gap in a half)")
    elif trip is not None and trip > COST_BAR:
        print(f"VERDICT: CLOSED on cost (median round trip at the entry hour {f(trip)}, above 5c)")
    else:
        print("VERDICT: the count survives both kill lines. Nothing is scored here; a scored test needs its own registration and the Head's go.")


if __name__ == "__main__":
    main()
