"""Plain assert tests for FWD1 (src/scalper/fwd1.py); run with: python tests/test_fwd1.py. Each states a consequence, not a mechanism."""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import e3f
from scalper import fwd1 as F

# Registered: the three live series, forward days only, its own file, E3F's start and read date and E3F's bar function.
assert F.SERIES == ("KXBTC15M", "KXETH15M", "KXGOLD15M") and A.ALT_DB.name == "fwd1.sqlite" and F.START_TS == e3f.START_TS == 1_791_936_000 and F.EARLIEST_READ_TS == e3f.EARLIEST_READ_TS
assert F.e3f.verdict is e3f.verdict
# Days that existed on 2026-10-13 never count; neither does another series.
mk = lambda s, c: {"series": s, "close_ts": c}
kept = F.forward([mk("KXBTC15M", F.START_TS - 1), mk("KXBTC15M", F.START_TS), mk("KXGOLD15M", F.START_TS + 5), mk("KXXRP15M", F.START_TS + 9)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXBTC15M", F.START_TS), ("KXGOLD15M", F.START_TS + 5)]
# The download always reaches back to the start: on the read date it is 33 or 34 days, never fewer.
d = F.fetch_days(F.EARLIEST_READ_TS)
assert d == 34 and F.fetch_days(F.START_TS) == 2 and F.fetch_days(F.START_TS + 86401) == 3, d
assert F.START_TS >= F.EARLIEST_READ_TS - d * 86400
# The single read is refused before the registered date and records nothing.
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    F.run(now_ts=F.EARLIEST_READ_TS - 1)
assert "Too early" in buf.getvalue()
code = "\n".join(l.split("#")[0] for l in Path(F.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("FWD1 passed")
