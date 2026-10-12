"""Exploratory read, information only: for every side-price bucket at three decision times, what did buying that side at the ask and holding to settlement earn?

No hypothesis, no verdict word, no variant counted, and it is not used to choose anything. It is the read that was already in view when OW1's lane bands were fixed
(README, "Pre-registration: OW1"), kept so that disclosure can be reproduced. Reading it for a new rule would be exactly the selection that section warns about.

Per bucket: entries, win rate against the mean price paid (the margin is the whole story: a calibrated market has none), net cents a contract after the 7% fee, the day
clustered z, and the average win and loss in cents, which is what a bigger win costs in win rate.

Usage: python -m scalper.ladder
"""
from __future__ import annotations

import statistics as st
from datetime import datetime, timezone

from . import lstrats as L
from . import opening as OW
from . import scalps
from .calibration import cluster_mean_z

BUCKETS = [(0.05, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.25), (0.25, 0.30), (0.30, 0.35), (0.35, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70),
           (0.70, 0.78), (0.78, 0.82), (0.82, 0.87), (0.87, 0.92), (0.92, 0.97)]
TIMES = ((600, "10 min left (the opening decision)"), (480, "8 min left"), (360, "6 min left (L1's own minute)"))


def _won(e: dict) -> bool:
    return e["gross"] + e["price"] > 0.5        # gross is won - price, so gross + price is 1 on a win and 0 on a loss


def row(es: list[dict]) -> dict | None:
    n = len(es)
    if n < 2:
        return None
    mean, _, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    wins = [e["net"] for e in es if _won(e)]
    losses = [e["net"] for e in es if not _won(e)]
    win, paid = len(wins) / n, sum(e["price"] for e in es) / n
    return {"n": n, "win": win, "paid": paid, "margin": win - paid, "mean": mean, "z": z,
            "avgwin": sum(wins) / len(wins) if wins else float("nan"), "avgloss": sum(losses) / len(losses) if losses else float("nan"),
            "fee": st.mean(scalps.fee(e["price"]) for e in es)}


def table(markets: list[tuple], left_s: int) -> list[tuple[tuple[float, float], list[dict]]]:
    """[(bucket, entries)]: one observation per market and bucket, from the candle that ends left_s before the close. Buckets are half open at the top, so none is counted twice."""
    return [((lo, hi), L.hold_rule(markets, left_s, (lo, round(hi - 0.0001, 4)))) for lo, hi in BUCKETS]


def main() -> None:
    markets, _ = scalps.load()
    if not markets:
        print("No data. Run: python -m scalper.backfill")
        return
    days = sorted({L._day(m[3]) for m in markets})
    print(f"{len(markets)} markets, {len(days)} days ({days[0]} to {days[-1]}), series: " + ", ".join(f"{s} {sum(1 for m in markets if m[1] == s)}" for s in sorted({m[1] for m in markets})))
    print("information only: no hypothesis, no verdict, no variant counted\n")
    for left_s, label in TIMES:
        print(f"=== side priced in the bucket at {label}; buy at the ask, hold to settlement, 7% fee unrounded ===")
        print(f"{'bucket':>11} {'n':>5} {'win%':>6} {'paid%':>6} {'margin':>7} {'net c/contract':>15} {'z':>6} {'avg win c':>10} {'avg loss c':>11} {'fee c':>6}")
        for (lo, hi), es in table(markets, left_s):
            r = row(es)
            if not r or r["n"] < 20:
                print(f"{lo*100:>4.0f}-{hi*100:<5.0f}c {len(es):>5}  (too few)")
                continue
            print(f"{lo*100:>4.0f}-{hi*100:<5.0f}c {r['n']:>5} {r['win']*100:>5.1f}% {r['paid']*100:>5.1f}% {r['margin']*100:>+6.1f} {r['mean']*100:>+14.2f}c {r['z']:>+6.2f} "
                  f"{r['avgwin']*100:>+9.1f} {r['avgloss']*100:>+10.1f} {r['fee']*100:>5.2f}")
        print()
    print("=== the two OW1 lanes at the 10 minute candle, one leg per market, on ALL the data loaded (information only) ===")
    lanes = OW.lane_entries(markets, after=0)
    for name, es in (("F early favourite 0.82-0.87", lanes["F"]), ("U early underdog 0.20-0.30", lanes["U"])):
        r = row(es)
        if not r:
            print(f"{name}: too few")
            continue
        print(f"{name}: n={r['n']}  ({r['n'] / len(days):.1f}/day)  win {r['win']*100:.1f}% vs paid {r['paid']*100:.1f}%  net {r['mean']*100:+.2f}c/contract  z {r['z']:+.2f}  "
              f"avg win {r['avgwin']*100:+.1f}c  avg loss {r['avgloss']*100:+.1f}c")
        for s in sorted({e["series"] for e in es}):
            sub = row([e for e in es if e["series"] == s])
            if sub:
                print(f"   {s}: n={sub['n']} win {sub['win']*100:.1f}% vs paid {sub['paid']*100:.1f}% net {sub['mean']*100:+.2f}c z {sub['z']:+.2f}")
    print("\n=== YES spread (ask minus bid, cents) by minutes left; median and the markets with a valid book ===")
    for left_s in (840, 780, 720, 660, 600, 540, 480, 420, 360, 300, 240, 180, 120):
        sp = []
        for _, _, cs, close_ts, _ in markets:
            c = next((x for x in cs if x[0] == close_ts - left_s), None)
            if c is not None and L.valid_quote(c[1], c[2]):
                sp.append(c[2] - c[1])
        print(f"{left_s / 60:>5.1f} min left: valid book in {len(sp):>5} markets, median spread {st.median(sp) * 100 if sp else float('nan'):.1f}c")


if __name__ == "__main__":
    main()
