"""GROWTH: what L1 could do to an account with monthly deposits, under the live sizing and stop rules, for a range of true edges. Information, not a hypothesis test: nothing here
is a try, and nothing in it changes the bot. Day-block bootstrap of the 40 days of L1 entries on Bitcoin, gold and Ethereum, each entry filled with probability FILL.

The rules are the live ones in their simplest form: contracts per trade = balance at the start of the day / 46.5 (the 2% of cash cap, about $43 a contract), at most 40; a window's
total cost is held to 4.5% of the balance (the first order of a window is never cut); the day stops when it is down 5% of its starting balance and stays off until the next day.
Left out on purpose: the profit add-on pool, the weekly review's step timing, open positions counted as lost, and fee changes. The scenarios shift every entry's net by a constant so
the mean net per contract equals the stated edge: a crude but honest way to ask "what if the edge is half what we measured, or zero?".

Usage: python -m scalper.growth
"""
from __future__ import annotations

import random
import statistics as st
from collections import defaultdict

from . import lstrats as L
from .scalps import load as load_markets

FILL = 0.58
PER_CONTRACT = 46.5            # dollars of balance per contract at the 2% cap
MAX_CONTRACTS = 40
WINDOW_CAP = 0.045
DAY_STOP = 0.05
START = 500.0
DEPOSIT = 500.0
PATHS = 400
HORIZON_DAYS = 360
CHECKPOINTS = (30, 90, 180, 360)
SERIES_ORDER = {"KXBTC15M": 0, "KXGOLD15M": 1, "KXETH15M": 2}


def by_day(entries: list[dict]) -> list[list[list[dict]]]:
    """days -> windows (entries sharing a close time, in series order) -> entries."""
    days: dict = defaultdict(lambda: defaultdict(list))
    for e in entries:
        days[e["day"]][e["close_ts"]].append(e)
    out = []
    for d in sorted(days):
        wins = [sorted(days[d][c], key=lambda e: SERIES_ORDER.get(e["series"], 9)) for c in sorted(days[d])]
        out.append(wins)
    return out


def simulate_path(day_pool: list, shift: float, rng: random.Random, horizon: int = HORIZON_DAYS, start: float = START, deposit: float = DEPOSIT, fill: float = FILL) -> list[float]:
    """Balance after each day. A deposit lands on day 0 of every 30 day block after the first."""
    bal = start
    out = []
    for t in range(horizon):
        if t and t % 30 == 0:
            bal += deposit
        day = rng.choice(day_pool)
        b0 = bal
        stopped = False
        k = max(1, min(MAX_CONTRACTS, int(b0 / PER_CONTRACT)))
        day_pl = 0.0
        for win in day:
            cost = 0.0
            for e in win:
                if stopped or rng.random() >= fill:
                    continue
                c = k * e["price"]
                if cost > 0 and cost + c > WINDOW_CAP * b0:
                    continue
                cost += c
                pnl = k * (e["net"] + shift)
                bal += pnl
                day_pl += pnl
                if day_pl <= -DAY_STOP * b0:
                    stopped = True
        out.append(bal)
    return out


def percentile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


def summarize(paths: list[list[float]], deposit: float = DEPOSIT, start: float = START) -> dict:
    out = {}
    for cp in CHECKPOINTS:
        paid = start + deposit * ((cp - 1) // 30)
        vals = [p[cp - 1] for p in paths]
        out[cp] = {"paid": paid, "p5": percentile(vals, 0.05), "p50": percentile(vals, 0.5), "p95": percentile(vals, 0.95), "below": sum(1 for v in vals if v < paid) / len(vals)}
    return out


def main() -> None:
    markets, _ = load_markets()
    entries = L.hold_rule(markets, **L.L1)
    pool = by_day(entries)
    mean_net = st.mean(e["net"] for e in entries)
    print(f"{len(entries)} L1 entries over {len(pool)} days ({len(entries) / len(pool):.0f} a day); measured mean net {mean_net * 100:+.2f}c per contract; fill rate assumed {FILL:.0%}.")
    print(f"Start ${START:.0f}, plus ${DEPOSIT:.0f} every 30 days. {PATHS} paths of {HORIZON_DAYS} days per scenario. Balances in dollars; 'below' is the share of paths under what was paid in.\n")
    rng = random.Random(31)
    for edge in (-0.005, 0.0, 0.0025, mean_net, 0.010):
        shift = edge - mean_net
        paths = [simulate_path(pool, shift, rng) for _ in range(PATHS)]
        s = summarize(paths)
        label = f"true edge {edge * 100:+.2f}c" + (" (the measured one)" if abs(edge - mean_net) < 1e-12 else "")
        print(label)
        for cp, v in s.items():
            print(f"   day {cp:>3}: paid in ${v['paid']:>6.0f}  5th ${v['p5']:>7.0f}  median ${v['p50']:>7.0f}  95th ${v['p95']:>7.0f}   below paid-in {v['below']:.0%}")
    print("\nNo scenario here is a forecast. The measured edge has a z of about 1.5 (not proven), so the zero and negative rows are as live as the others.")


if __name__ == "__main__":
    main()
