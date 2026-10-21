"""Plain assert tests for HS1 (src/scalper/hs1.py); run with: python tests/test_hs1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import hs1 as H
from scalper.scalps import fee

assert (H.BAND, H.MIN_LEFT_S, H.TRIGGER_BID, H.MIN_LEFT_TRIGGER_S, H.HEDGE, H.MIN_N, H.MIN_DAYS, H.Z_BAR, H.DIFF_Z_BAR) == ((0.38, 0.52), 300, 0.65, 60, 0.5, 300, 10, 2.7, 2.0), "the registered numbers"
close = 10_000
# candles: (end, yes_bid, yes_ask). Entry at 45c YES (ask 0.45), then bid reaches 0.66 four minutes later.
c = [(close - 600, 0.44, 0.45), (close - 540, 0.50, 0.52), (close - 480, 0.66, 0.67), (close - 420, 0.80, 0.81)]
r = H.simulate(c, close, "yes")
assert r and abs(r["p0"] - 0.45) < 1e-12 and abs(r["q"] - (1 - 0.66)) < 1e-12
win_unh = 1 - 0.45 - fee(0.45)
assert abs(r["unh"] - win_unh) < 1e-12
assert abs(r["hed"] - (win_unh - 0.5 * (0.34 + fee(0.34)))) < 1e-12, "a win pays the hedge's cost"
r2 = H.simulate(c, close, "no")
assert abs(r2["hed"] - (-(0.45 + fee(0.45)) + 0.5 * (1 - 0.34 - fee(0.34)))) < 1e-12 and abs(r2["unh"] + 0.45 + fee(0.45)) < 1e-12, "a loss is partly paid back by the hedge"
# no trigger -> no observation; trigger inside the last minute does not count; entry needs 5 minutes left
assert H.simulate([(close - 600, 0.44, 0.45), (close - 540, 0.50, 0.52)], close, "yes") is None
assert H.simulate([(close - 600, 0.44, 0.45), (close - 30, 0.90, 0.91)], close, "yes") is None
assert H.simulate([(close - 200, 0.44, 0.45), (close - 120, 0.90, 0.91)], close, "yes") is None, "entry minute must have 5 minutes left"
print("test_hs1: ok")
