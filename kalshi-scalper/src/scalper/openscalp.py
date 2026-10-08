"""OP1 to OP3: favorite scalps and a dip buy in the first minutes of a market. Rules fixed in the README before this file existed.

OP1/OP2: entry at the first candle close 3 to 5 minutes in (ending 720, 660 or 600 seconds before the close) where a side's ask is 0.70 to 0.90; exit at the first LATER close where that
side's bid is at least the entry ask plus the target (3c, 5c), else sold at the bid 6 minutes before the close. OP3: entry 3 to 6 minutes in where the side's ask is 0.70 to 0.90 and at
least 3c below its ask one minute earlier; exit when the bid is at least the earlier ask minus 1c, else the 6 minute bid. Taker fee both legs. A missing 6 minute candle holds to settlement
and is counted. Nothing here reads a result to decide an exit.

Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.openscalp
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .cheapscalp import side_prices
from .calibration import cluster_mean_z
from .scalps import STRESS, fee, load as load_markets

BAND = (0.70, 0.90)
TIME_EXIT_LEFT_S = 360
SPECS = {"OP1": {"target": 0.03, "lefts": (720, 660, 600), "dip": False},
         "OP2": {"target": 0.05, "lefts": (720, 660, 600), "dip": False},
         "OP3": {"target": None, "lefts": (720, 660, 600, 540), "dip": True}}
DIP = 0.03
MIN_N = 300
MIN_DAYS = 5
Z_BAR = 2.5


def find_entry(candles: list[tuple], close_ts: int, spec: dict):
    by = {c[0]: c for c in candles}
    for left in spec["lefts"]:
        c = by.get(close_ts - left)
        if c is None or not valid_quote(c[1], c[2]):
            continue
        for side in ("yes", "no"):
            ask, _ = side_prices(side, c)
            if ask is None or not (BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9):
                continue
            if not spec["dip"]:
                return {"side": side, "ask": ask, "left": left, "goal": ask + spec["target"]}
            prev = by.get(close_ts - left - 60)
            if prev is None or not valid_quote(prev[1], prev[2]):
                continue
            pask, _ = side_prices(side, prev)
            if pask is not None and pask - ask >= DIP - 1e-9:
                return {"side": side, "ask": ask, "left": left, "goal": round(pask - 0.01, 4)}
    return None


def trade(candles: list[tuple], close_ts: int, result: str, spec: dict, mult: float = 1.0):
    e = find_entry(candles, close_ts, spec)
    if e is None:
        return None
    side, ask = e["side"], e["ask"]
    entry_cost = ask + fee(ask, mult)
    # Only candles up to and including the 6 minute mark are looked at for the target: after it the position has already been sold at that bid.
    for c in sorted((c for c in candles if TIME_EXIT_LEFT_S <= close_ts - c[0] < e["left"]), key=lambda c: c[0]):
        _, bid = side_prices(side, c)
        if bid is not None and valid_quote(c[1], c[2]) and bid >= e["goal"] - 1e-9 and bid >= 0.001:
            return {"net": bid - entry_cost - fee(bid, mult), "how": "target", "ask": ask, "side": side}
    cx = next((c for c in candles if close_ts - c[0] == TIME_EXIT_LEFT_S), None)
    if cx is not None and close_ts - cx[0] < e["left"]:
        _, bid = side_prices(side, cx)
        bid = 0.0 if bid is None or bid < 0.001 else bid
        return {"net": bid - entry_cost - fee(bid, mult), "how": "time", "ask": ask, "side": side}
    if result not in ("yes", "no"):
        return None
    won = result == side
    return {"net": (1.0 if won else 0.0) - entry_cost, "how": "held (no time-exit candle)", "ask": ask, "side": side}


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def run(markets: list[tuple], spec: dict, mult0: float = 1.0) -> list[dict]:
    out = []
    for ticker, series, candles, close_ts, res in markets:
        t = trade(candles, close_ts, res, spec, mult0)
        if t:
            s = trade(candles, close_ts, res, spec, STRESS)
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


def opening_spreads(markets: list[tuple]) -> dict:
    """Information only: the median closing spread of the candles 1 to 5 minutes in, by UTC hour and weekday against weekend."""
    by_hour: dict = defaultdict(list)
    by_wk: dict = defaultdict(list)
    for _, _, candles, close_ts, _ in markets:
        sp = [c[2] - c[1] for c in candles if 600 <= close_ts - c[0] <= 840 and valid_quote(c[1], c[2])]
        if not sp:
            continue
        m = sorted(sp)[len(sp) // 2]
        d = datetime.fromtimestamp(close_ts, timezone.utc)
        by_hour[d.hour].append(m)
        by_wk["weekend" if d.weekday() >= 5 else "weekday"].append(m)
    med = lambda xs: sorted(xs)[len(xs) // 2]
    return {"hour": {h: (med(v), len(v)) for h, v in sorted(by_hour.items())}, "wk": {k: (med(v), len(v)) for k, v in by_wk.items()}}


def main() -> None:
    markets, mid = load_markets()
    print(f"{len(markets)} markets. Favorite scalps and the dip buy, first minutes. Net per contract, cents.\n")
    print(f"{'':4} {'n':>5} {'days':>5} {'mean':>8} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10}  verdict")
    detail = {}
    for name, spec in SPECS.items():
        rows = run(markets, spec)
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
        nosig = sum(1 for r in rows if "no time-exit" in r["how"])
        wins = [r["net"] for r in rows if r["net"] > 0]
        losses = [r["net"] for r in rows if r["net"] <= 0]
        print(f"  {name}: target hit {hit:.1%}; average win {(sum(wins)/len(wins)*100 if wins else 0):+.2f}c, average loss {(sum(losses)/len(losses)*100 if losses else 0):+.2f}c; "
              f"BTC {_m(rows, 'KXBTC15M')}, gold {_m(rows, 'KXGOLD15M')}; held for want of a 6 minute candle: {nosig}")
    for name, spec in SPECS.items():
        g = []
        for _, _, candles, close_ts, res in markets:
            t = trade(candles, close_ts, res, spec, 0.0)
            if t:
                g.append(t["net"])
        if g:
            print(f"  {name} gross of fees: {sum(g)/len(g)*100:+.2f}c (n {len(g)})")
    sp = opening_spreads(markets)
    print("\nMeasurement, no verdict: median spread (cents) of candles 1 to 5 minutes in")
    print("  weekday/weekend: " + ", ".join(f"{k} {v[0]*100:.1f}c (n {v[1]})" for k, v in sp["wk"].items()))
    print("  by UTC hour: " + ", ".join(f"{h:02d} {v[0]*100:.1f}" for h, v in sp["hour"].items()))


def _m(rows, series):
    r = [x["net"] for x in rows if x["series"] == series]
    return f"{sum(r)/len(r)*100:+.2f}c (n {len(r)})" if r else "n/a"


if __name__ == "__main__":
    main()
