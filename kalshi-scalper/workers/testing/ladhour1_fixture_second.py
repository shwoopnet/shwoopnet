#!/usr/bin/env python3
"""LADHOUR1 fixture, BUILD 2: four invented hourly series (KXINXU, KXNASDAQ100U, KXWTIH, KXGOLDH) built from the ETHLATE1 fixture generator with different seeds and strike counts, plus tickers outside the four series that the wall must drop.
Usage: ladhour1_fixture_second.py <out.json.gz>"""
import gzip, json, random, sys
import ethlate1_fixture_second as e1
def build():
    markets, candles = {}, {}
    for si, s in enumerate(("KXINXU", "KXNASDAQ100U", "KXWTIH", "KXGOLDH")):
        old = random.Random; seeded = random.Random(20261120 + si)
        J = e1.build_with(seeded, strikes=(5, 6, 4, 3)[si], hours=(16, 16, 8, 6)[si])
        for tk, v in J["markets"].items(): markets[tk.replace("KXETHD-", s + "-", 1)] = v
        for tk, v in J["candles"].items(): candles[tk.replace("KXETHD-", s + "-", 1)] = v
    markets["KXINXUD-1-06-T0"] = {"close_ts": 1793059200 + 86400 * 3 + 6 * 3600, "result": "yes"}; candles["KXINXUD-1-06-T0"] = {}
    markets["KXBTCD-1-06-T0"] = {"close_ts": 1793059200 + 86400 * 3 + 6 * 3600, "result": "yes"}; candles["KXBTCD-1-06-T0"] = {}
    return {"markets": markets, "candles": candles}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
