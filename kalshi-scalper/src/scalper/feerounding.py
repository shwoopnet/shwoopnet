"""What L1 nets per contract once Kalshi's per-order fee rounding is applied. A measurement of the cost model, not a hypothesis: no verdict.

The backtests charge the unrounded fee 0.07 * p * (1 - p) per contract. Kalshi's fee-rounding page says a non-direct member's balance
moves in whole cents, so a buy pays its fee plus whatever rounding brings the balance back to the cent: the whole order costs
ceil_to_the_cent(count * (price + fee)). A one contract order at 92c with a 0.5c fee therefore pays about 1c, not 0.5c. Two contracts of
the same pay 1c between them. This script prices L1's 3,400 entries both ways for counts 1 to 5.

Usage: python -m scalper.feerounding
"""
from __future__ import annotations

import math

from . import lstrats as L
from .scalps import fee, load as load_markets


def order_cost(price: float, count: int, mult: float = 1.0) -> float:
    """Dollars a taker BUY of `count` contracts at `price` costs in total: ceil to the cent of count * (price + fee), a single fill."""
    raw = count * (price + fee(price, mult))
    return math.ceil(round(raw * 100, 6)) / 100.0


def net_per_contract(entries: list[dict], count: int, rounded: bool, mult: float = 1.0) -> float:
    tot = 0.0
    for e in entries:
        win = 1.0 if e["gross"] + e["price"] > 0.5 else 0.0     # gross is won - price, so gross + price is 1 on a win and 0 on a loss
        cost = order_cost(e["price"], count, mult) if rounded else count * (e["price"] + fee(e["price"], mult))
        tot += (count * win - cost) / count
    return tot / len(entries)


def main() -> None:
    markets, _ = load_markets()
    ents = L.hold_rule(markets, **L.L1)
    print(f"L1: {len(ents)} entries. Net per contract, cents.\n")
    print("count   unrounded fee   cent-rounded order   difference   fee per contract (rounded)")
    for n in (1, 2, 3, 4, 5):
        a, b = net_per_contract(ents, n, False), net_per_contract(ents, n, True)
        extra = sum(order_cost(e["price"], n) - n * (e["price"] + fee(e["price"])) for e in ents) / len(ents) / n
        fpc = sum(order_cost(e["price"], n) - n * e["price"] for e in ents) / len(ents) / n
        print(f"{n:>5}   {a * 100:>+12.2f}c   {b * 100:>+17.2f}c   {(b - a) * 100:>+9.2f}c   {fpc * 100:>8.2f}c")
    print("\nInformation only. Cent-sized prices keep the whole order on the cent grid; tenth-of-a-cent prices lose up to a cent more to the rounding.")


if __name__ == "__main__":
    main()
