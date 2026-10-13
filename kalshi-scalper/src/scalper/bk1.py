"""BK1: seven basket and pair ideas on 40 days of Bitcoin, gold and Ethereum 15 minute markets. Rules fixed in the README ("Pre-registration: BK1") before this file ran on any
market. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.bk1
"""
from __future__ import annotations

from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .cheapscalp import side_prices
from .scalps import STRESS, fee, load as load_markets

SIGNAL_LEFT = 840      # the first minute after the open
ENTRY_LEFT = 780       # the next candle: strictly later than the signal
BK7_SIGNAL_LEFT = 480
BK7_ENTRY_LEFT = 420
BK7_EXTREME = 0.95
BK7_CAP = 0.90
DIVERGE = 0.10
NARROW = 0.01
HALF_DAYS = 20
MIN_N = 300
MIN_DAYS = 5
Z_BAR = 2.1
IDEAS = ("BK1", "BK2", "BK3", "BK4", "BK5", "BK6", "BK7")
BTC, GOLD, ETH = "KXBTC15M", "KXGOLD15M", "KXETH15M"


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def quote(by: dict, close_ts: int, left: int):
    """The candle ending `left` seconds before the close, if it has a usable two sided quote."""
    c = by.get(close_ts - left)
    return c if c is not None and valid_quote(c[1], c[2]) else None


def mid(c: tuple) -> float:
    return (c[1] + c[2]) / 2


def leg(c: tuple, res: str, side: str, mult: float = 1.0) -> float:
    """Net of one contract bought at the candle's closing ask and held to settlement."""
    ask, _ = side_prices(side, c)
    return (1.0 if res == side else 0.0) - ask - fee(ask, mult)


def other(side: str) -> str:
    return "no" if side == "yes" else "yes"


def build(markets: list[tuple]) -> dict:
    """close_ts -> {series: (candles_by_end_ts, result)} for settled markets only."""
    out: dict = {}
    for _t, series, cs, close_ts, res in markets:
        if res in ("yes", "no"):
            out.setdefault(close_ts, {})[series] = ({c[0]: c for c in cs}, res)
    return out


def _row(close_ts: int, net: float, stress: float, base: float) -> dict:
    return {"day": _day(close_ts), "close_ts": close_ts, "net": net, "stress": stress, "base": base}


def single_rows(built: dict, pick) -> list[dict]:
    """BK1 and BK2: `pick(mid_at_signal)` returns the side to buy or None."""
    rows = []
    for close_ts, per in built.items():
        for series, (by, res) in per.items():
            s, e = quote(by, close_ts, SIGNAL_LEFT), quote(by, close_ts, ENTRY_LEFT)
            if s is None or e is None:
                continue
            side = pick(mid(s))
            if side is None:
                continue
            base = (leg(e, res, "yes") + leg(e, res, "no")) / 2
            rows.append(_row(close_ts, leg(e, res, side), leg(e, res, side, STRESS), base))
    return rows


def pair_rows(built: dict, a: str, b: str, diverge: float | None = None) -> list[dict]:
    """BK3 to BK5: one unit is a pair (two contracts). Fixed: a YES, b NO. With `diverge`: YES on the lower mid at the signal, NO on the higher."""
    rows = []
    for close_ts, per in built.items():
        if a not in per or b not in per:
            continue
        (ba, ra), (bb, rb) = per[a], per[b]
        sa, sb = quote(ba, close_ts, SIGNAL_LEFT), quote(bb, close_ts, SIGNAL_LEFT)
        ea, eb = quote(ba, close_ts, ENTRY_LEFT), quote(bb, close_ts, ENTRY_LEFT)
        if None in (sa, sb, ea, eb):
            continue
        if diverge is None:
            sides = ("yes", "no")
        else:
            if abs(mid(sa) - mid(sb)) < diverge - 1e-9:
                continue
            sides = ("yes", "no") if mid(sa) < mid(sb) else ("no", "yes")
        net = leg(ea, ra, sides[0]) + leg(eb, rb, sides[1])
        stress = leg(ea, ra, sides[0], STRESS) + leg(eb, rb, sides[1], STRESS)
        base = sum(leg(ea, ra, x) + leg(eb, rb, y) for x in ("yes", "no") for y in ("yes", "no")) / 4
        rows.append(_row(close_ts, net, stress, base))
    return rows


def narrow_rows(built: dict) -> list[dict]:
    """BK6: buy YES at the entry candle only when its spread is 1c or less; the baseline is the day's mean YES buy over every market with a usable entry quote."""
    allyes: dict = {}
    cand = []
    for close_ts, per in built.items():
        for series, (by, res) in per.items():
            e = quote(by, close_ts, ENTRY_LEFT)
            if e is None:
                continue
            allyes.setdefault(_day(close_ts), []).append(leg(e, res, "yes"))
            if e[2] - e[1] <= NARROW + 1e-9:
                cand.append((close_ts, leg(e, res, "yes"), leg(e, res, "yes", STRESS)))
    daymean = {d: sum(v) / len(v) for d, v in allyes.items()}
    return [_row(ct, n, s, daymean[_day(ct)]) for ct, n, s in cand]


