"""Q1 to Q3: three filters on L1 (rules fixed in the README before this file existed).

Q1 spot support (Bitcoin only), Q2 the previous market's result agrees, Q3 the other series agrees. Each splits L1's entries into an ARM (kept)
and a COMPLEMENT (removed); entries a filter cannot evaluate are excluded from both and counted. Nothing here reads a result to decide an entry;
results only settle trades and, for Q2, define the previous market's side (a market that closed 900 s earlier, strictly before the decision).

No function takes a performance parameter. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.filters
"""
from __future__ import annotations

import random
import sqlite3
from collections import defaultdict

from . import distance as D
from . import lstrats as L
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB
from .scalps import STRESS, fee, load as load_markets

K_MAIN = 1.0
K_INFO = (0.5, 2.0)
PAIR_MARGIN = 0.05
PASS_Z = 2.4            # three filters, 5% one sided
DIFF_Z = 2.0
MIN_N = 300
MIN_DAYS = 5
NULL_REPS = 500
OTHER = {"KXBTC15M": "KXGOLD15M", "KXGOLD15M": "KXBTC15M"}


def spot_z(close_ts: int, strike, spot: dict):
    """The same z as H7 at the same decision minute (6 minutes left), or None."""
    t = close_ts - D.DECISION_LEFT_S
    return D.z_score([spot.get(t - 60 * k - 60) for k in range(D.SIGMA_WINDOW, -1, -1)], strike)


def split_q1(entries: list[dict], strikes: dict, spot: dict, k: float = K_MAIN):
    arm, comp, excl = [], [], 0
    for e in entries:
        if e["series"] != "KXBTC15M":
            excl += 1
            continue
        z = spot_z(e["close_ts"], strikes.get(e["ticker"]), spot)
        if z is None:
            excl += 1
        elif (e["side"] == "yes" and z >= k) or (e["side"] == "no" and z <= -k):
            arm.append(e)
        else:
            comp.append(e)
    return arm, comp, excl


def split_q2(entries: list[dict], results: dict):
    arm, comp, excl = [], [], 0
    for e in entries:
        prev = results.get((e["series"], e["close_ts"] - 900))
        if prev not in ("yes", "no"):
            excl += 1
        elif prev == e["side"]:
            arm.append(e)
        else:
            comp.append(e)
    return arm, comp, excl


def split_q3(entries: list[dict], quotes: dict):
    """quotes[(series, close_ts)] -> (bid, ask) at the decision candle (close - 360)."""
    arm, comp, excl = [], [], 0
    for e in entries:
        q = quotes.get((OTHER[e["series"]], e["close_ts"]))
        if q is None or not valid_quote(q[0], q[1]):
            excl += 1
            continue
        mid = (q[0] + q[1]) / 2
        if mid >= 0.5 + PAIR_MARGIN - 1e-9:
            pointing = "yes"
        elif mid <= 0.5 - PAIR_MARGIN + 1e-9:
            pointing = "no"
        else:
            excl += 1
            continue
        (arm if pointing == e["side"] else comp).append(e)
    return arm, comp, excl


def summarize(es: list[dict]) -> dict:
    n = len(es)
    if n < 2:
        return {"n": n, "mean": 0.0, "z": 0.0, "h1": 0.0, "h2": 0.0, "stress": 0.0, "days": len({e["day"] for e in es})}
    mean, _, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    ordered = sorted(es, key=lambda e: e["close_ts"])
    h = n // 2
    h1 = sum(e["net"] for e in ordered[:h]) / h
    h2 = sum(e["net"] for e in ordered[h:]) / (n - h)
    return {"n": n, "mean": mean, "z": z, "h1": h1, "h2": h2, "stress": sum(e["stress"] for e in es) / n, "days": len({e["day"] for e in es})}


