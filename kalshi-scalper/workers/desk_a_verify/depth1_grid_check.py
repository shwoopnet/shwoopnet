"""DEPTH1 read checklist item (Head, Nov 13, 2026), OUTSIDE the wrapper, run right before it. Prices grid check for the integer bars (Amendment 4: thousandths of a dollar are exact only for prices on the cent or tenth-of-a-cent grid).
  python3 -I depth1_grid_check.py <V2 kalshi-scalper dir>            REFUSES before 2026-11-14T00:00:00Z; at the read it opens the R6 BOOK files' price columns only (no coverage result, no trade file, no outcome is read)
  python3 -I depth1_grid_check.py <V2 kalshi-scalper dir> <fixture dir containing MADE_UP_DATA>      a made-up fixture, any time
Counts, over every book row of the recorded days (run folders dated 2026-10-29 to 2026-11-13) for KXGOLD15M and KXBTC15M, the level-1 prices that are NOT a multiple of 0.001 (within 1e-9), for the four prices a fill can use: the YES bid, the NO bid, and so the YES ask (1 - NO bid) and the NO ask (1 - YES bid); a count over ALL rows, a superset of the fill polls. If the count is not zero, both builds recompute the bars in exact fractions before any verdict is recorded."""
import sys, os, time, csv, gzip, io, subprocess
from pathlib import Path
root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else sys.exit(__doc__)
fx = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
READ = 1794614400
if fx is None and time.time() < READ: sys.exit("REFUSED: before 2026-11-14T00:00:00Z the grid check opens no recorded file")
if fx is not None: assert (fx / "MADE_UP_DATA").exists(), "a fixture must carry MADE_UP_DATA"
sys.path.insert(0, str(root / "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heldout_guard_v2 as heldout_guard
heldout_guard.refuse_heldout(str(root), "grid check")
from scalper import depth1 as D
if fx is not None:
    PFX = "book15r6/"
    names = lambda: [PFX + str(p.relative_to(fx)) for p in fx.glob("*/*/*.csv.gz")]
    blob = lambda path: list(csv.DictReader(io.TextIOWrapper(gzip.open(fx / path[len(PFX):])))) if (fx / path[len(PFX):]).exists() else []
else:
    names, blob = D._names, D._blob
off = rows = 0; examples = []
for n in sorted(x for x in names() if x.endswith("/book.csv.gz")):
    day = n.split("/")[1] if n.count("/") >= 3 else ""
    if fx is None and not ("2026-10-29" <= day <= "2026-11-13"): continue
    for r in blob(n):
        if r.get("series") not in D.UNIVERSE: continue
        rows += 1
        for col in ("yes_bid_px_1", "no_bid_px_1"):
            v = r.get(col)
            if v in (None, ""): continue
            x = float(v) * 1000
            if abs(x - round(x)) > 1e-9:
                off += 1
                if len(examples) < 3: examples.append((n, col, v))
print("GRID CHECK: book rows read %d (series %s); level-1 prices not on the 0.001 grid: %d%s" % (rows, ", ".join(D.UNIVERSE), off, "" if not off else " examples " + str(examples)))
print("GRID CHECK %s" % ("CLEAR: thousandths of a dollar are exact" if off == 0 else "STOP: both builds recompute the bars in exact fractions before any verdict is recorded; tell the Head"))
sys.exit(0 if off == 0 else 1)
