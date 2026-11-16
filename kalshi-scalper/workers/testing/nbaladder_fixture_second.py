#!/usr/bin/env python3
"""NBALADDER fixture, BUILD 2: 24 invented games over 8 UTC days, 3 players x 5 rungs each, minute candles from O - 9180 to O - 600 (plus the mark candle), invented prices and volumes; a few unusable and missing candles, some rungs that close early, one game with a bad clock.
Usage: nbaladder_fixture_second.py <out.json.gz>"""
import gzip, json, random, sys
def build():
    rng = random.Random(20261116); rungs, candles = [], {}
    base = 1792540800 + 30 * 3600
    for g in range(24):
        O = base + (g // 3) * 86400 + (g % 3) * 3 * 3600 + (1800 if g % 2 else 0); ev = "KXNBAPTS-26G%02d" % g; occ_bad = (g == 7)
        for pi in range(3):
            player = "P%d" % pi; line = 12 + 6 * pi
            for k in range(5):
                strike = line - 10 + 5 * k; tk = "%s-%s-%d" % (ev, player, strike); p = min(0.95, max(0.05, 0.5 + (line - strike) * 0.04 + rng.uniform(-0.1, 0.1)))
                close = O + rng.choice([3600, 3600, 3600, -420, -540]); res = rng.choice(["yes", "no"]) if rng.random() > 0.03 else "void"
                rungs.append({"ticker": tk, "event": ev, "player": player, "strike": strike, "open_time": O - rng.choice([3 * 3600, 9 * 3600, 26 * 3600]), "close_time": close, "occ": O + (60 if occ_bad and pi == 0 and k == 0 else 0), "result": res})
                s = {}; mid = p
                for t in range(O - 9180, O - 540, 60):
                    mid = min(0.97, max(0.03, mid + rng.gauss(0, 0.006))); sp = rng.choice([0.01, 0.02, 0.02, 0.04, 0.07]); vol = rng.choice([0, 1, 2, 5, 9]); r = rng.random()
                    if r < 0.03: continue
                    b, a = (mid + sp / 2, mid - sp / 2) if r < 0.05 else (mid - sp / 2, mid + sp / 2)
                    s[t] = [round(b, 4), round(a, 4), float(vol)]
                candles[tk] = {str(t): v for t, v in s.items()}
    return {"rungs": rungs, "candles": candles}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
