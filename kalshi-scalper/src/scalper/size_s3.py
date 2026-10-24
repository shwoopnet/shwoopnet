"""S3 (README, Pre-registration: S3): does a higher gold order ceiling pay after risk? Information about sizing, not a try, not a verdict. Gold only, L1 entries at 360 s from the 73 real days, day-block bootstrap
from $500, 90% fills, flat size per order (the window cap of 5.5% allows about 29 contracts), the 12% day stop, 30 and 90 day paths, and a stressed version with the loss rate raised to 6.6%
(the 95% upper bound of gold's 5.3%) by turning a random share of wins into losses. Usage: python -m scalper.size_s3
"""
from __future__ import annotations

import random
import statistics as st
from collections import defaultdict

from . import feat1 as F
from . import lstrats as L
from .fwd_reads import load_fresh
from .hs1 import load

START, FILL, STOP_FRAC, PATHS, SEED, UPPER_LOSS = 500.0, 0.9, 0.12, 4000, 23, 0.066
CEILINGS = (9, 12, 15, 20)


def outcome(e: dict, rng: random.Random, stress: bool, base_loss: float):
    """(net per contract) of one entry; in the stressed run a win turns into a loss with the probability that lifts the loss rate from base_loss to UPPER_LOSS."""
    won = e["gross"] + e["price"] > 0.5
    if stress and won and rng.random() < (UPPER_LOSS - base_loss) / (1 - base_loss):
        return -(e["price"] + L.fee(e["price"]))
    return e["net"]


def path(by, days, n, ndays, stress, base_loss, rng):
    bal, peak, dd, stops = START, START, 0.0, 0
    for _ in range(ndays):
        day = rng.choice(days)
        sb, pnl, stopped = bal, 0.0, False
        for e in by[day]:
            if stopped or rng.random() >= FILL:
                continue
            p = n * outcome(e, rng, stress, base_loss)
            bal += p
            pnl += p
            peak = max(peak, bal)
            dd = max(dd, peak - bal)
            if pnl <= -STOP_FRAC * sb:
                stopped = True
                stops += 1
    return bal - START, dd, stops


def main() -> None:
    mk = {}
    for m in load() + load_fresh():
        if m[1] == "KXGOLD15M" and m[4] in ("yes", "no") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = m
    full = [(t, s, [(e, b, a, b, a) for e, b, a, *_ in c], cl, r) for t, s, c, cl, r in mk.values()]
    rows, _, _ = F.build(full, 360)
    by = defaultdict(list)
    for r in rows:
        by[r["day"]].append(r)
    days = list(by)
    base_loss = sum(1 for r in rows if r["gross"] + r["price"] <= 0.5) / len(rows)
    print(f"gold {len(rows)} entries, {len(days)} days, loss rate {base_loss:.3f}; {PATHS} paths from ${START:.0f}, fill {FILL:.0%}, stop {STOP_FRAC:.0%} a day")
    print(f"{'ceiling':>8s} {'horizon':>8s} {'loss rate':>10s} {'mean $':>8s} {'5th':>7s} {'1st':>7s} {'dd 95th':>8s} {'$/$dd':>6s} {'stop days':>9s} {'P(end<$400)':>12s}")
    for ndays in (30, 90):
        for stress in (False, True):
            for n in CEILINGS:
                rng = random.Random(SEED)
                res = [path(by, days, n, ndays, stress, base_loss, rng) for _ in range(PATHS)]
                tot = sorted(r[0] for r in res)
                dd = sorted(r[1] for r in res)
                mean = st.mean(tot)
                d95 = dd[int(0.95 * len(dd))]
                pbad = sum(1 for t in tot if t < -100) / len(tot)
                print(f"{n:8d} {ndays:6d}d {('6.6% (stress)' if stress else f'{100 * base_loss:.1f}%'):>12s} {mean:8.1f} {tot[int(.05 * len(tot))]:7.1f} {tot[int(.01 * len(tot))]:7.1f} {d95:8.1f} {mean / d95 if d95 else 0:6.2f} {st.mean(r[2] for r in res):9.2f} {100 * pbad:11.1f}%")


if __name__ == "__main__":
    main()
