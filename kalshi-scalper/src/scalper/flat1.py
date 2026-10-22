"""FLAT1 (README, Pre-registration: FLAT1): are L1 favourites whose price barely moved in the last 5 minutes better than the rest? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flat1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict

from . import feat1 as F
from .crowd1 import diff_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
RNG5_MAX, RISE3_MAX = 0.02, 0.01
I_RISE3, I_RNG5 = 2, 6                         # positions in feat1.NUM
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_DAYS, MONTH_MIN, PLACEBO_REPS, SEED = 0.010, 2.0, 0.003, 1.0, 1500, 10, 200, 100, 61
LIVE = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")
RESULT = DATA_DIR / "flat1_result.txt"


def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """(flat, moving)."""
    flat = [r for r in rows if r["x"][I_RNG5] <= RNG5_MAX and abs(r["x"][I_RISE3]) <= RISE3_MAX]
    ids = {id(r) for r in flat}
    return flat, [r for r in rows if id(r) not in ids]


def judge(flat: list[dict], moving: list[dict], min_n: int = MIN_N, month_min: int = MONTH_MIN) -> dict:
    n, days = len(flat), len({r["day"] for r in flat})
    m, z, _ = diff_z(flat, moving)
    a, b = sorted(flat, key=lambda r: r["close_ts"]), sorted(moving, key=lambda r: r["close_ts"])
    ha, hb = len(a) // 2, len(b) // 2
    h1 = st.mean(r["net"] for r in a[:ha]) - st.mean(r["net"] for r in b[:hb]) if ha and hb else 0.0
    h2 = st.mean(r["net"] for r in a[ha:]) - st.mean(r["net"] for r in b[hb:]) if ha and hb else 0.0
    ms, _, _ = diff_z(flat, moving, "stress")
    months = defaultdict(lambda: [[], []])
    for r in flat:
        months[r["day"][:7]][0].append(r["net"])
    for r in moving:
        months[r["day"][:7]][1].append(r["net"])
    mdiff = {k: st.mean(v[0]) - st.mean(v[1]) for k, v in months.items() if len(v[0]) >= month_min and v[1]}
    rng = random.Random(SEED)
    pool = flat + moving
    pz = []
    for _ in range(PLACEBO_REPS):
        rng.shuffle(pool)
        pz.append(diff_z(pool[:len(flat)], pool[len(flat):])[1])
    p95 = sorted(pz)[int(0.95 * len(pz)) - 1]
    ok = (n >= min_n and days >= MIN_DAYS and m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0
          and sum(1 for v in mdiff.values() if v > 0) >= min(2, len(mdiff)) and z > p95)
    if n < min_n or days < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif ok:
        verdict = "NOT_YET_FALSIFIED"
    elif m < FALSIFY_C or z < FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    loss = lambda xs: 100 * sum(1 for r in xs if r["gross"] < 0) / max(1, len(xs))
    return {"verdict": verdict, "n_flat": n, "n_moving": len(moving), "flat_share_pct": 100 * n / max(1, n + len(moving)), "days": days,
            "diff_c": 100 * m, "z": z, "halves_c": (100 * h1, 100 * h2), "stress_diff_c": 100 * ms,
            "months_c": {k: 100 * v for k, v in sorted(mdiff.items())}, "placebo_tail": p95,
            "flat_c": 100 * st.mean(r["net"] for r in flat) if flat else 0.0, "moving_c": 100 * st.mean(r["net"] for r in moving) if moving else 0.0,
            "loss_pct_flat": loss(flat), "loss_pct_moving": loss(moving)}


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
    out = ["FLAT1 primary (all series)"] + [f"{k}: {v}" for k, v in judge(*split(rows)).items()]
    out.append("info: live five series only")
    out += [f"{k}: {v}" for k, v in judge(*split([r for r in rows if r["series"] in LIVE])).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
