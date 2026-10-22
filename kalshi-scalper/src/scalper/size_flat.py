"""SIZE1 (README, Pre-registration: SIZE1): 6 contracts on every FLAT entry and none elsewhere (B) against 1 contract on every entry (A), in dollars per day. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.size_flat run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict

from . import feat1 as F
from . import flat2
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
LIVE = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")
K, DIFF_Z_BAR, FALSIFY_Z, P5_SLACK, MIN_DAYS = 6, 2.0, 1.0, 1.25, 30
RESULT = DATA_DIR / "size_flat_result.txt"


def daily(rows: list[dict], k: int) -> dict[str, tuple[float, float]]:
    """day -> (A dollars at 1 contract on every entry, B dollars at k contracts on FLAT entries only)."""
    flat, _ = flat2.split(rows)
    ids = {id(r) for r in flat}
    out: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        out[r["day"]][0] += r["net"]
        if id(r) in ids:
            out[r["day"]][1] += k * r["net"]
    return {d: (a, b) for d, (a, b) in out.items()}


def pct5(xs: list[float]) -> float:
    return sorted(xs)[int(0.05 * len(xs))]


def judge(rows: list[dict], k: int = K) -> dict:
    d = daily(rows, k)
    days = sorted(d)
    a, b = [d[x][0] for x in days], [d[x][1] for x in days]
    diffs = [(x, d[x][1] - d[x][0]) for x in days]
    m, _, z = cluster_mean_z(diffs) if len(diffs) > 1 else (0.0, 0.0, 0.0)
    h = len(days) // 2
    h1, h2 = st.mean(b[:h]) - st.mean(a[:h]), st.mean(b[h:]) - st.mean(a[h:])
    pa, pb = pct5(a), pct5(b)
    risk_ok = pb >= P5_SLACK * pa if pa < 0 else pb >= pa
    c1 = len(days) >= MIN_DAYS and m > 0 and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0
    if len(days) < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif m <= 0 or z < FALSIFY_Z:
        verdict = "FALSIFIED"
    elif c1 and risk_ok:
        verdict = "NOT_YET_FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    return {"verdict": verdict, "days": len(days), "A_mean_per_day": st.mean(a), "B_mean_per_day": st.mean(b), "diff_per_day": m, "z": z, "halves": (h1, h2),
            "A_p5_day": pa, "B_p5_day": pb, "risk_ok": risk_ok, "A_worst_day": min(a), "B_worst_day": min(b), "days_B_lost_more_than_A": sum(1 for x, y in zip(a, b) if y < x),
            "A_sd": st.pstdev(a), "B_sd": st.pstdev(b)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    live = [r for r in rows if r["series"] in LIVE]
    out = ["SIZE1 primary: five live series, 6 contracts on FLAT"] + [f"{k}: {v}" for k, v in judge(live).items()]
    out.append("info: without gold")
    out += [f"{k}: {v}" for k, v in judge([r for r in live if r["series"] != "KXGOLD15M"]).items()]
    out.append("info: 3 contracts on FLAT")
    out += [f"{k}: {v}" for k, v in judge(live, 3).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
