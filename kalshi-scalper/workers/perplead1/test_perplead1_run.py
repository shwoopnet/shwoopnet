#!/usr/bin/env python3
"""Hand case of perplead1_run.py on INVENTED events (EXPECTED_perplead1_load_nov16.md, adapter part)."""
import os, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import perplead1_run as R
days = ["2026-10-%02d" % d for d in range(28, 32)] + ["2026-11-%02d" % d for d in range(1, 16)]
def ev(day, bid=1.9999, ask=2.0001): return {"day": day, "strikes": {"m120": [(1990, 0.9), (2010, 0.3)]}, "perp": {"m120": (bid, ask), "m60": (2.0011, 2.0013), "m0": (2.0011, 2.0013)}}
events = [ev(d) for d in days] + [ev("2026-10-29", 0.9999, 1.0001)]
ok = []
try: R.run(events); ok.append(("1 refuses without m_carried", False))
except SystemExit as e: ok.append(("1 refuses without m_carried", "m_carried is not set" in str(e)))
rep = R.run(events, m_carried=6290660)
near = lambda a, b, t=1e-2: abs(a - b) < t
cv = rep["rules"][(4, "m60", "convergence")]; fd = rep["rules"][(4, "m0", "fade")]
ok += [("2 scale 1000 from 2026-10-28, m_total 6290680", rep["scale"] == 1000.0 and rep["scale_day"] == "2026-10-28" and rep["m_total"] == 6290680),
       ("3 one scale drop, 9 SEARCH events and 10 VALIDATE events", rep["counts"]["scale drop (gap over 500 bps)"] == 1 and rep["search_events"] == 9 and rep["validate_events"] == 10 and rep["search_dates"] == 9 and rep["validate_dates"] == 10),
       ("4 20 rules, each 9 SEARCH trades", len(rep["rules"]) == 20 and all(r["search"]["n"] == 9 for r in rep["rules"].values())),
       ("5 convergence net -19.0002, PF 0, maker -5.0002; fade net -31.0004", near(cv["search"]["mean"], -19.0002) and cv["search"]["pf"] == 0.0 and near(cv["gross_edge_bps"], 4.9998) and near(fd["search"]["mean"], -31.0004)),
       ("6 next-minute column n 0, no passes, no survivors", cv["robust_next_minute"]["n"] == 0 and rep["search_passes"] == 0 and rep["validate_passes"] == 0 and rep["survivors"] == [])]
try: R.run([ev(d, 3.9998, 4.0002) for d in days], m_carried=1); ok.append(("7 scale not within 5% of a power of ten refuses", False))
except SystemExit as e: ok.append(("7 scale not within 5% of a power of ten refuses", "not within 5%" in str(e)))
import hashlib
rep["quote_data"] = "e78f54fa"; rep["runs"] = ["PERPETH1M_W8/s1", "PERPETH1M_W11/s2"]
ok.append(("8 header names the quote-data commit and both runs", R.header(rep).startswith("quote-data e78f54fa | runs PERPETH1M_W8/s1, PERPETH1M_W11/s2 | m_total 6290680")))
orig = R.SCORE_SHA; R.SCORE_SHA = "0" * 64
try: R._pinned_scorer(); ok.append(("9 a changed scorer is refused", False))
except SystemExit as e: ok.append(("9 a changed scorer is refused", "REFUSED: perplead1_score.py" in str(e)))
R.SCORE_SHA = orig
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
