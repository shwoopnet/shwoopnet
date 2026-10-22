"""Plain assert tests for DL10 (src/scalper/dl10.py); run with: python tests/test_dl10.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import dl10 as D

assert (D.ENTRY_S, D.WINDOW, D.MIN_PRIOR, D.BURN_DAYS, D.Z_BAR, D.DIFF_Z_BAR, D.PLACEBO_REPS) == (600, 100, 50, 14, 2.8, 2.0, 100), "the registered numbers"
def row(k):
    ts = 1_700_000_000 + k * 900
    return {"series": "A", "close_ts": ts, "day": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")}
rows = [row(k) for k in range(3000)]
y = [0.01 if k < 1500 else -0.01 for k in range(3000)]
dec, und = D.walk(rows, y)
late = max(i for i in dec if i < 1500)
assert dec[late] is False and dec[2999] is True, "kept while the last 100 are positive, skipped once negative"
y2 = y[:2000] + [5.0] * 1000
dec2, _ = D.walk(rows, y2)
assert dec2[2000] == dec[2000], "a decision cannot see its own result"
assert min(dec) >= D.MIN_PRIOR
print("test_dl10: ok")
