"""X1 to X4: does selling a collapsing L1 favourite early beat holding it to the close? (rules in the README, fixed before this file existed.)

Entries are exactly L1's. After entry the position is checked at the candle closes 5, 4, 3, 2 and 1 minutes before the close (strictly later than the entry candle);
at the first one where the held side's BID is at or below the threshold X (and is a real bid, at least 0.1c) it is sold there, at that bid, paying a taker fee on both legs.
Otherwise it is held to settlement. Nothing here reads a result to decide an exit: the result only settles a position that was never sold.

The fair-market null runs the same exit rule on the same price paths with each market's outcome drawn from its own late price, so the cost of the rule in a market with no edge
is measured, not assumed. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.exits
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

from . import feerounding as FR
from . import lstrats as L
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .scalps import STRESS, fee, load as load_markets

THRESHOLDS = {"X1": 0.50, "X2": 0.60, "X3": 0.70, "X4": 0.80, "X5": 0.40, "X6": 0.30, "X7": 0.20}
CHECK_LEFT_S = (300, 240, 180, 120, 60)
MIN_BID = 0.001
PASS_Z = 2.5                  # X1 to X4, four tries
PASS_Z_SEVEN = 2.7            # X5 to X7 (registered later): seven tries in all
MIN_N = 300
MIN_DAYS = 5
NULL_REPS = 500


def side_bid(side: str, c: tuple):
    """The bid of the side held at one candle (end, bid_c, ask_c, ...): YES bid, or for NO one minus the YES ask. None if there is no usable price."""
    if side == "yes":
        b = c[1]
    else:
        b = None if c[2] is None else round(1 - c[2], 4)
    return None if b is None else b


def find_exit(entry: dict, candles: list[tuple], x: float):
    """(exit price, seconds left) for the first check where the bid is at or below x, or None. Only candles strictly after the entry candle are looked at."""
    by = {c[0]: c for c in candles}
    for left in CHECK_LEFT_S:
        c = by.get(entry["close_ts"] - left)
        if c is None:
            continue
        b = side_bid(entry["side"], c)
        if b is not None and b >= MIN_BID - 1e-12 and b <= x + 1e-9:
            return b, left
    return None


def outcome(entry: dict, exit_: tuple | None, mult: float = 1.0, won: float | None = None) -> float:
    """Net per contract. Held: win - price - entry fee. Sold: bid - price - fee on both legs. `won` overrides the real result (the null world)."""
    p = entry["price"]
    if exit_ is not None:
        b = exit_[0]
        return b - p - fee(p, mult) - fee(b, mult)
    w = won if won is not None else (1.0 if entry["gross"] + p > 0.5 else 0.0)   # gross is won - price, so gross + price is 1 on a win and 0 on a loss
    return w - p - fee(p, mult)


def build(entries: list[dict], candles_by_ticker: dict, x: float) -> list[dict]:
    out = []
    for e in entries:
        ex = find_exit(e, candles_by_ticker.get(e["ticker"], []), x)
        out.append(dict(e, exit=ex, hold=outcome(e, None), net=outcome(e, ex), stress=outcome(e, ex, STRESS), hold_stress=outcome(e, None, STRESS)))
    return out


def late_prices(markets: list[tuple]) -> dict:
    """ticker -> the YES mid at the last valid candle at least a minute before the close (the price the fair-market outcome is drawn from)."""
    out = {}
    for ticker, _, candles, close_ts, _ in markets:
        ends = [c for c in candles if c[0] <= close_ts - 60 and valid_quote(c[1], c[2])]
        if ends:
            c = max(ends, key=lambda z: z[0])
            out[ticker] = min(max((c[1] + c[2]) / 2, 0.001), 0.999)
    return out


def null_diff_p95(rows: list[dict], late: dict, reps: int = NULL_REPS, seed: int = 11) -> float:
    """95th percentile of the mean (exit minus hold) when outcomes are drawn from each market's own late price: the rule's cost in a market with no edge."""
    rng = random.Random(seed)
    stopped = [r for r in rows if r["exit"] is not None and r["ticker"] in late]
    means = []
    for _ in range(reps):
        tot = 0.0
        for r in stopped:
            p_yes = late[r["ticker"]]
            yes = rng.random() < p_yes
            won = 1.0 if (yes if r["side"] == "yes" else not yes) else 0.0
            tot += r["net"] - outcome(r, None, won=won)
        means.append(tot / len(rows))
    means.sort()
    return means[int(0.95 * (len(means) - 1))]


def stats(rows: list[dict]) -> dict:
    n = len(rows)
    nets = [r["net"] for r in rows]
    mean = sum(nets) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in nets) / (n - 1))
    ordered = sorted(rows, key=lambda r: r["close_ts"])
    cum = peak = dd = 0.0
    for r in ordered:
        cum += r["net"]
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    by_day = defaultdict(float)
    for r in rows:
        by_day[r["day"]] += r["net"]
    h = n // 2
    stopped = [r for r in rows if r["exit"] is not None]
    return {"n": n, "days": len(by_day), "mean": mean, "sd": sd, "worst": min(nets), "worst_day": min(by_day.values()), "drawdown": dd,
            "h1": sum(r["net"] for r in ordered[:h]) / h, "h2": sum(r["net"] for r in ordered[h:]) / (n - h),
            "stress": sum(r["stress"] for r in rows) / n, "stopped": len(stopped) / n,
            "would_have_won": (sum(1 for r in stopped if r["hold"] > 0) / len(stopped)) if stopped else None}


def pass_z(name: str) -> float:
    return PASS_Z if name in ("X1", "X2", "X3", "X4") else PASS_Z_SEVEN


def verdict(rows: list[dict], null95: float | None, z_bar: float = PASS_Z) -> tuple[str, dict]:
    s = stats(rows)
    diffs = [(r["day"], r["net"] - r["hold"]) for r in rows]
    dm, _, dz = cluster_mean_z(diffs)
    s.update(diff=dm, diff_z=dz, null95=null95, hold_mean=sum(r["hold"] for r in rows) / len(rows))
    if s["n"] < MIN_N or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    ok = (dm > 0 and dz >= z_bar and s["mean"] > 0 and s["h1"] > 0 and s["h2"] > 0
          and sum(r["stress"] for r in rows) / len(rows) > 0 and (null95 is None or dm > null95))
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), s


def rounded_two_contracts(rows: list[dict]) -> float:
    """Information: net per contract at two contracts an order with Kalshi's cent rounding on each leg. A buy costs ceil_to_the_cent(2 * (p + fee)); a sale brings floor_to_the_cent(2 * (b - fee))."""
    tot = 0.0
    for r in rows:
        p = r["price"]
        cost = FR.order_cost(p, 2)
        if r["exit"] is not None:
            b = r["exit"][0]
            proceeds = math.floor(round(2 * (b - fee(b)) * 100, 6)) / 100.0
        else:
            proceeds = 2.0 if r["hold"] + p + fee(p) > 0.5 else 0.0
        tot += (proceeds - cost) / 2
    return tot / len(rows)


