import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import sports1 as M
close = 1_000_000
cs = [(close - 7 * 3600, 0.40, 0.42), (close - 6 * 3600, 0.50, 0.52), (close - 5 * 3600 + 60, 0.99, 0.995), (close - 9 * 3600, 0.10, 0.12)]
assert M.pre_quote(cs, close) == (0.50, 0.52)          # last quote in the window; later and earlier candles are ignored
assert M.pre_quote([(close - 1000, 0.5, 0.51)], close) is None
assert M.pre_quote([(close - 6 * 3600, None, 0.51)], close) is None
assert abs(M.fee(0.5) - 0.0175) < 1e-12
print("sports1 tests ok")
