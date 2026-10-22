"""FLAT3 (README, Pre-registration: FLAT3): FLAT2's cut read at 300, 420, 480 and 540 seconds left. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flat3 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys

from . import feat1 as F
from . import flat1, flat2
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
LEFTS = (300, 420, 480, 540)
MIN_N, MONTH_MIN = 300, 100
RESULT = DATA_DIR / "flat3_result.txt"


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    out = []
    for left in LEFTS:
        rows, _, _ = F.build(full, left)
        out.append(f"{left} seconds left")
        out += [f"{k}: {v}" for k, v in flat1.judge(*flat2.split(rows), min_n=MIN_N, month_min=MONTH_MIN).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
