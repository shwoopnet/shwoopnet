"""Hold-to-settlement calibration: are favourites priced too cheaply?

Hypothesis H1 (fixed 2026-10-05, before any calibration data was looked at):
buying the FAVOURITE side of a 15 minute market at 85c to 97c and holding it to
settlement earns more than it costs.

Counterparty: whoever is on the other side of that trade is buying the cheap
longshot (3c to 15c) as a lottery ticket. If longshots are overpaid for, a
favourite is underpriced by the same amount, and the favourite buyer collects it.

Prediction: mean net profit of at least +1.0c per contract, after the spread
(entry at the ask) and fees, at one or more of three entry times.

Kill criteria. H1 is FALSIFIED unless, for at least one entry time:
  1. n >= MIN_N markets,
  2. the mean net profit per contract is positive with a day-clustered z of at
     least Z_BAR (Bonferroni for the 3 entry times; the cluster is the UTC day
     because adjacent markets share a regime and a single day is not 96 trials),
  3. the mean is positive in BOTH halves of the window (first and second 15 days),
  4. the mean is still positive with fees 20% higher than modelled.
Passing all four is NOT_YET_FALSIFIED: permission to test it on data recorded
after today, never evidence of an edge. There is no verdict that means "trade".

One entry per market per entry time, so the unit is a market. A minute-by-minute
version would count the same outcome dozens of times.

Prior: low. These are liquid markets priced off live indices by professional
makers, so a bias this simple should already be gone. With roughly a thousand
markets per entry time the test can only see an edge of about 2.5c or more
(printed as "detectable"); FALSIFIED here means "no edge this large", not
"priced perfectly". A smaller edge is also barely worth the risk.

The calibration table printed after the verdict is DESCRIPTIVE. Nothing in it
affects the verdict, and anything interesting in it is a new hypothesis that
needs data it has not been fitted on.

Usage: python -m scalper.calibration
"""
from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .recorder import DB

# ---- fixed before the first run ----
TAU_MIN = (10, 5, 2)          # minutes before close at which the quote is taken
FAV_LO, FAV_HI = 0.85, 0.97   # the favourite's ask must lie in this band
FEE_RATE = 0.07               # matched two real fills; applied per contract, unrounded
STRESS = 1.2                  # fee multiplier for kill criterion 4
MIN_N = 300
Z_BAR = 2.2                   # one sided, about 0.0167 for 29 degrees of freedom
BANDS = [(0.0, 0.10), (0.10, 0.30), (0.30, 0.70), (0.70, 0.90), (0.90, 1.0001)]


def favourite(bid: float | None, ask: float | None) -> tuple[str, float] | None:
    """(side, ask price paid) for the favourite if it is in the band, else None.
    The NO side is bought at 1 - yes_bid. Unusable quotes never qualify."""
    if not valid_quote(bid, ask):
        return None
    if FAV_LO <= ask <= FAV_HI:
        return "yes", ask
    no_ask = 1 - bid
    if FAV_LO <= no_ask <= FAV_HI:
        return "no", no_ask
    return None


def net_pnl(side: str, price: float, result: str, fee_mult: float = 1.0) -> float | None:
    """Profit per contract held to settlement: $1 if the side won, less the price
    paid and the taker fee. Settlement itself costs nothing. None if the market
    did not resolve yes or no."""
    if result not in ("yes", "no"):
        return None
    fee = FEE_RATE * fee_mult * price * (1 - price)
    return (1.0 if result == side else 0.0) - price - fee


def cluster_mean_z(obs: list[tuple[str, float]]) -> tuple[float, float, float]:
    """(mean, se, z) with standard errors clustered by the first tuple element.
    Twenty outcomes from one day are closer to one observation than to twenty."""
    n = len(obs)
    if n < 2:
        return 0.0, float("inf"), 0.0
    mean = sum(x for _, x in obs) / n
    by: dict[str, float] = defaultdict(float)
    for c, x in obs:
        by[c] += x - mean
    se = math.sqrt(sum(v * v for v in by.values())) / n
    return mean, se, (mean / se if se > 0 else 0.0)


