#!/usr/bin/env python3
"""Checks ladhour1_load.py's internals on MADE-UP rows against EXPECTED_ladhour1_nov16.md. No real file read."""
import os, sys, collections, calendar, time, json, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ladhour1_load as L
def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
ok = []
try: L.dirs(); ok.append(("0 window not set refuses", False))
except SystemExit as e: ok.append(("0 window not set refuses", "window not set" in str(e)))
L.START = ts("2026-11-20T00:00:00Z"); L.CUT = ts("2026-11-21T00:00:00Z")
C = ts("2026-11-20T14:00:00Z"); TK = "KXINXU-26NOV2014-T7000.99"; ct = "2026-11-20T14:00:00Z"
class BTrap(dict):
    def __getitem__(self, k):
        if k != "ticker": raise AssertionError("poisoned column read on a wrong-series row: %r" % (k,))
        return super().__getitem__(k)
class Trap(dict):
    def __getitem__(self, k):
        if k not in ("close_time", "ticker"): raise AssertionError("read %r on a cut row" % (k,))
        return super().__getitem__(k)
def row(sec, b, a, tk=TK, close=ct): return {"t_recv_ms": str(int((C - sec) * 1000)), "ticker": tk, "close_time": close, "status": "active", "yes_bid": "%.2f" % b, "yes_ask": "%.2f" % a}
rows = [row(148, .28, .32), row(130, .30, .34), row(118, .31, .33), row(70, .32, .34), row(50, .35, .37), row(5, .40, .42), row(-3, .90, .92),
        BTrap(ticker="KXINX-26NOV2014-T7000.99"), Trap(close_time="2026-11-21T00:00:00Z", ticker="KXINXU-26NOV2100-T1.99")]
cnt = collections.Counter(); lad = L.ladder_rows(rows, cnt)
res = {"KXINXU": L.result_rows([{"ticker": TK, "close_time": ct, "result": "yes"}, {"ticker": "KXWTIH-26NOV2014-T60.99", "close_time": ct, "result": "no"}], "KXINXU", cnt)}
data = L.assemble(lad, res, cnt); m = data["KXINXU"][0]
ok += [("1 one market kept, result yes", len(data["KXINXU"]) == 1 and m["result"] == "yes" and m["close"] == C and data["KXWTIH"] == []),
       ("2 candles", m["candles"] == [(C - 120, .30, .34, None, 0, 0), (C - 60, .32, .34, None, 0, 0), (C, .40, .42, None, 0, 0)]),
       ("3 counts", cnt["ladder row dropped by the cut or no close"] == 1 and cnt["ticker outside the wall (dropped)"] == 1 and cnt["candle after close (dropped)"] == 1 and cnt["result ticker outside the wall (dropped)"] == 1 and res["KXINXU"] == {TK: "yes"}),
       ("4 KXINX- is outside the wall and the dirs run START to CUT date", L.series_of("KXINX-26NOV") is None and L.series_of("KXNASDAQ100U-X") == "KXNASDAQ100U" and L.dirs() == ["2026-11-20", "2026-11-21"])]
try: L.refuse_unless_allowed("2026-11-21T2000Z_1"); ok.append(("5 refuses without an allow line", False))
except SystemExit: ok.append(("5 refuses without an allow line", True))
def refused(p, s):
    try: L.check_run_name(p, s); return False
    except SystemExit: return True
ok.append(("6 only the series' own run folder is accepted", refused("/x/LADHOUR1_RESULTS_KXWTIH/s1", "KXINXU") and refused("/x/ETHD_RESULTS2/s1", "KXINXU") and L.check_run_name("/x/LADHOUR1_RESULTS_KXINXU/2026-11-21T2000Z_1", "KXINXU") == "2026-11-21T2000Z_1"))
d = tempfile.mkdtemp(); os.makedirs(d + "/quotes/2026-11-20"); os.makedirs(d + "/LADHOUR1_RESULTS_KXINXU/s1")
json.dump({"rows": [{"status": 200, "truncated": True, "file": "a"}, {"status": 500, "file": "b"}]}, open(d + "/LADHOUR1_RESULTS_KXINXU/s1/manifest.json", "w"))
L.refuse_unless_allowed = lambda run_name: None
try: L.load(d, {"KXINXU": d + "/LADHOUR1_RESULTS_KXINXU/s1"}); ok.append(("7 dropped manifest rows void the run", False))
except SystemExit as e: ok.append(("7 dropped manifest rows void the run", "RUN VOID: 2 manifest rows" in str(e)))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
