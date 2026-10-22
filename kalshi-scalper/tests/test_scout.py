"""Plain assert tests for the market scout (src/scalper/scout.py); run with: python tests/test_scout.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import scout as S

assert (S.WINDOW_DAYS, S.FRAC, S.BAND, S.MIN_MARKETS, S.MIN_MEDIAN_VOLUME, S.LEAD_N, S.LEAD_DAYS, S.LEAD_NET, S.LEAD_Z) == (69, 0.60, (0.88, 0.97), 100, 500.0, 150, 10, 0.01, 2.5), "the registered numbers"
cs = [(1000 + 60 * k, 0.5, 0.52) for k in range(10)]
# life 0..1000 s from open 1000: 60% of a 600 s life = open + 360 -> the last candle ending at or before 1360
d = S.decision_candle(cs, 1000, 1600)
assert d[0] == 1360, "the last candle ending at or before 60% of the life"
assert S.decision_candle(cs, 5000, 6000) is None or S.decision_candle(cs, 5000, 6000) == cs[-1], "nothing before the open means no decision (or the last earlier one)"
assert S.entry_of((1, 0.93, 0.94)) == ("yes", 0.94) and S.entry_of((1, 0.05, 0.06)) == ("no", 0.95)
assert S.entry_of((1, 0.50, 0.52)) is None and S.entry_of((1, None, 0.94)) is None
assert abs(S.net_of("yes", 0.94, "yes") - (1 - 0.94 - S.fee(0.94))) < 1e-12 and abs(S.net_of("yes", 0.94, "no") + 0.94 + S.fee(0.94)) < 1e-12
print("test_scout: ok")
