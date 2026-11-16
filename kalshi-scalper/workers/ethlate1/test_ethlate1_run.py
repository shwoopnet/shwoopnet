#!/usr/bin/env python3
"""Hand case of ethlate1_run.py on INVENTED markets (EXPECTED_ethlate1_run_nov16.md). Needs the four pinned engine files in a folder (ENGINE_DIR env is NOT used; pass the path as argv[1])."""
import os, sys, time, calendar
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ethlate1_run as R
eng = sys.argv[1]
base = calendar.timegm(time.strptime("2026-11-01", "%Y-%m-%d"))
mk = []; wins_placed = 0
for i in range(120):
    day, k = divmod(i, 10); close = base + day * 86400 + 14 * 3600 + k * 3600 + 0
    win = int(((i + 1) * 47) // 120) > int((i * 47) // 120)          # spreads 47 wins evenly through the 120
    mk.append({"series": "KXETHD", "ticker": "KXETHD-T%03d" % i, "close": close, "result": "yes" if win else "no",
               "candles": [(close - 120, 0.28, 0.30, None, 0, 0), (close - 60, 0.29, 0.31, None, 0, 0)]})
assert sum(1 for m in mk if m["result"] == "yes") == 47
K, N, S, D = R.import_engine(eng)
S.LAST_SEARCH["ETHD"] = "2026-12-31"       # invented constant, after the last date: every market is SEARCH
rep = R.run({"KXETHD": mk}, engine_dir=eng)
c = rep["cells"]; h1 = c[(120, 6, "cheap", None, "H")]; h2 = c[(120, 6, "cheap", ("spread", "low"), "H")]; m1 = c[(120, 6, "cheap", None, "M60")]
ok = [("1 header first line", R.header(rep).startswith("m_total 6290756 | cells selected 96 | primary haircut 2c (C8)")),
      ("2 cells scored 4, n 120 each", rep["search_cells_scored"] == 4 and h1["n"] == 120 and h2["n"] == 120 and m1["n"] == 120),
      ("3 H cells PF 1c 1.337 and 2c 1.272", abs(h1["pf_1c"] - 1.3372) < 5e-4 and abs(h1["pf_2c"] - 1.2723) < 5e-4 and abs(h2["pf_2c"] - 1.2723) < 5e-4),
      ("4 M60 cells PF 0", m1["pf_1c"] == 0.0 and m1["pf_2c"] == 0.0),
      ("5 C8: the driver's 1c gate would pass the H cells, the adapter passes none", D.passes(*[D.score_group([(m, {"side": "yes", "ask": 0.30, "entry_end": m["close"] - 120, "whole_cent": True}) for m in mk], "H")[0][h] for h in (0.01, 0.02)]) and rep["search_passes"] == 0),
      ("6 no VALIDATE markets, no survivors", rep["validate_markets"] == 0 and rep["survivors"] == [])]
R.PINS["engine1_core"] = "0" * 64
try: R.import_engine(eng); ok.append(("7 a changed engine file is refused", False))
except SystemExit as e: ok.append(("7 a changed engine file is refused", "REFUSED" in str(e)))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
