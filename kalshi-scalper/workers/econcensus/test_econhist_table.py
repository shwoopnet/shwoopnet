#!/usr/bin/env python3
"""Checks econhist_table.py on MADE-UP rows against EXPECTED_econhist_table_nov15.md."""
import os, sys, importlib.util
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import econhist_table as H
BAN = ("result", "volume", "volume_fp", "last_price", "last_price_dollars")
class M(dict):
    def __getitem__(self, k):
        if k in BAN: raise AssertionError("banned field read: %r" % (k,))
        return super().__getitem__(k)
    def get(self, k, d=None):
        if k in BAN: raise AssertionError("banned field read: %r" % (k,))
        return super().get(k, d)
class Trap(dict):
    def __init__(self, close): super().__init__(close_time=close)
    def __getitem__(self, k):
        if k != "close_time": raise AssertionError("dropped row read: %r" % (k,))
        return super().__getitem__(k)
    def get(self, k, d=None): raise AssertionError("dropped row read via get: %r" % (k,))
mk = lambda ev, c: M(ticker=ev + c, event_ticker=ev, close_time=c, result="yes", volume_fp="1", last_price_dollars="0.5")
cpi = [mk("A", "2025-09-25T23:59:59Z"), mk("A", "2025-09-25T23:59:58Z"), Trap("2025-09-26T00:00:00Z"), Trap("2026-03-12T13:30:00Z"), mk("D", "2025-05-13T12:30:00Z"), mk("D", "2025-05-13T12:31:00Z")]
pay = [mk("P", "2026-08-07T12:30:00Z"), mk("P", "2026-08-07T12:30:01Z")]
pce = [Trap("2025-09-26T00:00:00Z"), mk("Q", "2025-08-29T12:30:00Z")]
rows = [("hist_KXCPI", "KXCPI", {"markets": cpi}), ("hist_KXPAYROLLS", "KXPAYROLLS", {"markets": pay}), ("hist_KXPCECORE", "KXPCECORE", {"markets": pce})]
got = H.table(rows)
want = ["KXCPI: settled markets 4, after the held-out date dropped 2, close dates 2 (2025-05-13 to 2025-09-25), events 2",
        "KXPAYROLLS: settled markets 2, after the held-out date dropped 0, close dates 1 (2026-08-07 to 2026-08-07), events 1",
        "KXPCECORE: settled markets 1, after the held-out date dropped 1, close dates 1 (2025-08-29 to 2025-08-29), events 1"]
ok = [("1 lines", got == want), ("2 cut constant is 2025-09-26T00:00:00Z for KXCPI and KXPCECORE only", H.CUTS == {"KXCPI": 1758844800, "KXPCECORE": 1758844800}),
      ("3 source names no banned key", not any(('"%s"' % b) in open(os.path.join(here, "econhist_table.py")).read() for b in BAN)),
      ("4 ALLOWED_RUNS empty until landing", H.ALLOWED_RUNS == frozenset())]
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
