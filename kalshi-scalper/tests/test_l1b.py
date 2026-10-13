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
assert B.FLOOR_TS == 1_788_377_400 and B.FETCH_DAYS > 40
mk = lambda s, c: {"series": s, "close_ts": c}
kept = B.holdout([mk("KXBTC15M", B.FLOOR_TS - 1), mk("KXBTC15M", B.FLOOR_TS), mk("KXGOLD15M", B.FLOOR_TS - 900), mk("KXXRP15M", B.FLOOR_TS - 5)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXBTC15M", B.FLOOR_TS - 1), ("KXGOLD15M", B.FLOOR_TS - 900)], "an entry from the book's own days is not a holdout"
# The rule is L1's own, unchanged.
assert L.L1 == {"left_s": 360, "band": (0.88, 0.97)}
# fetch() points the shared fetcher at these series and restores what it found.
seen = {}
orig = A.fetch
A.fetch = lambda days: seen.update(series=A.ALTS, days=days)
try:
    B.fetch()
finally:
    A.fetch = orig
assert seen == {"series": B.SERIES, "days": 69}
code = "\n".join(l.split("#")[0] for l in Path(B.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("L1B passed")
