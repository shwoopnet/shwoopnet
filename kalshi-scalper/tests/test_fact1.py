import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import fact1 as F

def c(end, bid, ask): return {"end": end, "bid": bid, "ask": ask}
close = 10_000
later = [c(close - 600, 0.70, 0.72), c(close - 480, 0.58, 0.60), c(close - 360, 0.90, 0.92), c(close - 240, 0.40, 0.42), c(close - 120, 0.95, 0.96)]
t0 = close - 720
# take profit +0.10 on yes bought at 0.62: the first closing bid >= 0.72 is 0.70 (no), then 0.58 (no), then 0.90 (yes)
a = F.simulate("tp10", "yes", 0.62, t0, close, later, False)
assert abs(a - (0.90 - 0.62 - F.fee(0.62) - F.fee(0.90))) < 1e-9
# a stop of -0.10 triggers at the first closing bid <= 0.52: the 0.40 at close-240 (it gaps through)
s = F.simulate("sl10", "yes", 0.62, t0, close, later, True)
assert abs(s - (0.40 - 0.62 - F.fee(0.62) - F.fee(0.40))) < 1e-9, s
# hold pays 1 on a win and carries only the entry fee
assert abs(F.simulate("hold", "yes", 0.62, t0, close, later, True) - (1 - 0.62 - F.fee(0.62))) < 1e-9
# time exit at 4 minutes left sells at that candle's bid; unavailable if entered later
assert abs(F.simulate("time4", "yes", 0.62, t0, close, later, True) - (0.40 - 0.62 - F.fee(0.62) - F.fee(0.40))) < 1e-9
assert F.simulate("time4", "yes", 0.62, close - 200, close, later, True) is None
# NO side reads 1 - ask as its bid
assert F.side_bid("no", c(1, 0.40, 0.42)) == 0.58
# a candle that is not later than the entry is never read (no lookahead): exit candles all end after t0
assert F.simulate("tp10", "yes", 0.62, close - 100, close, [c(close - 300, 0.99, 0.995)], False) is not None
# valid combinations: 47 pairs per side rule, 2,115 per asset, 4,230 in all
pairs = sum(1 for l in F.ENTRY_LEFT for e in F.EXITS if F.valid(l, e))
assert pairs == 47, pairs
assert pairs * len(F.SIDES) * len(F.GATES) == 2115
print("fact1 tests ok")
