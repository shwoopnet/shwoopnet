#!/usr/bin/env python3
"""PERPSLANE4 fixture (first build): 8 invented perps (6 stock-like, KXGOLDPERP, KXUS500PERP) over ET weekdays 2026-10-26 to 2026-11-18 (EDT then EST, DST ends Nov 1), minute candles 09:20 to 17:05 ET, a daily print at 16:00 ET (DST aware), underlyings for the gap rules, a few missing and crossed candles, a name with no prints, a name with a shifted print time. Invented numbers only.
Usage: lane4_fixture_second.py <out.json.gz>"""
import calendar, gzip, json, math, random, sys
import engine1_perps_second as p
NAMES = ["KXAAAPERP", "KXBBBPERP", "KXCCCPERP", "KXDDDPERP", "KXEEEPERP", "KXFFFPERP", "KXGOLDPERP", "KXUS500PERP"]
def build():
    rng = random.Random(20261116); data, funding, under = {n: {} for n in NAMES}, {n: {} for n in NAMES}, {n: {} for n in NAMES}
    first = calendar.timegm((2026, 10, 26, 0, 0, 0)) // 86400 + 0
    L0 = p.et_local_day(calendar.timegm((2026, 10, 26, 12, 0, 0)))
    days = [L0 + i for i in range(24) if (L0 + i + 3) % 7 < 5]
    for ni, n in enumerate(NAMES):
        mid = 100.0 + 25 * ni; prev_close = None
        for k, L in enumerate(days):
            et0 = p.day_start_of_local(L); open_t = et0 + 9 * 3600 + 31 * 60
            gap = rng.gauss(0, 0.004); mid *= math.exp(gap)
            u_open = (prev_close or mid) * math.exp(gap + rng.gauss(0, 0.001)); under[n][str(L)] = [round(u_open, 4), round(prev_close or mid, 4)]
            for mi in range(0, 7 * 60 + 46):
                t = et0 + 9 * 3600 + 20 * 60 + 60 * mi + 60          # candle ends 09:21 ET ... 17:06 ET
                mid *= math.exp(rng.gauss(0, 0.0006)); sp = mid * rng.choice([0.00005, 0.0001, 0.0002]); r = rng.random()
                if r < 0.01: continue
                bid, ask = (mid + sp, mid - sp) if r < 0.02 else (mid - sp, mid + sp)
                data[n][str(t)] = [round(bid, 4), round(ask, 4)]
            prev_close = mid
            if n != "KXFFFPERP":
                tp = et0 + 16 * 3600 + (1800 if n == "KXEEEPERP" else 0)
                funding[n][str(tp)] = round(rng.gauss(0, 0.0003), 6)
    return {"data": data, "funding": funding, "under": under}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
