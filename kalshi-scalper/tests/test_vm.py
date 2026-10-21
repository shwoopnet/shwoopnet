"""Plain assert tests for VM (src/scalper/vm.py); run with: python tests/test_vm.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import vm as V

assert (V.SYMS, V.TARGET, V.VOL_DAYS, V.COST_SIDE, V.STRESS, V.MIN_MONTHS, V.Z_BAR, V.PLACEBO_REPS) == (["SPY", "QQQ", "USMV"], 0.10, 21, 0.0005, 1.2, 120, 2.7, 200), "the registered numbers"
dates = [f"{2010 + i // 252}-{(i % 252) // 21 + 1:02d}-{(i % 21) + 1:02d}" for i in range(900)]
# 1. A flat price has zero volatility, so the weight is the cap, 1.
px = [100.0] * 900
assert V.realised_vol(px, 100) == 0.0 and all(r["w"] == 1.0 for r in V.managed_rows(dates, px))
# 2. Volatility uses closes only up to the signal day: changing later prices cannot change a month's weight.
import random
rnd = random.Random(2)
px = [100.0]
for _ in range(899):
    px.append(px[-1] * (1 + rnd.gauss(0, 0.01)))
a = V.managed_rows(dates, px)
cut = dates.index(a[4]["date"])
px2 = px[:cut + 1] + [1.0] * (900 - cut - 1)
assert [r["w"] for r in V.managed_rows(dates, px2)[:5]] == [r["w"] for r in a[:5]], "no lookahead in the weight"
# 3. 20% daily noise is 4x the 10% target volatility's budget at least: weight well under 1.
assert 0 < min(r["w"] for r in a) <= 1.0
# 4. Cost is on the change of weight only.
rows = [{"date": "x", "w": 1.0, "ret": 0.01}] * 3
s, b = V.managed_series(rows, [1.0, 1.0, 0.5])
assert abs(s[0] - (0.01 - V.COST_SIDE)) < 1e-12 and abs(s[1] - 0.01) < 1e-12 and abs(s[2] - (0.005 - 0.5 * V.COST_SIDE)) < 1e-12
print("test_vm: ok")
