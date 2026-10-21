"""Plain assert tests for VM2 (src/scalper/vm2.py); run with: python tests/test_vm2.py."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import vm2 as V

assert (V.BURN_MONTHS, V.REFIT_EVERY, V.DEPTH, V.MIN_LEAF, V.DD_TRIGGER, V.VOL_RATIO_TRIGGER, V.Z_BAR, V.PLACEBO_REPS) == (120, 12, 2, 40, 0.15, 0.8, 2.8, 100), "the registered numbers"
dates = [f"{2000 + i // 252}-{(i % 252) // 21 + 1:02d}-{(i % 21) + 1:02d}" for i in range(4000)]
r = random.Random(5)
px = [100.0]
for _ in range(3999):
    px.append(px[-1] * (1 + r.gauss(0.0004, 0.012)))
rows = V.build_rows(dates, px)
assert len(rows) > 150 and all(len(x["feats"]) == 7 for x in rows)
# 1. Features at a signal day use only closes up to that day.
cut = dates.index(rows[40]["date"])
px2 = px[:cut + 1] + [1.0] * (4000 - cut - 1)
rows2 = V.build_rows(dates, px2)
assert [x["feats"] for x in rows2[:41]] == [x["feats"] for x in rows[:41]], "no lookahead in the features"
# 2. R1 only raises weight to 1.0, never lowers it.
assert all(a >= b for a, b in zip(V.r1_weights(rows), [x["w2"] for x in rows]))
# 3. The tree's weight is either V2's or 1.0, and a month's fit never sees its own label.
y = [x["ret"] for x in rows]
cuts = V.cut_points([{"feats": x["feats"]} for x in rows])
w = V.t1_weights(rows, y, cuts, 60)
assert all(wi == 1.0 or wi == rows[60 + k]["w2"] for k, wi in enumerate(w))
rows_b = [dict(x) for x in rows]
rows_b[100]["ret"] = 9.0                       # change one label: weights before month 100 cannot change
y_b = [x["ret"] for x in rows_b]
w_b = V.t1_weights(rows_b, y_b, cuts, 60)
assert w[:100 - 60] == w_b[:100 - 60], "earlier weights do not see a later label"
print("test_vm2: ok")
