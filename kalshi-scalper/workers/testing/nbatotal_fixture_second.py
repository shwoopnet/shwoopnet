#!/usr/bin/env python3
"""NBATOTAL fixture, BUILD 2: 20 invented games over 7 UTC days, 3 totals ladders x 4 strikes each (12 rungs), minute candles from O - 9 h - 3840 s to O - 12600 s, invented prices and volumes; unusable and missing candles, a jump inside the M35 guard window in two games, a bad clock in one, early closes.
Usage: nbatotal_fixture_second.py <out.json.gz>"""
import gzip, json, random, sys
def build():
    rng = random.Random(20261117); rungs, candles = [], {}
    base = 1792540800 + 20 * 3600
    for g in range(20):
        O = base + (g // 3) * 86400 + (g % 3) * 4 * 3600 + (1800 if g % 2 else 0); ev = "KXNBATOTAL-26G%02d" % g
        for pi in range(3):
            line = 215 + 6 * pi
            for k in range(4):
                strike = line - 6 + 4 * k; tk = "%s-P%d-T%d" % (ev, pi, strike); p = min(0.95, max(0.05, 0.5 + (line - strike) * 0.03 + rng.uniform(-0.1, 0.1)))
                close = O + rng.choice([3600, 3600, 3600, -12000, -13000]); res = rng.choice(["yes", "no"]) if rng.random() > 0.03 else "void"
                rungs.append({"ticker": tk, "event": ev, "player": "T", "strike": strike, "open_time": O - (70 * 3600 if (g == 8 and k == 2 and pi == 1) else rng.choice([8 * 3600, 20 * 3600, 40 * 3600, 70 * 3600])), "close_time": close, "occ": O + (60 if g == 5 and pi == 0 and k == 0 else 0), "result": res})
                s = {}; mid = p
                for t in range(O - 9 * 3600 - 3840, O - 12600 + 1, 60):
                    mid = min(0.97, max(0.03, mid + rng.gauss(0, 0.007)))
                    if g in (3, 11) and k == 1 and O - 14400 < t <= O - 13800: mid = min(0.97, mid + 0.02)
                    if g in (3, 11) and k == 1 and t == O - 13380: mid = min(0.97, mid + 0.2)          # a jump: the M35 guard
                    if g == 8 and k == 2 and pi == 1 and t == O - 9 * 3600: mid = min(0.97, mid + 0.18)          # an in-play guard at D = 9 h
                    sp = rng.choice([0.01, 0.02, 0.02, 0.04, 0.07]); vol = rng.choice([0, 1, 2, 5, 9]); r = rng.random()
                    if r < 0.03: continue
                    bid, ask = (mid + sp / 2, mid - sp / 2) if r < 0.05 else (mid - sp / 2, mid + sp / 2)
                    s[t] = [round(bid, 4), round(ask, 4), float(vol)]
                candles[tk] = {str(t): v for t, v in s.items()}
    return {"rungs": rungs, "candles": candles}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
