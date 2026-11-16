#!/usr/bin/env python3
"""ETHLATE1 driver, BUILD 2: runs the 96 rules and prints one deterministic line per rule. Pure."""
import math
import ethlate1_second as m
from nbaladder_driver_second import fmt

def run(markets, candles, mm=m.M_TOTAL):
    r = m.run(markets, candles, mm)
    lines = ["header m %d entries %d search_n %d validate_n %d last_search_day %s cuts %s search_passes %d validate_passes %d survivors %d" % (r["m"], r["entries"], r["search_n"], r["validate_n"], r["last_search_day"], r["cuts"], len(r["search_passes"]), len(r["validate_passes"]), len(r["survivors"]))]
    for key in sorted(r["rules"]):
        s, v = r["rules"][key]
        f = lambda t: "n %d events %d days %d per_day %s pf2 %s h1 %s h2 %s pf1 %s z %s" % (t["n"], t["events"], t["days"], fmt(t["per_day"]), fmt(t["pf2"]), fmt(t["h1"]), fmt(t["h2"]), fmt(t["pf1"]), fmt(t["z"]))
        lines.append("band%d|%s|%s | S %s | V %s | search %s validate %s survivor %s" % (key[0], key[1], key[2], f(s), f(v), key in r["search_passes"], key in r["validate_passes"], key in r["survivors"]))
    return lines
