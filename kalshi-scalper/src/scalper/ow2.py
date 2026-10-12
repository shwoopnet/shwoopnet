"""OW2: an opening scalp that is flat before L1 buys. Rules fixed in the README ("Pre-registration: OW2") before this file ran on any market.

Entry in a market's first two minutes (the candle ending 840 s, else 780 s, before the close), exit at the first later candle whose closing bid reaches the target, else
at the candle ending 480 s before the close. Nothing is held past that candle. Taker fee on both legs. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Nothing here means trade.

Usage: python -m scalper.ow2
"""
from __future__ import annotations

from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .cheapscalp import side_prices
from .scalps import STRESS, fee, load as load_markets

ENTRY_LEFTS = (840, 780)
EXIT_LEFT_S = 480          # the last candle a position may be sold on: 80 s before L1's earliest buy (400 s left)
SPECS = {"OW2-A": {"band": (0.20, 0.40), "target": 0.10},
         "OW2-B": {"band": (0.20, 0.40), "target": 0.15},
         "OW2-C": {"band": (0.40, 0.80), "target": 0.10},
         "OW2-D": {"band": (0.40, 0.80), "target": 0.15}}
MIN_N = 300
MIN_DAYS = 5
Z_BAR = 2.5


def find_entry(candles: list[tuple], close_ts: int, spec: dict):
    by = {c[0]: c for c in candles}
    for left in ENTRY_LEFTS:
        c = by.get(close_ts - left)
        if c is None or not valid_quote(c[1], c[2]):
            continue
        for side in ("yes", "no"):
            ask, _ = side_prices(side, c)
            if ask is not None and spec["band"][0] - 1e-9 <= ask <= spec["band"][1] + 1e-9:
                return {"side": side, "ask": ask, "left": left}
    return None


def trade(candles: list[tuple], close_ts: int, spec: dict, mult: float = 1.0):
    """One market: the net per contract after fees, or None when there is no entry. A market whose 480 s candle is missing returns {"unresolvable": True}: it is never settled as if held."""
    e = find_entry(candles, close_ts, spec)
    if e is None:
        return None
    side, ask = e["side"], e["ask"]
    cost = ask + fee(ask, mult)
    goal = ask * (1 + spec["target"])
    for c in sorted((c for c in candles if EXIT_LEFT_S <= close_ts - c[0] < e["left"]), key=lambda c: c[0]):
        _, bid = side_prices(side, c)
        if bid is not None and valid_quote(c[1], c[2]) and bid >= goal - 1e-9 and bid >= 0.001:
            return {"net": bid - cost - fee(bid, mult), "how": "target", "exit_left": close_ts - c[0], "ask": ask, "side": side}
    cx = next((c for c in candles if close_ts - c[0] == EXIT_LEFT_S), None)
    if cx is None:
        return {"unresolvable": True}
    _, bid = side_prices(side, cx)
    bid = 0.0 if bid is None or bid < 0.001 else bid
    return {"net": bid - cost - fee(bid, mult), "how": "time", "exit_left": EXIT_LEFT_S, "ask": ask, "side": side}


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def run(markets: list[tuple], spec: dict):
    rows, unresolvable = [], 0
    for ticker, series, candles, close_ts, _res in markets:
        t = trade(candles, close_ts, spec)
        if t is None:
            continue
        if t.get("unresolvable"):
            unresolvable += 1
            continue
        s = trade(candles, close_ts, spec, STRESS)
        rows.append(dict(t, ticker=ticker, series=series, day=_day(close_ts), close_ts=close_ts, stress=s["net"] if s and "net" in s else t["net"]))
    return rows, unresolvable


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
    print(f"{len(markets)} markets. OW2: opening scalp, flat by {EXIT_LEFT_S} s before the close. Net per contract, cents.\n")
    print(f"{'':6} {'n':>5} {'days':>5} {'mean':>8} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'hit%':>6} {'unres':>6}  verdict")
    for name, spec in SPECS.items():
        rows, unres = run(markets, spec)
        v, s = verdict(rows, mid)
        hit = sum(1 for r in rows if r["how"] == "target") / len(rows) * 100 if rows else float("nan")
        if "mean" in s:
            print(f"{name:6} {s['n']:>5} {s['days']:>5} {s['mean']*100:>8.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} {s['h2']*100:>9.2f} {s['stress']*100:>10.2f} {hit:>6.1f} {unres:>6}  {v}")
        else:
            m = sum(r["net"] for r in rows) / len(rows) * 100 if rows else float("nan")
            print(f"{name:6} {s['n']:>5} {s['days']:>5} {m:>8.2f}  (too few entries or days to judge)  hit {hit:.1f}%  unresolvable {unres}  {v}")


if __name__ == "__main__":
    main()
