import sys
sys.path.insert(0, "src")
from scalper import entry2 as T

cl = 1_700_000_000
def mkt(price420, price360, res="yes"):
    c = []
    if price420 is not None:
        c.append((cl - 420, price420 - 0.01, price420, price420 - 0.01, price420))
    c.append((cl - 360, price360 - 0.01, price360, price360 - 0.01, price360))
    return ("A", "KXXRP15M", c, cl, res)

e = T.tier_entry(mkt(0.95, 0.95))
assert e and e["net"] > 0                                   # a 0.95 favourite at 420 s is taken at 420 s
e2 = T.tier_entry(mkt(0.85, 0.90))
assert e2 and abs(e2["net"] - (1 - 0.90 - 0.07 * 0.90 * 0.10)) < 1e-9      # not in the 420 band, so the 360 s 0.88 to 0.93 band applies
assert T.tier_entry(mkt(0.85, 0.95)) is None                # 0.95 at 360 s is outside the 360 s tier band
assert T.baseline_entry(mkt(0.85, 0.95)) is not None
assert T.pick(mkt(None, 0.98), 360, (0.97, 0.995)) == ("yes", 0.98)
assert T.judge_mean([], 5)["verdict"] == "NOT_ENOUGH_DATA"
assert T.forward(now=0.0).startswith("Refusing the registered read")
assert T.EARLY_LEFT == 540 and T.EARLY_BAND == (0.80, 0.93) and T.judge_mean([], 5, 0.01, 2.0)["verdict"] == "NOT_ENOUGH_DATA"
print("ok")
