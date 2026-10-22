"""FEAT4 (README, Pre-registration: FEAT4): enter at the first minute (12 to 5 minutes before the close) at which a walk-forward logistic model's predicted expected net clears the
60th percentile of its training rows; one entry per market. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.feat4 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict

import numpy as np

from . import feat1 as F
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
LEFTS = (720, 660, 600, 540, 480, 420, 360, 300)
KEEP_Q, BURN_DAYS, REFIT_DAYS = 0.40, 14, 7
Z_BAR, DIFF_Z_BAR, MIN_N, MIN_DAYS, MONTH_MIN, PLACEBO_REPS, SEED = 3.0, 2.0, 1500, 10, 300, 30, 41
RESULT = DATA_DIR / "feat4_result.txt"


def expected_net(p: np.ndarray, price: np.ndarray) -> np.ndarray:
    f = 0.07 * price * (1 - price)
    return (1 - p) * (1 - price - f) - p * (price + f)


def build_all(full: list[tuple]):
    base_rows, series, _ = F.build(full, 360)
    rows = []
    for left in LEFTS:
        rs, _, _ = F.build(full, left, series)
        for r in rs:
            r["left"] = left
            r["x"] = r["x"] + [float(left)]
            rows.append(r)
    return rows, series


def first_yes(cands: list[tuple]) -> int:
    """Among (left, is_yes, index) of one market's candidates, the index of the earliest time that is a yes, or -1."""
    best = None
    for left, yes, i in cands:
        if yes and (best is None or left > best[0]):
            best = (left, i)
    return -1 if best is None else best[1]


def walk(rows: list[dict], lost: np.ndarray, X: np.ndarray, price: np.ndarray) -> list[int]:
    days = sorted({r["day"] for r in rows})
    day_arr = np.array([r["day"] for r in rows])
    taken = []
    for b in range(BURN_DAYS, len(days), REFIT_DAYS):
        start = days[b]
        tr = day_arr < start
        te = np.where(np.isin(day_arr, days[b:b + REFIT_DAYS]))[0]
        if tr.sum() < 2000 or len(te) == 0:
            continue
        model = F.fit_logit(X[tr], lost[tr])
        thr = np.quantile(expected_net(F.predict(model, X[tr]), price[tr]), 1 - KEEP_Q)
        ev = expected_net(F.predict(model, X[te]), price[te])
        by = defaultdict(list)
        for i, e in zip(te, ev):
            by[rows[i]["ticker"]].append((rows[i]["left"], e >= thr, i))
        for cands in by.values():
            j = first_yes(cands)
            if j >= 0:
                taken.append(j)
    return taken


MODEL_FILE = DATA_DIR.parent / "studies" / "feat4_model_2026-10-22.json"


def freeze() -> None:
    """Fit FEAT4's model once on all rows and write it (standardisation, weights, series list, keep threshold) for the fresh-day read."""
    import json
    if MODEL_FILE.exists():
        print(f"Refusing: {MODEL_FILE} exists (the model is frozen; delete only on purpose and log it in the README).")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, series = build_all(full)
    X = np.array([r["x"] for r in rows])
    model = F.fit_logit(X, np.array([r["lost"] for r in rows]))
    thr = float(np.quantile(expected_net(F.predict(model, X), X[:, 0]), 1 - KEEP_Q))
    MODEL_FILE.write_text(json.dumps({"series": series, "mu": model[0].tolist(), "sd": model[1].tolist(), "w": model[2].tolist(), "keep_threshold_expected_net": thr, "trained_rows": len(rows)}, indent=1))
    print(f"frozen on {len(rows)} rows; threshold {thr:.5f}")


