#!/usr/bin/env python3
"""Hand case of ladhour1_run.py on INVENTED markets (EXPECTED_ladhour1_nov16.md). Pass the folder of the four pinned engine files as argv[1]."""
import os, sys, time, calendar
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ladhour1_run as R
eng = sys.argv[1]
base = calendar.timegm(time.strptime("2026-11-01", "%Y-%m-%d")); mk = []
for i in range(120):
    day, k = divmod(i, 10); close = base + day * 86400 + 14 * 3600 + k * 3600
    win = int(((i + 1) * 47) // 120) > int((i * 47) // 120)
    mk.append({"series": "KXINXU", "ticker": "KXINXU-T%03d" % i, "close": close, "result": "yes" if win else "no", "candles": [(close - 120, 0.28, 0.30, None, 0, 0), (close - 60, 0.29, 0.31, None, 0, 0)]})
K, N, S, D = R.import_engine(eng)
ok = []
try: R.run({"KXINXU": mk}, engine_dir=eng); ok.append(("0 refuses while m_total is not set", False))
except SystemExit as e: ok.append(("0 refuses while m_total is not set", "m_total is not set" in str(e)))
try: R.run({"KXINXU": mk}, m_total=1000, engine_dir=eng); ok.append(("1 refuses without a dated constant for INXU", False))
except SystemExit as e: ok.append(("1 refuses without a dated constant for INXU", "no dated constant for INXU" in str(e)))
S.LAST_SEARCH["INXU"] = "2026-12-31"
rep = R.run({"KXINXU": mk}, m_total=1000, engine_dir=eng)
ok += [("2 header counts 384 cells selected, 4 H/M60 cells scored, series line", rep["cells_selected"] == 384 and rep["search_cells_scored"] == 4 and rep["series"]["KXINXU"]["search_markets"] == 120 and rep["series"]["KXWTIH"] == {"markets": 0}),
       ("3 events rule and C8 mean no pass even though the 1c PF is 1.337", rep["search_passes"] == 0 and rep["survivors"] == [])]
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
