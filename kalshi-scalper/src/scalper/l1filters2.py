"""OP4 and OP5: two more filters on L1 (rules fixed in the README before this file existed).

OP4: the side bought already had an ask of 0.85 or more 10 minutes before the close. OP5: the entry candle's spread is 0.02 or less. Each splits L1's entries into an ARM (kept)
and a COMPLEMENT (removed); entries a filter cannot evaluate are excluded from both and counted. Nothing here reads a result to decide an entry; results only settle trades.
Pass criteria are filters.verdict with the pre-registered bar for two tries (z 2.3).

Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.l1filters2
"""
from __future__ import annotations

from . import filters as F
from . import lstrats as L
from .analyze import valid_quote
from .scalps import load as load_markets
from .cheapscalp import side_prices

EARLY_LEFT_S = 600
EARLY_ASK = 0.85
TIGHT = 0.02
Z_BAR = 2.3        # two tries


def split_op4(entries: list[dict], candles_by_ticker: dict, close_by_ticker: dict):
    arm, comp, excl = [], [], 0
    for e in entries:
        candles = candles_by_ticker.get(e["ticker"], [])
        c = next((x for x in candles if close_by_ticker[e["ticker"]] - x[0] == EARLY_LEFT_S), None)
        if c is None or not valid_quote(c[1], c[2]):
            excl += 1
            continue
        ask, _ = side_prices(e["side"], c)
        if ask is None:
            excl += 1
        elif ask >= EARLY_ASK - 1e-9:
            arm.append(e)
        else:
            comp.append(e)
    return arm, comp, excl


def split_op5(entries: list[dict], spread_by_ticker: dict):
    arm, comp, excl = [], [], 0
    for e in entries:
        sp = spread_by_ticker.get(e["ticker"])
        if sp is None:
            excl += 1
        elif sp <= TIGHT + 1e-9:
            arm.append(e)
        else:
            comp.append(e)
    return arm, comp, excl


def verdict(arm, comp, null95=None):
    old = F.PASS_Z
    F.PASS_Z = Z_BAR
    try:
        return F.verdict(arm, comp, null95)
    finally:
        F.PASS_Z = old


def line(name: str, arm, comp, excl) -> str:
    v, s = verdict(arm, comp, F.null_p95(arm) if len(arm) >= F.MIN_N else None)
    c = F.summarize(comp)
    f = lambda x: f"{x * 100:+.2f}c"
    return (f"{name}: arm n={s['n']} on {s['days']} days net {f(s['mean'])} z {s['z']:+.2f} halves {f(s['h1'])} / {f(s['h2'])} fees x{F.STRESS} {f(s['stress'])}"
            f"\n   complement n={c['n']} net {f(c['mean'])}; arm minus complement {f(s['diff'])} (day clustered z {s['diff_z']:+.2f}); excluded {excl}"
            + (f"; fair market 95th percentile {f(s['null95'])}" if s["null95"] is not None else "") + f"\n   VERDICT: {v}")


def main() -> None:
    markets, _ = load_markets()
    base = L.hold_rule(markets, **L.L1)
    candles = {m[0]: m[2] for m in markets}
    closes = {m[0]: m[3] for m in markets}
    spread = {}
    for ticker, _, cs, close_ts, _ in markets:
        c = next((x for x in cs if close_ts - x[0] == L.L1["left_s"]), None)
        if c is not None and c[1] is not None and c[2] is not None:
            spread[ticker] = round(c[2] - c[1], 4)
    s0 = F.summarize(base)
    print(f"base L1: n={s0['n']} net {s0['mean'] * 100:+.2f}c z {s0['z']:+.2f} on {s0['days']} days\n")
    print(line("OP4 early favorite (ask 0.85 or more at 10 min left)", *split_op4(base, candles, closes)) + "\n")
    print(line("OP5 tight book (spread 0.02 or less at 6 min left)", *split_op5(base, spread)) + "\n")
    print("No verdict here means trade. NOT_YET_FALSIFIED is permission to test forward and nothing more.")


if __name__ == "__main__":
    main()
