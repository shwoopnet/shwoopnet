#!/usr/bin/env python3
"""Extras driver (Desk C's rulings): per cell the margin report on TT trades (mean_pct_of_margin, stop_beyond_liquidation at 10, 25, 50 percent of page max) and adverse selection per fill window N in 2, 5 (filled_n, filled_mean_bps, unfilled_n, unfilled_mean_bps). Stress is the TS column of the main lines. Usage: perpscalp2_driver2_second.py fixture.json"""
import json, sys
import perpscalp2_second as m
fx = json.load(open(sys.argv[1]))
data = {n: {int(t): tuple(c) for t, c in s.items()} for n, s in fx["data"].items()}
fund = {n: {int(t): r for t, r in f.items()} for n, f in fx["funding"].items()}
lm = {n: m.LMAX.get(n, 10.0) for n in data}   # fixture names are not on the page list: 10.0
for cell in m.cells():
    tr, _ = m.run_cell(data, fund, fx["ticks"], cell, "TT")
    print(json.dumps({"cell": [cell[0][0], cell[1], cell[2], cell[3]], "margin": m.margin(tr, lm), "adverse": {str(N): m.adverse(data, fund, fx["ticks"], cell, N) for N in (2, 5)}}, sort_keys=True, default=str))
