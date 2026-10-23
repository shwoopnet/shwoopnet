"""TAIL1 (README, Pre-registration: TAIL1): does buying gold's cheap side (ask 0.04 to 0.10, 360 s out) pay? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.tail1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the tail outcomes were computed ----
SERIES, LEFT_S, LO, HI = "KXGOLD15M", 360, 0.04, 0.10
MEAN_C, Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N = 0.010, 2.0, 0.003, 1.0, 500
RESULT = DATA_DIR / "tail1_result.txt"


def entries(markets: list[tuple], lo: float = LO, hi: float = HI, series=SERIES) -> list[dict]:
    """One observation per qualifying side per market: the side whose ask is in [lo, hi] at the candle ending LEFT_S before the close."""
    out = []
    for ticker, s, candles, close_ts, res in markets:
        if (series is not None and s != series) or res not in ("yes", "no"):
            continue
        c = next((x for x in candles if x[0] == close_ts - LEFT_S), None)
        if c is None or c[1] is None or c[2] is None:
            continue
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        for side, ask in (("yes", c[2]), ("no", round(1 - c[1], 4))):
            if lo <= ask <= hi:
                out.append({"day": day, "net": L.net(side, ask, res == "yes"), "stress": L.net(side, ask, res == "yes", L.STRESS)})
    return out


def summary(rows: list[dict], key: str = "net"):
    return cluster_mean_z([(r["day"], r[key]) for r in rows])


def judge(rows: list[dict]) -> dict:
    if len(rows) < MIN_N:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(rows)}
    m, _, z = summary(rows)
    ms = summary(rows, "stress")[0]
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h1, h2 = (summary([r for r in rows if (r["day"] < mid) == first])[0] for first in (True, False))
    ok = m >= MEAN_C and z >= Z_BAR and h1 > 0 and h2 > 0 and ms > 0
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "n": len(rows), "mean": m, "z": z, "h1": h1, "h2": h2, "stress": ms}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = load()
    j = judge(entries(mk))
    out = [f"TAIL1: verdict {j['verdict']}, gold n={j['n']}"]
    if "mean" in j:
        out.append(f"mean {100 * j['mean']:+.2f}c z {j['z']:+.2f} halves {100 * j['h1']:+.2f}/{100 * j['h2']:+.2f} stress {100 * j['stress']:+.2f}")
    for name, rows in (("all series 0.04-0.10", entries(mk, series=None)), ("gold 0.01-0.04", entries(mk, 0.01, 0.04)), ("gold 0.10-0.20", entries(mk, 0.10, 0.20))):
        if rows:
            m, _, z = summary(rows)
            out.append(f"(not judged) {name}: n={len(rows)} mean {100 * m:+.2f}c z {z:+.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
