"""Plain assert tests for E3B (src/scalper/e3b.py); run with: python tests/test_e3b.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import e3b as B
from scalper import e3f as F

# Registered: the same two series as E3F, its own file, the bar is E3F's function.
assert B.SERIES == ("KXXRP15M", "KXDOGE15M") == F.SERIES and A.ALT_DB.name == "e3b.sqlite" and B.e3f.verdict is F.verdict
# E3's earliest close was 2026-09-03 20:00 UTC; the E3B window ends strictly before it.
assert B.FLOOR_TS == 1_788_465_600
mk = lambda s, c: {"series": s, "close_ts": c, "day": "d", "net": 0.01, "stress": 0.0}
kept = B.holdout([mk("KXXRP15M", B.FLOOR_TS - 1), mk("KXXRP15M", B.FLOOR_TS), mk("KXDOGE15M", B.FLOOR_TS - 900), mk("KXHYPE15M", B.FLOOR_TS - 5)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXDOGE15M", B.FLOOR_TS - 900), ("KXXRP15M", B.FLOOR_TS - 1)], "an entry from E3's own days would not be a holdout"
# The data window reaches back past E3's 40 days, otherwise there is nothing to test.
assert B.FETCH_DAYS > 40
code = "\n".join(l.split("#")[0] for l in Path(B.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("E3B passed")
