"""B4 (README, Pre-registration: B4): L1 unchanged except the band, 84c up to but not including 88c, on the Bitcoin and gold history. Research only: nothing here places an order.

Usage: python -m scalper.band84        (one read; prints the observation count first)
"""
from __future__ import annotations

import statistics as st

from . import lstrats as L
from .calibration import cluster_mean_z
from .scalps import MIN_N, STRESS, Z_BAR
from .scalps import load as load_main

MIN_DAYS = 5
LEFT_S = L.L1["left_s"]          # 360 s, the same minute as L1
BAND = (0.84, 0.8799)            # an ask of exactly 0.88 stays with L1, so nothing is counted twice


def summarize(es: list[dict]) -> tuple[str, dict]:
    """The pre-registered pass bar, the same as every earlier test."""
    if not es:
        return "FALSIFIED", {"n": 0}
    es = sorted(es, key=lambda e: e["close_ts"])
    mean, se, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    days = sorted({e["day"] for e in es})
    mid = (es[0]["close_ts"] + es[-1]["close_ts"]) / 2
    h1 = [e["net"] for e in es if e["close_ts"] < mid]
    h2 = [e["net"] for e in es if e["close_ts"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in es) / len(es)
    win = sum(1 for e in es if e["gross"] + e["price"] > 0.5) / len(es)
    ok = len(es) >= MIN_N and len(days) >= MIN_DAYS and z >= Z_BAR and mean > 0 and stress > 0 and m1 > 0 and m2 > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(es), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress,
                                                           "win": win, "paid": sum(e["price"] for e in es) / len(es)}


def _row(name: str, es: list[dict]) -> None:
    v, s = summarize(es)
    if not s["n"]:
        print(f"{name}: no observations -> {v}")
        return
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"{name}: n={s['n']} on {s['days']} days ({s['n'] / s['days']:.1f}/day), net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, "
          f"fees x{STRESS} {f(s['stress'])}, win {s['win']:.1%} against {s['paid']:.1%} paid -> {v}")


def run() -> None:
    markets, _ = load_main()
    es = L.hold_rule(markets, left_s=LEFT_S, band=BAND)
    print(f"{len(markets)} Bitcoin and gold markets; signal count first: {len(es)} observations in the 84c to 88c band")
    _row("B4 84c to 88c, both series", es)
    print("-- information only (the pre-registered verdict is the line above) --")
    for series in ("KXBTC15M", "KXGOLD15M"):
        _row(f"  {series}", [e for e in es if e["series"] == series])
    _row("  sub-band 84c to 86c", [e for e in es if e["price"] < 0.86])
    _row("  sub-band 86c to 88c", [e for e in es if e["price"] >= 0.86])
    _row("reference: L1's own band (88c to 97c), same days", L.hold_rule(markets, **L.L1))


if __name__ == "__main__":
    run()
