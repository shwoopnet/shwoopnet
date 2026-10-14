"""Plain assert tests for E5B and E3C (src/scalper/e5b.py, e3c.py); run with: python tests/test_e5b_e3c.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import backfill
from scalper import e3c as C
from scalper import e5
from scalper import e5b as B

mk = lambda s, c: {"series": s, "close_ts": c}
# E5B: WTI only, strictly before E5's split.
kept = B.holdout([mk("KXWTI15M", e5.SPLIT_TS - 1), mk("KXWTI15M", e5.SPLIT_TS), mk("KXSILVER15M", e5.SPLIT_TS - 5)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXWTI15M", e5.SPLIT_TS - 1)] and B.SERIES == "KXWTI15M"
# E3C: HYPE and BNB only, strictly before E3's floor, its own file.
assert C.SERIES == ("KXHYPE15M", "KXBNB15M") and C.FLOOR_TS == e5.SPLIT_TS == 1_788_465_600 and C.FETCH_DAYS == 69
kept = C.holdout([mk("KXHYPE15M", C.FLOOR_TS - 1), mk("KXHYPE15M", C.FLOOR_TS), mk("KXBNB15M", C.FLOOR_TS - 900), mk("KXXRP15M", C.FLOOR_TS - 5)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXHYPE15M", C.FLOOR_TS - 1), ("KXBNB15M", C.FLOOR_TS - 900)]
assert A.ALT_DB.name in ("alts4.sqlite", "alts3.sqlite")
# fetch() asks only for the days before the floor and restores the shared series list.
seen = {}
orig, saved = backfill._fetch, backfill.SERIES
backfill._fetch = lambda db, lo, hi, label, skip_empty=False: (seen.update(series=backfill.SERIES, hi=hi, skip=skip_empty) or (0, 0, 0))
try:
    C.fetch()
finally:
    backfill._fetch = orig
assert seen["series"] == C.SERIES and seen["hi"] == C.FLOOR_TS - 1 and seen["skip"] is True and backfill.SERIES == saved
for m in (B, C):
    code = "\n".join(l.split("#")[0] for l in Path(m.__file__).read_text().splitlines())
    assert "promote" not in code.lower()
print("E5B and E3C passed")
