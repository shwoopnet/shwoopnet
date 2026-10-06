"""H3: do resting buy orders earn the spread that H2 pays? (rules in the README, fixed
2026-10-06 before any trade tape was fetched.)

A one contract bid is rested at a side's best bid when it is in the 40c or 50c band, for
2 minutes. It counts as filled only if the tape prints strictly THROUGH our price on our
side inside that window, so everything ahead of us in the queue was eaten first. A print
AT our price does not count, because our queue place is unknown. That understates fills,
and the report says so. A filled order is held to settlement. Entry fee is Kalshi's taker
formula even though a resting order may pay less, so a possible discount cannot flatter it.

The number that decides what a result means is printed beside the verdict: the fill rate
and what the orders that did NOT fill would have earned. A profit on filled orders next to
a strong result on the missed ones is selection, not execution. (Crypto's maker test fell
into exactly that.)

No verdict means "trade". Fewer than 300 filled orders is NOT_ENOUGH_DATA and crosses nothing off.

Usage: python -m scalper.makers   (after python -m scalper.tape)
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB
from .scalps import BANDS, FEE_RATE, MIN_LEFT_S, MIN_N, STRESS, Z_BAR, judge

WINDOW_S = 120        # the primary resting time
INFO_WINDOW_S = 300   # information only
FETCH_S = INFO_WINDOW_S


def fee(price: float, mult: float = 1.0) -> float:
    return FEE_RATE * mult * price * (1 - price)


def plan(candles: list[tuple], close_ts: int, band: tuple[float, float]) -> tuple | None:
    """The one resting order for a market and band, or None. candles: (end, bid_c, ask_c) in
    time order. At the FIRST minute close with 5 or more minutes left and a usable quote where
    the YES bid, then the NO bid, is in the band. Returns (end_ts, side, bid, ask): ask is the
    price a taker would have paid for the same side at that minute (the comparison)."""
    lo, hi = band
    for end, bid, ask in candles:
        if close_ts - end < MIN_LEFT_S or not valid_quote(bid, ask):
            continue
        for side, b, a in (("yes", bid, ask), ("no", 1 - ask, 1 - bid)):
            if lo <= round(b, 4) <= hi:
                return end, side, round(b, 4), round(a, 4)
    return None


def filled(order: tuple, trades: list[tuple], window: int = WINDOW_S, strict: bool = True) -> bool:
    """trades: (ts, taker_side, yes_price, no_price). A YES bid at p fills when a taker buying NO
    (taker 'no') prints at a YES price below p; a NO bid at q fills when a taker buying YES
    (taker 'yes') prints at a NO price below q. Only prints after the order and inside the window."""
    end, side, price = order[0], order[1], order[2]
    for ts, taker, yes, no in trades:
        if not (end < ts <= end + window):
            continue
        if side == "yes" and taker == "no" and (round(yes, 4) < price if strict else round(yes, 4) <= price):
            return True
        if side == "no" and taker == "yes" and (round(no, 4) < price if strict else round(no, 4) <= price):
            return True
    return False


def net(side: str, result: str, price: float, mult: float = 1.0) -> float:
    """Profit per contract bought at `price` and held to settlement."""
    return (1.0 if result == side else 0.0) - price - fee(price, mult)


def orders_for(markets: list[tuple], results: dict) -> dict[str, list[dict]]:
    """markets: (ticker, series, candles, close_ts, result). results[(ticker, order minute)] =
    (fill, fill_opt, fill5, side, price), recorded when the tape window was fetched. An order
    whose window was never fetched, or was fetched for a different side or price, is left out:
    a window that was never fetched is not a window with no trades."""
    rows: dict[str, list[dict]] = {b: [] for b in BANDS}
    for ticker, _, candles, close_ts, result in markets:
        if result not in ("yes", "no"):
            continue
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        for b, band in BANDS.items():
            o = plan(candles, close_ts, band)
            if o is None:
                continue
            _, side, bid, ask = o
            got = results.get((ticker, o[0]))
            if got is None or got[3] != side or abs(got[4] - bid) > 1e-9:
                continue
            rows[b].append({
                "day": day, "close_ts": close_ts, "fill": got[0], "fill_opt": got[1], "fill5": got[2],
                "net": net(side, result, bid), "net_stress": net(side, result, bid, STRESS),
                "net_nofee": net(side, result, bid) + fee(bid), "net_ask": net(side, result, ask),
            })
    return rows


def verdict(rows: dict[str, list[dict]], midpoint: float) -> tuple[str, list[dict]]:
    """NOT_ENOUGH_DATA unless some band has MIN_N filled orders; then the README's kill criteria."""
    filled_rows = {b: [(r["day"], r["close_ts"], r["net"], r["net_stress"]) for r in rs if r["fill"]] for b, rs in rows.items()}
    if not any(len(v) >= MIN_N for v in filled_rows.values()):
        return "NOT_ENOUGH_DATA", [{"band": b, "n": len(v)} for b, v in sorted(filled_rows.items())]
    nonempty = {b: v for b, v in filled_rows.items() if v}
    return judge(nonempty, midpoint)


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def load() -> tuple[list[tuple], float, dict]:
    db = sqlite3.connect(DB)
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts, m.result "
         "FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
    for s, t, end, bc, ac, close_ts, res in db.execute(q):
        m = by[t]
        m["c"].append((end, bc, ac)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    markets = [(t, m["s"], m["c"], m["close"], m["res"]) for t, m in by.items()]
    closes = [m[3] for m in markets]
    mid = (min(closes) + max(closes)) / 2 if closes else 0.0
    results: dict = {}
    if db.execute("SELECT name FROM sqlite_master WHERE name='fills'").fetchone():
        for t, e, side, price, f1, f2, f5 in db.execute("SELECT ticker, end_ts, side, price, fill, fill_opt, fill5 FROM fills"):
            results[(t, e)] = (bool(f1), bool(f2), bool(f5), side, price)
    return markets, mid, results


def main() -> None:
    markets, mid, results = load()
    rows = orders_for(markets, results)
    total = sum(len(v) for v in rows.values())
    if not total:
        print("No orders with fetched tape. Run: python -m scalper.tape")
        return
    v, summ = verdict(rows, mid)
    print(f"H3: rest a one contract bid at the best bid in the 40c or 50c band for {WINDOW_S}s; held to settlement if filled.")
    print(f"{total} orders have a fetched tape window (the rest of {len(markets)} markets are not covered yet). Cents per contract.\n")
    print(f"{'band':>5} {'orders':>7} {'filled':>7} {'fill rate':>10} {'net filled':>11} {'net missed':>11} {'net all@bid':>12} {'at the ask':>11}")
    for b, rs in sorted(rows.items()):
        f = [r for r in rs if r["fill"]]
        m = [r for r in rs if not r["fill"]]
        c = lambda x: f"{x * 100:>9.2f}c" if x is not None else f"{'-':>10}"
        print(f"{b:>5} {len(rs):>7} {len(f):>7} {len(f) / len(rs) * 100 if rs else 0:>9.1f}% {c(mean([r['net'] for r in f])):>11} "
              f"{c(mean([r['net'] for r in m])):>11} {c(mean([r['net'] for r in rs])):>12} {c(mean([r['net_ask'] for r in rs])):>11}")
    print("\n'net missed' is what the orders that did NOT fill would have earned held from the same price. A filled")
    print("mean above zero beside a strongly positive missed mean is selection, not execution.\n")
    if v == "NOT_ENOUGH_DATA":
        print(f"VERDICT (pre-registered): NOT_ENOUGH_DATA. Filled orders per band: " + ", ".join(f"{s['band']} {s['n']}" for s in summ) + f" (needs {MIN_N}). Nothing is crossed off.")
    else:
        print(f"{'band':>5} {'filled':>7} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'detectable':>11} {'passes':>7}")
        for s in summ:
            print(f"{s['band']:>5} {s['n']:>7} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} "
                  f"{s['h2']*100:>9.2f} {s['stress']*100:>10.2f} {s['detectable']*100:>10.2f}c {str(s['ok']):>7}")
        print(f"\nVERDICT (pre-registered, bar z>={Z_BAR}, filled>={MIN_N}, both halves, fees x{STRESS}): {v}")
        print("  " + ("No band clears every criterion." if v == "FALSIFIED" else "Permission to test on unseen data. Not evidence of an edge."))
    print("\nINFORMATION ONLY, affects nothing above. Mean net per contract on filled orders, cents:")
    for name, key, fk in (("primary (strictly through, 2 min)", "net", "fill"), ("fills also when a print is AT our price", "net", "fill_opt"),
                          ("5 minute window", "net", "fill5"), ("no entry fee", "net_nofee", "fill")):
        cells = []
        for b, rs in sorted(rows.items()):
            x = mean([r[key] for r in rs if r[fk]])
            n = sum(1 for r in rs if r[fk])
            cells.append(f"{b} {x * 100:>6.2f}c (n={n})" if x is not None else f"{b} -")
        print(f"{name:>42}: " + "   ".join(cells))


if __name__ == "__main__":
    main()
