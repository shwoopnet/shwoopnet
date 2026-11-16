#!/usr/bin/env python3
"""POOL1 fixture, BUILD 2: six invented stock perps over 7 invented trading days (all EST), 1 minute candles 13:00 to 21:00 UTC, daily funding prints. Invented numbers only (a seeded generator); the JSON is what a second build reads.
Usage: pool1_fixture_second.py <out.json.gz>"""
import gzip, json, math, random, sys, datetime
DAYS = [(2026, 11, 9), (2026, 11, 10), (2026, 11, 11), (2026, 11, 12), (2026, 11, 13), (2026, 11, 16), (2026, 11, 17)]
NAMES = ["KXAAAPERP", "KXBBBPERP", "KXCCCPERP", "KXDDDPERP", "KXEEEPERP", "KXFFFPERP"]
PRINT_HOUR = {"KXAAAPERP": 20, "KXBBBPERP": 20, "KXCCCPERP": 14, "KXDDDPERP": 20, "KXEEEPERP": 21, "KXFFFPERP": 14}
def U(y, mo, d, hh, mi): return int(datetime.datetime(y, mo, d, hh, mi, tzinfo=datetime.timezone.utc).timestamp())
def build():
    rng = random.Random(20261116); data, fund = {}, {}
    for k, n in enumerate(NAMES):
        mid = 100.0 + 20 * k; s = {}; f = {}
        for (y, mo, d) in DAYS:
            mid *= math.exp(rng.gauss(0, 0.004))          # an overnight gap
            for mi in range(0, 481):
                t = U(y, mo, d, 13, 0) + 60 * mi
                mid *= math.exp(rng.gauss(0, 0.0007)); sp = mid * rng.choice([0.00005, 0.0001, 0.0002])
                if rng.random() < 0.01: s[t] = [round(mid + sp, 4), round(mid - sp, 4)]          # an unusable (crossed) candle now and then
                elif rng.random() < 0.01: continue          # a missing candle
                else: s[t] = [round(mid - sp, 4), round(mid + sp, 4)]
            f[U(y, mo, d, PRINT_HOUR[n], 0)] = round(rng.gauss(0, 0.0003), 6)
        data[n] = {str(t): v for t, v in s.items()}; fund[n] = {str(t): v for t, v in f.items()}
    return {"data": data, "funding": fund}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
