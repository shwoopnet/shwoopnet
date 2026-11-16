#!/usr/bin/env python3
"""Hand case of ethlate1_run.py on INVENTED markets (EXPECTED_ethlate1_run_nov16.md). Needs the four pinned engine files in a folder (ENGINE_DIR env is NOT used; pass the path as argv[1])."""
import os, sys, time, calendar, hashlib
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
# 8 the VALIDATE and BH path (EXPECTED_ethlate1_run_nov16.md, Test 8; figures from hand_validate_case.py)
R.PINS["engine1_core"] = hashlib.sha256(open(os.path.join(eng, "engine1_core.py"), "rb").read()).hexdigest()
WIN = {"A_S": [3, 7, 2, 8, 4, 6, 5, 7, 3, 6, 4, 8], "A_V": [3, 7, 2, 8, 4, 6, 5, 7, 3, 6, 4, 8], "B_S": [6, 7, 5, 6, 7, 5, 6, 7, 5, 6, 7, 5], "B_V": [9, 9, 9, 9, 9, 8, 1, 1, 0, 0, 1, 1]}
mk8 = []
for ph, d0 in (("S", 0), ("V", 12)):
    for d in range(12):
        for cellname, bid, ask, side in (("A", 0.28, 0.30, "yes"), ("B", 0.58, 0.60, "no")):
            w = WIN[cellname + "_" + ph][d]
            for j in range(9):
                close = base + (d0 + d) * 86400 + 14 * 3600 + (j if cellname == "A" else 9 + j) * 3600
                mk8.append({"series": "KXETHD", "ticker": "KXETHD-%s%s%02d%d" % (cellname, ph, d, j), "close": close, "result": side if j < w else ("no" if side == "yes" else "yes"),
                            "candles": [(close - 120, bid, ask, None, 0, 0), (close - 60, bid + 0.01, ask + 0.01, None, 0, 0)]})
S.LAST_SEARCH["ETHD"] = "2026-11-12"
big = R.run({"KXETHD": mk8}, m_total=6290756, engine_dir=eng); small = R.run({"KXETHD": mk8}, m_total=2, engine_dir=eng)
ok.append(("8a search cells 8, passes 4, validate bar passes 2", big["search_cells_scored"] == 8 and big["search_passes"] == 4 and big["validate_bar_passes"] == 2))
ok.append(("8b BH at m_total keeps none", big["survivors"] == []))
ok.append(("8c the same p-values at m = 2 keep both A cells, not B", len(small["survivors"]) == 2 and all(s["cell"][1] == 6 for s in small["survivors"]) and all(abs(s["pf_2c"] - 2.7667) < 5e-4 for s in small["survivors"])))
# 9 events < 40: nine strikes of one hourly event share one close (EXPECTED_ethlate1_run_nov16.md, Amendment 3)
mk9 = []
for m in mk8:
    d = (m["close"] - base) // 86400; q = dict(m); q["close"] = base + d * 86400 + 14 * 3600 + (0 if m["ticker"].startswith("KXETHD-A") else 3600)
    q["candles"] = [(q["close"] - 120, m["candles"][0][1], m["candles"][0][2], None, 0, 0), (q["close"] - 60, m["candles"][1][1], m["candles"][1][2], None, 0, 0)]; mk9.append(q)
r9 = R.run({"KXETHD": mk9}, m_total=2, engine_dir=eng)
ok.append(("9 same strikes in 12 events a phase: n 108 and PF pass, events 12 < 40, so nothing passes even at m = 2", r9["search_cells_scored"] >= 4 and r9["search_passes"] == 0 and r9["validate_bar_passes"] == 0 and r9["survivors"] == []))
ok.append(("10 test 8 survivors carry their events (108)", all(s["events"] == 108 for s in small["survivors"])))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
