"""Plain assert tests for FEAT3 (src/scalper/feat3.py); run with: python tests/test_feat3.py."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import feat3 as F

assert (F.LEFTS, F.PRICE_LO, F.PRICE_HI, F.BURN_DAYS, F.REFIT_DAYS, F.KEEP_Q, F.LAM, F.Z_BAR, F.MIN_N, F.MIN_DAYS, F.MONTH_MIN, F.PLACEBO_REPS) == ((360, 600), 0.50, 0.97, 14, 7, 0.97, 1.0, 3.0, 1500, 10, 300, 50), "the registered numbers"
# the offset model learns a known correction: true P(win) = sigmoid(logit(price) + 0.6 * feature)
rng = np.random.default_rng(2)
n = 40000
price = rng.uniform(0.6, 0.95, n)
f = rng.normal(size=n)
true_p = 1 / (1 + np.exp(-(F.logit(price) + 0.6 * f)))
y = (rng.random(n) < true_p).astype(float)
X = np.column_stack([price, f])
model = F.fit_offset_logit(X, y, F.logit(price))
assert 0.4 < model[2][2] * 1.0 / (1.0 / model[1][1]) < 0.8, "the correction weight on the feature is recovered (about 0.6 per unit)"
assert abs(model[2][1]) < 0.15, "no correction on the price itself beyond the offset"
# without a correction in the data the model stays near the market price
y0 = (rng.random(n) < price).astype(float)
m0 = F.fit_offset_logit(X, y0, F.logit(price))
p0 = F.predict_p(m0, X, F.logit(price))
assert abs(p0.mean() - price.mean()) < 0.01
assert abs(F.expected_net(np.array([0.95]), np.array([0.95]))[0] + 0.07 * 0.95 * 0.05) < 1e-12, "a fair price has expected net of minus the fee"
# candidate builder: price range and one candidate per side and time
close = 10_000_000
cs = [(close - 900 + 60 * (i + 1), 0.91, 0.92, 0, 0) for i in range(15)]
rows, series = F.build([("T", "KXBTC15M", cs, close, "yes")])
assert {r["side"] for r in rows} == {"yes"} and {r["left"] for r in rows} == {360, 600}, "the NO side costs 0.09, below the 0.50 floor, so only YES candidates exist"
assert all(F.PRICE_LO <= r["price"] <= F.PRICE_HI for r in rows) and rows[0]["won"] == 1.0
print("test_feat3: ok")