def lag_rows(built: dict) -> list[dict]:
    """BK7: Ethereum follows Bitcoin's early extreme. The baseline is a random Ethereum side at the same candle."""
    rows = []
    for close_ts, per in built.items():
        if BTC not in per or ETH not in per:
            continue
        (bb, _), (be, re) = per[BTC], per[ETH]
        sb = quote(bb, close_ts, BK7_SIGNAL_LEFT)
        e = quote(be, close_ts, BK7_ENTRY_LEFT)
        if sb is None or e is None:
            continue
        m = mid(sb)
        side = "yes" if m >= BK7_EXTREME - 1e-9 else ("no" if m <= 1 - BK7_EXTREME + 1e-9 else None)
        if side is None:
            continue
        ask, _ = side_prices(side, e)
        if ask is None or ask > BK7_CAP + 1e-9:
            continue
        base = (leg(e, re, "yes") + leg(e, re, "no")) / 2
        rows.append(_row(close_ts, leg(e, re, side), leg(e, re, side, STRESS), base))
    return rows


def all_rows(built: dict) -> dict:
    return {
        "BK1": single_rows(built, lambda m: None if abs(m - 0.5) < 1e-9 else ("yes" if m > 0.5 else "no")),
        "BK2": single_rows(built, lambda m: None if abs(m - 0.5) < 1e-9 else ("no" if m > 0.5 else "yes")),
        "BK3": pair_rows(built, BTC, ETH),
        "BK4": pair_rows(built, BTC, GOLD),
        "BK5": pair_rows(built, BTC, ETH, diverge=DIVERGE),
        "BK6": narrow_rows(built),
        "BK7": lag_rows(built),
    }


def summary(rows: list[dict], t0: int) -> dict | None:
    n = len(rows)
    if not n:
        return None
    mean, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    cmean, _, zc = cluster_mean_z([(r["day"], r["net"] - r["base"]) for r in rows])
    cut = t0 + HALF_DAYS * 86400
    h = [[r["net"] for r in rows if r["close_ts"] < cut], [r["net"] for r in rows if r["close_ts"] >= cut]]
    return {"n": n, "days": len({r["day"] for r in rows}), "mean": mean, "z": z, "cmean": cmean, "zc": zc, "stress": sum(r["stress"] for r in rows) / n,
            "h1": sum(h[0]) / len(h[0]) if h[0] else None, "h2": sum(h[1]) / len(h[1]) if h[1] else None}


def verdict(s: dict | None) -> str:
    if s is None or s["n"] < MIN_N or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA"
    ok = (s["mean"] > 0 and s["z"] >= Z_BAR and s["cmean"] > 0 and s["zc"] >= Z_BAR and s["h1"] is not None and s["h2"] is not None
          and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0)
    return "NOT_YET_FALSIFIED" if ok else "FALSIFIED"


def main() -> None:
    markets, _ = load_markets()
    built = build(markets)
    t0 = min(built)
    print(f"{sum(len(p) for p in built.values())} settled markets in {len(built)} windows, {_day(t0)} to {_day(max(built))}. Halves split after {HALF_DAYS} days.\n")
    controls = single_rows(built, lambda m: "yes"), single_rows(built, lambda m: "no")
    for name, rows in zip(("control: YES at E, every market", "control: NO at E, every market"), controls):
        s = summary(rows, t0)
        print(f"{name}: n={s['n']} net {s['mean']*100:+.2f}c")
    print()
    print(f"{'idea':<5} {'n':>6} {'days':>4} {'net c':>7} {'z':>6} {'contrast c':>10} {'zc':>6} {'half1 c':>8} {'half2 c':>8} {'stress c':>9}  verdict")
    for name, rows in all_rows(built).items():
        s = summary(rows, t0)
        if s is None:
            print(f"{name:<5} {0:>6}  no entries  NOT_ENOUGH_DATA")
            continue
        h1 = "n/a" if s["h1"] is None else f"{s['h1']*100:+.2f}"
        h2 = "n/a" if s["h2"] is None else f"{s['h2']*100:+.2f}"
        print(f"{name:<5} {s['n']:>6} {s['days']:>4} {s['mean']*100:>+7.2f} {s['z']:>6.2f} {s['cmean']*100:>+10.2f} {s['zc']:>6.2f} {h1:>8} {h2:>8} {s['stress']*100:>+9.2f}  {verdict(s)}")
    print("\nUnits: BK3, BK4 and BK5 are pairs (two contracts); the others are one contract. Net is after the fee; contrast is net minus the matched random-side baseline.")


if __name__ == "__main__":
    main()
