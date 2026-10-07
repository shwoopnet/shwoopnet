"""H7: does how far Bitcoin spot sits from the market's target predict the outcome better than the market's price?
(Rules in the README, fixed 2026-10-07 before this was written.)

One observation per market, at the minute close with 6 minutes left. The distance is measured in units of how far
Bitcoin typically moves in that time: z = ln(spot / strike) / (sigma * sqrt(6)), sigma the standard deviation of the
1 minute log returns over the previous 60 minutes. Markets are ordered by close time; the first half ESTIMATES the share
that resolve YES in each z bucket, the second half TESTS a single fixed rule. `describe` prints the plain table (how
often the market finished above its target at each distance) from the estimation half ONLY and cannot see the test
half. `verdict` runs the rule on the test half.

No verdict means "trade". Fewer than 300 entered markets is NOT_ENOUGH_DATA and crosses nothing off.

Usage: python -m scalper.distance describe     (estimation half only)
       python -m scalper.distance              (the one verdict run)
"""
from __future__ import annotations

import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .marketmaker import fee
from .paths import DB
from .scalps import MIN_N, STRESS, judge

SERIES = "KXBTC15M"
DECISION_LEFT_S = 360          # 6 minutes left
MINUTES_LEFT = 6
SIGMA_WINDOW = 60              # minutes of spot returns behind sigma
EDGES = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)     # 8 buckets
MIN_BUCKET = 20                # an estimation bucket thinner than this is not traded
MARGIN = 0.02                  # fixed, not tuned


def bucket(z: float) -> int:
    """0 for z below the first edge, up to len(EDGES) for z at or above the last. A value on an edge goes up."""
    return sum(1 for e in EDGES if z >= e)


def bucket_label(i: int) -> str:
    lo = "below" if i == 0 else f"{EDGES[i - 1]:g}"
    hi = "above" if i == len(EDGES) else f"{EDGES[i]:g}"
    return f"{hi} {EDGES[-1]:g}" if i == len(EDGES) else (f"below {EDGES[0]:g}" if i == 0 else f"{lo} to {hi}")


def z_score(spot_closes: list[float], strike: float) -> float | None:
    """spot_closes: the SIGMA_WINDOW + 1 closes ending at the decision minute, oldest first."""
    if len(spot_closes) != SIGMA_WINDOW + 1 or not strike or strike <= 0 or any(not c or c <= 0 for c in spot_closes):
        return None
    rets = [math.log(b / a) for a, b in zip(spot_closes, spot_closes[1:])]
    mean = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / (len(rets) - 1))
    if sd <= 0:
        return None
    return math.log(spot_closes[-1] / strike) / (sd * math.sqrt(MINUTES_LEFT))


def observations(markets: list[tuple], spot: dict) -> list[dict]:
    """markets: (ticker, close_ts, strike, result, {end_ts: (bid, ask)}). spot: start_ts -> close.
    The price at a candle END is the close of the 1 minute candle that STARTED a minute earlier, as in the lag study."""
    out = []
    for ticker, close_ts, strike, result, quotes in markets:
        if result not in ("yes", "no") or strike is None:
            continue
        t = close_ts - DECISION_LEFT_S
        q = quotes.get(t)
        if q is None or not valid_quote(q[0], q[1]):
            continue
        closes = [spot.get(t - 60 * k - 60) for k in range(SIGMA_WINDOW, -1, -1)]      # oldest first, last is the price at t
        z = z_score(closes, strike)
        if z is None:
            continue
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        out.append({"ticker": ticker, "close_ts": close_ts, "day": day, "z": z, "bid": q[0], "ask": q[1], "yes": result == "yes"})
    return sorted(out, key=lambda o: o["close_ts"])


