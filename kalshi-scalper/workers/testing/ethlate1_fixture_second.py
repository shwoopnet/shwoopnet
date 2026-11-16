#!/usr/bin/env python3
"""ETHLATE1 fixture, BUILD 2: invented hourly Ethereum ladders: 19 UTC days, 16 hourly closes a day, 6 strikes each, a look candle at close - 120 and a mark candle at close - 60 (some missing, some crossed), invented quotes, results and a few voids.
Usage: ethlate1_fixture_second.py <out.json.gz>"""
import gzip, json, random, sys
def build(): return build_with(random.Random(20261116), 6, 16)
def build_with(rng, strikes=6, hours=16):
    markets, candles = {}, {}
    day0 = 1793059200          # 2026-10-27T00:00Z
    for d in range(1, 20):
        for hh in range(6, 6 + hours):
            close = day0 + d * 86400 + hh * 3600
            for k in range(strikes):
                tk = "KXETHD-%d-%02d-T%d" % (d, hh, k); p = min(0.9, max(0.04, rng.betavariate(0.8, 1.3))); sp = rng.choice([0.01, 0.02, 0.02, 0.03, 0.05, 0.08])
                r = rng.random(); res = "yes" if rng.random() < p else "no"
                if rng.random() < 0.02: res = "void"
                markets[tk] = {"close_ts": close, "result": res}
                bid, ask = round(max(0.01, p - sp / 2), 4), round(min(0.99, p + sp / 2), 4)
                c = {}
                if r > 0.04: c[str(close - 120)] = [ask, bid] if r < 0.06 else [bid, ask]
                if rng.random() > 0.15:
                    q = min(0.97, max(0.03, p + rng.gauss(0, 0.04))); c[str(close - 60)] = [round(q - sp / 2, 4), round(q + sp / 2, 4)]
                if rng.random() < 0.1: c[str(close - 61)] = [bid, ask]
                candles[tk] = c
    return {"markets": markets, "candles": candles}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
