"""Plain assert tests for the MM1 scorer's queue logic (src/scalper/mm1.py) on SYNTHETIC windows only
(no recorded gold quote or trade is used); run with: python tests/test_mm1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import mm1 as M

CLOSE = 10_000.0
T0 = CLOSE - 150
Q0 = (T0, 0.40, 0.42, 5.0, 3.0)          # bid 40c (5 ahead), ask 42c (3 ahead)
quiet = [(T0 + i, 0.40, 0.42, 5.0, 3.0) for i in range(0, 140, 2)]

assert (M.NEEDED, M.FLAT_S, M.SIZES, M.VERDICT_RATE, M.Z_BAR) == (300, 20, (1, 10), 0.07, 5.17), "the amendment's numbers"

# fees: rounded up per order
assert M.order_fee(0.07, 1, 0.40) == 0.02, "7% x 0.24 = 1.68c -> 2c"
assert M.order_fee(0.07, 10, 0.40) == 0.17, "16.8c -> 17c"
assert M.order_fee(0.0, 1, 0.40) == 0.0 and M.order_fee(0.07, 0, 0.4) == 0.0

# 1. no two-sided quote: nothing posted
assert M.simulate([(T0, 0.40, None, 5, None)], [], CLOSE) is None

# 2. quote moves away, no trades: no fill (cancels and quote moves never fill or advance us)
moved = [Q0] + [(T0 + 10 + i, 0.38, 0.41, 1.0, 1.0) for i in range(0, 100, 2)]
w = M.simulate(moved, [], CLOSE)
assert w["fb"] == 0 and w["fs"] == 0 and w["gross"] == 0, "the quote moving (size ahead cancelled) is not a fill"
# ... but the ask moving down THROUGH our bid is a crossing fill
w = M.simulate([Q0] + [(T0 + 10 + i, 0.30, 0.33, 1.0, 1.0) for i in range(0, 100, 2)], [], CLOSE)
assert w["fb"] == 1 and w["fs"] == 0

# 3. trades at our bid: the 5 ahead must trade first; 5 does not fill us, 5.5 fills half, 6 fills fully
for vol, want in ((5.0, 0.0), (5.5, 0.5), (6.0, 1.0)):
    w = M.simulate(quiet, [(T0 + 5, 0.40, vol, -1)], CLOSE)
    assert abs(w["fb"] - want) < 1e-9, (vol, w["fb"])
# split prints add up, and a taker BUY at our bid price does not count for our buy
w = M.simulate(quiet, [(T0 + 5, 0.40, 3, -1), (T0 + 6, 0.40, 2.5, 1), (T0 + 7, 0.40, 2.5, -1)], CLOSE)
assert w["fb"] == 0.5

# 4. a print before we are live (inside the 250 ms) does not fill us
w = M.simulate(quiet, [(T0 + 0.1, 0.39, 50, -1)], CLOSE)
assert w["fb"] == 0
w = M.simulate(quiet, [(T0 + 0.3, 0.39, 1, -1)], CLOSE)
assert w["fb"] == 1, "a print through our price fills the whole order"

# 5. the opposite quote crossing our price fills us at OUR price
crossed = [Q0, (T0 + 30, 0.38, 0.40, 2, 2)] + quiet[20:]
w = M.simulate(crossed, [], CLOSE)
assert w["fb"] == 1 and w["fs"] == 0

# 6. completed cycle: buy and sell both fill -> spread 2c, fees 2c + 2c at C=1
w = M.simulate(quiet, [(T0 + 5, 0.40, 10, -1), (T0 + 9, 0.42, 10, 1)], CLOSE)
assert w["fb"] == 1 and w["fs"] == 1 and w["inv"] == 0
assert abs(w["spread"] - 0.02) < 1e-9 and abs(M.pnl(w, 0.07) - (0.02 - 0.04)) < 1e-9
assert abs(M.pnl(w, 0.0) - 0.02) < 1e-9

# 7. one-sided fill, flattened at the last quote at or before close - 20 s (adverse move)
drift = [Q0] + [(T0 + 10 + i, 0.30, 0.32, 5, 5) for i in range(0, 130, 2)]
w = M.simulate(drift, [(T0 + 5, 0.39, 1, -1)], CLOSE)
assert w["fb"] == 1 and w["inv"] == 1 and w["flat_price"] == 0.30
assert abs(w["flat"] - (0.30 - 0.40)) < 1e-9
assert abs(M.pnl(w, 0.07) - (-0.10 - 0.02 - 0.02)) < 1e-9, "maker 2c + flatten taker 7% x .21 = 1.47c -> 2c"
# trades after close - 20 s are ignored
w = M.simulate(quiet, [(CLOSE - 10, 0.39, 100, -1)], CLOSE)
assert w["fb"] == 0

# 8. missing opposing side at the flatten poll = worst case
gone = [Q0] + [(T0 + 10 + i, None, 0.99, 0, 5) for i in range(0, 130, 2)]
w = M.simulate(gone, [(T0 + 5, 0.39, 1, -1)], CLOSE)
assert w["flat_price"] == 0.0 and abs(w["flat"] + 0.40) < 1e-9

# 9. size 10 needs 10 past the queue
w = M.simulate(quiet, [(T0 + 5, 0.40, 12, -1)], CLOSE, size=10)
assert abs(w["fb"] - 7) < 1e-9

# 10. clock offset shifts our live time onto the exchange clock
w = M.simulate(quiet, [(T0 + 0.3, 0.39, 1, -1)], CLOSE, offset_s=0.2)
assert w["fb"] == 0, "live at T0 + 0.2 + 0.25"

# statistics
assert M.pf([1, -1, 2]) == 3 and M.pf([-1]) == 0
s = M.summarise([(CLOSE + i * 900, M.simulate(quiet, [], CLOSE)) for i in range(6)], 0.07)
assert s["n"] == 6 and s["net"] == 0 and not M.passes(s, s)
assert M.central_date(1793275200) == "2026-10-29"
print("test_mm1: ok")