def split(obs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Ordered by close time: the first half estimates, the second half tests."""
    h = len(obs) // 2
    return obs[:h], obs[h:]


def estimate(est: list[dict]) -> dict[int, dict]:
    """bucket -> {n, p}. p is the share of that bucket's markets that resolved YES. Thin buckets carry p None."""
    by: dict = defaultdict(list)
    for o in est:
        by[bucket(o["z"])].append(o["yes"])
    out = {}
    for i in range(len(EDGES) + 1):
        ys = by.get(i, [])
        out[i] = {"n": len(ys), "p": (sum(ys) / len(ys)) if len(ys) >= MIN_BUCKET else None}
    return out


def describe(est: list[dict]) -> list[dict]:
    """The plain table for the estimation half: how often the market finished above its target, against the price."""
    by: dict = defaultdict(list)
    for o in est:
        by[bucket(o["z"])].append(o)
    rows = []
    for i in range(len(EDGES) + 1):
        os_ = by.get(i, [])
        n = len(os_)
        rows.append({"bucket": bucket_label(i), "n": n,
                     "yes_rate": (sum(1 for o in os_ if o["yes"]) / n) if n else None,
                     "mean_ask": (sum(o["ask"] for o in os_) / n) if n else None})
    return rows


def decide(p: float | None, bid: float, ask: float) -> tuple[str, float] | None:
    """The one rule. Buy YES at the ask, or NO at 1 - bid, only when the bucket's rate beats the price, the fee and MARGIN."""
    if p is None:
        return None
    if p - ask - fee(ask) > MARGIN:
        return ("yes", ask)
    no_price = 1 - bid
    if (1 - p) - no_price - fee(no_price) > MARGIN:
        return ("no", no_price)
    return None


def net(side: str, price: float, yes_won: bool, mult: float = 1.0) -> float:
    won = yes_won if side == "yes" else (not yes_won)
    return (1.0 if won else 0.0) - price - fee(price, mult)


def run(test: list[dict], est_table: dict[int, dict]) -> list[dict]:
    """The entered markets of a half, with net and fee-stressed net, in dollars."""
    out = []
    for o in test:
        d = decide(est_table[bucket(o["z"])]["p"], o["bid"], o["ask"])
        if d is None:
            continue
        side, price = d
        out.append({"day": o["day"], "close_ts": o["close_ts"], "side": side, "price": price, "yes": o["yes"],
                    "net": net(side, price, o["yes"]), "stress": net(side, price, o["yes"], STRESS), "gross": net(side, price, o["yes"], 0.0)})
    return out


def verdict(entries: list[dict]) -> tuple[str, list[dict]]:
    if len(entries) < MIN_N:
        return "NOT_ENOUGH_DATA", [{"band": "h7", "n": len(entries)}]
    mid = sorted(e["close_ts"] for e in entries)[len(entries) // 2]
    return judge({"h7": [(e["day"], e["close_ts"], e["net"], e["stress"]) for e in entries]}, mid)


def load(db) -> tuple[list[tuple], dict]:
    quotes: dict = defaultdict(dict)
    for t, end, b, a in db.execute("SELECT c.ticker, c.end_ts, c.bid_c, c.ask_c FROM candle c JOIN market m ON m.ticker = c.ticker WHERE m.series = ?", (SERIES,)):
        quotes[t][end] = (b, a)
    markets = [(t, c, k, r, quotes.get(t, {})) for t, c, k, r in db.execute(
        "SELECT ticker, close_ts, strike, result FROM market WHERE series = ? AND strike IS NOT NULL", (SERIES,))]
    spot = {ts: c for ts, c in db.execute("SELECT ts, c FROM spot")}
    return markets, spot


def _pct(x):
    return "   n/a" if x is None else f"{x * 100:5.1f}%"


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "verdict"
    db = sqlite3.connect(DB)
    markets, spot = load(db)
    obs = observations(markets, spot)
    est, test = split(obs)
    print(f"H7: {len(obs)} Bitcoin markets with a usable quote at 6 minutes left and 61 spot minutes. Estimation half {len(est)}, test half {len(test)}.\n")
    print("HOW OFTEN THE MARKET FINISHED ABOVE ITS TARGET, by how far spot sat from it at 6 minutes left")
    print("(estimation half only; z is the distance in units of typical Bitcoin movement over those 6 minutes)")
    print(f"{'z bucket':>12} {'markets':>8} {'finished YES':>13} {'YES ask charged':>16}")
    for r in describe(est):
        print(f"{r['bucket']:>12} {r['n']:>8} {_pct(r['yes_rate']):>13} {_pct(r['mean_ask']):>16}")
    if mode == "describe":
        print("\nDescriptive only. The test half has not been looked at.")
        return
    table = estimate(est)
    entries = run(test, table)
    v, summ = verdict(entries)
    n = len(entries)
    print(f"\nRULE ON THE TEST HALF: {n} entered markets of {len(test)}.")
    if v == "NOT_ENOUGH_DATA":
        print(f"VERDICT (pre-registered): NOT_ENOUGH_DATA, {n} entered markets (needs {MIN_N}). Nothing is crossed off.")
    else:
        s = summ[0]
        print(f"{'entered':>8} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'passes':>7}")
        print(f"{s['n']:>8} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} {s['h2']*100:>9.2f} {s['stress']*100:>10.2f} {str(s['ok']):>7}")
        print(f"\nVERDICT (pre-registered, bar z>=2.1, entered>={MIN_N}, both halves, fees x{STRESS}): {v}")
        print("  " + ("The distance rule does not clear every criterion." if v == "FALSIFIED" else "Permission to test on unseen days. Not evidence of an edge."))
    if n:
        yes = [e for e in entries if e["side"] == "yes"]
        no_ = [e for e in entries if e["side"] == "no"]
        wr = lambda es: (sum(1 for e in es if net(e["side"], 0, e["yes"]) > 0) / len(es)) if es else None
        print(f"\nDECOMPOSITION (cents per entered market): gross {sum(e['gross'] for e in entries)/n*100:.2f}, fees {-(sum(e['gross'] - e['net'] for e in entries)/n)*100:.2f}, net {sum(e['net'] for e in entries)/n*100:.2f}")
        print(f"  YES entries {len(yes)} (won {_pct(wr(yes))}, mean price {_pct(sum(e['price'] for e in yes)/len(yes) if yes else None)}), "
              f"NO entries {len(no_)} (won {_pct(wr(no_))}, mean price {_pct(sum(e['price'] for e in no_)/len(no_) if no_ else None)})")
        ins = run(est, table)
        if ins:
            print(f"  In-sample (estimation half, same rule): {len(ins)} entered, net {sum(e['net'] for e in ins)/len(ins)*100:.2f}c, so the gap to the test half is visible")


if __name__ == "__main__":
    main()
