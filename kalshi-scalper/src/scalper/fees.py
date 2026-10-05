"""Kalshi fee model.

Why this exists as its own module: for a scalper the fee is the product.
It is quadratic in price (largest at 50c, tiny near 0 or 100), and a
position closed before settlement pays it on BOTH legs, while one held to
settlement pays it once. Every strategy decision has to be made net of this.

ASSUMPTION TO VERIFY: the 0.07 taker rate and the cent rounding are from
memory of Kalshi's published schedule. The series endpoint reports
fee_type='quadratic' and a fee_multiplier; confirm the rate against the
fee schedule and against real fills (fills carry the fee actually charged)
before trusting any number built on this.
"""
from __future__ import annotations

import math

TAKER_RATE = 0.07


def taker_fee(price: float, contracts: int = 1, multiplier: float = 1.0) -> float:
    """Dollar fee for one taker order. Rounded UP to the next cent per order."""
    if not 0.0 < price < 1.0:
        return 0.0
    raw = TAKER_RATE * multiplier * contracts * price * (1.0 - price)
    return math.ceil(round(raw * 100, 9)) / 100.0


def round_trip_cost(entry_ask: float, exit_bid: float, contracts: int = 1,
                    multiplier: float = 1.0) -> float:
    """Dollars lost to cross the spread and pay fees on both legs, before any
    price movement. Entry at the ask, exit at the bid. Break-even needs the
    market to move by at least this much in our favour."""
    spread_loss = (entry_ask - exit_bid) * contracts
    fees = taker_fee(entry_ask, contracts, multiplier) + taker_fee(exit_bid, contracts, multiplier)
    return spread_loss + fees
