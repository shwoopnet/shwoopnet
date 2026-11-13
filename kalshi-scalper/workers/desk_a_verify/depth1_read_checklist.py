"""DEPTH1 read checklist (Head's ruling Nov 13, 2026), OUTSIDE the frozen wrapper, run BEFORE the wrapper and before the started marker can be written.
  python3 -I depth1_read_checklist.py <V2 kalshi-scalper dir>
Prints: (1) data/fresh.sqlite must be ABSENT, no file and no symlink of that name (dangling included); if present, prints STOP and exits 1, the read is not run and the Head is told; (2) no result file and no started marker exist;
(3) the read time has come. States that every Bitcoin window will be 'unknown' for the OICORE mark (the mark prints a split only; the verdict is on all windows). Reads no R6 file and no outcome."""
import os, sys, time
from pathlib import Path
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else sys.exit(__doc__)
data = root / "data"; fresh = data / "fresh.sqlite"
bad = False
present = os.path.lexists(str(fresh)) or os.path.lexists(str(root / "data" / "fresh.sqlite-wal")) or os.path.lexists(str(root / "data" / "fresh.sqlite-journal"))
print("CHECK 1 data/fresh.sqlite (and its -wal/-journal): %s" % ("PRESENT (symlink: %s)" % os.path.islink(str(fresh)) if present else "absent (no file, no symlink)"))
bad |= present
for name in ("depth1_result.txt", "depth1_started", "depth1_started.txt"):
    p = data / name
    if os.path.lexists(str(p)): print("CHECK 2 %s EXISTS: the read has been run or started once; do not run it again" % p); bad = True
print("CHECK 2 result file and started marker: %s" % ("FOUND, see above" if bad and not present else "none"))
READ_NOT_BEFORE = 1794614400
now = time.time(); ok = now >= READ_NOT_BEFORE
print("CHECK 3 read time 2026-11-14T00:00:00Z: %s (now %s UTC)" % ("reached" if ok else "NOT reached: the read refuses itself", time.strftime("%Y-%m-%d %H:%M", time.gmtime(now))))
bad |= not ok
print("NOTE: Bitcoin's OICORE overlap mark will be 'unknown' for every Bitcoin window (no candle file); the split 'without held windows' prints n 0 for Bitcoin; the verdict is on all windows (Head, Nov 13).")
print("CHECKLIST %s" % ("STOP: tell the Head before running anything" if bad else "CLEAR"))
sys.exit(1 if bad else 0)
