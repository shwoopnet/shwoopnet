"""Pre-trade risk gate. Every order must pass through check_order.

Design rules, each from a way this goes wrong with real money:
- Fail closed. Any error, missing field or unknown state rejects the order.
- Limits are in dollars at risk (price * contracts), not contract counts.
  On a binary contract the most you can lose is what you pay.
- Same-underlying positions are ONE bet. Several BTC strikes or expiries
  move together, so exposure is capped per underlying, not just in total.
- A kill switch file halts everything and cannot be bypassed by strategy code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .fees import taker_fee

KILL_FILE = Path(__file__).resolve().parents[2] / "KILL"


@dataclass
class Limits:
    bankroll: float
    max_risk_per_trade_pct: float = 0.01
    max_open_risk_pct: float = 0.05
    max_per_underlying_pct: float = 0.03
    daily_loss_limit_pct: float = 0.02
    min_edge_after_fees: float = 0.03   # probability points above cost, per contract
    max_spread: float = 0.04            # refuse to cross wide books


@dataclass
class State:
    open_risk_by_underlying: dict = field(default_factory=dict)  # {"BTC": dollars}
    realized_pnl_today: float = 0.0


@dataclass
class Order:
    underlying: str       # "BTC" or "GOLD"
    price: float          # dollars we pay per contract (the ask when taking)
    contracts: int
    my_prob: float        # our estimate that the contract settles at $1
    spread: float


def check_order(o: Order, lim: Limits, st: State) -> tuple[bool, list[str]]:
    why: list[str] = []
    try:
        if KILL_FILE.exists():
            return False, ["kill switch file present"]
        if not (0.0 < o.price < 1.0) or o.contracts <= 0 or not (0.0 <= o.my_prob <= 1.0):
            return False, ["malformed order"]

        risk = o.price * o.contracts
        if risk > lim.bankroll * lim.max_risk_per_trade_pct:
            why.append(f"trade risk ${risk:.2f} over per-trade cap")
        total_open = sum(st.open_risk_by_underlying.values())
        if total_open + risk > lim.bankroll * lim.max_open_risk_pct:
            why.append("total open risk cap")
        if st.open_risk_by_underlying.get(o.underlying, 0.0) + risk > lim.bankroll * lim.max_per_underlying_pct:
            why.append(f"{o.underlying} correlated exposure cap")
        if st.realized_pnl_today <= -lim.bankroll * lim.daily_loss_limit_pct:
            why.append("daily loss limit hit, no new risk today")
        if o.spread > lim.max_spread:
            why.append("spread too wide")

        fee_per = taker_fee(o.price, o.contracts) / o.contracts
        edge = o.my_prob - o.price - fee_per
        if edge < lim.min_edge_after_fees:
            why.append(f"edge after fees {edge:+.3f} under minimum")
    except Exception as e:
        return False, [f"gate error, failing closed: {e}"]
    return (not why), why
