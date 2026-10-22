"""Plain assert tests for SIDE1, HOUR1 and XLEAD1 (src/scalper/cuts3.py); run with: python tests/test_cuts3.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import cuts3 as C

assert (C.Z_BAR, C.MIN_GROUP, C.MIN_DAYS, sorted(C.FOLLOWERS)) == (2.4, 500, 10, ["KXBNB15M", "KXDOGE15M", "KXETH15M", "KXHYPE15M", "KXNEAR15M", "KXXRP15M", "KXZEC15M"]), "the registered numbers"
mk = lambda n, day, net, ts: [{"day": f"2026-09-{d:02d}", "net": net, "close_ts": ts + d * 86400 + i} for d in range(1, 16) for i in range(n // 15)]
a, b = mk(600, 1, 0.03, 1_790_000_000), mk(600, 1, 0.0, 1_790_000_000)
text, v = C.compare(a, b, "x")
assert "a minus b per day +3.00c" in text
small = C.compare(a[:100], b, "y")[1]
assert small == "NOT_ENOUGH_DATA", "a group under 500 entries is not judged"
print("test_cuts3: ok")
