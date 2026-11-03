import math, sys
from datetime import date, timedelta
sys.path.insert(0, "src")
import numpy as np
from scalper import gas2

assert gas2.fee(0.5) == math.ceil(0.07 * 10 * 0.25 * 100) / 100 / 10      # 0.175 -> 0.18 per 10 -> 0.018
assert abs(gas2.fee(0.10) - 0.007) < 1e-9 or abs(gas2.fee(0.10) - 0.007) < 0.0011
assert abs(gas2.net_of("yes", 0.10, "yes") - (0.9 - gas2.fee(0.10))) < 1e-12
assert gas2.net_of("no", 0.10, "yes") < 0
assert gas2.profit_factor([1, -1]) == 1 and gas2.profit_factor([1]) == math.inf
assert gas2.event_value([{"expiration_value": "4.2786"}, {"expiration_value": "4.2786"}]) == 4.2786
assert abs(gas2.event_value([{"result": "yes", "floor_strike": 4.275}, {"result": "no", "floor_strike": 4.277}]) - 4.276) < 1e-9
assert gas2.event_value([{"result": "yes", "floor_strike": 4.0}, {"result": "no", "floor_strike": 4.5}]) is None
p, q = gas2.side_probs(np.array([1., 2., 3., 4.]), 2.5)
assert p == 0.5 and q == 0.5
c = [{"series": "A", "date": "d", "ratio": r} for r in (5, 4, 3)] + [{"series": "B", "date": "d", "ratio": 9}]
assert [x["ratio"] for x in gas2.pick(c)] == [9, 5, 4]
# model: a random walk with drift gives a near-zero slope and a usable prediction
rng = np.random.default_rng(0)
vals = {}
for s in "ABCDE":
    v, d0, out = 4.0, date(2026, 1, 1), {}
    for i in range(80):
        v += rng.normal(0.001, 0.005)
        out[d0 + timedelta(days=i)] = v
    vals[s] = out
r = gas2.fit_predict_samples(vals, date(2026, 3, 10), "A")
assert r is not None and abs(r[0] - r[1]) < 0.03 and len(r[2]) >= 200
assert gas2.fit_predict_samples(vals, date(2026, 1, 8), "A") is None
print("test_gas2 ok")
