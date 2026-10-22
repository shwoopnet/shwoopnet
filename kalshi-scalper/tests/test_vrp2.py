"""Plain assert tests for VRP2 (src/scalper/vrp2.py); run with: python tests/test_vrp2.py."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import vrp2 as V

assert (V.HOLD_DAYS, V.SHORT_K, V.LONG_K, V.COST, V.COST_STRESS, V.MIN_MONTHS, V.Z_BAR) == (21, 0.95, 0.90, 0.03, 0.04, 300, 2.9), "the registered numbers"
# put-call parity at zero rates: C - P = S - K, with C from the same formula by symmetry
s, k, sg, t = 100.0, 100.0, 0.2, 0.25
call = V.bs_put(s, k, sg, t) + s - k
assert abs(call - 3.987) < 0.01, "at the money put=call=3.99 for sigma 0.2, T 0.25"
assert V.bs_put(100, 50, 0.2, 0.1) < 1e-6 and abs(V.bs_put(100, 200, 0.2, 0.1) - 100) < 1e-6
# a spread settled above the short strike keeps the credit, less cost; below the long strike loses the width less the credit
ks, kl = 95.0, 90.0
credit = V.bs_put(100, ks, 0.2, 21 / 252) - V.bs_put(100, kl, 0.2, 21 / 252)
win = V.spread_month(100, 100, 20.0, 0.0)
assert abs(win - credit / (5 - credit)) < 1e-12
lose = V.spread_month(100, 80, 20.0, 0.0)
assert abs(lose - (credit - 5) / (5 - credit)) < 1e-12 and abs(lose + 1) < 1e-9, "max loss is -100% of margin"
assert V.spread_month(100, 100, 20.0, 0.03) < win
print("test_vrp2: ok")
