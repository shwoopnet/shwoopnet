"""Plain assert tests for E3F (src/scalper/e3f.py); run with: python tests/test_e3f.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import e3f as F
from scalper.scalps import STRESS, fee

# Registered: two series, forward days only (from 2026-10-14 UTC), its own file, one read on or after 2026-11-16.
assert F.SERIES == ("KXXRP15M", "KXDOGE15M") and A.ALT_DB.name == "e3f.sqlite"
assert F.START_TS == 1_791_936_000 and F.EARLIEST_READ_TS - F.START_TS == 33 * 86400, (F.START_TS, F.EARLIEST_READ_TS)

# Days that existed when E3 was read can never count: an entry that closed before the start is dropped, as is any other series.
mk = lambda s, c: {"series": s, "close_ts": c, "day": "d", "net": 0.01, "stress": 0.0}
kept = F.forward([mk("KXXRP15M", F.START_TS - 1), mk("KXXRP15M", F.START_TS), mk("KXDOGE15M", F.START_TS + 5), mk("KXHYPE15M", F.START_TS + 9)])
assert [(e["series"], e["close_ts"]) for e in kept] == [("KXXRP15M", F.START_TS), ("KXDOGE15M", F.START_TS + 5)]

# The one read is refused before the registered date and records nothing.
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    F.run(now_ts=F.EARLIEST_READ_TS - 1)
assert "Too early" in buf.getvalue()

# Verdicts.
def rows(day_net, n_days=12, per=50, stress_off=0.0):
    return [{"series": "KXXRP15M", "close_ts": d, "day": f"2026-11-{d + 1:02d}", "net": day_net(d), "stress": day_net(d) - stress_off} for d in range(n_days) for _ in range(per)]
assert F.verdict(rows(lambda d: 0.05, per=10))[0] == "NOT_ENOUGH_DATA" and F.verdict(rows(lambda d: 0.05, n_days=5, per=200))[0] == "NOT_ENOUGH_DATA"
# Clears every part: positive in both halves with a high z.
v, s = F.verdict(rows(lambda d: 0.10 if d % 2 else 0.04))
assert v == "NOT_YET_FALSIFIED" and s["z"] >= F.Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0, (v, s)
# Each part bites alone.
v, s = F.verdict(rows(lambda d: 0.10 if d < 6 else -0.01)); assert s["h1"] > 0 > s["h2"] and s["z"] >= F.Z_BAR and v == "FALSIFIED", (v, s)
v, s = F.verdict(rows(lambda d: -0.01 if d < 6 else 0.10)); assert s["h2"] > 0 > s["h1"] and s["z"] >= F.Z_BAR and v == "FALSIFIED", (v, s)
v, s = F.verdict(rows(lambda d: 0.10 if d % 2 else 0.04, stress_off=0.2)); assert s["stress"] < 0 < s["mean"] and s["z"] >= F.Z_BAR and v == "FALSIFIED", (v, s)
v, s = F.verdict(rows(lambda d: 0.30 if d % 2 else -0.20)); assert 0 < s["mean"] and s["z"] < F.Z_BAR and s["h1"] > 0 and s["h2"] > 0 and v == "FALSIFIED", (v, s)
v, s = F.verdict(rows(lambda d: -0.02)); assert v == "FALSIFIED"

code = "\n".join(l.split("#")[0] for l in Path(F.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("E3F passed")
