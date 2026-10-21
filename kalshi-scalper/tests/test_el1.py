"""Plain assert tests for EL1 (src/scalper/el1.py); run with: python tests/test_el1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import el1 as E

assert (E.LEFT_S, E.BASE_LEFT_S, E.MIN_N, E.MIN_DAYS, E.Z_BAR, E.DIFF_Z_BAR, E.MIN_SERIES_POSITIVE) == (600, 360, 1000, 10, 2.8, 2.0, 10), "the registered numbers"
close = 100_000
mk = [("T1", "S", [(close - 600, 0.92, 0.93), (close - 360, 0.95, 0.96)], close, "yes"), ("T2", "S", [(close - 360, 0.60, 0.61)], close, "yes")]
early, base = E.entries_for(mk, 600), E.entries_for(mk, 360)
assert set(early) == {"T1"} and set(base) == {"T1"}, "only the 88c-97c favourites qualify; the entry candle ends exactly left_s before the close"
assert abs(early["T1"]["price"] - 0.93) < 1e-12 and abs(base["T1"]["price"] - 0.96) < 1e-12
print("test_el1: ok")