def diff_z(arm: list[dict], comp: list[dict]) -> tuple[float, float]:
    """Per UTC day, the arm's mean minus the complement's mean, over days where both exist: (mean difference, day clustered z)."""
    a, c = defaultdict(list), defaultdict(list)
    for e in arm:
        a[e["day"]].append(e["net"])
    for e in comp:
        c[e["day"]].append(e["net"])
    days = sorted(set(a) & set(c))
    if len(days) < 2:
        return 0.0, 0.0
    d = [(day, sum(a[day]) / len(a[day]) - sum(c[day]) / len(c[day])) for day in days]
    mean, _, z = cluster_mean_z([(str(i), v) for i, (_, v) in enumerate(d)])
    return mean, z


def null_p95(arm: list[dict], reps: int = NULL_REPS, seed: int = 3) -> float:
    """95th percentile of the arm's mean net if every entry won with probability equal to its own price (a fair market)."""
    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        tot = 0.0
        for e in arm:
            p = e["price"]
            tot += (1.0 if rng.random() < p else 0.0) - p - fee(p)
        means.append(tot / len(arm))
    means.sort()
    return means[int(0.95 * (len(means) - 1))]


def verdict(arm: list[dict], comp: list[dict], null95: float | None = None) -> tuple[str, dict]:
    s = summarize(arm)
    dm, dz = diff_z(arm, comp)
    s.update(diff=dm, diff_z=dz, null95=null95)
    if s["n"] < MIN_N or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    ok = (s["mean"] > 0 and s["z"] >= PASS_Z and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0
          and dm > 0 and dz >= DIFF_Z and (null95 is None or s["mean"] > null95))
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), s


def line(name: str, arm, comp, excl, with_null=True) -> str:
    v, s = verdict(arm, comp, null_p95(arm) if (with_null and len(arm) >= MIN_N) else None)
    c = summarize(comp)
    f = lambda x: f"{x * 100:+.2f}c"
    return (f"{name}: arm n={s['n']} on {s['days']} days net {f(s['mean'])} z {s['z']:+.2f} halves {f(s['h1'])} / {f(s['h2'])} fees x{STRESS} {f(s['stress'])}"
            f"\n   complement n={c['n']} net {f(c['mean'])}; arm minus complement {f(s['diff'])} (day clustered z {s['diff_z']:+.2f}); excluded {excl}"
            + (f"; fair market 95th percentile {f(s['null95'])}" if s["null95"] is not None else "") + f"\n   VERDICT: {v}")


def main() -> None:
    markets, _ = load_markets()
    base = L.hold_rule(markets, **L.L1)
    db = sqlite3.connect(DB)
    strikes = {t: k for t, k in db.execute("SELECT ticker, strike FROM market")}
    spot = {ts: c for ts, c in db.execute("SELECT ts, c FROM spot")}
    results = {(s, ct): r for s, ct, r in ((m[1], m[3], m[4]) for m in markets) if r in ("yes", "no")}
    quotes = {}
    for _, series, candles, close_ts, _ in markets:
        for c in candles:
            if c[0] == close_ts - 360:
                quotes[(series, close_ts)] = (c[1], c[2])
    s0 = summarize(base)
    print(f"base L1: n={s0['n']} net {s0['mean'] * 100:+.2f}c z {s0['z']:+.2f} on {s0['days']} days\n")
    for name, (arm, comp, excl) in (("Q1 spot support (Bitcoin)", split_q1(base, strikes, spot)),
                                    ("Q2 previous result agrees", split_q2(base, results)),
                                    ("Q3 other series agrees", split_q3(base, quotes))):
        print(line(name, arm, comp, excl) + "\n")
    print("Information only (counted as tries, decide nothing):")
    for k in K_INFO:
        arm, comp, excl = split_q1(base, strikes, spot, k)
        print(line(f"Q1 at K={k}", arm, comp, excl, with_null=False) + "\n")
    print("No verdict here means trade. NOT_YET_FALSIFIED is permission to test forward and nothing more.")


if __name__ == "__main__":
    main()
