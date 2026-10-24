"""S2 (README, Pre-registration: S2): the owner's "start high, scale out after each win" idea, replayed on gold with today's rules. Information about sizing, not a try, not a verdict.
Gold only (the one series whose size follows a ladder), L1 entries at 360 s from the real days, day-block bootstrap, 30 days a path. Sizes in contracts per order:
FLAT9 (today's ceiling at about $500), STEP_DOWN (start at 9, each filled win takes one off down to 2, any filled loss goes back to 9), STEP_UP (start at 3, each win adds one up to 9, a loss goes back to 3),
HALF (flat 4). The loss stop is 12% of the balance at the start of the day (the day ends at that loss), no pool, no add-on. Usage: python -m scalper.size_s2
"""
from __future__ import annotations

import random
import statistics as st
from collections import defaultdict

from . import feat1 as F
from . import lstrats as L
from .fwd_reads import load_fresh
from .hs1 import load

START, FILL, STOP_FRAC, PATHS, NDAYS, SEED, MAXN, MINN = 500.0, 0.9, 0.12, 4000, 30, 17, 9, 2


def next_size(rule: str, n: int, won: bool) -> int:
    if rule == "FLAT9":
        return MAXN
    if rule == "HALF":
        return 4
    if rule == "STEP_DOWN":
        return max(MINN, n - 1) if won else MAXN
    if rule == "STEP_UP":
        return min(MAXN, n + 1) if won else 3
    raise ValueError(rule)


def path(by: dict, days: list, rule: str, rng: random.Random):
    """(final profit, deepest drawdown, stopped days). Size for the first order is the rule's start (MAXN for FLAT9, STEP_DOWN; 3 for STEP_UP; 4 for HALF)."""
    n = {"FLAT9": MAXN, "STEP_DOWN": MAXN, "STEP_UP": 3, "HALF": 4}[rule]
    bal, peak, dd, stops = START, START, 0.0, 0
    for _ in range(NDAYS):
        day = rng.choice(days)
        start_bal, pnl, stopped = bal, 0.0, False
        for e in by[day]:
            if stopped or rng.random() >= FILL:
                continue
            won = e["gross"] + e["price"] > 0.5
            per = e["net"]                                                    # net per contract, win or lose, fee included
            pnl_o = n * per
            bal += pnl_o
            pnl += pnl_o
            n = next_size(rule, n, won)
            peak = max(peak, bal)
            dd = max(dd, peak - bal)
            if pnl <= -STOP_FRAC * start_bal:
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
    print(f"gold entries {len(rows)} on {len(days)} days; {PATHS} paths of {NDAYS} days from ${START:.0f}; fill {FILL:.0%}; stop {STOP_FRAC:.0%} a day")
    print(f"{'rule':10s} {'mean $':>8s} {'5th pct':>8s} {'1st pct':>8s} {'dd 95th':>8s} {'$ per $dd':>10s} {'stop days':>10s}")
    for rule in ("FLAT9", "STEP_DOWN", "STEP_UP", "HALF"):
        rng = random.Random(SEED)
        res = [path(by, days, rule, rng) for _ in range(PATHS)]
        tot = sorted(r[0] for r in res)
        dd = sorted(r[1] for r in res)
        mean = st.mean(tot)
        d95 = dd[int(0.95 * len(dd))]
        print(f"{rule:10s} {mean:8.1f} {tot[int(0.05 * len(tot))]:8.1f} {tot[int(0.01 * len(tot))]:8.1f} {d95:8.1f} {mean / d95 if d95 else 0:10.2f} {st.mean(r[2] for r in res):10.2f}")


if __name__ == "__main__":
    main()
