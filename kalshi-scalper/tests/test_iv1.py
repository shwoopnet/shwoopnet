import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import iv1

# at the strike the model is a coin flip
assert abs(iv1.p_yes(100.0, 100.0, 50.0) - 0.5) < 1e-9
# far above the strike with real volatility is near certain; far below is near zero
assert iv1.p_yes(101.0, 100.0, 40.0) > 0.99 and iv1.p_yes(99.0, 100.0, 40.0) < 0.01
# bad inputs trade nothing
assert iv1.p_yes(0, 100.0, 40.0) is None and iv1.p_yes(100.0, 100.0, 0) is None
# flat price history has no volatility, so no model probability
assert iv1.p_yes_realised([100.0] * 61, 100.0) is None and iv1.p_yes_realised([100.0] * 60, 100.0) is None
# decision: no trade inside the margin, a trade when the model is far from the book, none on a crossed book
assert iv1.decide(0.5, 0.49, 0.51) is None
assert iv1.decide(0.95, 0.70, 0.72)[0] == "yes"
assert iv1.decide(0.05, 0.70, 0.72)[0] == "no"
assert iv1.decide(0.95, 0.72, 0.70) is None and iv1.decide(None, 0.5, 0.52) is None
# the averaging minute widens the variance: tau is 5 + 1/3, not 6
assert abs(iv1.TAU - 16 / 3) < 1e-12
# no lookahead: with bars stamped at their START, the decision at t may use only the bar stamped t - 60
mk = [("T", "KXBTC15M", [(1000 - 360, 0.50, 0.52)], 1000, "yes")]
bars = {"KXBTC15M": {}}
for k in range(0, 90):
    bars["KXBTC15M"][1000 - 360 - 60 - 60 * k] = 100.0 + 0.01 * (k % 3)
bars["KXBTC15M"][1000 - 900 - 60] = 100.0
bars["KXBTC15M"][1000 - 360] = 999.0          # the bar that closes after the decision must never be read
dv = {"KXBTC15M": {1000 - 360 - 60: 50.0, 1000 - 360: 999.0}}
o = iv1.observations(mk, bars, dv)
assert len(o) == 1 and o[0]["p_iv"] is not None and abs(o[0]["p_iv"] - 0.5) < 0.01
print("iv1 tests ok")
