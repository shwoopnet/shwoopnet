"""Plain assert tests for scalper.seriescensus on fake lists only (no network). Run: cd kalshi-scalper && PYTHONPATH=src python tests/test_seriescensus.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import seriescensus as C

DAY = 24 * 3600
t0 = 1_800_000_000.0
settled = {"A", "B"}
lst = lambda: ["A", "B", "C", "D"]
st = lambda t: t in settled

# first census: baseline, no NEW SERIES, counts only
s = {}
line = C.census(s, t0, lst, st)
assert line.startswith("SERIES CENSUS: 4 fifteen_min series, 2 with at least one settled market"), line
assert "NEW SERIES" not in line and s[C.KEY]["has"] == {"A": True, "B": True, "C": False, "D": False}

# not due for 7 days: returns None and changes nothing
before = dict(s[C.KEY])
assert C.census(s, t0 + 6 * DAY, lst, st) is None and s[C.KEY] == before

# due: nothing changed, no NEW SERIES; settled series are not asked again
asked = []
line = C.census(s, t0 + 7 * DAY, lst, lambda t: asked.append(t) or t in settled)
assert "NEW SERIES" not in line and asked == ["C", "D"], (line, asked)

# an empty series gains a settled market: the line begins with NEW SERIES and names it
settled.add("C")
line = C.census(s, t0 + 14 * DAY, lst, st)
assert line.startswith("NEW SERIES C now settled: 4 fifteen_min series, 3 with at least one"), line

# a newly listed series that already settled counts as new; one that did not does not
line = C.census(s, t0 + 21 * DAY, lambda: ["A", "B", "C", "D", "E", "F"], lambda t: t in settled | {"E"})
assert line.startswith("NEW SERIES E now settled") and "F" not in line.split(":")[0], line

# errors are caught and the state is left alone (tried again next pass)
def boom(): raise RuntimeError("down")
state_before = dict(s[C.KEY])
line = C.census(s, t0 + 28 * DAY, boom, st)
assert line.startswith("SERIES CENSUS: failed") and s[C.KEY] == state_before and C.due(s, t0 + 28 * DAY)

# a failing per-series call counts as none, not a crash
s2 = {}
def flaky(t):
    if t == "B": raise RuntimeError("429")
    return t == "A"
line = C.census(s2, t0, lst, flaky)
assert "1 with at least one settled market" in line and s2[C.KEY]["has"]["B"] is False
print("test_seriescensus: ok")
