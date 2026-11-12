"""DEPTH1 price-free pre-check (Auditor B's remark): how many otherwise-eligible windows have a coverage `result` that is NOT yes/no, BEFORE the one read, so a recorder that wrote coverage rows before settlement cannot silently trip the 1% stop and spend the read.
Reads only the coverage files (a presence count of the result column; no price, no size, no book, no tape). Does NOT write the started marker or the result file.
  python3 -I depth1_precheck.py <path to the kalshi-scalper dir of V2's branch>
Prints, per market, exactly: otherwise-eligible windows (V2's usable() with the result forced to yes, dated inside the blocks), windows with a yes/no result present (combined) and windows without, and the share without (yes and no are never counted apart: that would read a base rate of the read window) (the wrapper's STOP is above 1% of FIRED windows; a window fires on nearly every poll, so this share is the number to watch)."""
import sys, collections
from pathlib import Path
def precheck(D, cov=None):
    """per market exactly two numbers from the result column: windows with a yes/no result present (yes and no COMBINED, never split) and windows without one, plus the share without. Nothing else is read from that column."""
    cov = D._coverage() if cov is None else cov
    out = {m: [0, 0] for m in D.UNIVERSE}
    for (close, ser), (r, row) in cov.items():
        if ser not in out: continue
        rr = dict(row); rr["result"] = "yes"                      # V2's own usable() with the result forced, so only coverage health decides eligibility
        d = D.central_date(close)
        if not D.usable(close, rr) or d < D.FIRST_DATE or D.block_of(d) is None: continue
        out[ser][0 if row.get("result") in ("yes", "no") else 1] += 1
    lines = []
    for m, (p, n) in out.items():
        lines.append(f"{m}: otherwise-eligible windows {p + n}; with a result present {p}; without one {n} ({100 * n / (p + n):.2f}%)" if p + n else f"{m}: no eligible windows")
    return lines, out
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src")); from scalper import depth1 as D
    print("\n".join(precheck(D)[0]))
