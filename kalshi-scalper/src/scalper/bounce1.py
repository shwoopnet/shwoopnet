"""BOUNCE1 (README, Pre-registration: BOUNCE1): the owner's trade: buy the cheap side (ask 0.10 to 0.30) of a Bitcoin 15 minute market with about 8 minutes left when the
spot is within $50 of the strike, and sell on the bounce. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.bounce1 run   (once; a second run is refused)
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT = DATA_DIR / "bounce1_result.txt"
SOURCES = ["book", "l1b", "fresh"]
LEFT_S, DIST, LO, HI = 480, 50.0, 0.10, 0.30
MULTS, SELL_BEFORE = (1.2, 1.3, 1.5), 120
MIN_N, BAR_C, BAR_Z, BASE_C, FALSIFY_C = 300, 0.010, 2.5, 0.005, 0.003


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def spot_map() -> dict[int, float]:
    db = sqlite3.connect(DATA_DIR / "search5k.sqlite")
    return {ts // 1000: c for ts, c in db.execute("select ts, c from bar where cur='BTC'")}


def markets() -> dict[str, tuple]:
    out = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        by = {}
        for tk, strike, close_ts, res in db.execute("select ticker, strike, close_ts, result from market where series='KXBTC15M' and strike is not null"):
            by[tk] = (strike, close_ts, res)
        for tk, (strike, close_ts, res) in by.items():
            if tk in out or res not in ("yes", "no"):
                continue
            cs = {r[0]: r for r in db.execute("select end_ts, bid_h, bid_c, ask_l, ask_c from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                out[tk] = (strike, close_ts, res, cs)
    return out


def run_variants(M: dict, spot: dict, left_s: int, dist: float, strict: bool = False):
    """Per variant, a list of (day, net, roi, net_stressed). Variants: HOLD, and A1/A2/B x multiples."""
    res: dict[str, list] = {}
    for tk, (strike, close_ts, result, cs) in M.items():
        t = close_ts - left_s
        c0 = cs.get(t)
        s = spot.get(t - 60)
        if c0 is None or s is None or abs(s - strike) >= dist:
            continue
        yes_ask, no_ask = c0[4], round(1 - c0[2], 4)
        if LO <= yes_ask <= HI:
            side = "yes"
        elif LO <= no_ask <= HI:
            side = "no"
        else:
            continue
        e = yes_ask if side == "yes" else no_ask
        payoff = 1.0 if result == side else 0.0
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        later = sorted(k for k in cs if t < k <= close_ts)
        def bid_hi(k):
            c = cs[k]
            return c[1] if side == "yes" else (None if c[3] is None else round(1 - c[3], 4))
        def bid_cl(k):
            c = cs[k]
            return c[2] if side == "yes" else round(1 - c[4], 4)
        pre = cs.get(close_ts - SELL_BEFORE)
        early_bid = None if pre is None else (pre[2] if side == "yes" else round(1 - pre[4], 4))
        def add(name, net_fn):
            r = [net_fn(1.0), net_fn(1.2)]
            res.setdefault(name, []).append((day, r[0], r[0] / e, r[1]))
        add("HOLD", lambda m: payoff - e - fee(e, m))
        for M_ in MULTS:
            T = round(e * M_, 4)
            hit = None
            for k in later:
                b = bid_cl(k) if strict else bid_hi(k)
                if b is not None and b >= T - 1e-9:
                    hit = k; break
            add(f"A1 x{M_}", (lambda m, T=T, hit=hit: (T - e - fee(e, m) - fee(T, m)) if hit else (payoff - e - fee(e, m))))
            add(f"A2 x{M_}", (lambda m, T=T, hit=hit: (T - e - fee(e, m) - fee(T, m)) if hit else ((early_bid - e - fee(e, m) - fee(early_bid, m)) if early_bid is not None else (payoff - e - fee(e, m)))))
            add(f"B  x{M_}", (lambda m, T=T, hit=hit: (0.3 * (T - fee(T, m)) + 0.7 * payoff - e - fee(e, m)) if hit else (payoff - e - fee(e, m))))
    return res


def summarize(v: list, cut: str):
    m, _, z = cluster_mean_z([(d, n) for d, n, _, _ in v])
    h1 = [n for d, n, _, _ in v if d < cut]; h2 = [n for d, n, _, _ in v if d >= cut]
    ms = sum(x[3] for x in v) / len(v)
    roi = sum(x[2] for x in v) / len(v)
    w = sum(n for _, n, _, _ in v if n > 0); l = -sum(n for _, n, _, _ in v if n < 0)
    return {"n": len(v), "mean": m, "z": z, "h1": sum(h1) / max(len(h1), 1), "h2": sum(h2) / max(len(h2), 1), "stress": ms, "roi": roi, "pf": (w / l if l else 99.0)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    M, spot = markets(), spot_map()
    main_res = run_variants(M, spot, LEFT_S, DIST)
    days = sorted({d for v in main_res.values() for d, *_ in v}); cut = days[len(days) // 2]
    lines = [f"BOUNCE1: {len(M)} Bitcoin 15 minute markets, entries {len(main_res.get('HOLD', []))}, {len(days)} days"]
    S = {k: summarize(v, cut) for k, v in main_res.items()}
    base = S["HOLD"]["mean"]
    passed = []
    for k, s in S.items():
        ok = k != "HOLD" and s["n"] >= MIN_N and s["mean"] >= BAR_C and s["z"] >= BAR_Z and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0 and s["mean"] - base >= BASE_C
        if ok: passed.append(k)
        lines.append(f"{k:8s} n={s['n']:4d} net {100 * s['mean']:+.2f}c ROI {100 * s['roi']:+.1f}% z {s['z']:+.2f} halves {100 * s['h1']:+.2f}/{100 * s['h2']:+.2f} stress {100 * s['stress']:+.2f}c PF {s['pf']:.2f} {'PASS' if ok else ''}")
    best = max((s["mean"] for k, s in S.items() if k != "HOLD"), default=0.0)
    n = S["HOLD"]["n"]
    verdict = "NOT_YET_FALSIFIED" if passed else ("NOT_ENOUGH_DATA" if n < MIN_N else ("FALSIFIED" if best < FALSIFY_C else "NOT_ENOUGH_DATA"))
    lines.insert(1, f"VERDICT {verdict}; passing: {passed}")
    lines.append("information (not claims): A1 x1.3 under other settings")
    for label, ls, dist, strict in (("dist $25", LEFT_S, 25.0, False), ("dist $100", LEFT_S, 100.0, False), ("6 min left", 360, DIST, False), ("10 min left", 600, DIST, False), ("closing-bid fills", LEFT_S, DIST, True)):
        r = run_variants(M, spot, ls, dist, strict)
        if r.get("A1 x1.3"):
            s = summarize(r["A1 x1.3"], cut); h = summarize(r["HOLD"], cut)
            lines.append(f"  {label:18s} n={s['n']:4d} A1 x1.3 net {100 * s['mean']:+.2f}c ROI {100 * s['roi']:+.1f}% z {s['z']:+.2f} | hold {100 * h['mean']:+.2f}c")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
