"""Plain assert tests for MC1, SF1 and CAP1 (src/scalper/mc_sf.py); run with: python tests/test_mc_sf.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import mc_sf as M

assert (M.TIMES, M.DEFAULT_T, M.BURN_DAYS, M.REFIT_DAYS, M.MIN_TRAIN, M.MC_Z, M.MC_DIFF_Z, M.MC_MIN_N, M.MIN_DAYS, M.SF_Z, M.SF_MIN_GROUP, M.SF_PREV) == (
    (360, 480, 600), 360, 21, 7, 100, 2.8, 2.0, 1000, 10, 2.4, 500, 3), "the registered numbers"
# the chooser picks the best time with enough history, else the default
assert M.choose({360: [0.0] * 150, 480: [0.01] * 150, 600: [0.02] * 99}) == 480, "600 has too little history"
assert M.choose({360: [0.0] * 10, 480: [0.01] * 10, 600: [0.02] * 10}) == 360, "nothing has enough history: default"
assert M.choose({360: [0.01] * 150, 480: [0.01] * 150, 600: [0.0] * 150}) == 360, "a tie goes to the default"
d = M.day_diff([{"day": "a", "net": 0.02}, {"day": "b", "net": 0.04}], [{"day": "a", "net": 0.01}, {"day": "b", "net": 0.01}])
assert abs(d[0] - 0.02) < 1e-12
print("test_mc_sf: ok")
