#!/usr/bin/env python3
"""Extras driver: per cell, TT stress PF (taker legs +2 bps each), margin report on TT trades (x 10, 25, 50 percent of page max), and per maker column the adverse-selection comparison. Usage: perpscalp2_driver2_second.py fixture.json"""
import json, sys
import perpscalp2_second as m
fx = json.load(open(sys.argv[1]))
data = {n: {int(t): tuple(c) for t, c in s.items()} for n, s in fx["data"].items()}
fund = {n: {int(t): r for t, r in f.items()} for n, f in fx["funding"].items()}
lm = {n: m.LMAX.get(n, 10.0) for n in data}   # fixture names are not in the page list: 10.0 stands in
for cell in m.cells():
    tr, _ = m.run_cell(data, fund, fx["ticks"], cell, "TT")
    sv = [m.stress_net(t) for t in sorted(tr, key=lambda t: (t["e"], t["side"]))]
    k = len(sv); h = k // 2
    print(json.dumps({"cell": [cell[0][0], cell[1], cell[2], cell[3]], "kind": "stress_margin", "stress_pf": m.pf(sv), "stress_h1": m.pf(sv[:h]), "stress_h2": m.pf(sv[h:]), "margin": {str(x): v for x, v in m.margin(tr, lm).items()}}, sort_keys=True, default=str))
    for col in ("MT2", "MT5", "MM2", "MM5"):
        print(json.dumps({"cell": [cell[0][0], cell[1], cell[2], cell[3]], "col": col, "kind": "adverse", **m.adverse(data, fund, fx["ticks"], cell, col)}, sort_keys=True, default=str))
