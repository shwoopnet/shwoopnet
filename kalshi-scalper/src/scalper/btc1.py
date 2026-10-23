"""BTC1 (README, Pre-registration: BTC1): does the prior window's result predict the next Bitcoin 15 minute window? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.btc1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from . import feat1 as F
from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before any outcome was split by the prior window ----
SERIES, WINDOW_S, OPEN_LEFT_S = "KXBTC15M", 900, 780
MEAN_C, Z_BAR, PF_BAR, FALSIFY_C, FALSIFY_Z, MIN_N = 0.020, 2.6, 1.3, 0.005, 1.0, 300
RESULT = DATA_DIR / "btc1_result.txt"


def day_of(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def prior_results(markets: list[tuple]) -> dict[int, str]:
    return {m[3]: m[4] for m in markets if m[1] == SERIES and m[4] in ("yes", "no")}


def l1_groups(markets: list[tuple], prior: dict[int, str]):
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in markets
            if s == SERIES and all(x[1] is not None and x[2] is not None for x in c)]
    rows, _, _ = F.build(full, 360)
    agree, dis = [], []
    for r in rows:
        p = prior.get(r["close_ts"] - WINDOW_S)
        if p is None:
            continue
        (agree if p == r["side"] else dis).append({"day": r["day"], "close_ts": r["close_ts"], "net": r["net"], "stress": r["stress"]})
    return agree, dis


def open_groups(markets: list[tuple], prior: dict[int, str]):
    cont, fade = [], []
    for t, s, c, cl, res in markets:
        p = prior.get(cl - WINDOW_S)
        if s != SERIES or res not in ("yes", "no") or p is None:
            continue
        x = next((x for x in c if x[0] == cl - OPEN_LEFT_S), None)
        if x is None or x[1] is None or x[2] is None:
            continue
        for grp, side in ((cont, p), (fade, "no" if p == "yes" else "yes")):
            ask = x[2] if side == "yes" else round(1 - x[1], 4)
            yes = res == "yes"
            grp.append({"day": day_of(cl), "close_ts": cl, "net": L.net(side, ask, yes), "stress": L.net(side, ask, yes, L.STRESS)})
    return cont, fade


def pf(rows: list[dict]) -> float:
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    return w / l if l > 0 else float("inf")


def judge(rows: list[dict]) -> dict:
    if len(rows) < MIN_N:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(rows)}
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    ms = sum(r["stress"] for r in rows) / len(rows)
    o = sorted(rows, key=lambda r: r["close_ts"])
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h = [sum(r["net"] for r in rows if (r["day"] < mid) == first) / max(1, sum(1 for r in rows if (r["day"] < mid) == first)) for first in (True, False)]
    p = pf(rows)
    ok = m >= MEAN_C and z >= Z_BAR and h[0] > 0 and h[1] > 0 and ms > 0 and p >= PF_BAR
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "n": len(rows), "mean": m, "z": z, "h1": h[0], "h2": h[1], "stress": ms, "pf": p, "loss": sum(1 for r in rows if r["net"] < 0) / len(rows)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = load()
    prior = prior_results(mk)
    a, d = l1_groups(mk, prior)
    c, f = open_groups(mk, prior)
    out = []
    for name, rows in (("AGREE", a), ("DISAGREE", d), ("CONT", c), ("FADE", f)):
        j = judge(rows)
        if "mean" in j:
            out.append(f"{name}: {j['verdict']} n={j['n']} mean {100 * j['mean']:+.2f}c z {j['z']:+.2f} halves {100 * j['h1']:+.2f}/{100 * j['h2']:+.2f} stress {100 * j['stress']:+.2f} PF {j['pf']:.2f} loss {100 * j['loss']:.1f}%")
        else:
            out.append(f"{name}: {j['verdict']} n={j['n']}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
