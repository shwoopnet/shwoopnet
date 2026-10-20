"""TP1 (README, Pre-registration: TP1): take profit at 99c on L1's entries. Rules fixed in the README before this file existed.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Entries are exactly L1's. After entry the held side's bid is read at the candle closes 300, 240, 180, 120 and 60 s before the close (strictly later than the entry candle); at the first one
where it is at or above 0.99 the position is sold there, at that bid, paying a taker fee on both legs. Otherwise it is held to settlement. The result only settles a position that was never sold.
It runs on two windows, each read ONCE: the 40 days in book.sqlite (primary) and the 28 older days in l1b.sqlite (holdout). The rule must pass in both.

Usage, ONCE: python -m scalper.tp1
"""
from __future__ import annotations

from collections import defaultdict

from . import altseries as A
from . import l1b
from . import lstrats as L
from .calibration import cluster_mean_z
from .exits import CHECK_LEFT_S, late_prices, null_diff_p95, outcome, side_bid
from .scalps import STRESS, load as load_markets

TP = 0.99
PASS_Z = 2.5
MIN_N = 300
MIN_DAYS = 5


def find_tp(entry: dict, candles: list[tuple]):
    """(exit bid, seconds left) at the first check where the held side's bid is at or above TP, or None. Only candles strictly after the entry candle are looked at."""
    by = {c[0]: c for c in candles}
    for left in CHECK_LEFT_S:
        c = by.get(entry["close_ts"] - left)
        if c is None:
            continue
        b = side_bid(entry["side"], c)
        if b is not None and b >= TP - 1e-9:
            return b, left
    return None


def build(entries: list[dict], candles_by_ticker: dict) -> list[dict]:
    out = []
    for e in entries:
        ex = find_tp(e, candles_by_ticker.get(e["ticker"], []))
        out.append(dict(e, exit=ex, hold=outcome(e, None), net=outcome(e, ex), stress=outcome(e, ex, STRESS), hold_stress=outcome(e, None, STRESS)))
    return out


def flip_rate(rows: list[dict]) -> tuple[int, int]:
    """(entries that reached the take-profit line, how many of those then LOST at settlement). Information only: break-even is about 1% to 1.5%."""
    hit = [r for r in rows if r["exit"] is not None]
    return len(hit), sum(1 for r in hit if r["hold"] <= 0)


def verdict(rows: list[dict], null95: float | None) -> tuple[str, dict]:
    """The registered bar, per window: n and days, difference above zero, day clustered z of the difference, both halves of the DAYS positive, positive with fees x1.2, above the fair-market 95th percentile."""
    n = len(rows)
    diffs = [(r["day"], r["net"] - r["hold"]) for r in rows]
    dm, _, dz = cluster_mean_z(diffs)
    days = sorted({r["day"] for r in rows})
    first = set(days[: len(days) // 2])
    h1 = [r["net"] - r["hold"] for r in rows if r["day"] in first]
    h2 = [r["net"] - r["hold"] for r in rows if r["day"] not in first]
    s = {"n": n, "days": len(days), "diff": dm, "diff_z": dz, "h1": sum(h1) / len(h1) if h1 else 0.0, "h2": sum(h2) / len(h2) if h2 else 0.0,
         "stress_diff": sum(r["stress"] - r["hold_stress"] for r in rows) / n if n else 0.0, "null95": null95,
         "mean": sum(r["net"] for r in rows) / n if n else 0.0, "hold_mean": sum(r["hold"] for r in rows) / n if n else 0.0}
    if n < MIN_N or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    ok = dm > 0 and dz >= PASS_Z and s["h1"] > 0 and s["h2"] > 0 and s["stress_diff"] > 0 and (null95 is None or dm > null95)
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), s


def report(name: str, markets: list[tuple], entries: list[dict]) -> str:
    candles = {m[0]: m[2] for m in markets}
    rows = build(entries, candles)
    v, s = verdict(rows, null_diff_p95(rows, late_prices(markets)))
    hit, lost = flip_rate(rows)
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"{name}: n={s['n']} on {s['days']} days; the line was reached in {hit} entries ({hit / max(1, s['n']) * 100:.1f}%), and {lost} of those then LOST at settlement (flip rate {lost / max(1, hit) * 100:.2f}%, break-even about 1% to 1.5%)")
    print(f"   rule {f(s['mean'])} vs HOLD {f(s['hold_mean'])}: difference {f(s['diff'])} per entry (day clustered z {s['diff_z']:+.2f}); fair-market 95th percentile of the difference {f(s['null95'])}")
    print(f"   halves of the days {f(s['h1'])} / {f(s['h2'])}; fees x{STRESS} difference {f(s['stress_diff'])}")
    print(f"   VERDICT ({name}; bar z>={PASS_Z}, n>={MIN_N}, both halves, fees x{STRESS}, above the fair-market difference): {v}\n")
    return v


def run() -> None:
    markets, _ = load_markets()
    v1 = report("book.sqlite, the 40 days (primary)", markets, L.hold_rule(markets, **L.L1))
    A.ALT_DB = l1b.DATA_DIR / "l1b.sqlite"
    old, _ = A.load_alts()
    v2 = report("l1b.sqlite, the 28 older days (holdout)", old, l1b.holdout(L.hold_rule(old, **L.L1)))
    both = "NOT_YET_FALSIFIED" if v1 == v2 == "NOT_YET_FALSIFIED" else ("NOT_ENOUGH_DATA" if "NOT_ENOUGH_DATA" in (v1, v2) and "FALSIFIED" not in (v1, v2) else "FALSIFIED")
    print(f"TP1 overall (must pass in BOTH windows): {both}\nNo verdict here means trade.")


if __name__ == "__main__":
    run()
