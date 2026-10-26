import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import lad1 as M
assert abs(M.p_yes(100.0, 100.0, 0.001, 30) - 0.5) < 1e-9
assert M.p_yes(101.0, 100.0, 0.001, 15) > 0.99 and M.p_yes(99.0, 100.0, 0.001, 15) < 0.01
assert M.p_yes(0, 100.0, 0.001, 15) is None and M.p_yes(100.0, 100.0, 0.0, 15) is None
assert M.decide(0.9, 0.55, 0.56)[0] == "yes"            # model far above the ask
assert M.decide(0.1, 0.55, 0.56)[0] == "no"
assert M.decide(0.56, 0.55, 0.56) is None                # inside the margin
assert M.decide(0.9, 0.50, 0.56) is None                 # spread over 2c
assert M.decide(0.99, 0.94, 0.95) is None                # ask outside the 0.10 to 0.90 band
assert M.decide(None, 0.5, 0.51) is None
print("lad1 tests ok")
