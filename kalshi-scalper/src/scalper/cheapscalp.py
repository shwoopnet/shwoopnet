"""C1 to C3: buy the 8c to 15c side in the first five minutes of a market and take a few cents. Rules fixed in the README before this file existed.

Entry: the first minute close in the first five minutes (candles ending 840, 780, 720, 660 or 600 seconds before the close) at which either side's ask is 0.08 to 0.15 on a real
quote. One entry per market. Exit: the first LATER minute close at which that side's bid is at least the entry ask plus the target T, sold at that bid, taker fee on both legs.
C1: T 5c, else held to settlement. C2: T 5c, else sold at the bid 6 minutes before the close. C3: T 10c, else sold as in C2. Nothing here reads a result to decide an exit: the
result only settles a position that was never sold. A market with no candle at the 6 minutes left mark, for C2 and C3, is held to settlement and counted (stated in the output).

Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.cheapscalp
"""
from __future__ import annotations

from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .scalps import STRESS, fee, load as load_markets

BAND = (0.08, 0.15)
ENTRY_LEFT_S = (840, 780, 720, 660, 600)
TIME_EXIT_LEFT_S = 360
VARIANTS = {"C1": (0.05, False), "C2": (0.05, True), "C3": (0.10, True)}
MIN_N = 300
MIN_DAYS = 5
Z_BAR = 2.5          # three tries
INFO_TARGET = 0.03   # information only


def side_prices(side: str, c: tuple):
    """(ask, bid) of the side at one candle (end, bid_c, ask_c, ...), snapped to 4 places. NO is priced as one minus the YES quote."""
    if side == "yes":
        return c[2], c[1]
    return (None if c[1] is None else round(1 - c[1], 4)), (None if c[2] is None else round(1 - c[2], 4))


def find_entry(candles: list[tuple], close_ts: int):
    by = {c[0]: c for c in candles}
    for left in ENTRY_LEFT_S:
        c = by.get(close_ts - left)
        if c is None or not valid_quote(c[1], c[2]):
            continue
        for side in ("yes", "no"):
            ask, _ = side_prices(side, c)
            if ask is not None and BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9:
                return {"side": side, "ask": ask, "left": left}
    return None


def trade(candles: list[tuple], close_ts: int, result: str, target: float, time_exit: bool, mult: float = 1.0):
    """One market. Returns {net, how, ask, side} or None (no entry, or no result for a position that needs one)."""
    e = find_entry(candles, close_ts)
    if e is None:
        return None
    side, ask = e["side"], e["ask"]
    entry_cost = ask + fee(ask, mult)
    # With a time exit, the target is only looked for up to and including the 6 minute mark: after it the position has already been sold at that bid.
    floor_left = TIME_EXIT_LEFT_S if time_exit else 0
    later = sorted((c for c in candles if floor_left <= close_ts - c[0] < e["left"]), key=lambda c: c[0])
    for c in later:
        _, bid = side_prices(side, c)
        if bid is not None and bid >= ask + target - 1e-9 and valid_quote(c[1], c[2]):
            return {"net": bid - entry_cost - fee(bid, mult), "how": "target", "ask": ask, "side": side}
    if time_exit:
        cx = next((c for c in candles if close_ts - c[0] == TIME_EXIT_LEFT_S), None)
        if cx is not None and close_ts - cx[0] < e["left"]:
            _, bid = side_prices(side, cx)
            bid = 0.0 if bid is None or bid < 0.001 else bid
            return {"net": bid - entry_cost - fee(bid, mult), "how": "time", "ask": ask, "side": side}
    if result not in ("yes", "no"):
        return None
    won = result == side
    return {"net": (1.0 if won else 0.0) - entry_cost, "how": "held" if not time_exit else "held (no time-exit candle)", "ask": ask, "side": side}


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def run(markets: list[tuple], target: float, time_exit: bool) -> list[dict]:
    out = []
    for ticker, series, candles, close_ts, res in markets:
        t = trade(candles, close_ts, res, target, time_exit)
        if t:
            s = trade(candles, close_ts, res, target, time_exit, STRESS)
            out.append(dict(t, ticker=ticker, series=series, day=_day(close_ts), close_ts=close_ts, stress=s["net"] if s else t["net"]))
    return out


def verdict(rows: list[dict], midpoint: float):
    n = len(rows)
    days = len({r["day"] for r in rows})
    if n < MIN_N or days < MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n": n, "days": days}
    mean, se, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    h1 = [r["net"] for r in rows if r["close_ts"] < midpoint]
    h2 = [r["net"] for r in rows if r["close_ts"] >= midpoint]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(r["stress"] for r in rows) / n
    ok = z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "days": days, "mean": mean, "se": se, "z": z, "h1": m1, "h2": m2, "stress": stress}


def main() -> None:
    markets, mid = load_markets()
    print(f"{len(markets)} markets. Cheap side (ask {BAND[0]:.2f} to {BAND[1]:.2f}) in the first five minutes. Net per contract, cents.\n")
    print(f"{'':4} {'n':>5} {'days':>5} {'mean':>8} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10}  verdict")
    detail = {}
    for name, (target, tx) in VARIANTS.items():
        rows = run(markets, target, tx)
        v, s = verdict(rows, mid)
        detail[name] = rows
        if "mean" in s:
            print(f"{name:4} {s['n']:>5} {s['days']:>5} {s['mean']*100:>8.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} {s['h2']*100:>9.2f} {s['stress']*100:>10.2f}  {v}")
        else:
            m = sum(r["net"] for r in rows) / len(rows) * 100 if rows else float("nan")
            print(f"{name:4} {s['n']:>5} {s['days']:>5} {m:>8.2f}  (too few entries or days to judge)  {v}")
    print("\nInformation only, unable to rescue a failure:")
    for name, rows in detail.items():
        if not rows:
            continue
        n = len(rows)
        hit = sum(1 for r in rows if r["how"] == "target") / n
        wins = [r["net"] for r in rows if r["net"] > 0]
        losses = [r["net"] for r in rows if r["net"] <= 0]
        nosig = sum(1 for r in rows if "no time-exit" in r["how"])
        print(f"  {name}: target hit {hit:.1%}; average win {(sum(wins)/len(wins)*100 if wins else 0):+.2f}c, average loss {(sum(losses)/len(losses)*100 if losses else 0):+.2f}c; "
              f"BTC {_m(rows, 'KXBTC15M')}, gold {_m(rows, 'KXGOLD15M')}; held for want of a 6 minute candle: {nosig}")
    extra = run(markets, INFO_TARGET, False)
    if extra:
        print(f"  3c target, held otherwise (not a registered variant): n {len(extra)}, mean {sum(r['net'] for r in extra)/len(extra)*100:+.2f}c")


def _m(rows, series):
    r = [x["net"] for x in rows if x["series"] == series]
    return f"{sum(r)/len(r)*100:+.2f}c (n {len(r)})" if r else "n/a"


if __name__ == "__main__":
    main()
