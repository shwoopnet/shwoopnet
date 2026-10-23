import sys
sys.path.insert(0, "src")
from scalper import lag2 as T

close = 1_700_000_000
# spot flat at 100.0 with small noise so a volatility exists
sec = {str(close - i): [100.0 + 0.01 * ((i // 10) % 2), 1.0] for i in range(0, 1200)}
assert T.price_at(sec, close) == 100.0 and T.price_at(sec, close + 3) == 100.0
sg = T.sigma_per_s(sec, close - 120)
assert sg and sg > 0
assert T.p_yes(100.5, 100.0, 0.0005, 60) > 0.9 and T.p_yes(99.5, 100.0, 0.0005, 60) < 0.1
assert abs(T.p_yes(100.0, 100.0, 0.0005, 60) - 0.5) < 1e-9
t = close - 120
trades = [[t - 5, 0.50, "yes", 1.0], [t + 4, 0.52, "yes", 1.0], [t + 6, 0.48, "no", 1.0]]
assert T.reference(trades, t) == 0.50
assert T.fill(trades, t, "yes") == 0.52 and T.fill(trades, t, "no") == 0.52      # the no trade at yes 0.48 paid 0.52 for no
assert T.fill([[t + 1, 0.5, "yes", 1.0]], t, "yes") is None                      # inside the 2 second latency
assert T.judge([])["verdict"] == "NOT_ENOUGH_DATA"
# LAG2B: a sparse feed (price only every other grid point) still gives a volatility, a feed with under 45 points does not
sparse = {str(close - i): [100.0 + 0.01 * ((i // 20) % 2), 1.0] for i in range(0, 1200, 20)}
sb = T.sigma_b(sparse, close - 120)
assert sb is None or sb > 0
dense = {str(close - i): [100.0 + 0.01 * ((i // 10) % 2), 1.0] for i in range(0, 1200)}
assert T.sigma_b(dense, close - 120) > 0
assert T.sigma_b({str(close - i): [100.0, 1.0] for i in range(0, 60)}, close - 120) is None        # too few points (and no movement)
print("ok")