def main() -> None:
    markets, _ = load_markets()
    entries = L.hold_rule(markets, **L.L1)
    candles = {m[0]: m[2] for m in markets}
    late = late_prices(markets)
    base = build(entries, candles, -1.0)           # a threshold nothing can reach: HOLD
    b = stats(base)
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"HOLD: n={b['n']} on {b['days']} days, mean {f(b['mean'])}, sd {b['sd'] * 100:.1f}c, worst loss {f(b['worst'])}, worst day {f(b['worst_day'])}, drawdown {b['drawdown'] * 100:.1f}c, two contracts rounded {f(rounded_two_contracts(base))}\n")
    for name, x in THRESHOLDS.items():
        rows = build(entries, candles, x)
        v, s = verdict(rows, null_diff_p95(rows, late), pass_z(name))
        print(f"{name} (sell at {x * 100:.0f}c): stopped {s['stopped'] * 100:.1f}% of entries ({s['would_have_won'] * 100:.0f}% of those would have won if held)")
        print(f"   mean {f(s['mean'])} vs HOLD {f(s['hold_mean'])}: difference {f(s['diff'])} (day clustered z {s['diff_z']:+.2f}), fair-market 95th percentile of the difference {f(s['null95'])}")
        print(f"   sd {s['sd'] * 100:.1f}c, worst loss {f(s['worst'])}, worst day {f(s['worst_day'])}, drawdown {s['drawdown'] * 100:.1f}c, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, two contracts rounded {f(rounded_two_contracts(rows))}")
        print(f"   VERDICT (bar z>={pass_z(name)}, n>={MIN_N}, both halves, fees x{STRESS}, above the fair-market difference): {v}\n")
    print("No verdict here means trade.")


if __name__ == "__main__":
    main()
