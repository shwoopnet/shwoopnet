"""L8 and L9 (rules fixed in the README before this file existed): Bitcoin settles on the average of the last 60 seconds of BRTI,
against the same average before the open, so a settlement value is less uncertain than a single end price.

Model, nothing fitted. S is spot at the decision minute, K the stored strike, sigma the sd of the 60 one minute log returns ending there
(H7's volatility). With tau minutes before the final averaging minute begins, the settlement value has variance sigma^2 x (tau + 1/3)
minutes, not (tau + 1). p(YES) = Phi(ln(S/K) / (sigma x sqrt(tau + 1/3))). Entry as in H7 with the margin fixed at 2c: buy the side whose
model probability beats its price, the fee and the margin. One entry per market, held to settlement, taker fee on entry.

L9 decides with 1 minute left (tau = 0). L8 decides with 14 minutes left (tau = 13).
Verdicts: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Usage: python -m scalper.avgsettle
"""
from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timezone

from . import distance as dist
from .analyze import valid_quote
from .lstrats import report
from .paths import DB

MARGIN = 0.02
RULES = {"L9": {"left_s": 60, "tau": 0.0}, "L8": {"left_s": 840, "tau": 13.0}}


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def model_p(z6: float, tau: float) -> float:
    """z6 is H7's z, ln(S/K) / (sigma x sqrt(6)). Rescale to this rule's variance: sigma^2 x (tau + 1/3)."""
    return phi(z6 * math.sqrt(dist.MINUTES_LEFT) / math.sqrt(tau + 1.0 / 3.0))


def entries(markets: list[tuple], spot: dict, left_s: int, tau: float) -> list[dict]:
    """markets: distance.load's (ticker, close_ts, strike, result, {end_ts: (bid, ask)}). One observation per market."""
    out = []
    for ticker, close_ts, strike, result, quotes in markets:
        if result not in ("yes", "no") or strike is None:
            continue
        t = close_ts - left_s
        q = quotes.get(t)
        if q is None or not valid_quote(q[0], q[1]):
            continue
        closes = [spot.get(t - 60 * k - 60) for k in range(dist.SIGMA_WINDOW, -1, -1)]
        z6 = dist.z_score(closes, strike)
        if z6 is None:
            continue
        p = model_p(z6, tau)
        d = dist.decide(p, q[0], q[1])
        if d is None:
            continue
        side, price = d
        yes = result == "yes"
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        out.append({"ticker": ticker, "series": dist.SERIES, "day": day, "close_ts": close_ts, "side": side, "price": price, "p": p, "yes": yes,
                    "net": dist.net(side, price, yes), "stress": dist.net(side, price, yes, dist.STRESS), "gross": dist.net(side, price, yes, 0.0)})
    return sorted(out, key=lambda o: o["close_ts"])


def calibration(markets: list[tuple], spot: dict, left_s: int, tau: float) -> list[tuple]:
    """Information only: how often YES happened against the model's own p, in deciles. Decides nothing."""
    rows = []
    for ticker, close_ts, strike, result, quotes in markets:
        if result not in ("yes", "no") or strike is None:
            continue
        t = close_ts - left_s
        q = quotes.get(t)
        if q is None or not valid_quote(q[0], q[1]):
            continue
        z6 = dist.z_score([spot.get(t - 60 * k - 60) for k in range(dist.SIGMA_WINDOW, -1, -1)], strike)
        if z6 is not None:
            rows.append((model_p(z6, tau), (q[0] + q[1]) / 2, result == "yes"))
    out = []
    for d in range(10):
        b = [r for r in rows if min(int(r[0] * 10), 9) == d]
        if b:
            out.append((d / 10, len(b), sum(r[0] for r in b) / len(b), sum(r[1] for r in b) / len(b), sum(r[2] for r in b) / len(b)))
    return out


def main() -> None:
    db = sqlite3.connect(DB)
    markets, spot = dist.load(db)
    print(f"{len(markets)} Bitcoin markets with a strike.\n")
    for name, r in RULES.items():
        e = entries(markets, spot, r["left_s"], r["tau"])
        print(report(f"{name} (decision {r['left_s'] // 60} min left, variance factor {r['tau'] + 1 / 3:.2f})", e))
        fav = [x for x in e if x["price"] >= 0.80]
        if e:
            print(f"   information only: {len(fav)} favorites (80c or more) mean net {sum(x['net'] for x in fav) / max(len(fav), 1) * 100:+.2f}c; the rest {sum(x['net'] for x in e if x['price'] < 0.80) / max(len(e) - len(fav), 1) * 100:+.2f}c")
        print("   model calibration (information only): decile, n, mean model p, mean market mid, YES rate")
        for d in calibration(markets, spot, r["left_s"], r["tau"]):
            print(f"     {d[0]:.1f}  n={d[1]:>5}  model {d[2]:.2f}  market {d[3]:.2f}  YES {d[4]:.2f}")
        print()


if __name__ == "__main__":
    main()
