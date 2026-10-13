"""Plain assert tests for GROWTH3 (src/scalper/growth3.py); run with: python tests/test_growth3.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import growth as G
from scalper import growth3 as G3

# Drawdown is the largest fall from the running peak, as a share of that peak.
assert G3.max_drawdown([100, 120, 90, 130, 117]) == 0.25 and G3.max_drawdown([100, 110, 120]) == 0.0 and G3.max_drawdown([100, 50, 100]) == 0.5
# The knobs are what the sizing reads, and main() restores the live values afterwards.
win = [[[{"series": "KXBTC15M", "close_ts": 1, "price": 0.92, "net": 0.05, "day": "d"}]]]
live = G.simulate_path(win, 0.0, __import__("random").Random(1), horizon=1, fill=1.0)[0]
live_vals = (G.PER_CONTRACT, G.MAX_CONTRACTS)
small = G3.simulate(win, 0.0, 23.25, 40, 1)[0][0]
assert small > live and (G.PER_CONTRACT, G.MAX_CONTRACTS) == (23.25, 40), "twice the contracts earn about twice as much on the same entry"
G.PER_CONTRACT, G.MAX_CONTRACTS = live_vals
assert G.PER_CONTRACT == 46.5 and G.MAX_CONTRACTS == 40
code = "\n".join(l.split("#")[0] for l in Path(G3.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("GROWTH3 passed")
