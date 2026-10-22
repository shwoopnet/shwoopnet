"""Plain assert tests for FIX1 and the JUMP1 look (src/scalper/cuts4.py); run with: python tests/test_cuts4.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import cuts4 as C

assert (C.FIX_MINUTES, C.FIX_HALF_WINDOW_MIN, C.MIN_GROUP_FIX, C.JUMP_CUT) == ((570, 840), 30, 100, 0.05), "the registered numbers"
ts = lambda d, h, m=0: int(datetime(2026, 9, d, h, m, tzinfo=timezone.utc).timestamp())
assert C.near_fix(ts(23, 9, 0)) and C.near_fix(ts(23, 10, 0)) and not C.near_fix(ts(23, 10, 1)), "a weekday, 09:00 to 10:00 UTC"
assert C.near_fix(ts(23, 13, 30)) and C.near_fix(ts(23, 14, 30)) and not C.near_fix(ts(23, 14, 31))
assert not C.near_fix(ts(26, 9, 30)), "Saturday 2026-09-26 is not counted"
c = [(1000, 0.80, 0.82), (1180, 0.90, 0.92)]
assert abs(C.d3_of(c, 1180 + 0, "yes") if False else (C.d3_of([(820, 0.80, 0.82), (1000, 0.90, 0.92)], 1000, "yes") - 0.10)) < 1e-12
assert abs(C.d3_of([(820, 0.80, 0.82), (1000, 0.90, 0.92)], 1000, "no") + 0.10) < 1e-12, "a NO favourite's mid falls when YES rises"
assert C.d3_of([(1000, 0.90, 0.92)], 1000, "yes") is None
print("test_cuts4: ok")
