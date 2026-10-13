"""Plain assert tests for E3 (src/scalper/e3.py); run with: python tests/test_e3.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import e3 as E

# The seven registered series, no more: a series added later would be an unregistered try.
assert E.SERIES == ("KXXRP15M", "KXDOGE15M", "KXHYPE15M", "KXBNB15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M") and len(set(E.SERIES)) == 7
# History goes to its own file, never the Bitcoin and gold database or the ETH and SOL one.
assert A.ALT_DB.name == "alts2.sqlite" and A.ALT_DB.name not in ("book.sqlite", "alts.sqlite")
# The rule is L1's, unchanged: the same minute and band as the live bot's study constants.
from scalper import lstrats as L
assert L.L1 == {"left_s": 360, "band": (0.88, 0.97)}
# fetch() points the shared fetcher at these seven series and restores what it found, so nothing else is affected.
from scalper import backfill
seen = {}
orig = A.fetch
A.fetch = lambda days: seen.update(series=A.ALTS, days=days)
try:
    E.fetch()
finally:
    A.fetch = orig
assert seen == {"series": E.SERIES, "days": 40}
code = "\n".join(l.split("#")[0] for l in Path(E.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("E3 passed")
