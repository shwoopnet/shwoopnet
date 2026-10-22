"""History information for SQ1 and TS1 (README, Pre-registration: SQ1, TS1 and CW10). In-sample by construction (the cuts came from this data): NOT a test, decides nothing.
Usage: python -m scalper.hist_sq_ts
"""
from __future__ import annotations

from . import fwd_reads as R
from .hs1 import load


def main() -> None:
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    print("INFORMATION ONLY (in-sample by construction), TREE2 pool, 69 days")
    print(R.sq1(full))
    print(R.ts1(full))
    for line in R.cw10(full):
        print(line)


if __name__ == "__main__":
    main()
