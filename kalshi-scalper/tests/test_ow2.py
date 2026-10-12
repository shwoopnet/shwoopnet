"""Plain assert tests for OW2 (src/scalper/ow2.py); run with: python tests/test_ow2.py. Each states a consequence, not a mechanism."""
import inspect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import ow2 as W
from scalper import scalps

CLOSE = 1_800_000_000          # a close time; candles are (end_ts, bid, ask, bid_h, ask_l)


def candle(left, bid, ask):
    return (CLOSE - left, bid, ask, bid, ask)


def market(candles):
    return ("T", "KXBTC15M", candles, CLOSE, "yes")


A = W.SPECS["OW2-A"]

# A: the entry is the FIRST candle (840 s left) whose side is in band, at its ask (26c); the target is 26c x 1.10 = 28.6c of closing bid, and the first later candle to reach it sells.
cs = [candle(840, 0.23, 0.26), candle(780, 0.24, 0.25), candle(720, 0.25, 0.26), candle(660, 0.285, 0.29), candle(600, 0.27, 0.28), candle(480, 0.20, 0.21)]
t = W.trade(cs, CLOSE, A)
assert t["how"] == "time", "28.5c is just under 28.6c, so no sale yet"          # the 660 s candle misses by half a cent
cs[3] = candle(660, 0.29, 0.30)
t = W.trade(cs, CLOSE, A)
assert t["how"] == "target" and t["ask"] == 0.26 and t["exit_left"] == 660, t
assert abs(t["net"] - (0.29 - (0.26 + scalps.fee(0.26)) - scalps.fee(0.29))) < 1e-9, "sold at the closing bid after both fees"
assert t["exit_left"] < 780 and t["exit_left"] >= W.EXIT_LEFT_S, "after the entry and before the cut-off"

# A position never outlives the 480 s candle: with no target hit it is sold at that candle's bid, not held to settlement.
cs = [candle(780, 0.24, 0.25), candle(720, 0.22, 0.23), candle(480, 0.10, 0.12)]
t = W.trade(cs, CLOSE, A)
assert t["how"] == "time" and t["exit_left"] == 480, t
assert abs(t["net"] - (0.10 - (0.25 + scalps.fee(0.25)) - scalps.fee(0.10))) < 1e-9, "sold at the closing bid after both fees"
print("OW2 exits passed")

# Never a settled outcome: a market with no 480 s candle is reported unresolvable, and the settled result is not read.
cs = [candle(780, 0.24, 0.25), candle(720, 0.22, 0.23)]
assert W.trade(cs, CLOSE, A) == {"unresolvable": True}
rows, unres = W.run([("T", "KXBTC15M", cs, CLOSE, "yes")], A)
assert rows == [] and unres == 1
print("OW2 unresolvable passed")

# The entry is only in the first two minutes: a 25c ask at 720 s left is no entry.
assert W.trade([candle(720, 0.24, 0.25), candle(480, 0.30, 0.31)], CLOSE, A) is None
# The target cannot be reached on an intrabar high: only closing bids count.
cs = [(CLOSE - 780, 0.24, 0.25, 0.24, 0.25), (CLOSE - 720, 0.22, 0.23, 0.40, 0.23), candle(480, 0.20, 0.21)]
assert W.trade(cs, CLOSE, A)["how"] == "time", "a high of 40c inside the minute is not credited"
print("OW2 entry and bar rules passed")

# No overlap with L1: every exit is at or before the 480 s candle, which is earlier than L1's earliest buy (400 s left).
live = (Path(__file__).resolve().parents[2] / "functions" / "kalshiLiveLib.js").read_text()
l1 = re.search(r"L1_WINDOW_MS = \[(\d+), (\d+)\]", live)
assert l1 and W.EXIT_LEFT_S > int(l1.group(2)) / 1000, "the last exit is before L1's earliest buy"
for cs in ([candle(780, 0.24, 0.25), candle(480, 0.5, 0.52)], [candle(840, 0.24, 0.25), candle(600, 0.5, 0.52), candle(480, 0.1, 0.12)]):
    assert W.trade(cs, CLOSE, A)["exit_left"] >= W.EXIT_LEFT_S
print("OW2 does not overlap L1 passed")

# Too little data never passes; the verdict words are the three only; nothing takes a performance parameter.
assert W.verdict([], 0)[0] == "NOT_ENOUGH_DATA"
src = re.sub(r"#.*|\"\"\"[\s\S]*?\"\"\"", "", Path(W.__file__).read_text())
assert not re.search(r"promote|PROMOTE", src)
bad = {"target_pf", "min_pf", "pf", "edge", "threshold", "z_bar", "min_n", "band", "bands"}
for name, fn in inspect.getmembers(W, inspect.isfunction):
    if fn.__module__ == W.__name__:
        assert not (set(inspect.signature(fn).parameters) & bad), name
print("OW2 tests passed")
