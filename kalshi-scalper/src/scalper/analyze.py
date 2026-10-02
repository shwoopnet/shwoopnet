"""Does a scalp have any room? Measure it from recorded books.

For every recorded market and several holding horizons, compare the mid-price
move over that horizon with the cost of crossing the spread and paying fees on
both legs. The headline number is the share of horizons where the move beat the
cost in EITHER direction, which is the most generous possible reading: it
assumes perfect foresight of direction. If even that is rare, no directional
signal can rescue the strategy. If it is common, a signal is worth researching.

Usage: python -m scalper.analyze
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict

from .fees import round_trip_cost
from .recorder import DB

HORIZONS = (10, 30, 60, 120)  # seconds


def main() -> None:
    db = sqlite3.connect(DB)
    rows = db.execute("SELECT series,ticker,ts,yes_bid,yes_ask FROM snap "
                      "WHERE yes_bid IS NOT NULL AND yes_ask IS NOT NULL ORDER BY ticker,ts").fetchall()
    by = defaultdict(list)
    for s, t, ts, b, a in rows:
        by[(s, t)].append((ts, b, a))
    stats = defaultdict(lambda: [0, 0, 0.0, 0.0])  # n, beat, sum_cost, sum_absmove
    for (s, _), pts in by.items():
        for i, (ts, b, a) in enumerate(pts):
            for h in HORIZONS:
                j = next((k for k in range(i + 1, len(pts)) if pts[k][0] - ts >= h), None)
                if j is None:
                    break
                _, b2, a2 = pts[j]
                move = abs((b2 + a2) / 2 - (b + a) / 2)
                cost = round_trip_cost(a, b)
                st = stats[(s, h)]
                st[0] += 1; st[1] += move > cost; st[2] += cost; st[3] += move
    print(f"{'series':10} {'hold':>5} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'move>cost':>10}")
    for (s, h), (n, beat, c, m) in sorted(stats.items()):
        print(f"{s:10} {h:>4}s {n:>7} {c/n:>9.4f} {m/n:>11.4f} {beat/n:>9.1%}")
    print("\nmove>cost assumes perfect foresight of direction. It is a ceiling.")


if __name__ == "__main__":
    main()