def apply_frozen(markets: list[tuple]):
    """(entries, plain_360) on `markets` with the frozen model: the earliest yes per market, and every 360 second L1 entry for comparison."""
    import json
    m = json.loads(MODEL_FILE.read_text())
    rows = []
    for left in LEFTS:
        rs, _, _ = F.build(markets, left, m["series"])
        for r in rs:
            r["left"] = left
            r["x"] = r["x"] + [float(left)]
            rows.append(r)
    if not rows:
        return [], []
    X = np.array([r["x"] for r in rows])
    ev = expected_net(F.predict((np.array(m["mu"]), np.array(m["sd"]), np.array(m["w"])), X), X[:, 0])
    by = defaultdict(list)
    for i, (r, e) in enumerate(zip(rows, ev)):
        by[r["ticker"]].append((r["left"], bool(e >= m["keep_threshold_expected_net"]), i))
    taken = [rows[j] for j in (first_yes(c) for c in by.values()) if j >= 0]
    return taken, [r for r in rows if r["left"] == 360]


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "freeze":
        return freeze()
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, series = build_all(full)
    rows.sort(key=lambda r: r["close_ts"])
    X = np.array([r["x"] for r in rows])
    lost = np.array([r["lost"] for r in rows])
    price = X[:, 0]
    taken = walk(rows, lost, X, price)
    kept = [rows[i] for i in taken]
    n, days = len(kept), len({r["day"] for r in kept})
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in kept]) if n > 1 else (0.0, 0.0, 0.0)
    ordered = sorted(kept, key=lambda r: r["close_ts"])
    h = n // 2
    h1, h2 = st.mean(r["net"] for r in ordered[:h]), st.mean(r["net"] for r in ordered[h:])
    stress = st.mean(r["stress"] for r in kept)
    burn_end = sorted({r["day"] for r in rows})[BURN_DAYS]
    plain = [r for r in rows if r["left"] == 360 and r["day"] >= burn_end]
    d = defaultdict(lambda: [[], []])
    for r in kept:
        d[r["day"]][0].append(r["net"])
    for r in plain:
        d[r["day"]][1].append(r["net"])
    dm, _, dz = cluster_mean_z([(k, st.mean(v[0]) - st.mean(v[1])) for k, v in d.items() if v[0] and v[1]])
    months = defaultdict(list)
    for r in kept:
        months[r["day"][:7]].append(r["net"])
    month_ok, month_lines = True, []
    for mo in sorted(months):
        if len(months[mo]) < MONTH_MIN:
            month_lines.append(f"   {mo}: {len(months[mo])} entries (under {MONTH_MIN}, not judged)")
            continue
        mm = st.mean(months[mo])
        month_lines.append(f"   {mo}: {len(months[mo])} entries at {mm * 100:+.2f}c")
        month_ok = month_ok and mm > 0
    rng = random.Random(SEED)
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[(r["day"], r["left"])].append(i)
    placebo = []
    for _ in range(PLACEBO_REPS):
        l2 = lost.copy()
        nprng = np.random.default_rng(rng.randrange(1 << 30))
        for ix in groups.values():
            v = lost[ix].copy()
            nprng.shuffle(v)
            l2[ix] = v
        t2 = walk(rows, l2, X, price)
        nets = [(1.0 - l2[i]) - rows[i]["price"] - 0.07 * rows[i]["price"] * (1 - rows[i]["price"]) for i in t2]
        placebo.append(sum(nets) / len(nets) if nets else 0.0)
    placebo.sort()
    p95 = placebo[int(0.95 * (len(placebo) - 1))]
    ok = n >= MIN_N and days >= MIN_DAYS and m > 0 and z >= Z_BAR and h1 > 0 and h2 > 0 and stress > 0 and dm > 0 and dz >= DIFF_Z_BAR and m > p95 and month_ok
    verdict = "NOT_ENOUGH_DATA" if (n < MIN_N or days < MIN_DAYS) else ("NOT_YET_FALSIFIED" if ok else "FALSIFIED")
    c = lambda x: f"{x * 100:+.2f}c"
    lines = [f"FEAT4: {len(rows)} candidate rows; entries {n} on {days} days ({n / max(1, days):.0f} a day); net {c(m)} (z {z:+.2f}); halves {c(h1)} / {c(h2)}; fees x1.2 {c(stress)}; "
             f"plain L1 at 360 s on the same days n={len(plain)} at {c(st.mean(r['net'] for r in plain))}; entry arm minus plain per day {c(dm)} (day clustered z {dz:+.2f}); placebo 95th percentile {c(p95)}",
             "   by month:"] + month_lines + [f"   VERDICT: {verdict}", f"   kept loss rate {100 * sum(r['lost'] for r in kept) / n:.1f}%; mean entry price {100 * st.mean(r['price'] for r in kept):.1f}c; mean seconds left {st.mean(r['left'] for r in kept):.0f}"]
    for left in LEFTS:
        g = [r for r in kept if r["left"] == left]
        if g:
            lines.append(f"   entered at {left // 60}:{left % 60:02d} left: {len(g)} entries ({100 * len(g) / n:.0f}%) at {c(st.mean(r['net'] for r in g))}")
    per = defaultdict(list)
    for r in kept:
        per[r["series"]].append(r["net"])
    lines.append("   by series: " + ", ".join(f"{k[2:-3]} {len(v)} at {st.mean(v) * 100:+.2f}c" for k, v in sorted(per.items())))
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
