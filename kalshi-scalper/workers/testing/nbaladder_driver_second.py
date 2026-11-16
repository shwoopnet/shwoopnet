#!/usr/bin/env python3
"""NBALADDER driver, BUILD 2: runs the 624 cells and prints one deterministic line per cell (for the 1e-9 compare). Pure."""
import math
import nbaladder_second as m

def fmt(x):
    if x is None: return "None"
    if isinstance(x, float) and math.isinf(x): return "inf"
    if isinstance(x, float) and math.isnan(x): return "nan"
    return "%.12g" % x if isinstance(x, float) else str(x)

def run(rungs, candles, carried=0):
    cells, cnt, surv = m.search(rungs, candles, carried)
    lines = ["cells %d m_total %d games_dropped_clock %d survivors %d" % (len(cells), m.N_CELLS + carried, cnt.get("games_dropped_clock", 0), len(surv))]
    for k in sorted(cells, key=lambda c: (c[0], c[1], c[2], c[3], c[4])):
        s = cells[k]
        lines.append("D%d|band%.2f|%s|%s|%s | n %d games %d days %d | pf1 %s h1 %s h2 %s pf2 %s | net1 %s weekly5 %s | z %s p %s | marked_n %d marked_pf %s | pass %s" % (
            k[0], k[1], k[2], k[3], k[4], s["n"], s["games"], s["days"], fmt(s["pf1"]), fmt(s["h1"]), fmt(s["h2"]), fmt(s["pf2"]), fmt(s["net1"]), fmt(s["weekly5"]), fmt(s["z"]), fmt(s["p"]), s["marked_n"], fmt(s["marked_pf"]), k in surv))
    return lines
