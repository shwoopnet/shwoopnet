#!/usr/bin/env python3
"""Hand case of perplead1_score.py on INVENTED numbers (EXPECTED_perplead1_nov16.md)."""
import os, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import perplead1_score as P
def ev(day, strikes, exit_c, entry=(1999.9, 2000.1)):
    d = {"day": day, "strikes": {"m120": strikes}, "perp": {"m120": entry}}
    if exit_c: d["perp"]["m60"] = exit_c
    return d
A = ev("d1", [(1990, 0.9), (2010, 0.3)], (2001.0, 2001.2)); B = ev("d2", [(1990, 0.6), (2000, 0.4)], (1995.8, 1996.0)); C = ev("d3", [(1990, 0.9), (2010, 0.3)], (2008.0, 2008.2))
D = ev("d4", [(1999, 0.52), (2001, 0.48)], (2000.0, 2000.2)); E = ev("d5", [(1990, 0.9), (2010, 0.8)], (2000.0, 2000.2)); F = ev("d6", [(1990, 0.9), (2010, 0.3)], None)
evs = [A, B, C, D, E, F]
cnt = collections.Counter(); tr = P.score_rule(evs, 4, "m60", "convergence", 24, cnt); s = P.summary(tr)
nets = [round(n, 4) for _, n in tr]
near = lambda a, b, t=1e-3: abs(a - b) < t
ok = [("1 median A 2003.3333, B 1995.0, E none", near(P.implied_median(A["strikes"]["m120"]), 2003.3333, 1e-3) and near(P.implied_median(B["strikes"]["m120"]), 1995.0) and P.implied_median(E["strikes"]["m120"]) is None),
      ("2 gaps +16.667, -25.0, 0.0", near(P.gap_bps(2003.3333, 2000.0), 16.667) and near(P.gap_bps(1995.0, 2000.0), -25.0) and near(P.gap_bps(2000.0, 2000.0), 0.0)),
      ("3 convergence nets -19.5002, -4.4990, +15.4980", len(nets) == 3 and near(nets[0], -19.5002) and near(nets[1], -4.4990) and near(nets[2], 15.4980)),
      ("4 summary n 3, mean -2.8337, PF 0.6458", s["n"] == 3 and near(s["mean"], -2.8337) and near(s["pf"], 0.6458)),
      ("5 counts: no signal 1, under theta 1, exit missing 1", cnt["no signal"] == 1 and cnt["under theta"] == 1 and cnt["exit candle missing"] == 1)]
cf = collections.Counter(); trf = P.score_rule(evs, 4, "m60", "fade", 24, cf); nf = [round(n, 4) for _, n in trf]
ok.append(("6 fade nets -30.5003, -45.4989, -65.5021 and PF 0", len(nf) == 3 and near(nf[0], -30.5003) and near(nf[1], -45.4989) and near(nf[2], -65.5021) and P.summary(trf)["pf"] == 0.0))
m = P.margin_print(s["mean"])
ok.append(("7 margin print: ROM -0.0630, -0.1574, -0.3149 and liquidation 40.5, 13.5, 4.5", near(m[0]["return_on_margin_pct"], -0.0630, 5e-4) and near(m[1]["return_on_margin_pct"], -0.1574, 5e-4) and near(m[2]["return_on_margin_pct"], -0.3149, 5e-4) and near(m[0]["liquidation_distance_pct"], 40.5) and near(m[1]["liquidation_distance_pct"], 13.5) and near(m[2]["liquidation_distance_pct"], 4.5)))
se, va = P.split_dates(["2026-10-%02d" % d for d in range(28, 32)] + ["2026-11-%02d" % d for d in range(1, 16)])
ok.append(("8 split: 19 dates, 9 SEARCH 10 VALIDATE, the 9th is 2026-11-05", len(se) == 9 and len(va) == 10 and max(se) == "2026-11-05"))
cr = collections.Counter(); P.score_rule([A], 4, "m0", "convergence", 24, cr, shift=1)
ok.append(("9 robust shift past the close is not scored", cr["exit after the close (not scored)"] == 1))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
