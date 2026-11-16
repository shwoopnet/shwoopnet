#!/usr/bin/env python3
"""Driver for perpscalp2_second.py on a fixture file: prints one JSON line per (cell, column) with n, days, pf, h1, h2, z, mean_bps, spanning_funding, counts. Usage: perpscalp2_driver_second.py fixture.json"""
import json, sys
import perpscalp2_second as m
fx = json.load(open(sys.argv[1]))
data = {n: {int(t): tuple(c) for t, c in s.items()} for n, s in fx["data"].items()}
fund = {n: {int(t): r for t, r in f.items()} for n, f in fx["funding"].items()}
for cell in m.cells():
    for col in m.COLUMNS:
        tr, cnt = m.run_cell(data, fund, fx["ticks"], cell, col); st = m.stats(tr)
        print(json.dumps({"cell": [cell[0][0], cell[1], cell[2], cell[3]], "col": col, **st, **cnt}, sort_keys=True, default=str))
