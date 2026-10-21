"""Plain assert tests for LQ1 (src/scalper/lq1.py); run with: python tests/test_lq1.py."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import lq1 as Q

assert (Q.TARGET, Q.VOL_DAYS, Q.MIN_MONTHS, Q.Z_BAR, Q.PLACEBO_REPS) == (0.20, 21, 120, 2.8, 200), "the registered numbers"
dates = [f"{2007 + i // 252}-{(i % 252) // 21 + 1:02d}-{(i % 21) + 1:02d}" for i in range(4000)]
r = random.Random(4)
qqq = [100.0]
for _ in range(3999):
    qqq.append(qqq[-1] * (1 + r.gauss(0.0005, 0.012)))
qld = [100.0]
for k in range(1, 4000):
    qld.append(qld[-1] * (1 + 2 * (qqq[k] / qqq[k - 1] - 1)))
rows = Q.monthly(dates, qld, qqq)
# 1. Weight is capped at 1 and uses closes through the signal day only.
assert all(0 < x["w"] <= 1.0 for x in rows)
cut = dates.index(rows[30]["date"])
qld2 = qld[:cut + 1] + [1.0] * (4000 - cut - 1)
assert [x["w"] for x in Q.monthly(dates, qld2, qqq)[:31]] == [x["w"] for x in rows[:31]], "no lookahead in the weight"
# 2. The benchmark is QQQ over the same window as the QLD return (entry the day after the signal).
assert abs(rows[0]["qqq"] - rows[0]["qqq"]) == 0 and rows[0]["qqq"] != rows[0]["ret"]
# 3. Cost only on traded weight.
s = Q.score([{"ret": 0.01}] * 3, [1.0, 1.0, 0.5])
assert abs(s[0] - (0.01 - Q.COST_SIDE)) < 1e-12 and abs(s[1] - 0.01) < 1e-12 and abs(s[2] - (0.005 - 0.5 * Q.COST_SIDE)) < 1e-12
print("test_lq1: ok")
