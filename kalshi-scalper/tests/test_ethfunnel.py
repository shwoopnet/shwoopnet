"""Plain assert tests for ETHFUNNEL (src/scalper/ethfunnel.py) on made-up candles. Run: cd kalshi-scalper && PYTHONPATH=src python tests/test_ethfunnel.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import ethfunnel as E

assert E.pick(0.89, 0.90) == ("yes", 0.90)
assert E.pick(0.02, 0.03) is None   # NO at 0.98 is out of the band
assert E.pick(0.05, 0.06) == ("no", 0.95)
assert E.pick(0.50, 0.52) is None
assert E.pick(0.001, 1.0) is None                      # empty book
# a smooth path: 9 candles climbing 0.01 a minute from 0.62 mid to 0.90
cs = [(60 * i, 0.61 + 0.0366 * i, 0.63 + 0.0366 * i) for i in range(8)]
e, mn, cl = E.shape(cs, "yes")
assert e == 7 and mn > 0 and cl > 0.10
# a pullback of one cent: -0.0050000000000000044 in floats, which is NOT smooth (same as pathShape)
cs2 = [(0, 0.60, 0.62), (60, 0.61, 0.63), (120, 0.62, 0.64), (180, 0.63, 0.65), (240, 0.64, 0.66), (300, 0.635, 0.655)] + [(360, 0.80, 0.82)]
e2, mn2, cl2 = E.shape(cs2, "yes")
assert mn2 < 0 and E.histogram([-0.005])[3][1] in (0, 1)
# a decision needs the candle ending exactly 360 s before the close
m = {"close": 1000 + 360, "c": [(1000 - 60, 0.5, 0.52), (1000, 0.9, 0.91)], "s": E.ETH}
assert E.decide(m)["state"] == "inband"
m2 = {"close": 1000 + 360, "c": [(940, 0.9, 0.91)], "s": E.ETH}
assert E.decide(m2)["state"] == "nocandle"
print("test_ethfunnel: ok")
