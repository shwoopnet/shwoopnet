"""What per-order size and the session loss stop do to a day, at a roughly $100 account. A measurement of sizing: no verdict, no parameter reads a result.

L1's 3,400 entries are replayed in time order. Each is taken with probability FILL (the live bot fills IOC orders on a share of signals; 0.6 is a
round number between the observed 50 and 70 percent, not a fitted one). A taken order buys COUNT contracts and costs the cent-rounded
order_cost. The bot's loss stop counts orders that have not settled yet as lost (their whole cost), so the replay does the same: before each
order, risk = settled profit so far minus the cost of orders still open; at or below minus STOP the session halts for the rest of the day.
Days are the UTC days in the data, each replayed FILL_DRAWS times with different fill draws (fixed seed). Overlap between bitcoin and gold is
real in the data, so concurrent exposure is already in the open-order count.

Usage: python -m scalper.riskcap
"""
from __future__ import annotations

import random
import statistics as st
from collections import defaultdict

from . import lstrats as L
from .feerounding import order_cost
from .scalps import load as load_markets

FILL = 0.6
FILL_DRAWS = 40
COUNTS = (1, 2, 3)
STOPS = (7.0, 10.0, 15.0)
SEED = 20261008


def run_day(entries: list[dict], count: int, stop: float, rng: random.Random) -> dict:
    """One day: returns profit, whether the stop tripped, orders taken, and the worst single order loss."""
    taken = [e for e in entries if rng.random() < FILL]
    open_orders: list[tuple[int, float]] = []   # (close_ts, cost)
    settled = 0.0
    worst_order = 0.0
    n = 0
    tripped = False
    for e in taken:
        t = e["close_ts"] - L.L1["left_s"]
        keep = []
        for close_ts, cost, won in open_orders:
            if close_ts <= t:
                settled += (count if won else 0.0) - cost
            else:
                keep.append((close_ts, cost, won))
        open_orders = keep
        if settled - sum(c for _, c, _ in open_orders) <= -stop:
            tripped = True
            break
        cost = order_cost(e["price"], count)
        won = e["gross"] + e["price"] > 0.5
        open_orders.append((e["close_ts"], cost, won))
        n += 1
        if not won:
            worst_order = min(worst_order, -cost)
    for _, cost, won in open_orders:
        settled += (count if won else 0.0) - cost
    return {"pnl": settled, "tripped": tripped, "n": n, "worst": worst_order}


def main() -> None:
    markets, _ = load_markets()
    ents = L.hold_rule(markets, **L.L1)
    by_day: dict[str, list[dict]] = defaultdict(list)
    for e in ents:
        by_day[e["day"]].append(e)
    days = sorted(by_day)
    print(f"{len(ents)} L1 entries over {len(days)} days, fill {FILL:.0%}, {FILL_DRAWS} fill draws per day. Dollars per day on a UTC day.\n")
    print("count  stop   mean/day     sd    5th pct   worst day   stop trips   orders/day   worst single order")
    for count in COUNTS:
        for stop in STOPS:
            rng = random.Random(SEED)
            rows = [run_day(by_day[d], count, stop, rng) for d in days for _ in range(FILL_DRAWS)]
            p = sorted(r["pnl"] for r in rows)
            print(f"{count:>5}  ${stop:>4.0f}  {st.mean(p):>+8.2f}  {st.pstdev(p):>6.2f}  {p[int(0.05 * len(p))]:>+8.2f}  {p[0]:>+9.2f}  "
                  f"{sum(r['tripped'] for r in rows) / len(rows):>9.1%}  {st.mean(r['n'] for r in rows):>10.1f}  {min(r['worst'] for r in rows):>+16.2f}")
        print()
    print("Information only. Days are resampled from 69 real days; fills are a coin at FILL, so the live fill rate and the 69 day sample both move these.")


if __name__ == "__main__":
    main()
