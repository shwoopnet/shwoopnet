#!/usr/bin/env python3
"""Checks census_table.py on MADE-UP rows against EXPECTED_census_table_nov15.md. No network, no Kalshi data."""
import contextlib, io, os, sys, importlib.util
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
spec = importlib.util.spec_from_file_location("ct", os.path.join(here, "census_table.py")); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
class M(dict):
    """A market whose result is never allowed to be read."""
    def __getitem__(self, k):
        if k == "result": raise AssertionError("result read")
        return super().__getitem__(k)
    def get(self, k, d=None):
        if k == "result": raise AssertionError("result read")
        return super().get(k, d)
class Trap(dict):
    def __init__(self, close): super().__init__(close_time=close)
    def __getitem__(self, k):
        if k != "close_time": raise AssertionError("dropped row read: %r" % (k,))
        return super().__getitem__(k)
    def get(self, k, d=None): raise AssertionError("dropped row read via get: %r" % (k,))
def mk(ev, close, v, lp): return M(ticker=ev + str(v), event_ticker=ev, close_time=close, volume_fp="%.2f" % v, last_price_dollars="%.4f" % lp, result="yes")
p1 = [mk("E1", "2026-01-15T14:00:00Z", 10, .05), mk("E1", "2026-01-15T14:00:00Z", 20, .95), mk("E2", "2026-02-12T14:00:00Z", 30, .30), mk("E2", "2026-02-12T14:00:00Z", 40, .70),
      mk("E3", "2026-03-12T14:00:00Z", 50, .55), mk("E3", "2026-03-12T14:00:00Z", 0, .45), Trap("2026-10-20T14:00:00Z")]
p2 = [mk("E3", "2026-03-12T14:00:00Z", 5, .52)]
fed = [mk("F1", "2025-06-18T18:00:00Z", 7, .60), Trap("2025-10-01T18:00:00Z")]
rows = [("settled_KXCPI", "KXCPI", {"markets": p1}), ("settled_KXCPI", "KXCPI", {"markets": p2}), ("settled_KXFED", "KXFED", {"markets": fed}),
        ("series_economics", None, {"series": [{"ticker": "KXZZ", "frequency": "monthly", "title": "t"}]})]
lines, ns = C.table(rows)
d = {l.split(":")[0]: l for l in lines}
ok = [("1 KXCPI line", d["KXCPI"] == "KXCPI: settled markets 7, after the cut dropped 1, close dates 3 (2026-01-15 to 2026-03-12), events 3, markets with volume above 0 6, median volume 20, last price bands: [0.0,0.1) 1, [0.3,0.4) 1, [0.4,0.5) 1, [0.5,0.6) 2, [0.7,0.8) 1, [0.9,1.0] 1"),
      ("2 KXFED line", d["KXFED"] == "KXFED: settled markets 1, after the cut dropped 1, close dates 1 (2025-06-18 to 2025-06-18), events 1, markets with volume above 0 1, median volume 7, last price bands: [0.6,0.7) 1"),
      ("3 series list counted", ns == 1)]
src = open(os.path.join(here, "census_table.py")).read()
ok.append(("4 source does not read a result key", 'get("result"' not in src and '["result"]' not in src))
ok.append(("5 empty ALLOWED_RUNS refuses a listed run", C.ALLOWED_RUNS == frozenset()))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
