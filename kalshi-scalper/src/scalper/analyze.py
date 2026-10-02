"""Does a scalp have any room? Measure it from recorded books.

For every recorded market and several holding horizons, compare the mid-price
move over that horizon with the cost of crossing the spread and paying fees on
both legs. "move>cost" assumes perfect foresight of direction, so it is a
ceiling and not an estimate. The column that matters is "needs": the share of
direction calls that must be RIGHT just to break even. A guesser at 50% loses
the whole cost on every trade.

Two cuts expose what the headline averages hide:
- by price level: fees are cheap near 0 and 100, dear near 50
- by time left: prices collapse toward 0 or 100 as a market closes, and that
  late move inflates the average without being an opportunity anyone can
  call in advance

Samples overlap (a 10s window starts every 2s), so n is not a count of
independent trades. The header reports distinct markets and hours instead.

Usage: python -m scalper.analyze
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime

from .fees import round_trip_cost
from .recorder import DB

HORIZONS = (10, 30, 60, 120)  # seconds
CUT_HORIZON = 60
PRICE_BANDS = [(0.0, 0.10), (0.10, 0.30), (0.30, 0.70), (0.70, 0.90), (0.90, 1.0001)]
TIME_BANDS = [(600, 1e9, "over 10 min left"), (300, 600, "5 to 10 min"),
              (120, 300, "2 to 5 min"), (0, 120, "under 2 min")]


def needed_accuracy(avg_cost: float, avg_move: float) -> float | None:
    """Hit rate needed to break even, assuming symmetric moves: a right call
    earns the move, a wrong one loses it, and both pay the cost.
        (2p - 1) * move - cost = 0   ->   p = 0.5 + cost / (2 * move)
    Above 1.0 means break-even is impossible even with a perfect predictor."""
    if not avg_move or avg_move <= 0:
        return None
    return 0.5 + avg_cost / (2 * avg_move)


def _acc(x: float | None) -> str:
    if x is None:
        return "-"
    return "never" if x > 1 else f"{x:.0%}"


def _secs_left(close_iso: str | None, ts: float) -> float | None:
    try:
        return datetime.fromisoformat(close_iso.replace("Z", "+00:00")).timestamp() - ts
    except Exception:
        return None


def _summ(rows: list[tuple]) -> tuple:
    n = len(rows)
    cost = sum(r[0] for r in rows) / n
    move = sum(r[1] for r in rows) / n
    beat = sum(r[1] > r[0] for r in rows) / n
    return n, cost, move, beat, needed_accuracy(cost, move)


def collect() -> tuple[list[tuple], dict]:
    db = sqlite3.connect(DB)
    q = ("SELECT series,ticker,ts,yes_bid,yes_ask,close_time FROM snap "
         "WHERE yes_bid IS NOT NULL AND yes_ask IS NOT NULL ORDER BY ticker,ts")
    by = defaultdict(list)
    for s, t, ts, b, a, c in db.execute(q):
        by[(s, t)].append((ts, b, a, c))
    recs = []  # (series, horizon, mid, secs_left, cost, move)
    for (s, _), pts in by.items():
        for i, (ts, b, a, c) in enumerate(pts):
            for h in HORIZONS:
                j = next((k for k in range(i + 1, len(pts)) if pts[k][0] - ts >= h), None)
                if j is None:
                    break
                _, b2, a2, _ = pts[j]
                recs.append((s, h, (a + b) / 2, _secs_left(c, ts),
                             round_trip_cost(a, b), abs((b2 + a2) / 2 - (b + a) / 2)))
    hours = sum((p[-1][0] - p[0][0]) for p in by.values()) / 3600
    return recs, {"markets": len(by), "hours": hours}


def main() -> None:
    recs, info = collect()
    if not recs:
        print("Not enough recorded data yet.")
        return
    print(f"{info['markets']} markets, {info['hours']:.1f} hours of market time recorded\n")

    print(f"{'series':10} {'hold':>5} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'move>cost':>10} {'needs':>7}")
    for s in sorted({r[0] for r in recs}):
        for h in HORIZONS:
            rows = [(r[4], r[5]) for r in recs if r[0] == s and r[1] == h]
            if rows:
                n, c, m, beat, need = _summ(rows)
                print(f"{s:10} {h:>4}s {n:>7} {c:>9.4f} {m:>11.4f} {beat:>9.1%} {_acc(need):>7}")
    print("\n'needs' = share of direction calls that must be right to break even.")
    print("move>cost assumes perfect foresight. Random calls lose the full cost.\n")

    print(f"--- {CUT_HORIZON}s hold, by price level (mid at entry) ---")
    print(f"{'series':10} {'price':>9} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'needs':>7}")
    for s in sorted({r[0] for r in recs}):
        for lo, hi in PRICE_BANDS:
            rows = [(r[4], r[5]) for r in recs if r[0] == s and r[1] == CUT_HORIZON and lo <= r[2] < hi]
            if len(rows) >= 30:
                n, c, m, _, need = _summ(rows)
                print(f"{s:10} {lo*100:>3.0f}-{min(hi,1)*100:<4.0f}c {n:>7} {c:>9.4f} {m:>11.4f} {_acc(need):>7}")

    print(f"\n--- {CUT_HORIZON}s hold, by time left in the market ---")
    print(f"{'series':10} {'time left':>17} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'needs':>7}")
    for s in sorted({r[0] for r in recs}):
        for lo, hi, label in TIME_BANDS:
            rows = [(r[4], r[5]) for r in recs if r[0] == s and r[1] == CUT_HORIZON
                    and r[3] is not None and lo <= r[3] < hi]
            if len(rows) >= 30:
                n, c, m, _, need = _summ(rows)
                print(f"{s:10} {label:>17} {n:>7} {c:>9.4f} {m:>11.4f} {_acc(need):>7}")
    print("\nA bucket with few markets behind it is noise. Judge on days of data, not rows.")


if __name__ == "__main__":
    main()
