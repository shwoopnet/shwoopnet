"""CROWD1 (README, Pre-registration: CROWD1): is the first entry of a window where 2+ live series qualify worse than a solo entry? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.crowd1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict

from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
ORDER = ["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M"]
CRYPTO = ORDER[:4]
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_DAYS, MONTH_MIN, PLACEBO_REPS, SEED = -0.015, -2.0, -0.005, -1.0, 300, 10, 3, 100, 53
RESULT = DATA_DIR / "crowd1_result.txt"


def groups(ents: list[dict], order: list[str]):
    """(solo, crowd_first, crowd_extra) entry lists; k is the count of qualifying series in the window at the same minute."""
    by = defaultdict(list)
    for e in ents:
        if e["series"] in order:
            by[e["close_ts"]].append(e)
    solo, first, extra = [], [], []
    for es in by.values():
        es.sort(key=lambda e: order.index(e["series"]))
        if len(es) == 1:
            solo.append(es[0])
        else:
            first.append(es[0])
            extra.extend(es[1:])
    return solo, first, extra


def diff_z(a: list[dict], b: list[dict], key: str = "net"):
    """Per-day mean(a) - mean(b) over days with both, day-clustered: (mean diff, z, days)."""
    d = defaultdict(lambda: [[], []])
    for r in a:
        d[r["day"]][0].append(r[key])
    for r in b:
        d[r["day"]][1].append(r[key])
    xs = [(k, st.mean(v[0]) - st.mean(v[1])) for k, v in d.items() if v[0] and v[1]]
    if len(xs) < 2:
        return 0.0, 0.0, len(xs)
    m, _, z = cluster_mean_z(xs)
    return m, z, len(xs)


def judge(solo, first, extra) -> dict:
    n, days = len(first), len({r["day"] for r in first})
    m, z, nd = diff_z(first, solo)
    ordered = sorted(first, key=lambda r: r["close_ts"])
    h = len(ordered) // 2
    sol = sorted(solo, key=lambda r: r["close_ts"])
    hs = len(sol) // 2
    d1 = st.mean(r["net"] for r in ordered[:h]) - st.mean(r["net"] for r in sol[:hs]) if h and hs else 0.0
    d2 = st.mean(r["net"] for r in ordered[h:]) - st.mean(r["net"] for r in sol[hs:]) if h and hs else 0.0
    ms, _, _ = diff_z(first, solo, "stress")
    months = defaultdict(lambda: [[], []])
    for r in first:
        months[r["day"][:7]][0].append(r["net"])
    for r in solo:
        months[r["day"][:7]][1].append(r["net"])
    mdiff = {k: st.mean(v[0]) - st.mean(v[1]) for k, v in months.items() if len(v[0]) >= 30 and v[1]}
    rng = random.Random(SEED)
    pool = first + solo
    pz = []
    for _ in range(PLACEBO_REPS):
        rng.shuffle(pool)
        pz.append(diff_z(pool[:n], pool[n:])[1])
    p95 = sorted(pz)[int(0.05 * len(pz))]          # the most negative 5% tail
    ok = (n >= MIN_N and days >= MIN_DAYS and m <= DIFF_C and z <= DIFF_Z_BAR and d1 < 0 and d2 < 0 and ms < 0
          and sum(1 for v in mdiff.values() if v < 0) >= min(MONTH_MIN, len(mdiff)) and z < p95)
    if n < MIN_N or days < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif ok:
        verdict = "NOT_YET_FALSIFIED"
    elif m > FALSIFY_C or z > FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    return {"verdict": verdict, "n_first": n, "n_solo": len(solo), "n_extra": len(extra), "days": days, "diff_c": 100 * m, "z": z,
            "halves_c": (100 * d1, 100 * d2), "stress_diff_c": 100 * ms, "months_c": {k: 100 * v for k, v in sorted(mdiff.items())},
            "placebo_tail": p95, "solo_c": 100 * st.mean(r["net"] for r in solo) if solo else 0.0,
            "first_c": 100 * st.mean(r["net"] for r in first) if first else 0.0,
            "extra_c": 100 * st.mean(r["net"] for r in extra) if extra else 0.0}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    ents = L.hold_rule(mk, L.L1["left_s"], L.L1["band"])
    out = ["CROWD1 primary (five live series)"]
    r = judge(*groups(ents, ORDER))
    out += [f"{k}: {v}" for k, v in r.items()]
    out.append("info: crypto only")
    r2 = judge(*groups(ents, CRYPTO))
    out += [f"{k}: {v}" for k, v in r2.items()]
    by = defaultdict(list)
    for e in ents:
        if e["series"] in ORDER:
            by[e["close_ts"]].append(e)
    lossrate = sum(1 for e in ents if e["series"] in ORDER and e["gross"] < 0) / max(1, sum(1 for e in ents if e["series"] in ORDER))
    two = [es for es in by.values() if len(es) == 2]
    both = sum(1 for es in two if all(e["gross"] < 0 for e in es)) / max(1, len(two))
    out.append(f"info: two-entry windows {len(two)}; both lose {100*both:.2f}% against {100*lossrate**2:.2f}% if independent")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
