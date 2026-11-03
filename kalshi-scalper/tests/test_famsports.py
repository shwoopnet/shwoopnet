"""Plain assert tests for src/scalper/famsports.py, synthetic data only. Run: cd kalshi-scalper && PYTHONPATH=src python tests/test_famsports.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import famsports as F

assert abs(F.norm_cdf(0.0) - 0.5) < 1e-12
assert abs(F.p_over(220.0, 220.0, 19.0) - 0.5) < 1e-12
assert F.p_over(240.0, 220.5, 19.0) > 0.8 and F.p_over(200.0, 220.5, 19.0) < 0.2
assert F.pred_total(110, 100, 120, 105) == (110 + 105) / 2 + (120 + 100) / 2

# trailing uses only earlier days, last 10, at least 5
g = [("2026-01-%02d" % d, 0, "AAA", "BBB", 100 + d, 90) for d in range(1, 13)]
h = F.build_history(g)
assert F.trailing(h, "AAA", "2026-01-04") is None            # 3 earlier games
f, a = F.trailing(h, "AAA", "2026-01-12")                     # games 1..11 -> last 10 are days 2..11
assert abs(f - sum(100 + d for d in range(2, 12)) / 10) < 1e-9 and a == 90
assert F.trailing(h, "AAA", "2026-01-12") == F.trailing(h, "AAA", "2026-01-12")   # same-day game never in its own history
assert F.trailing(h, "ZZZ", "2026-02-01") is None

# team code split
T = {"MIA", "TOR", "LAR", "SF", "GS", "WSH"}
assert F.split_code("MIATOR", T) == ("MIA", "TOR")
assert F.split_code("SFLAR", T) == ("SF", "LAR")
assert F.split_code("GSWSH", T) == ("GS", "WSH")
assert F.split_code("XXYY", T) is None

# quote validity
assert F.valid_quote(0.40, 0.45) and not F.valid_quote(0.40, 0.55) and not F.valid_quote(None, 0.5) and not F.valid_quote(0.5, 0.5) and not F.valid_quote(0.0, 0.05)

# choose: best edge, threshold, deterministic
o = [(0.05, "A", "yes", 0.5, True), (0.09, "B", "no", 0.4, False), (0.09, "C", "yes", 0.3, True)]
assert F.choose(o, 0.08)[1] == "C" and F.choose(o, 0.15) is None and F.choose([], 0.08) is None
assert abs(F.brier([(0.5, 1.0), (0.5, 0.0)]) - 0.25) < 1e-12
print("famsports tests ok")
