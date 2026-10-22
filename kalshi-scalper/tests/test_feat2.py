"""Plain assert tests for FEAT2 (src/scalper/feat2.py); run with: python tests/test_feat2.py."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import feat2 as G

assert G.KEEP_Q == 0.40
# expected net: a 0.95 entry with a 4% chance of losing is worth (0.96)(0.05-0.0033) - 0.04(0.9533) ~ +0.0067; with 6% it is negative
p, pr = np.array([0.04, 0.06, 0.04]), np.array([0.95, 0.95, 0.90])
e = G.expected_net(p, pr)
assert abs(e[0] - (0.96 * (1 - 0.95 - 0.07 * 0.95 * 0.05) - 0.04 * (0.95 + 0.07 * 0.95 * 0.05))) < 1e-12
assert e[0] > 0 > e[1], "at the same price a higher loss chance lowers the value"
assert e[2] > e[0], "at the same loss chance a lower price pays more"
print("test_feat2: ok")
