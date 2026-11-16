#!/usr/bin/env python3
"""Checks perplead1_load.py's internals on MADE-UP rows against EXPECTED_perplead1_load_nov16.md. No real file read."""
import os, sys, collections, json, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import perplead1_load as L
C = 1794319200; S1 = "KXETHD-26NOV1014-T1990.99"; S2 = "KXETHD-26NOV1014-T2010.99"; ct = "2026-11-10T14:00:00Z"
class BTrap(dict):
    def __getitem__(self, k):
        if k != "ticker": raise AssertionError("poisoned column read on a wrong-series row: %r" % (k,))
        return super().__getitem__(k)
def row(tk, sec, b, a, k, status="active", close=ct): return {"t_recv_ms": str(int((C - sec) * 1000)), "ticker": tk, "close_time": close, "status": status, "yes_bid": str(b), "yes_ask": str(a), "strike": str(k)}
rows = [row(S1, 130, .88, .92, 1990.99), row(S2, 125, .28, .32, 2010.99), row(S1, 118, .50, .54, 1990.99), row(S1, 110, .58, .62, 1990.99), row(S2, 30, .18, .22, 2010.99),
        BTrap(ticker="KXBTCD-26NOV1014-T80000.99"), row(S1, 100, .5, .6, 1990.99, close="2026-11-16T00:00:00Z"), row(S1, 90, .5, .6, 1990.99, status="closed"), row(S1, 80, 0, .6, 1990.99)]
cnt = collections.Counter(); lad = L.ladder_rows(rows, cnt)
body1 = {"candlesticks": [{"end_period_ts": C - 120, "bid": {"close": "1999.9"}, "ask": {"close": "2000.1"}}, {"end_period_ts": C - 60, "bid": {"close": 2001.0}, "ask": {"close": 2001.2}},
                          {"end_period_ts": C - 30, "bid": {"close": 2001.0}, "ask": {"close": 2000.0}}, {"end_period_ts": C - 20, "ask": {"close": 2000.0}}]}
perp = L.perp_candles(body1, {"path": "/markets/KXETHPERP/candlesticks", "params": {"start_ts": C - 86400}}, cnt)
L.perp_candles({"candlesticks": []}, {"path": "/markets/KXBTCPERP/candlesticks", "params": {"start_ts": C}}, cnt)
L.perp_candles({"candlesticks": []}, {"path": "/markets/KXETHPERP/candlesticks", "params": {"start_ts": 1793000000}}, cnt)
def close_to(a, b): return len(a) == len(b) and all(abs(x[0] - y[0]) < 1e-9 and abs(x[1] - y[1]) < 1e-9 for x, y in zip(sorted(a), sorted(b)))
ev = L.assemble(lad, perp, cnt)
e = ev[0]
ok = [("1 one event, close C", len(ev) == 1 and e["close"] == C and e["day"] == "2026-11-10"),
      ("2 strikes m120, m60 (last row of the minute), m0", close_to(e["strikes"]["m120"], [(1990.99, 0.90), (2010.99, 0.30)]) and close_to(e["strikes"]["m60"], [(1990.99, 0.60)]) and close_to(e["strikes"]["m0"], [(2010.99, 0.20)])),
      ("3 perp m120 and m60, none at m0", e["perp"] == {"m120": (1999.9, 2000.1), "m60": (2001.0, 2001.2)}),
      ("4 counts", cnt["ticker outside the wall (dropped)"] == 1 and cnt["ladder row dropped by the cut or no close"] == 1 and cnt["ladder row not active (dropped)"] == 1 and cnt["ladder row not two sided (dropped)"] == 1
        and cnt["perp request outside the wall (dropped)"] == 1 and cnt["perp request outside the window (dropped)"] == 1 and cnt["perp candle not two sided (dropped)"] == 1 and cnt["perp candle unreadable (dropped)"] == 1)]
try: L.refuse_unless_allowed("2026-11-17T0000Z_1"); ok.append(("5 refuses without an allow line", False))
except SystemExit: ok.append(("5 refuses without an allow line", True))
def refused(p):
    try: L.check_run_name(p); return False
    except SystemExit: return True
ok.append(("6 run binding", refused("/x/NOT_PERP/s1") and refused("/x/PERPETH1M/s1") and L.check_run_name("/x/PERPETH1M_W8/s1") == "s1" and L.check_run_name("/x/PERPETH1M_W11/s2") == "s2"))
d = tempfile.mkdtemp(); os.makedirs(d + "/quotes/2026-11-10"); os.makedirs(d + "/PERPETH1M_W8/s1")
json.dump({"rows": [{"status": 200, "truncated": True, "file": "a"}, {"status": 500, "file": "b"}]}, open(d + "/PERPETH1M_W8/s1/manifest.json", "w"))
L.refuse_unless_allowed = lambda run_name: None
try: L.load(d, [d + "/PERPETH1M_W8/s1"]); ok.append(("7 dropped manifest rows void the run", False))
except SystemExit as ex: ok.append(("7 dropped manifest rows void the run", "RUN VOID: 2 manifest rows" in str(ex)))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
