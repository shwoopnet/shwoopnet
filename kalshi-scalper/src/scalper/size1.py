"""SIZE1 (README, Pre-registration: HL1, SL1, an interim look at ML1, and SIZE1): Kelly fractions per series from L1's measured win rate. Information only.
Usage: python -m scalper.size1
"""
from __future__ import annotations

import statistics as st

from .gold1 import jeffreys, load
from .lstrats import L1, hold_rule
from .paths import DATA_DIR

FEE = 0.005
SERIES = ["KXGOLD15M", "KXBTC15M", "KXETH15M"]


def kelly(loss_rate: float, price: float) -> float:
    b = (1 - price - FEE) / (price + FEE)               # win payoff per dollar risked
    w = 1 - loss_rate
    return max(0.0, (w * b - (1 - w)) / b)


def main() -> None:
    markets = []
    for name in ("l1b", "book"):
        markets += load(DATA_DIR / f"{name}.sqlite")
    print("series      n   price  loss% (95% upper)   Kelly@point  Kelly@upper  half-Kelly@point   break-even loss%")
    for ser in SERIES:
        es = hold_rule([m for m in markets if m[1] == ser], L1["left_s"], L1["band"])
        n, k = len(es), sum(1 for e in es if e["gross"] < 0)
        p = st.mean(e["price"] for e in es)
        lo, hi = jeffreys(k, n)
        gain = 1 - p - FEE
        be = gain / (gain + p + FEE)
        print(f"{ser:10s} {n:5d}  {100*p:5.1f}c  {100*k/n:5.2f} ({100*hi:5.2f})   {100*kelly(k/n,p):9.1f}%  {100*kelly(hi,p):9.1f}%  {50*kelly(k/n,p):12.1f}%   {100*be:6.2f}")


if __name__ == "__main__":
    main()
