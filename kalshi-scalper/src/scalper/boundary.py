"""N1 and N2: H7's distance rule with the decision at 2 and 1 minutes left (rules in the README, fixed before this file existed).

This only re-points distance.py at a different decision minute; the rule, the half split and the costs are H7's. The pass mark is stricter than H7's (day
clustered z of 2.4, two tries). Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.boundary
"""
from __future__ import annotations

import sqlite3

from . import distance as D
from .paths import DB
from .scalps import STRESS

PASS_Z = 2.4
VARIANTS = (("N1", 120, 2), ("N2", 60, 1))


def run_variant(markets, spot, left_s: int, minutes: int):
    """Run H7's pipeline at another decision time and restore the module constants afterwards."""
    old = (D.DECISION_LEFT_S, D.MINUTES_LEFT)
    D.DECISION_LEFT_S, D.MINUTES_LEFT = left_s, minutes
    try:
        obs = D.observations(markets, spot)
        est, test = D.split(obs)
        table = D.estimate(est)
        entries = D.run(test, table)
    finally:
        D.DECISION_LEFT_S, D.MINUTES_LEFT = old
    return obs, test, entries


def decide(entries: list[dict]) -> tuple[str, dict | None]:
    """H7's judge, then the stricter z. A pass of H7's bar below PASS_Z is FALSIFIED here."""
    v, summ = D.verdict(entries)
    if v == "NOT_ENOUGH_DATA":
        return v, None
    s = summ[0]
    if v == "NOT_YET_FALSIFIED" and s["z"] < PASS_Z:
        v = "FALSIFIED"
    return v, s


def main() -> None:
    db = sqlite3.connect(DB)
    markets, spot = D.load(db)
    for name, left_s, minutes in VARIANTS:
        obs, test, entries = run_variant(markets, spot, left_s, minutes)
        v, s = decide(entries)
        print(f"{name} ({minutes} minute(s) left): {len(obs)} Bitcoin markets with a usable quote, test half {len(test)}, entered {len(entries)}")
        if entries:
            n = len(entries)
            print(f"   gross {sum(e['gross'] for e in entries) / n * 100:+.2f}c, net {sum(e['net'] for e in entries) / n * 100:+.2f}c per contract")
        if s:
            print(f"   z {s['z']:+.2f}  halves {s['h1'] * 100:+.2f}c / {s['h2'] * 100:+.2f}c  fees x{STRESS} {s['stress'] * 100:+.2f}c")
        print(f"   VERDICT (bar z>={PASS_Z}, entered>={D.MIN_N}, both halves, fees x{STRESS}): {v}\n")
    print("No verdict here means trade.")


if __name__ == "__main__":
    main()
