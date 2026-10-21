"""Plain assert tests for PERP1 (src/scalper/perp1.py); run with: python tests/test_perp1.py. Each states a consequence, not a mechanism."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import perp1 as P

assert (P.N_ENTRY, P.N_EXIT, P.ATR_N, P.STOP_ATR, P.FEE_SIDE, P.SLIP_SIDE, P.FUNDING_DAY, P.MIN_TRADES, P.MIN_YEARS, P.Z_BAR) == (20, 10, 14, 1.5, 0.0012, 0.0001, 0.0002, 100, 4, 2.1), "the registered numbers"


def mk(closes, spread=1.0, opens=None):
    d0 = datetime(2020, 1, 1)
    bars = []
    for i, c in enumerate(closes):
        o = opens[i] if opens else c
        bars.append([(d0 + timedelta(days=i)).strftime("%Y-%m-%d"), o, max(o, c) + spread, min(o, c) - spread, c])
    return bars


# A signal at a day's close is filled at the NEXT day's open, never at that close: the entry index is strictly later than the signal day.
flat = [100.0] * 25
up = flat + [110.0, 111.0, 112.0, 113.0]            # day 25 closes above the 20 day high -> long at day 26's open
t = P.simulate(mk(up, opens=[100.0] * 25 + [110.0, 111.5, 112.0, 113.0]), "X")
assert t == [], "an open position at the end of the data is not counted"
ext = up + [90.0] * 3                              # then a collapse: the 10 day low breaks
t = P.simulate(mk(ext), "X")
assert len(t) >= 1 and t[0]["side"] == 1 and t[0]["entry_i"] == 26 and t[0]["entry"] == 111.0, t
# The stop fills at its price (or the open if the day gaps through it), and is flagged.
gap = flat + [110.0, 110.0, 110.0, 110.0] + [80.0]
bars = mk(gap)
bars[-1][1] = 80.0                                  # gaps down through the stop at the open
t = P.simulate(bars, "X")
assert t and t[0]["stopped"] and t[0]["exit"] == 80.0, "a gap through the stop fills at the open, not at the stop price"
# A short mirrors the long.
down = [100.0] * 25 + [90.0, 89.0, 88.0, 100.0, 120.0]
t = P.simulate(mk(down), "X")
assert t and t[0]["side"] == -1 and t[0]["entry_i"] == 26, t
# Costs: a round trip pays both sides' fee and slippage plus funding for each calendar day held, and a harsher multiplier costs more.
trade = {"gross": 0.05, "days": 10}
assert abs(P.net(trade) - (0.05 - 0.0026 - 0.002)) < 1e-12 and P.net(trade, 1.2) < P.net(trade)
# No trade means no verdict made up: too few trades reads NOT_ENOUGH_DATA.
assert P.verdict([], [])[0] == "NOT_ENOUGH_DATA"
# A losing book is FALSIFIED however many trades it has.
many = [{"market": "X", "side": 1, "entry_date": f"20{10 + i % 12:02d}-{1 + i % 12:02d}-05", "days": 5, "gross": -0.01, "stopped": True, "stop_dist": 0.02, "entry_i": 0, "exit_i": 5} for i in range(150)]
assert P.verdict(many, [0.0] * 5)[0] == "FALSIFIED"
print("ok test_perp1")
