"""FLAT2 (README, Pre-registration: FLAT2): FLAT1 with the looser cut rng5 <= 0.15 and |rise3| <= 0.05. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flat2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys

from . import feat1 as F
from . import flat1
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
RNG5_MAX, RISE3_MAX = 0.15, 0.05
RESULT = DATA_DIR / "flat2_result.txt"


def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    flat = [r for r in rows if r["x"][flat1.I_RNG5] <= RNG5_MAX and abs(r["x"][flat1.I_RISE3]) <= RISE3_MAX]
    ids = {id(r) for r in flat}
    return flat, [r for r in rows if id(r) not in ids]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    out = ["FLAT2 primary (all series)"] + [f"{k}: {v}" for k, v in flat1.judge(*split(rows)).items()]
    out.append("info: live five series only")
    out += [f"{k}: {v}" for k, v in flat1.judge(*split([r for r in rows if r["series"] in flat1.LIVE])).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
