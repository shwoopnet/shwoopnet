"""Plain assert tests for FEAT4 (src/scalper/feat4.py); run with: python tests/test_feat4.py."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import feat4 as G

assert (G.LEFTS, G.KEEP_Q, G.BURN_DAYS, G.REFIT_DAYS, G.Z_BAR, G.DIFF_Z_BAR, G.MIN_N, G.MIN_DAYS, G.MONTH_MIN, G.PLACEBO_REPS) == ((720, 660, 600, 540, 480, 420, 360, 300), 0.40, 14, 7, 3.0, 2.0, 1500, 10, 300, 30), "the registered numbers"
# the stopping rule takes the EARLIEST yes (largest seconds left), never a later better one
assert G.first_yes([(360, True, 5), (600, False, 3), (480, True, 4)]) == 4, "480 is the earliest yes"
assert G.first_yes([(300, False, 1), (360, False, 2)]) == -1, "no yes means no entry"
assert G.first_yes([(720, True, 9), (360, True, 8)]) == 9
print("test_feat4: ok")
