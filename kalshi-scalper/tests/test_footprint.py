import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import footprint as FP
t = {"created_time": "2026-10-25T00:00:30Z", "yes_price_dollars": "0.6300", "count_fp": "120.50", "taker_outcome_side": "yes"}
assert FP.parse(t)[1:] == (63, 120.5, 1)
assert FP.parse({**t, "taker_outcome_side": "no"})[3] == -1
rows = [(60.0, 50, 100.0, 1), (61.0, 50, 20.0, -1), (62.0, 51, 400.0, 1), (130.0, 52, 10.0, -1)]
bars = FP.footprint(rows)
assert sorted(bars) == [60, 120] and bars[60][50] == [20.0, 100.0] and bars[60][51] == [0.0, 400.0]
s = FP.bar_stats(bars[60])
assert s["buy"] == 500.0 and s["sell"] == 20.0 and s["delta"] == 480.0 and s["poc"] == 51 and s["stacked"] == 2
print("footprint tests ok")
