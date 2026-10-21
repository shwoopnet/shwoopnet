"""Plain assert tests for V3/V4 (src/scalper/vm34.py); run with: python tests/test_vm34.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import vm34 as V

assert V.CELLS == {"V3": "TLT", "V4": "GLD"} and V.vm.Z_BAR == 2.8 and V.vm.TARGET == 0.10 and V.vm.COST_SIDE == 0.0005 and V.vm.MIN_MONTHS == 120 and V.vm.PLACEBO_REPS == 200, "the registered numbers"
print("test_vm34: ok")
