"""Plain assert tests for RECFEED (src/scalper/recfeed.py, the recorder status line); run with: python tests/test_recfeed.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import recfeed as R

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc).timestamp()
H = 3600
names = [r[0] for r in R.RECORDERS]
fresh = {n: int(NOW - 1 * H) for n in names}

# 1. everything recent: no STALE
body, stale = R.describe(NOW, fresh)
assert stale == [] and "STALE" not in body

# 2. one recorder past its allowance is named, the others are not
p = dict(fresh); p[names[0]] = int(NOW - 9 * H)
body, stale = R.describe(NOW, p)
assert stale == [names[0]] and "STALE: " + names[0] in body

# 3. never pushed is STALE
p = dict(fresh); p[names[3]] = None
assert R.describe(NOW, p)[1] == [names[3]]

# 4. R6 after its end date is "ended", not stale, however old
late = datetime(2026, 11, 20, tzinfo=timezone.utc).timestamp()
p = {n: int(late - 1 * H) for n in names}; p[names[2]] = int(late - 100 * H)
body, stale = R.describe(late, p)
assert names[2] not in stale and "ended 2026-11-13" in body

# 5. the status line never raises, even when git fails
R._git = lambda *a: (_ for _ in ()).throw(RuntimeError("no git"))
line = R.status_line(do_fetch=False)
assert line.startswith("RECORDERS: status failed"), line

# 6. the git pathspec is anchored at the repo root (cwd is kalshi-scalper/, the folders are not under it)
seen = []
R._git = lambda *a: (seen.append(a), b"1793000000\n")[1]
assert R.last_push("origin/quote-data", "quotes") == 1793000000 and ":(top)quotes" in seen[0]
print("recfeed: all passed")
