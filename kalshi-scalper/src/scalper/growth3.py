"""GROWTH3: how the live sizing rules shape growth and drawdown, for a range of true edges. Information, not a hypothesis test: nothing here is a try and nothing in it changes the bot.

Same bootstrap as `growth.py` (day blocks of the 69 days of public candles on Bitcoin, gold and Ethereum, fills 58%, the 4.5% window limit, the 5% day stop, $500 plus $500 every 30 days),
varying the two sizing knobs: dollars of balance per contract (the live value is 46.5, the 2% cap) and the ceiling on contracts (the live value is 40). A bigger ceiling or a smaller
dollars-per-contract is a decision for the owner and for the weekly size review, not something this file recommends.
Usage: python -m scalper.growth3
"""
from __future__ import annotations

import random

from . import growth as G
from . import growth2 as G2


def max_drawdown(path: list[float], deposits_at: set[int] | None = None) -> float:
    """Largest peak-to-trough fall as a share of the peak, counting a deposit as new money (a deposit day never makes a fall)."""
    peak = path[0]
    worst = 0.0
    for t, b in enumerate(path):
        peak = max(peak, b)
        worst = max(worst, (peak - b) / peak if peak > 0 else 0.0)
    return worst


def simulate(pool: list, shift: float, per_contract: float, ceiling: int, paths: int, seed: int = 61) -> list[list[float]]:
    G.PER_CONTRACT, G.MAX_CONTRACTS = per_contract, ceiling
    rng = random.Random(seed)
    return [G.simulate_path(pool, shift, rng) for _ in range(paths)]


def main() -> None:
    saved = (G.PER_CONTRACT, G.MAX_CONTRACTS)
    ents = [e for e in G2.load_entries() if e["series"] in G2.LIVE]
    pool = G.by_day(ents)
    mean_net = sum(e["net"] for e in ents) / len(ents)
    print(f"{len(ents)} entries on {len(pool)} days, measured mean {mean_net * 100:+.2f}c. {G.PATHS} paths of {G.HORIZON_DAYS} days; start ${G.START:.0f} plus ${G.DEPOSIT:.0f} every 30 days.\n")
    print(f"{'true edge':>10} {'$/contract':>10} {'ceiling':>8} | {'median':>8} {'5th pct':>8} {'95th':>8} | {'below paid-in':>13} | {'median worst drop':>17} {'95th pct worst drop':>20}")
    try:
        for edge in (0.0, 0.0041, mean_net):
            for per, ceil in ((46.5, 40), (46.5, 80), (30.0, 40), (30.0, 80), (20.0, 80)):
                paths = simulate(pool, edge - mean_net, per, ceil, G.PATHS)
                end = sorted(p[-1] for p in paths)
                dd = sorted(max_drawdown(p) for p in paths)
                paid = G.START + G.DEPOSIT * ((G.HORIZON_DAYS - 1) // 30)
                print(f"{edge * 100:>+9.2f}c {per:>10.1f} {ceil:>8d} | {end[len(end) // 2]:>8.0f} {end[int(0.05 * len(end))]:>8.0f} {end[int(0.95 * len(end))]:>8.0f} | "
                      f"{sum(1 for v in end if v < paid) / len(end):>13.0%} | {dd[len(dd) // 2]:>17.1%} {dd[int(0.95 * len(dd))]:>20.1%}")
            print()
    finally:
        G.PER_CONTRACT, G.MAX_CONTRACTS = saved
    print("No row is a forecast or a recommendation. 'Worst drop' is the largest fall from a running peak in a path, deposits counted as new money.")


if __name__ == "__main__":
    main()
