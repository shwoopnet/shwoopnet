"""STACK1 (README, Pre-registration: STACK1): is FLAT2's gap present inside the live 10 minute entry (claim A) and the one-crypto-order-per-window rule (claim B)? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.stack1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys
from collections import defaultdict

from . import feat1 as F
from . import flat1, flat2
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
ORDER = ["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"]
MIN_N, MONTH_MIN = 300, 100
RESULT = DATA_DIR / "stack1_result.txt"


def first_per_window(rows: list[dict]) -> list[dict]:
    """The #459 rule: of the crypto entries in one window keep the first in ORDER."""
    by = defaultdict(list)
    for r in rows:
        if r["series"] in ORDER:
            by[r["close_ts"]].append(r)
    return [sorted(v, key=lambda r: ORDER.index(r["series"]))[0] for v in by.values()]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    r6, _, _ = F.build(full, 360)
    r10, _, _ = F.build(full, 600)
    out = []
    for name, rows in (("A: 10 minute entries", r10), ("B: first crypto per window at 6 minutes", first_per_window(r6))):
        out.append(name)
        out += [f"{k}: {v}" for k, v in flat1.judge(*flat2.split(rows), min_n=MIN_N, month_min=MONTH_MIN).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
