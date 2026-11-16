#!/usr/bin/env python3
"""Checks ethlate1_load.py's internals on MADE-UP rows against EXPECTED_ethlate1_load_nov16.md. No file read."""
import os, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ethlate1_load as L
C = 1794319200; TK = "KXETHD-26NOV1014-T2000.99"; ct = "2026-11-10T14:00:00Z"
class Trap(dict):
    def __getitem__(self, k):
        if k != "close_time": raise AssertionError("read %r on a cut row" % (k,))
        return super().__getitem__(k)
def row(sec, b, a, tk=TK, close=ct): return {"t_recv_ms": str(int((C - sec) * 1000)), "ticker": tk, "close_time": close, "status": "active", "yes_bid": "%.2f" % b, "yes_ask": "%.2f" % a}
rows = [row(148, .28, .32), row(130, .30, .34), row(118, .31, .33), row(70, .32, .34), row(50, .35, .37), row(5, .40, .42), row(-3, .90, .92),
        row(100, .5, .6, tk="KXBTCD-26NOV1014-T80000.99"), Trap(close_time="2026-11-16T00:00:00Z")]
cnt = collections.Counter(); lad = L.ladder_rows(rows, cnt)
res = L.result_rows([{"ticker": TK, "close_time": ct, "result": "yes"}, {"ticker": "KXETHD-26NOV1014-T2100.99", "close_time": ct, "result": "void"}], cnt)
data = L.assemble(lad, res, cnt)
m = data["KXETHD"][0]
ok = [("1 one market kept, result yes", len(data["KXETHD"]) == 1 and m["result"] == "yes" and m["close"] == C),
      ("2 candles", m["candles"] == [(C - 120, .30, .34, None, 0, 0), (C - 60, .32, .34, None, 0, 0), (C, .40, .42, None, 0, 0)]),
      ("3 counts", cnt["ladder row dropped by the cut or no close"] == 1 and cnt["ticker outside the wall (dropped)"] == 1 and cnt["candle after close (dropped)"] == 1 and cnt["result not yes or no (dropped)"] == 1),
      ("4 the cut row is dropped on close_time alone (trap)", True),
      ("5 refuses without an allow-line", (lambda: (L.refuse_unless_allowed(), False)[1])() if False else True)]
try: L.refuse_unless_allowed(); ok[4] = ("5 refuses without an allow-line", False)
except SystemExit: pass
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
