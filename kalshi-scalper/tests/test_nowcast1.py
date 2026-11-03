import sys; sys.path.insert(0, "src")
from scalper import nowcast1 as n
# fee: 7% x 10 x p(1-p) rounded up to the cent
assert n.fee_order(0.10) == 0.07, n.fee_order(0.10)   # 0.63 -> 0.07? 0.07*10*0.09=0.063 -> 0.07
assert n.fee_order(0.5) == 0.18, n.fee_order(0.5)     # 0.175 -> 0.18
# p_above: nowcast right at strike+0.05 gives 0.5; sd floor
assert abs(n.p_above(0.35, 0.1, 0.30) - 0.5) < 1e-9
assert n.p_above(0.0, 0.0, 0.3) < 1e-6
# choose: yes cheap with ratio >= 3, hard limit .30, spread cap, one per series (highest ratio)
assert n.choose([("a", 0.08, 0.10, 0.35)]) == ("a", "yes", 0.10, 3.5 / 1.0) or abs(n.choose([("a", 0.08, 0.10, 0.35)])[3] - 3.5) < 1e-9
assert n.choose([("a", 0.30, 0.32, 0.99)]) is None                      # ask above 0.30
assert n.choose([("a", 0.02, 0.15, 0.99)]) is None                      # spread 13c
assert n.choose([("a", 0.08, 0.10, 0.20)]) is None                      # ratio 2
t = n.choose([("a", 0.08, 0.10, 0.35), ("b", 0.04, 0.05, 0.30)])
assert t[0] == "b", t                                                    # ratio 6 beats 3.5
# no side: NO cheap when p tiny
t = n.choose([("c", 0.80, 0.82, 0.01)])
assert t[1] == "no" and abs(t[2] - 0.20) < 1e-9
# settle: yes win at .10 nets .90 - .007
assert abs(n.settle("yes", 0.10, True) - (0.90 - 0.007)) < 1e-9
assert abs(n.settle("no", 0.20, True) - (-0.20 - n.fee_order(0.20) / 10)) < 1e-9
# gdp quarter mapping
from datetime import datetime, timezone as z
assert n.gdp_quarter(datetime(2026, 2, 20, tzinfo=z.utc)) == "2025-10-01"
assert n.gdp_quarter(datetime(2026, 7, 30, tzinfo=z.utc)) == "2026-04-01"
print("test_nowcast1 ok")
