import sys
sys.path.insert(0, "src")
from scalper import wx1 as T

# whole degree maximum ~ N(71, 3): P(max >= 75) = P(N >= 74.5), P(max <= 66) = P(N <= 66.5), the two tails and the middle sum to one
a = T.p_yes("greater", 74, None, 71, 3)
b = T.p_yes("less", None, 67, 71, 3)
mids = sum(T.p_yes("between", lo, lo + 1, 71, 3) for lo in (67, 69, 71, 73))
assert abs(a + b + mids - 1) < 1e-9, (a, b, mids)
assert abs(a - (1 - T.phi((74.5 - 71) / 3))) < 1e-12
# decide: p = 0.50 with ask 0.40 clears 7c after the fee; with ask 0.50 it does not; NO side: p = 0.2, bid 0.5 -> no price 0.5, (0.8-0.5-fee) clears
assert T.decide(0.50, 0.38, 0.40, 0.07) == ("yes", 0.40)
assert T.decide(0.50, 0.48, 0.50, 0.07) is None
d = T.decide(0.20, 0.50, 0.52, 0.07)
assert d is not None and d[0] == "no" and abs(d[1] - 0.50) < 1e-12, d
assert abs(T.net("yes", 0.4, "yes") - (0.6 - 0.07 * 0.4 * 0.6)) < 1e-12
print("ok")
