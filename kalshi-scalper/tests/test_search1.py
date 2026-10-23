import sys
sys.path.insert(0, "src")
from scalper import search1 as T
from scalper import lstrats as L

cl = 1_700_000_000
later = [(cl - 300, 0.97, 0.98, 0.97, 0.98), (cl - 200, 0.99, 1.0, 0.99, 1.0)]
price = 0.90
assert abs(T.settle("yes", price, "yes", "TP97", later, cl) - (0.97 - 0.90 - L.fee(0.90) - L.fee(0.97))) < 1e-9
assert abs(T.settle("yes", price, "yes", "HOLD", later, cl) - L.net("yes", price, True)) < 1e-9
sl = [(cl - 300, 0.45, 0.46, 0.45, 0.46)]
assert T.settle("yes", price, "no", "SL50", sl, cl) < -0.45                    # sold at 0.45 after paying 0.90 and two fees
assert T.settle("yes", price, "no", "SL50", [(cl - 300, 0.8, 0.81, 0.8, 0.81)], cl) == L.net("yes", price, False)    # never triggered: lost at settlement
t120 = [(cl - 120, 0.60, 0.61, 0.60, 0.61)]
assert abs(T.settle("yes", price, "no", "T120", t120, cl) - (0.60 - 0.90 - L.fee(0.90) - L.fee(0.60))) < 1e-9
assert abs(T.settle("no", 0.90, "no", "TP4", [(cl - 300, 0.05, 0.06, 0.05, 0.06)], cl) - (0.94 - 0.90 - L.fee(0.90) - L.fee(0.94))) < 1e-9   # no side bid = 1 - yes ask = 0.94
print("ok")
