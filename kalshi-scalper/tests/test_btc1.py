import sys
sys.path.insert(0, "src")
from scalper import btc1 as T

cl = 1_700_000_000
c1 = (cl - 780, 0.49, 0.51, 0.49, 0.51)
m = [("A", "KXBTC15M", [c1], cl - 900, "yes"), ("B", "KXBTC15M", [c1], cl, "yes"), ("C", "KXETH15M", [c1], cl, "yes")]
prior = T.prior_results(m)
assert prior == {cl - 900: "yes", cl: "yes"}                      # only Bitcoin, only settled
cont, fade = T.open_groups(m, prior)
assert len(cont) == 1 and len(fade) == 1                          # A has no prior, C is not Bitcoin
assert cont[0]["net"] > 0.4 and fade[0]["net"] < -0.4             # the prior said yes, the market said yes: continuing wins
assert abs(T.pf([{"net": 0.3}, {"net": -0.1}]) - 3.0) < 1e-9
assert T.judge(cont)["verdict"] == "NOT_ENOUGH_DATA"
print("ok")
