"""Plain assert tests for FEAT1 (src/scalper/feat1.py); run with: python tests/test_feat1.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import feat1 as F

assert (F.LEFT_S, F.BURN_DAYS, F.REFIT_DAYS, F.KEEP_Q, F.LAM, F.Z_BAR, F.DIFF_Z_BAR, F.PLACEBO_REPS) == (360, 14, 7, 0.40, 1.0, 3.0, 2.0, 100), "the registered numbers"
# logistic regression recovers a known direction
rng = np.random.default_rng(1)
X = rng.normal(size=(6000, 3))
logit = -2.0 + 1.5 * X[:, 0] - 1.0 * X[:, 1]
y = (rng.random(6000) < 1 / (1 + np.exp(-logit))).astype(float)
m = F.fit_logit(X, y)
assert m[2][1] > 1.0 and m[2][2] < -0.6 and abs(m[2][3]) < 0.2, "weights have the right signs and the null feature is near zero"
p = F.predict(m, X)
assert p[y == 1].mean() > p[y == 0].mean()
# walk-forward: a block's decisions do not change when later labels change
def row(day, k, x0):
    ts = 1_700_000_000 + day * 86400 + k * 900
    return {"day": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"), "close_ts": ts, "x": [x0, 0.5, 0.0], "net": 0.01}
rows = [row(d, k, float((d * 7 + k) % 5)) for d in range(40) for k in range(40)]
lost = [1.0 if r["x"][0] > 3 else 0.0 for r in rows]
dec = F.walk(rows, lost)
days = sorted({r["day"] for r in rows})
first_block = min(i for i, r in enumerate(rows) if r["day"] >= days[14])
assert dec and min(dec) >= first_block, "no decisions inside the burn-in"
lost2 = lost[:30 * 40] + [1.0 - v for v in lost[30 * 40:]]
dec2 = F.walk(rows, lost2)
cut_day = rows[30 * 40]["day"]
early = [i for i in dec if rows[i]["day"] < cut_day]
assert early and all(dec[i] == dec2[i] for i in early), "earlier decisions do not see later labels"
print("test_feat1: ok")
