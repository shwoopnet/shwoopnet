"""L1, L2 and L3 from the README ledger (rules fixed in the README before this file existed).

L1  buy the favorite (ask 0.88 to 0.97) with 6 minutes left, hold to settlement.
L3  buy the favorite (ask 0.90 to 0.98) with 2 minutes left, hold to settlement.
L2  H7's entered markets, but sell at 80c on the first LATER minute close where the side's bid is 80c or more.

Every rule enters at the ask, pays a 7% x p x (1-p) taker fee on the way in (and on the 80c exit for L2), and is judged
by the same bar as H2: n at least 300, day clustered z at least 2.1, positive in both halves, positive with fees x1.2.
Verdicts are only FALSIFIED, NOT_YET_FALSIFIED and NOT_ENOUGH_DATA. Nothing here has a parameter that reads a result.

Usage: python -m scalper.lstrats
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from . import distance as dist
from .analyze import valid_quote
from .paths import DB
from .scalps import STRESS, Z_BAR, MIN_N, fee, judge, load as load_markets

L1 = {"left_s": 360, "band": (0.88, 0.97)}
L3 = {"left_s": 120, "band": (0.90, 0.98)}
EXIT = 0.80


def favorite(bid: float, ask: float, band: tuple[float, float]):
    """The side whose ask is inside the band, as (side, price), or None. YES is bought at its ask, NO at 1 minus the YES bid,
    snapped to 4 places so a price of exactly 97c is not lost to floating point (1 - 0.03 is 0.97 only after rounding)."""
    if not valid_quote(bid, ask):
        return None
    lo, hi = band
    if lo <= ask <= hi:
        return ("yes", ask)
    no = round(1 - bid, 4)
    if lo <= no <= hi:
        return ("no", no)
    return None


def net(side: str, price: float, yes_won: bool, mult: float = 1.0) -> float:
    won = yes_won if side == "yes" else (not yes_won)
    return (1.0 if won else 0.0) - price - fee(price, mult)


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def hold_rule(markets: list[tuple], left_s: int, band: tuple[float, float]) -> list[dict]:
    """One observation per market, from the candle that ENDS exactly left_s before the close. A market with no candle at that
    minute, no usable quote or no result has no observation; nothing earlier or later is substituted."""
    out = []
    for ticker, series, candles, close_ts, res in markets:
        if res not in ("yes", "no"):
            continue
        t = close_ts - left_s
        c = next((x for x in candles if x[0] == t), None)
        if c is None:
            continue
        pick = favorite(c[1], c[2], band)
        if pick is None:
            continue
        side, price = pick
        yes = res == "yes"
        out.append({"ticker": ticker, "series": series, "day": _day(close_ts), "close_ts": close_ts, "side": side,
                    "price": price, "net": net(side, price, yes), "stress": net(side, price, yes, STRESS), "gross": net(side, price, yes, 0.0)})
    return sorted(out, key=lambda o: o["close_ts"])


def l2_rule(markets: list[tuple], spot: dict) -> list[dict]:
    """H7's test-half entries with H2's exit. The bucket table comes from H7's estimation half only."""
    obs = dist.observations(markets, spot)
    est, test = dist.split(obs)
    table = dist.estimate(est)
    quotes = {m[0]: m[4] for m in markets}
    out = []
    for o in test:
        d = dist.decide(table[dist.bucket(o["z"])]["p"], o["bid"], o["ask"])
        if d is None:
            continue
        side, price = d
        t = o["close_ts"] - dist.DECISION_LEFT_S
        q = quotes.get(o["ticker"], {})
        exit_ = False
        for end in sorted(e for e in q if e > t):          # strictly later than the decision minute
            bid, ask = q[end]
            side_bid = bid if side == "yes" else round(1 - ask, 4)
            if side_bid >= EXIT:
                exit_ = True
                break

        def pnl(mult):
            if exit_:
                return EXIT - fee(EXIT, mult) - price - fee(price, mult)
            return net(side, price, o["yes"], mult)
        out.append({"ticker": o["ticker"], "series": dist.SERIES, "day": o["day"], "close_ts": o["close_ts"], "side": side,
                    "price": price, "net": pnl(1.0), "stress": pnl(STRESS), "gross": pnl(0.0), "exited": exit_})
    return sorted(out, key=lambda o: o["close_ts"])


def verdict(entries: list[dict]) -> tuple[str, dict | None]:
    if len(entries) < MIN_N:
        return "NOT_ENOUGH_DATA", None
    mid = sorted(e["close_ts"] for e in entries)[len(entries) // 2]
    v, summ = judge({"x": [(e["day"], e["close_ts"], e["net"], e["stress"]) for e in entries]}, mid)
    return v, summ[0]


def report(name: str, entries: list[dict]) -> str:
    v, s = verdict(entries)
    n = len(entries)
    gross = sum(e["gross"] for e in entries) / n if n else 0.0
    lines = [f"{name}: n={n}  gross {gross*100:+.2f}c" + (
        f"  net {s['mean']*100:+.2f}c  z {s['z']:+.2f}  1st half {s['h1']*100:+.2f}c  2nd half {s['h2']*100:+.2f}c  fees x{STRESS} {s['stress']*100:+.2f}c" if s else "")]
    for series in sorted({e["series"] for e in entries}):
        sub = [e for e in entries if e["series"] == series]
        lines.append(f"   {series}: n={len(sub)} mean net {sum(e['net'] for e in sub)/len(sub)*100:+.2f}c  (information only)")
    lines.append(f"   VERDICT (bar z>={Z_BAR}, n>={MIN_N}, both halves, fees x{STRESS}): {v}")
    return "\n".join(lines)


def main() -> None:
    markets, _ = load_markets()
    if not markets:
        print("No data. Run: python -m scalper.backfill")
        return
    print(f"{len(markets)} markets. Net profit per contract after the entry fee, held to settlement unless stated.\n")
    print(report("L1 favorite 0.88-0.97 at 6 min left", hold_rule(markets, **L1)))
    print()
    print(report("L3 favorite 0.90-0.98 at 2 min left", hold_rule(markets, **L3)))
    print()
    db = sqlite3.connect(DB)
    dm, spot = dist.load(db)
    print(report("L2 H7 entries, sell at 80c", l2_rule(dm, spot)))


if __name__ == "__main__":
    main()
