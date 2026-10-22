"""FEAT2 (README, Pre-registration: FEAT2): FEAT1's walk-forward logistic model, ranked by predicted expected net per contract instead of by loss probability.
Everything else is FEAT1's. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.feat2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import sys

import numpy as np

from . import feat1 as F
from . import tree1 as T
from .hs1 import load
from .paths import DATA_DIR
from .scalps import fee

RESULT = DATA_DIR / "feat2_result.txt"
KEEP_Q = 0.40


def expected_net(p_hat: np.ndarray, price: np.ndarray) -> np.ndarray:
    f = 0.07 * price * (1 - price)
    return (1 - p_hat) * (1 - price - f) - p_hat * (price + f)


def walk(rows: list[dict], lost: list[float]) -> dict[int, bool]:
    days = T.day_order(rows)
    X = np.array([r["x"] for r in rows])
    y = np.array(lost)
    price = X[:, 0]
    dec = {}
    for b in range(F.BURN_DAYS, len(days), F.REFIT_DAYS):
        start = days[b]
        block = set(days[b:b + F.REFIT_DAYS])
        tr = np.array([r["day"] < start for r in rows])
        te = [i for i, r in enumerate(rows) if r["day"] in block]
        if tr.sum() < 500 or not te:
            continue
        model = F.fit_logit(X[tr], y[tr])
        ev_tr = expected_net(F.predict(model, X[tr]), price[tr])
        thr = np.quantile(ev_tr, 1 - KEEP_Q)                       # keep the best 40% by predicted expected net
        ev = expected_net(F.predict(model, X[te]), price[te])
        for i, e in zip(te, ev):
            dec[i] = bool(e < thr)
    return dec


MODEL_FILE = DATA_DIR.parent / "studies" / "feat2_model_2026-10-22.json"


def freeze() -> None:
    """Fit FEAT2's model once on all history and write it (weights, standardisation, series list, keep threshold) so it can be read on fresh days without refitting."""
    import json
    if MODEL_FILE.exists():
        print(f"Refusing: {MODEL_FILE} exists (the model is frozen; delete only on purpose and log it in the README).")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, series, _ = F.build(full, F.LEFT_S)
    X = np.array([r["x"] for r in rows])
    y = np.array([r["lost"] for r in rows])
    model = F.fit_logit(X, y)
    ev = expected_net(F.predict(model, X), X[:, 0])
    thr = float(np.quantile(ev, 1 - KEEP_Q))
    MODEL_FILE.write_text(json.dumps({"numeric": F.NUM, "series": series, "mu": model[0].tolist(), "sd": model[1].tolist(), "w": model[2].tolist(), "keep_threshold_expected_net": thr,
                                      "trained_entries": len(rows), "kept_share_in_training": float((ev >= thr).mean())}, indent=1))
    print(f"frozen on {len(rows)} entries; threshold {thr:.5f}; wrote {MODEL_FILE}")


def apply_frozen(markets: list[tuple]):
    """(kept, skipped) entry lists on `markets` using the frozen model; entries of a series the model has not seen are dropped and counted."""
    import json
    m = json.loads(MODEL_FILE.read_text())
    rows, _, dropped = F.build(markets, F.LEFT_S, m["series"])
    rows = [r for r in rows if r["series"] in m["series"]]
    X = np.array([r["x"] for r in rows])
    model = (np.array(m["mu"]), np.array(m["sd"]), np.array(m["w"]))
    ev = expected_net(F.predict(model, X), X[:, 0])
    thr = m["keep_threshold_expected_net"]
    return [r for r, e in zip(rows, ev) if e >= thr], [r for r, e in zip(rows, ev) if e < thr], dropped


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "freeze":
        return freeze()
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    F.walk = walk                                                    # FEAT1's runner, FEAT2's ranking
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, series, dropped = F.build(full, F.LEFT_S)
    rows.sort(key=lambda r: r["close_ts"])
    rng = random.Random(F.SEED)
    gains = []
    for _ in range(F.PLACEBO_REPS):
        z = F.shuffled_labels(rows, [r["lost"] for r in rows], rng)
        d = walk(rows, z)
        kept = [rows[i]["net"] for i, sk in d.items() if not sk]
        allv = [rows[i]["net"] for i in d]
        gains.append(sum(kept) / len(kept) - sum(allv) / len(allv) if kept else 0.0)
    gains.sort()
    p95 = gains[int(0.95 * (len(gains) - 1))]
    v, s, dec = F.judge_run(rows, p95)
    c = lambda x: f"{x * 100:+.2f}c"
    kept = [rows[i] for i, sk in dec.items() if not sk]
    skipped = [rows[i] for i, sk in dec.items() if sk]
    lines = [f"FEAT2 (360 s): {len(rows)} entries ({dropped} dropped); decided {s.get('decided')}, skipped {s.get('skipped')} ({100 * s.get('skipped', 0) / max(1, s.get('decided', 1)):.1f}%), kept n={s.get('n')} on {s.get('days')} days; all decided {c(s.get('base', 0))}",
             f"   kept net {c(s.get('mean', 0))} z {s.get('z', 0):+.2f} halves {c(s.get('h1', 0))} / {c(s.get('h2', 0))} fees x1.2 {c(s.get('stress', 0))}",
             f"   kept minus skipped {c(s.get('diff', 0))} (day clustered z {s.get('diff_z', 0):+.2f}); gain {c(s.get('gain', 0))}; placebo 95th percentile {c(p95)}",
             "   by month:"] + s.get("months", []) + [f"   VERDICT: {v}",
             f"   kept loss rate {100 * sum(r['lost'] for r in kept) / len(kept):.1f}%, skipped {100 * sum(r['lost'] for r in skipped) / len(skipped):.1f}%; kept mean price {100 * np.mean([r['price'] for r in kept]):.1f}c, skipped {100 * np.mean([r['price'] for r in skipped]):.1f}c; kept entries a day {len(kept) / max(1, s.get('days', 1)):.0f}"]
    per = {}
    for r in kept:
        per.setdefault(r["series"], []).append(r["net"])
    lines.append("   kept by series (information): " + ", ".join(f"{k[2:-3]} {len(v)} at {100 * np.mean(v):+.2f}c" for k, v in sorted(per.items())))
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
