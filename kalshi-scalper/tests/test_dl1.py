"""Plain assert tests for DL1 (src/scalper/dl1.py); run with: python tests/test_dl1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import dl1 as D

assert (D.WINDOW, D.MIN_PRIOR, D.BURN_DAYS, D.LAG_S, D.Z_BAR, D.DIFF_Z_BAR, D.PLACEBO_REPS) == (200, 100, 14, 360, 2.7, 2.0, 100), "the registered numbers"
from datetime import datetime, timezone

def row(series, k, per_day=100):
    ts = 1_700_000_000 + k * 900
    return {"series": series, "close_ts": ts, "day": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")}

rows = [row("A", k) for k in range(3000)]
y = [0.01 if k < 1500 else -0.01 for k in range(3000)]
dec, undecided = D.walk(rows, y)
assert dec and all(isinstance(v, bool) for v in dec.values())
# 1. After a long run of losses the series is skipped; during a run of gains it is kept.
late = max(i for i in dec if i < 1500)
assert dec[late] is False, "kept while the last 200 are positive"
assert dec[2999] is True, "skipped once the last 200 are negative"
# 2. A decision cannot see its own result or later ones: changing y from i onward leaves the decision at i unchanged.
i = 2000
y2 = y[:i] + [5.0] * (3000 - i)
dec2, _ = D.walk(rows, y2)
assert dec2[i] == dec[i], "no lookahead"
# 3. Entries inside the burn-in or with too little history are not decided.
assert min(dec) >= D.MIN_PRIOR and undecided >= 0
print("test_dl1: ok")
