"""Plain assert tests for L1B (src/scalper/l1b.py); run with: python tests/test_l1b.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import l1b as B
from scalper import lstrats as L

# The three live series, no more; its own file, never book.sqlite.
assert B.SERIES == ("KXBTC15M", "KXETH15M", "KXGOLD15M") and A.ALT_DB.name == "l1b.sqlite"
# The window ends strictly before the earliest close the book holds (2026-09-02 19:30 UTC).
assert B.FLOOR_TS == 1_788_377_400 and B.FETCH_DAYS == 69
mk = lambda s, c: {"series": s, "close_ts": c}
kept = B.holdout([mk("KXBTC15M", B.FLOOR_TS - 1), mk("KXBTC15M", B.FLOOR_TS), mk("KXGOLD15M", B.FLOOR_TS - 900), mk("KXXRP15M", B.FLOOR_TS - 5)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXBTC15M", B.FLOOR_TS - 1), ("KXGOLD15M", B.FLOOR_TS - 900)], "an entry from the book's own days is not a holdout"
# The rule is L1's own, unchanged.
assert L.L1 == {"left_s": 360, "band": (0.88, 0.97)}
# fetch() asks the shared fetcher for the three series and ONLY the days before the floor, then restores what it found.
from scalper import backfill
seen = {}
orig, saved = backfill._fetch, backfill.SERIES
def fake(db, lo, hi, label, skip_empty=False):
    seen.update(series=backfill.SERIES, lo=lo, hi=hi, skip=skip_empty)
    return 0, 0, 0
backfill._fetch = fake
try:
    B.fetch()
finally:
    backfill._fetch = orig
assert seen["series"] == B.SERIES and seen["hi"] == B.FLOOR_TS - 1 and seen["skip"] is True and backfill.SERIES == saved
import time
assert abs((time.time() - seen["lo"]) - 69 * 86400) < 60
code = "\n".join(l.split("#")[0] for l in Path(B.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("L1B passed")