def judge(rows_by_tau: dict[int, list[tuple]], midpoint: float) -> tuple[str, list[dict]]:
    """rows: (cluster, close_ts, net, net_stressed). Returns the verdict and one
    summary per entry time. The verdict is NOT_YET_FALSIFIED only if some entry
    time passes every kill criterion."""
    out, passed = [], False
    for tau in sorted(rows_by_tau):
        rows = rows_by_tau[tau]
        mean, se, z = cluster_mean_z([(r[0], r[2]) for r in rows])
        h1 = [r[2] for r in rows if r[1] < midpoint]
        h2 = [r[2] for r in rows if r[1] >= midpoint]
        m1 = sum(h1) / len(h1) if h1 else 0.0
        m2 = sum(h2) / len(h2) if h2 else 0.0
        stress = sum(r[3] for r in rows) / len(rows) if rows else 0.0
        ok = (len(rows) >= MIN_N and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0)
        passed = passed or ok
        out.append({"tau": tau, "n": len(rows), "mean": mean, "se": se, "z": z, "h1": m1, "h2": m2,
                    "stress": stress, "detectable": 2.8 * se if se != float("inf") else float("inf"), "ok": ok})
    return ("NOT_YET_FALSIFIED" if passed else "FALSIFIED"), out


def load() -> tuple[dict[int, list[tuple]], list[tuple], dict]:
    db = sqlite3.connect(DB)
    gaps = tuple(t * 60 for t in TAU_MIN)
    q = ("SELECT c.series, c.ticker, c.bid_c, c.ask_c, m.close_ts, m.result, m.close_ts - c.end_ts "
         "FROM candle c JOIN market m ON m.ticker = c.ticker "
         f"WHERE m.close_ts - c.end_ts IN ({','.join('?' * len(gaps))})")
    rows_by_tau: dict[int, list[tuple]] = {t: [] for t in TAU_MIN}
    desc: list[tuple] = []   # (tau, yes_mid, yes_won)
    info = {"unresolved": 0, "no_quote": 0, "markets": 0}
    closes = [r[0] for r in db.execute("SELECT close_ts FROM market")]
    midpoint = (min(closes) + max(closes)) / 2 if closes else 0.0
    seen = set()
    for series, ticker, bid, ask, close_ts, result, gap in db.execute(q, gaps):
        tau = gap // 60
        seen.add(ticker)
        if result not in ("yes", "no"):
            info["unresolved"] += 1
            continue
        if not valid_quote(bid, ask):
            info["no_quote"] += 1
            continue
        desc.append((tau, (bid + ask) / 2, 1 if result == "yes" else 0))
        fav = favourite(bid, ask)
        if fav is None:
            continue
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        rows_by_tau[tau].append((day, close_ts, net_pnl(fav[0], fav[1], result),
                                 net_pnl(fav[0], fav[1], result, STRESS)))
    info["markets"] = len(seen)
    return rows_by_tau, desc, {**info, "midpoint": midpoint}


def main() -> None:
    rows_by_tau, desc, info = load()
    if not any(rows_by_tau.values()):
        print("No data. Run: python -m scalper.backfill")
        return
    v, summ = judge(rows_by_tau, info["midpoint"])
    print(f"{info['markets']} markets. Unresolved (not yes/no): {info['unresolved']}. "
          f"Entry quote unusable: {info['no_quote']}.\n")
    print("H1: buy the favourite at 85c to 97c, hold to settlement. Net profit per contract, cents.")
    print(f"{'entry':>10} {'n':>6} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'detectable':>11} {'passes':>7}")
    for s in summ:
        print(f"{s['tau']:>6} min {s['n']:>6} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} "
              f"{s['h1']*100:>9.2f} {s['h2']*100:>9.2f} {s['stress']*100:>10.2f} {s['detectable']*100:>10.2f}c {str(s['ok']):>7}")
    print(f"\nVERDICT (pre-registered, bar z>={Z_BAR}, n>={MIN_N}, both halves, fees x{STRESS}): {v}")
    if v == "FALSIFIED":
        print("  No entry time clears every criterion: no favourite edge as large as 'detectable' above.")
    else:
        print("  Permission to test on data recorded after this run. Not evidence of an edge.")

    print("\nDESCRIPTIVE ONLY, affects nothing above. Did YES win as often as its mid price said?")
    print(f"{'entry':>10} {'yes mid':>9} {'n':>6} {'priced':>8} {'won':>7} {'gap':>7}")
    for tau in TAU_MIN:
        for lo, hi in BANDS:
            r = [d for d in desc if d[0] == tau and lo <= d[1] < hi]
            if len(r) >= 30:
                priced = sum(d[1] for d in r) / len(r)
                won = sum(d[2] for d in r) / len(r)
                print(f"{tau:>6} min {lo*100:>3.0f}-{min(hi,1)*100:<4.0f}c {len(r):>6} {priced*100:>7.1f}% {won*100:>6.1f}% {100*(won-priced):>+6.1f}")


if __name__ == "__main__":
    main()
