"""Plain assert tests for CM1 and VT1 (src/scalper/fam5.py); run with: python tests/test_fam5.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import fam5 as F

assert (len(F.COUNTRIES), F.CM_TOP, F.CM_COST, F.Z_BAR, F.PLACEBO_REPS, F.VT_THRESHOLD, F.VT_COST, F.VT_LAGS, F.VT_MIN_DAYS, F.STRESS) == (17, 5, 0.0008, 3.0, 200, 0.95, 0.0006, 10, 2500, 1.2), "the registered numbers"
# the position on day u comes from the flag two days earlier
assert F.vt_positions([True, False, True, True]) == [False, False, True, False]
# cost only on a change of position, and the day's return only when held
s = F.vt_series([0.01, 0.01, 0.01, 0.01, 0.01], [True, True, False, False, False])
assert abs(s[0]) == 0 and abs(s[1]) == 0
assert abs(s[2] - (0.01 - F.VT_COST)) < 1e-12 and abs(s[3] - 0.01) < 1e-12 and abs(s[4] - (0 - F.VT_COST)) < 1e-12
assert abs(F.drawdown([0.1, -0.5, 0.1]) - (-0.5)) < 1e-12
print("test_fam5: ok")
