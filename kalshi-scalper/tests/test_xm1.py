"""Plain assert tests for XM1 (src/scalper/xm1.py); run with: python tests/test_xm1.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import xm1 as X
from scalper.scalps import fee

# The registered pairs, no more; history in its own file.
assert X.PAIRS == {"KXBTC15M": "KXBTCD", "KXETH15M": "KXETHD"} and X.XM_DB.name == "xm1.sqlite" and X.ENTRY_LEFT_S == 360

# Strike choice uses the strike alone: within 1.5% of the 15 minute strike, both sides.
assert X.near_strikes([80000, 82000, 83000, 83100, 84000, 90000], 83100.0) == [82000, 83000, 83100, 84000]

# Interpolation: the ladder's mid, linear between the bracketing strikes; exactly on a strike gives that strike's mid; no bracket or a bad quote gives None.
q = {83000.0: (0.18, 0.20), 83100.0: (0.08, 0.10)}
assert abs(X.interpolate(q, 83050.0) - (0.19 + (0.09 - 0.19) * 0.5)) < 1e-12
assert abs(X.interpolate(q, 83000.0) - 0.19) < 1e-12 and abs(X.interpolate(q, 83100.0) - 0.09) < 1e-12
assert X.interpolate(q, 83200.0) is None and X.interpolate(q, 82900.0) is None, "no bracket, no probability"
assert X.interpolate({83000.0: (0.18, 0.20), 83100.0: (0.0, 1.0)}, 83050.0) is None, "a bracket strike with an unusable quote means no trade"
four = {83000.0: (0.78, 0.80), 83050.0: (0.58, 0.60), 83100.0: (0.38, 0.40), 83150.0: (0.08, 0.10)}
assert abs(X.interpolate(four, 83060.0) - (0.59 + (0.39 - 0.59) * 0.2)) < 1e-12, "the NEAREST two strikes bracket, not the outermost"
assert X.interpolate({83000.0: (0.18, 0.20)}, 83000.0) == 0.19, "a single strike exactly at the 15 minute strike is the answer"

# Trade choice: larger edge after the fee, at least 2c, price inside 3c to 97c.
y = X.xm_trade(0.60, 0.50, 0.52)
assert y[0] == "yes" and abs(y[2] - (0.60 - 0.52 - fee(0.52))) < 1e-12
n = X.xm_trade(0.30, 0.50, 0.52)
assert n[0] == "no" and abs(n[1] - 0.50) < 1e-12 and abs(n[2] - (0.70 - 0.50 - fee(0.50))) < 1e-12
assert X.xm_trade(0.52, 0.50, 0.52) is None, "no edge, no trade"
assert X.xm_trade(0.55, 0.50, 0.52) is None, "an edge of 1.25c after the fee is under the registered 2c"
assert X.xm_trade(0.999, 0.01, 0.02) is None, "a price outside 3c to 97c is never taken"

# Simulation: a window whose ladder says 60% while the 15 minute ask is 52c trades YES and is scored on the 15 minute market's own result at the 15 minute ask.
C = 1_800_000_000
w = {"ticker": "T", "series": "KXBTC15M", "close_ts": C, "result": "yes", "k": 83050.0, "bid": 0.50, "ask": 0.52}
tr, gaps = X.simulate([w], {"T": {83000.0: (0.64, 0.66), 83100.0: (0.54, 0.56)}})
assert len(tr) == 1 and tr[0]["side"] == "yes" and abs(tr[0]["price"] - 0.52) < 1e-12 and abs(tr[0]["net"] - (1 - 0.52 - fee(0.52))) < 1e-12
assert abs(gaps[0]["gap"] - (0.60 - 0.51)) < 1e-12
# No ladder quotes or no bracket: no trade and no gap row, never a guess.
assert X.simulate([w], {}) == ([], []) and X.simulate([w], {"T": {83100.0: (0.54, 0.56)}}) == ([], [])
# A losing result is scored as a loss.
tr2, _ = X.simulate([dict(w, result="no")], {"T": {83000.0: (0.64, 0.66), 83100.0: (0.54, 0.56)}})
assert abs(tr2[0]["net"] - (-0.52 - fee(0.52))) < 1e-12

code = "\n".join(l.split("#")[0] for l in Path(X.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("XM1 passed")
