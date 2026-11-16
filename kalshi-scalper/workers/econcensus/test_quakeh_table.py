#!/usr/bin/env python3
"""Checks quakeh_table.py on MADE-UP rows against EXPECTED_quakeh_table_nov16.md."""
import os, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import quakeh_table as Q
class T(dict):
    """Raises on any key outside ALLOW."""
    def __init__(self, allow, **kw): super().__init__(**kw); self.allow = allow
    def __getitem__(self, k):
        if k not in self.allow: raise AssertionError("read banned key %r" % (k,))
        return super().__getitem__(k)
    def get(self, k, d=None):
        if k not in self.allow: raise AssertionError("read banned key %r" % (k,))
        return super().get(k, d)
mk = lambda ev, n, c: [T(("ticker", "close_time", "event_ticker"), ticker="KXBIGGESTQUAKEH-%s-%d" % (ev, i), event_ticker=ev, close_time=c, result="yes", volume_fp="1", last_price_dollars="0.5") for i in range(n)]
rows = [("settled", "KXBIGGESTQUAKEH", {"markets": mk("E1", 3, "2026-09-20T05:00:00Z") + mk("E2", 2, "2026-09-20T06:00:00Z") + mk("E3", 4, "2026-09-21T05:00:00Z") + mk("E4", 1, "2026-10-16T23:59:59Z")
        + [T(("ticker", "close_time"), ticker="KXBIGGESTQUAKEH-E5-%d" % i, close_time="2026-10-17T00:00:00Z") for i in range(2)] + [T(("ticker",), ticker="KXOTHER-X")], "cursor": ""})]
got = Q.table(rows)
want = ["markets 10 | events 4 | days 3 | median markets a day 4 | median events a day 1 | dropped outside the series 1 | dropped outside the window 2 | last page complete",
        "2026-09-20: markets 5, events 2", "2026-09-21: markets 4, events 1", "2026-10-16: markets 1, events 1"]
ok = [("1 lines", got == want),
      ("2 a cursor on the last page is said", "carries a cursor" in Q.table([("s", "x", {"markets": [], "cursor": "abc"})])[0]),
      ("3 ALLOWED_RUNS empty until landing", Q.ALLOWED_RUNS == frozenset()),
      ("4 source names no banned key", not any(('"%s"' % b) in open(os.path.join(here, "quakeh_table.py")).read() for b in ("result", "volume", "volume_fp", "last_price", "last_price_dollars", "status")))]
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
