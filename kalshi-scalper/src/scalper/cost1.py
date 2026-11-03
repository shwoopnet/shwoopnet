"""COST1 (workers/COST1_REGISTRATION.md): Kalshi cost by price. Measurement only, no strategy scored.
Usage: python -m scalper.cost1 fees | spread | table
"""
from __future__ import annotations

import math
import statistics
import sys
from collections import defaultdict

BANDS = [(1, 5), (5, 15), (15, 30), (30, 70), (70, 85), (85, 97), (97, 99)]
CLASSES = {
    "crypto": ("BTC", "ETH", "SOL", "XRP", "DOGE", "BNB", "HYPE", "ZEC", "NEAR"),
    "metals_energy": ("GOLD", "SILVER", "COPPER", "PALLADIUM", "PLATINUM", "WTI", "NATGAS", "BRENT"),
    "fx": ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"),
    "rates": ("10YRRATE", "2YRRATE", "30YRRATE", "5YRRATE"),
}
MAKER_RATE = 0.0175
TAKER_RATE = 0.07


def fee_cents(price_c: int, contracts: int, rate: float = TAKER_RATE) -> int:
    """Whole-cent fee for one order: ceil(rate * C * p * (1-p)) in dollars, as cents."""
    p = price_c / 100.0
    return math.ceil(round(rate * contracts * p * (1 - p) * 100, 9))


def fee_row(price_c: int, contracts: int, rate: float = TAKER_RATE):
    f = fee_cents(price_c, contracts, rate)
    return f, f / contracts, 100.0 * f / (contracts * price_c)


def band_of(price_c: float):
    for lo, hi in BANDS:
        if lo <= price_c <= hi:
            return (lo, hi)
    return None


def band_fee(lo, hi, c, rate=TAKER_RATE):
    ps = range(lo, hi + 1)
    return statistics.mean(fee_cents(p, c, rate) / c for p in ps)


def klass(series: str) -> str:
    s = series[2:-3] if series.startswith("KX") and series.endswith("15M") else series
    for k, names in CLASSES.items():
        if s in names:
            return k
    return "other"


def fees_csv():
    out = ["price_c," + ",".join(f"C{c}_total_c,C{c}_per_c,C{c}_pct" for c in (1, 5, 10, 50, 100))]
    for p in range(1, 100):
        cells = []
        for c in (1, 5, 10, 50, 100):
            f, per, pct = fee_row(p, c)
            cells += [str(f), f"{per:.3f}", f"{pct:.2f}"]
        out.append(f"{p}," + ",".join(cells))
    return "\n".join(out)


def spread_stats():
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load as hl
    obs = defaultdict(list)   # (class, band) -> spreads in cents
    look = defaultdict(list)  # same, only the candle at the 6 minute look
    for m in hl() + load_fresh() + load_rep():
        if not m[1].endswith("15M"):
            continue
        k = klass(m[1])
        for row in m[2]:
            e, b, a = row[0], row[1], row[2]
            if b is None or a is None or b <= 0 or a >= 1 or a < b:
                continue
            sp = round((a - b) * 100, 4)
            mid = (a + b) / 2 * 100
            for pc in (mid, 100 - mid):  # a NO buyer faces the same spread at 1 - mid
                bd = band_of(round(pc))
                if bd:
                    obs[(k, bd)].append(sp)
                    obs[("all", bd)].append(sp)
                    if e == m[3] - 360:
                        look[(k, bd)].append(sp)
                        look[("all", bd)].append(sp)
    return obs, look


def med(xs):
    return statistics.median(xs) if xs else float("nan")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fees"
    if cmd == "fees":
        print(fees_csv())
    elif cmd == "spread":
        obs, look = spread_stats()
        for k in ["all", "crypto", "metals_energy", "fx", "rates", "other"]:
            for bd in BANDS:
                xs = obs.get((k, bd), [])
                ys = look.get((k, bd), [])
                print(f"{k:14s} {bd[0]:>2}-{bd[1]:<2}  n={len(xs):>8}  med={med(xs):5.2f}c  p25/p75="
                      f"{(sorted(xs)[len(xs)//4] if xs else float('nan')):.1f}/{(sorted(xs)[3*len(xs)//4] if xs else float('nan')):.1f}"
                      f"  look6 n={len(ys):>6} med={med(ys):5.2f}c")
