"""Plain assert tests for src/scalper/famxv.py, synthetic data only. Run: cd kalshi-scalper && PYTHONPATH=src python tests/test_famxv.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import famxv as X

s = X.slug_candidates("nba", "MIA", "TOR", 1791068400)
assert s[0] == "nba-mia-tor-2026-10-03" and s[1] == "nba-tor-mia-2026-10-03" and len(s) == len(set(s))

m = {"outcomes": '["Heat", "Raptors"]'}
assert X.team_token(m, ["TOR", "Toronto", "Raptors"]) == 1 and X.team_token(m, ["MIA", "Miami", "Heat"]) == 0 and X.team_token(m, ["X"]) is None

h = [(100, 0.5), (200, 0.6), (300, 0.7)]
assert X.pm_at(h, 250) == 0.6 and X.pm_at(h, 50) is None and X.pm_at(h, 300 + 901) is None and X.pm_at(h, 300) == 0.7   # nothing after the look is used

S = 100000
cs = [(S - 6000, 0.5, 0.52), (S - 3600, 0.5, 0.52), (S - 3000, 0.55, 0.57), (S - 1000, 0.9, 0.95)]
assert X.k_ask(cs, S) == (0.57, 0.55, S - 3000)                      # the 1000 s candle is too late, the 6000 s too early
assert X.k_ask([(S - 3000, 0.4, 0.6)], S) is None                     # spread over 10c
assert X.pick([(0.05, "h", 0.5, True), (0.01, "a", 0.5, False)], 0.04)[1] == "h" and X.pick([(0.05, "h", 0.5, True)], 0.08) is None
print("famxv tests ok")
