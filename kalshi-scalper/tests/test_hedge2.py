"""Plain assert tests for HL1 and SL1 (src/scalper/hedge2.py); run with: python tests/test_hedge2.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import hedge2 as H
from scalper.scalps import fee

assert (H.HEDGE_L1, H.LADDER_LOW, H.LADDER_HIGH, H.MIN_N, H.MIN_DAYS, H.Z_BAR, H.DIFF_Z_BAR) == (0.10, 0.60, 0.80, 300, 10, 2.8, 2.0), "the registered numbers"
close = 10_000
# HL1: YES favourite at ask 0.94, bid 0.93: the other side (NO) costs 1 - bid = 0.07.
c = [(close - 360, 0.93, 0.94)]
w = H.hl1(c, close, "yes")
assert abs(w["plain"] - (1 - 0.94 - fee(0.94))) < 1e-12 and abs(w["q"] - 0.07) < 1e-12
assert abs(w["hedged"] - (w["plain"] + 0.1 * (0 - 0.07 - fee(0.07)))) < 1e-12, "a win pays for the hedge"
l = H.hl1(c, close, "no")
assert abs(l["plain"] + (0.94 + fee(0.94))) < 1e-12 and abs(l["hedged"] - (l["plain"] + 0.1 * (1 - 0.07 - fee(0.07)))) < 1e-12, "a flip is partly paid back"
assert H.hl1([(close - 300, 0.93, 0.94)], close, "yes") is None, "the entry candle must end exactly 360 s before the close"
# NO favourite: YES bid 0.05, ask 0.06 -> NO costs 1 - 0.05 = 0.95; the hedge buys YES at its ask 0.06.
n = H.hl1([(close - 360, 0.05, 0.06)], close, "no")
assert abs(n["p"] - 0.95) < 1e-12 and abs(n["q"] - 0.06) < 1e-12
# SL1: entry 0.45, bid reaches 0.66 then 0.82; every entry counts, a no-trigger entry equals plain hold.
cs = [(close - 600, 0.44, 0.45), (close - 540, 0.66, 0.67), (close - 480, 0.82, 0.83)]
r = H.sl1(cs, close, "no")
f0 = fee(0.45)
exp = ((0.60 - 0.45 - f0 - fee(0.60)) + (0.80 - 0.45 - f0 - fee(0.80)) + (-(0.45 + f0))) / 3
assert abs(r["ladder"] - exp) < 1e-12 and abs(r["plain"] + 0.45 + f0) < 1e-12
nt = H.sl1([(close - 600, 0.44, 0.45), (close - 540, 0.50, 0.52)], close, "yes")
assert nt["ladder"] == nt["plain"], "no trigger: ladder equals plain hold"
low_only = H.sl1([(close - 600, 0.44, 0.45), (close - 540, 0.62, 0.63)], close, "yes")
assert abs(low_only["ladder"] - (((0.60 - 0.45 - f0 - fee(0.60)) + 2 * (1 - 0.45 - f0)) / 3)) < 1e-12
print("test_hedge2: ok")
