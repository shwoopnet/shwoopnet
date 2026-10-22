"""LOSSCL1 (README, Pre-registration: LOSSCL1): do L1 favourite flips cluster within a series? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.losscl1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
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
NEAR_S, FAR_S = 1800, 3600                     # earlier entries of the same series closing between FAR_S and NEAR_S before this one
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_DAYS, MONTH_MIN, PLACEBO_REPS, SEED = 0.010, 2.0, 0.003, 1.0, 1000, 10, 200, 100, 71
RESULT = DATA_DIR / "losscl1_result.txt"


def classify(rows: list[dict], market_wide: bool = False) -> tuple[list[dict], list[dict]]:
    """(rl, not_rl): rl = an earlier entry (same series, or any series when market_wide) in the stretch lost; entries with no earlier entry in the stretch are dropped."""
    by = defaultdict(list)
    for r in rows:
        by[None if market_wide else r["series"]].append(r)
    rl, nrl = [], []
    for rs in by.values():
        rs.sort(key=lambda r: r["close_ts"])
        for i, r in enumerate(rs):
            prev = [x for x in rs[:i] if r["close_ts"] - FAR_S <= x["close_ts"] <= r["close_ts"] - NEAR_S]
            if not prev:
                continue
            (rl if any(x["gross"] < 0 for x in prev) else nrl).append(r)
    return rl, nrl


def judge(rl: list[dict], nrl: list[dict]) -> dict:
    n, days = len(rl), len({r["day"] for r in rl})
    m, z, _ = diff_z(nrl, rl)
    a, b = sorted(nrl, key=lambda r: r["close_ts"]), sorted(rl, key=lambda r: r["close_ts"])
    ha, hb = len(a) // 2, len(b) // 2
    h1 = st.mean(r["net"] for r in a[:ha]) - st.mean(r["net"] for r in b[:hb]) if ha and hb else 0.0
    h2 = st.mean(r["net"] for r in a[ha:]) - st.mean(r["net"] for r in b[hb:]) if ha and hb else 0.0
    ms, _, _ = diff_z(nrl, rl, "stress")
    months = defaultdict(lambda: [[], []])
    for r in nrl:
        months[r["day"][:7]][0].append(r["net"])
    for r in rl:
        months[r["day"][:7]][1].append(r["net"])
    mdiff = {k: st.mean(v[0]) - st.mean(v[1]) for k, v in months.items() if len(v[1]) >= MONTH_MIN and v[0]}
    rng = random.Random(SEED)
    pool = nrl + rl
    pz = []
    for _ in range(PLACEBO_REPS):
        rng.shuffle(pool)
        pz.append(diff_z(pool[:len(nrl)], pool[len(nrl):])[1])
    p95 = sorted(pz)[int(0.95 * len(pz)) - 1]
    ok = (n >= MIN_N and days >= MIN_DAYS and m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0
          and sum(1 for v in mdiff.values() if v > 0) >= min(2, len(mdiff)) and z > p95)
    if n < MIN_N or days < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif ok:
        verdict = "NOT_YET_FALSIFIED"
    elif m < FALSIFY_C or z < FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    loss = lambda xs: 100 * sum(1 for r in xs if r["gross"] < 0) / max(1, len(xs))
    return {"verdict": verdict, "n_rl": n, "n_not_rl": len(nrl), "days": days, "diff_c": 100 * m, "z": z, "halves_c": (100 * h1, 100 * h2), "stress_diff_c": 100 * ms,
            "months_c": {k: 100 * v for k, v in sorted(mdiff.items())}, "placebo_tail": p95, "rl_c": 100 * st.mean(r["net"] for r in rl) if rl else 0.0,
            "not_rl_c": 100 * st.mean(r["net"] for r in nrl) if nrl else 0.0, "loss_pct_rl": loss(rl), "loss_pct_not_rl": loss(nrl)}


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
    out = ["LOSSCL1 primary (same series)"] + [f"{k}: {v}" for k, v in judge(*classify(rows)).items()]
    out.append("info: market-wide")
    out += [f"{k}: {v}" for k, v in judge(*classify(rows, True)).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
