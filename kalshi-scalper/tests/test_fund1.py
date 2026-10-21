"""Plain assert tests for FUND1 (src/scalper/fund1.py); run with: python tests/test_fund1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import fund1 as F

assert (F.COINS, round(F.COST, 6), F.STRESS, F.MIN_MONTHS, F.Z_BAR, F.NW_LAGS, F.MARGIN) == (["BTC", "ETH"], 0.0094, 1.2, 36, 2.1, 3, 1.2), "the registered numbers"
# a constant series has the constant mean and an infinite z only because its error is zero
m, z = F.nw_mean_z([0.01] * 20)
assert abs(m - 0.01) < 1e-12
# noisy positive series: z is large for a big mean, small for zero mean
import random
r = random.Random(1)
ys = [0.01 + r.gauss(0, 0.002) for _ in range(40)]
assert F.nw_mean_z(ys)[1] > 10
ys0 = [r.gauss(0, 0.002) for _ in range(40)]
assert abs(F.nw_mean_z(ys0)[1]) < 3
# monthly keeps only full months, sums hourly rates
rows = [[1_690_000_000_000 + h * 3_600_000, 0.0001, 0.0] for h in range(24 * 40)]
out = F.monthly(rows)
assert all(abs(v - 0.0001 * 24 * 31) < 0.0001 * 24 * 3 for v in out.values()) and len(out) >= 1
print("test_fund1: ok")
