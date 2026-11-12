"""DEPTH1 price-free pre-check (Auditor B's remark): how many otherwise-eligible windows have a coverage `result` that is NOT yes/no, BEFORE the one read, so a recorder that wrote coverage rows before settlement cannot silently trip the 1% stop and spend the read.
Reads only the coverage files (counts and result values; no price, no size, no book, no tape). Does NOT write the started marker or the result file.
  python3 -I depth1_precheck.py <path to the kalshi-scalper dir of V2's branch>
Prints, per market: otherwise-eligible windows (V2's usable() with the result forced to yes, dated inside the blocks) and the count by raw result value; and the share that is not yes/no (the wrapper's STOP is above 1% of FIRED windows; a window fires on nearly every poll, so this share is the number to watch)."""
import sys, collections
from pathlib import Path
def precheck(D, cov=None):
    cov = D._coverage() if cov is None else cov
    out = {}
    for m in D.UNIVERSE: out[m] = collections.Counter()
    for (close, ser), (r, row) in cov.items():
        if ser not in out: continue
        rr = dict(row); rr["result"] = "yes"
        d = D.central_date(close)
        if not D.usable(close, rr) or d < D.FIRST_DATE or D.block_of(d) is None: continue
        out[ser][row.get("result") or "(empty)"] += 1
    lines = []
    for m, c in out.items():
        n = sum(c.values()); bad = n - c.get("yes", 0) - c.get("no", 0)
        lines.append(f"{m}: otherwise-eligible windows {n}; by result {dict(c)}; not yes/no {bad} ({100 * bad / n:.2f}%)" if n else f"{m}: no eligible windows")
    return lines, out
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src")); from scalper import depth1 as D
    print("\n".join(precheck(D)[0]))
