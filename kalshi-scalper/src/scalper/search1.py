"""SEARCH1 (README, Pre-registration: SEARCH1): a walk-forward search over entry time x price band x exit rule on Bitcoin and Ethereum pooled. The best combination on the first two
thirds of the days is tested ONCE on the last third. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.search1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before any combination was scored ----
SERIES = ("KXBTC15M", "KXETH15M")
LEFTS = (720, 660, 600, 540, 480, 420, 360, 300, 240)
BANDS = ((0.55, 0.70), (0.70, 0.80), (0.80, 0.88), (0.88, 0.93), (0.93, 0.97), (0.97, 0.995))
EXITS = ("HOLD", "TP97", "TP4", "SL50", "T120")
DISC_FRAC, MIN_DISC, MIN_CONF, CONF_C, CONF_Z, FALSIFY_C, FALSIFY_Z = 2 / 3, 300, 150, 0.010, 1.65, 0.003, 1.0
RESULT = DATA_DIR / "search1_result.txt"


def bid_of(c: tuple, side: str) -> float:
    return c[1] if side == "yes" else round(1 - c[2], 4)


def settle(side: str, price: float, res: str, exit_kind: str, later: list[tuple], close: int) -> float:
    """Net per contract for one entry under one exit rule. Later candles are those strictly after the entry candle and ending at least 30 s before the close; an exit sells at that candle's
    bid (one fee on each leg). HOLD: to settlement. TP97: sell once the bid is >= 0.97. TP4: sell once the bid is >= entry + 0.04. SL50: sell once the bid is <= 0.50. T120: sell at the
    bid of the candle ending 120 s before the close."""
    for c in later:
        b = bid_of(c, side)
        if (exit_kind == "TP97" and b >= 0.97) or (exit_kind == "TP4" and b >= round(price + 0.04, 4)) or (exit_kind == "SL50" and b <= 0.50) or (exit_kind == "T120" and c[0] == close - 120):
            return b - price - L.fee(price) - L.fee(b)
    return L.net(side, price, res == "yes")


def combos(markets: list[tuple]) -> dict[tuple, list[dict]]:
    out: dict[tuple, list[dict]] = {}
    for t, s, c, cl, res in markets:
        cs = sorted(c)
        for left in LEFTS:
            x = next((y for y in cs if y[0] == cl - left), None)
            if x is None:
                continue
            for band in BANDS:
                p = L.favorite(x[1], x[2], band)
                if p is None:
                    continue
                side, price = p
                later = [y for y in cs if cl - left < y[0] <= cl - 30]
                day = datetime.fromtimestamp(cl, timezone.utc).strftime("%Y-%m-%d")
                for ex in EXITS:
                    out.setdefault((left, band, ex), []).append({"day": day, "close_ts": cl, "net": settle(side, price, res, ex, later, cl)})
    return out


def pf(rows: list[dict]) -> float:
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    return w / l if l else float("inf")


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = {}
    for m in load() + load_fresh():
        if m[1] in SERIES and m[4] in ("yes", "no") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = m
    allc = combos(list(mk.values()))
    days = sorted({r["day"] for rows in allc.values() for r in rows})
    cut = days[int(len(days) * DISC_FRAC)]
    scored = []
    for key, rows in allc.items():
        d = [r for r in rows if r["day"] < cut]
        if len(d) < MIN_DISC:
            continue
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in d])
        scored.append((z, m, key, len(d)))
    scored.sort(reverse=True)
    out = [f"SEARCH1: {len(mk)} markets, {len(allc)} combinations, {len(scored)} with discovery n >= {MIN_DISC}; discovery before {cut}"]
    out.append("top 5 on discovery (information): " + "; ".join(f"{k[0]}s {k[1]} {k[2]} z {z:+.2f} {100 * m:+.2f}c n {n}" for z, m, k, n in scored[:5]))
    z0, m0, key, nd = scored[0]
    conf = [r for r in allc[key] if r["day"] >= cut]
    if len(conf) < MIN_CONF:
        verdict, line = "NOT_ENOUGH_DATA", f"n={len(conf)}"
    else:
        cm, _, cz = cluster_mean_z([(r["day"], r["net"]) for r in conf])
        cd = sorted({r["day"] for r in conf})
        mid = cd[len(cd) // 2]
        h = [st.mean(r["net"] for r in conf if (r["day"] < mid) == first) for first in (True, False)]
        ok = cm >= CONF_C and cz >= CONF_Z and h[0] > 0 and h[1] > 0
        verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (cm < FALSIFY_C or cz < FALSIFY_Z) else "NOT_ENOUGH_DATA")
        line = f"confirmation n={len(conf)} mean {100 * cm:+.2f}c z {cz:+.2f} halves {100 * h[0]:+.2f}c / {100 * h[1]:+.2f}c PF {pf(conf):.2f}"
    out.append(f"CHOSEN {key[0]}s band {key[1]} exit {key[2]} (discovery z {z0:+.2f}, {100 * m0:+.2f}c, n {nd}): {verdict}; {line}")
    placebo = sum(1 for z, m, k, n in scored if z >= z0)
    out.append(f"combinations at or above the chosen discovery z: {placebo}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
