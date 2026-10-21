"""ML1 (README, Pre-registration: RP1, CS1, FA1 and ML1): L1's band by minutes left for gold, Bitcoin and Ethereum. Information only: no verdict, no try.
Usage: python -m scalper.ml1
"""
from __future__ import annotations

import statistics as st

from .gold1 import jeffreys, load
from .lstrats import L1, hold_rule
from .paths import DATA_DIR

MINUTES = [10, 9, 8, 7, 6, 5, 4, 3]
SERIES = ["KXGOLD15M", "KXBTC15M", "KXETH15M"]


def main() -> None:
    markets = []
    for name in ("l1b", "book"):
        markets += load(DATA_DIR / f"{name}.sqlite")
    for ser in SERIES:
        mk = [m for m in markets if m[1] == ser]
        print(f"\n== {ser}  ({len(mk)} markets, 69 days)")
        print("  min  n     net     loss%  Jeffreys95        mean price")
        for m in MINUTES:
            es = hold_rule(mk, m * 60, L1["band"])
            if not es:
                print(f"  {m:2d}   0")
                continue
            n = len(es)
            k = sum(1 for e in es if e["gross"] < 0)
            lo, hi = jeffreys(k, n)
            print(f"  {m:2d} {n:5d} {100 * st.mean(e['net'] for e in es):+6.2f}c {100 * k / n:6.2f}  {100 * lo:5.2f}-{100 * hi:5.2f}     {100 * st.mean(e['price'] for e in es):5.1f}c")


if __name__ == "__main__":
    main()
