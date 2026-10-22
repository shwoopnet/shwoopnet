"""ENTRY1 (README, Pre-registration: ENTRY1): does each series' best entry minute, chosen on earlier days, beat a fixed 360 seconds on later days? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.entry1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict

from . import feat1 as F
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
LEFTS = (720, 660, 600, 540, 480, 420, 360, 300)
BASE, TRAIN_DAYS, MIN_TRAIN, MIN_CHANGED = 360, 46, 150, 5
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, PLACEBO_REPS, SEED = 0.005, 2.0, 0.002, 1.0, 100, 67
RESULT = DATA_DIR / "entry1_result.txt"


def choose(train: dict[tuple[str, int], list[float]]) -> dict[str, int]:
    """series -> entry minute (seconds left) with the highest TRAIN mean among minutes with at least MIN_TRAIN entries; BASE when none is eligible."""
    best: dict[str, tuple[float, int]] = {}
    for (s, left), nets in train.items():
        if len(nets) >= MIN_TRAIN and (s not in best or st.mean(nets) > best[s][0]):
            best[s] = (st.mean(nets), left)
    series = {s for s, _ in train}
    return {s: (best[s][1] if s in best else BASE) for s in series}


def stat(test: list[dict], pick: dict[str, int], key: str = "net"):
    """(mean diff, z, days, n_series_changed): chosen-minute entries minus BASE entries of the series that changed, per test day."""
    changed = {s for s, left in pick.items() if left != BASE}
    d = defaultdict(lambda: [[], []])
    for r in test:
        if r["series"] not in changed:
            continue
        if r["left"] == pick[r["series"]]:
            d[r["day"]][0].append(r[key])
        if r["left"] == BASE:
            d[r["day"]][1].append(r[key])
    xs = [(k, st.mean(v[0]) - st.mean(v[1])) for k, v in d.items() if v[0] and v[1]]
    if len(xs) < 2:
        return 0.0, 0.0, len(xs), len(changed)
    m, _, z = cluster_mean_z(xs)
    return m, z, len(xs), len(changed)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows = []
    for left in LEFTS:
        rs, _, _ = F.build(full, left)
        for r in rs:
            r["left"] = left
            rows.append(r)
    days = sorted({r["day"] for r in rows})
    cut = days[TRAIN_DAYS]
    train_rows, test = [r for r in rows if r["day"] < cut], [r for r in rows if r["day"] >= cut]
    train = defaultdict(list)
    for r in train_rows:
        train[(r["series"], r["left"])].append(r["net"])
    pick = choose(train)
    m, z, nd, nch = stat(test, pick)
    ms, _, _, _ = stat(test, pick, "stress")
    tdays = sorted({r["day"] for r in test})
    mid = tdays[len(tdays) // 2]
    h1 = stat([r for r in test if r["day"] < mid], pick)[0]
    h2 = stat([r for r in test if r["day"] >= mid], pick)[0]
    rng = random.Random(SEED)
    elig = defaultdict(list)
    for (s, left), nets in train.items():
        if len(nets) >= MIN_TRAIN:
            elig[s].append(left)
    pz = []
    for _ in range(PLACEBO_REPS):
        pl = {s: rng.choice(v) for s, v in elig.items()}
        pl.update({s: BASE for s in pick if s not in pl})
        pz.append(stat(test, pl)[1])
    p95 = sorted(pz)[int(0.95 * len(pz)) - 1]
    ok = m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0 and nch >= MIN_CHANGED and z > p95
    verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    out = [f"ENTRY1: verdict {verdict}", f"diff_c: {100 * m:+.2f}, z: {z:+.2f}, test days: {nd}, series changed: {nch}", f"halves_c: {100 * h1:+.2f} / {100 * h2:+.2f}, stress_c: {100 * ms:+.2f}, placebo_tail_z: {p95:+.2f}",
           "info: chosen minute by series (seconds left): " + ", ".join(f"{s[2:-3]}={v}" for s, v in sorted(pick.items())), "info: TRAIN and TEST mean net (c) by series and minute"]
    test_by = defaultdict(list)
    for r in test:
        test_by[(r["series"], r["left"])].append(r["net"])
    for s in sorted({s for s, _ in train}):
        cells = []
        for left in LEFTS:
            tr, te = train.get((s, left), []), test_by.get((s, left), [])
            cells.append(f"{left}:" + (f"{100 * st.mean(tr):+.1f}" if tr else "--") + "/" + (f"{100 * st.mean(te):+.1f}" if te else "--"))
        out.append(f"{s[2:-3]:9s} " + " ".join(cells))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
