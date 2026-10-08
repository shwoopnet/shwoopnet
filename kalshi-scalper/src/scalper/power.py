"""How long until a forward test of L1 can clear the bar, if the edge is what the 69 days measured, or half of it, or nothing.

Information only, no hypothesis, reads no forward data. L1 entries are resampled BY DAY (a day bootstrap keeps the clustering), days are
drawn until the sample has N entries, and the day clustered z is computed the way the bar computes it. The true edge is set by shifting
every net by a constant so the resampled mean equals scale x the measured mean (scale 1, 0.5, 0).

Usage: python -m scalper.power
"""
from __future__ import annotations

import random
from collections import defaultdict

from . import lstrats as L
from .calibration import cluster_mean_z
from .scalps import Z_BAR, load as load_markets

SIZES = (300, 600, 1000, 2000)
SCALES = (1.0, 0.5, 0.0)
REPS = 1000


def by_day(entries: list[dict]) -> dict[str, list[float]]:
    d: dict = defaultdict(list)
    for e in entries:
        d[e["day"]].append(e["net"])
    return d


def pass_rate(days: dict[str, list[float]], n: int, scale: float, reps: int = REPS, seed: int = 5) -> tuple[float, float]:
    """(share of samples with mean > 0 and z >= Z_BAR, mean number of days needed)."""
    rng = random.Random(seed)
    keys = sorted(days)
    allv = [x for k in keys for x in days[k]]
    shift = (scale - 1.0) * sum(allv) / len(allv)
    ok, need = 0, 0
    for _ in range(reps):
        obs, k = [], 0
        while len(obs) < n:
            d = rng.choice(keys)
            k += 1
            obs += [(f"{k}", x + shift) for x in days[d]]
        mean, _, z = cluster_mean_z(obs)
        ok += mean > 0 and z >= Z_BAR
        need += k
    return ok / reps, need / reps


def main() -> None:
    markets, _ = load_markets()
    ents = L.hold_rule(markets, **L.L1)
    days = by_day(ents)
    per_day = len(ents) / len(days)
    print(f"L1: {len(ents)} entries over {len(days)} days ({per_day:.1f} a day), measured mean net {sum(e['net'] for e in ents) / len(ents) * 100:+.2f}c\n")
    print("share of forward samples that clear z >= %.1f with a positive mean (days needed in brackets)" % Z_BAR)
    print("entries    edge = measured     edge = half         edge = zero (false pass rate)")
    for n in SIZES:
        cells = []
        for sc in SCALES:
            p, k = pass_rate(days, n, sc)
            cells.append(f"{p * 100:5.1f}% ({k:4.1f}d)")
        print(f"{n:>7}    " + "      ".join(cells))


if __name__ == "__main__":
    main()
