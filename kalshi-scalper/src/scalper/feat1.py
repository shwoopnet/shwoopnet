"""FEAT1 (README, Pre-registration: FEAT1): a walk-forward L2 logistic model of "this L1 entry lost", keeping the safest 40% by training-set threshold. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.feat1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import sys
from collections import defaultdict

import numpy as np

from . import lstrats as L
from . import tree1 as T
from . import tree2 as T2
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
LEFT_S, BURN_DAYS, REFIT_DAYS, KEEP_Q, LAM, NEWTON = 360, 14, 7, 0.40, 1.0, 25
Z_BAR, DIFF_Z_BAR, PLACEBO_REPS, SEED = 3.0, 2.0, 100, 31
NUM = ["price", "spread", "rise3", "d1", "tib", "dip", "rng5"]
RESULT = DATA_DIR / "feat1_result.txt"


def build(markets: list[tuple], left_s: int, series=None):
    """Entries with the numeric features and the series; entries lacking the needed candles are dropped and counted."""
    idx = {m[0]: m[2] for m in markets}
    ents = L.hold_rule(markets, left_s, L.L1["band"])
    series = series if series is not None else sorted({e["series"] for e in ents})
    rows, dropped = [], 0
    for e in ents:
        c = idx[e["ticker"]]
        byt = {x[0]: x for x in c}
        t, side = e["close_ts"] - left_s, e["side"]
        now, m1, m3 = byt.get(t), byt.get(t - 60), byt.get(t - 180)
        if now is None or m1 is None or m3 is None:
            dropped += 1
            continue
        mid = lambda x: (x[1] + x[2]) / 2 if side == "yes" else 1 - (x[1] + x[2]) / 2
        ask = lambda x: x[2] if side == "yes" else 1 - x[1]
        tib, k = 0, t - 60
        while k in byt and ask(byt[k]) >= 0.88 and tib < 8:
            tib += 1
            k -= 60
        earlier = [mid(x) for x in c if x[0] < t]
        win = [mid(byt[j]) for j in range(t - 300, t + 1, 60) if j in byt]
        if not earlier or len(win) < 2:
            dropped += 1
            continue
        f = [e["price"], now[2] - now[1], mid(now) - mid(m3), mid(now) - mid(m1), float(tib), min(earlier), max(win) - min(win)] + [1.0 if e["series"] == s else 0.0 for s in series]
        rows.append({**e, "x": f, "lost": 1.0 if e["gross"] < 0 else 0.0})
    return rows, series, dropped


def fit_logit(X: np.ndarray, y: np.ndarray, lam: float = LAM, iters: int = NEWTON):
    """L2 logistic regression by Newton steps on standardised features; intercept unpenalised. Returns (mean, std, weights)."""
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = np.hstack([np.ones((len(X), 1)), (X - mu) / sd])
    w = np.zeros(Z.shape[1])
    pen = np.full(Z.shape[1], lam)
    pen[0] = 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ (p - y) + pen * w
        H = (Z * (p * (1 - p))[:, None]).T @ Z + np.diag(pen) + 1e-9 * np.eye(Z.shape[1])
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return mu, sd, w


def predict(model, X: np.ndarray) -> np.ndarray:
    mu, sd, w = model
    Z = np.hstack([np.ones((len(X), 1)), (X - mu) / sd])
    return 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))


def walk(rows: list[dict], lost: list[float]) -> dict[int, bool]:
    """{row index: skipped?} for rows after the burn-in. A block's decisions use a model fitted on rows of strictly earlier days only; the keep threshold is the
    KEEP_Q quantile of the model's own predictions on those training rows."""
    days = T.day_order(rows)
    X = np.array([r["x"] for r in rows])
    y = np.array(lost)
    dec = {}
    for b in range(BURN_DAYS, len(days), REFIT_DAYS):
        start = days[b]
        block = set(days[b:b + REFIT_DAYS])
        tr = np.array([r["day"] < start for r in rows])
        te = [i for i, r in enumerate(rows) if r["day"] in block]
        if tr.sum() < 500 or not te:
            continue
        model = fit_logit(X[tr], y[tr])
        thr = np.quantile(predict(model, X[tr]), KEEP_Q)
        p = predict(model, X[te])
        for i, pi in zip(te, p):
            dec[i] = bool(pi > thr)
    return dec


def shuffled_labels(rows: list[dict], lost: list[float], rng: random.Random) -> list[float]:
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["day"]].append(i)
    z = list(lost)
    for ix in by.values():
        v = [lost[i] for i in ix]
        rng.shuffle(v)
        for i, x in zip(ix, v):
            z[i] = x
    return z


def judge_run(rows: list[dict], p95_gain):
    dec = walk(rows, [r["lost"] for r in rows])
    v, s = T2.judge(rows, dec, p95_gain)
    if v != "NOT_ENOUGH_DATA":
        ok = (s["mean"] > 0 and s["z"] >= Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0 and s["diff"] > 0 and s["diff_z"] >= DIFF_Z_BAR
              and p95_gain is not None and s["gain"] > p95_gain and s["month_ok"])
        v = "NOT_YET_FALSIFIED" if ok else "FALSIFIED"
    return v, s, dec


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    c = lambda x: f"{x * 100:+.2f}c"
    lines = []
    for left in (LEFT_S, 600):
        rows, series, dropped = build(full, left)
        rows.sort(key=lambda r: r["close_ts"])
        if left == LEFT_S:
            rng = random.Random(SEED)
            gains = []
            for _ in range(PLACEBO_REPS):
                z = shuffled_labels(rows, [r["lost"] for r in rows], rng)
                d = walk(rows, z)
                kept = [rows[i]["net"] for i, sk in d.items() if not sk]
                allv = [rows[i]["net"] for i in d]
                gains.append(sum(kept) / len(kept) - sum(allv) / len(allv) if kept else 0.0)
            gains.sort()
            p95 = gains[int(0.95 * (len(gains) - 1))]
        else:
            p95 = None
        v, s, dec = judge_run(rows, p95)
        tag = "FEAT1 (registered, 360 s)" if left == LEFT_S else "information, 600 s (no placebo)"
        lines += [f"{tag}: {len(rows)} entries ({dropped} dropped for missing candles); decided {s.get('decided')}, skipped {s.get('skipped')} ({100 * s.get('skipped', 0) / max(1, s.get('decided', 1)):.1f}%), kept n={s.get('n')} on {s.get('days')} days; all decided {c(s.get('base', 0))}",
                  f"   kept net {c(s.get('mean', 0))} z {s.get('z', 0):+.2f} halves {c(s.get('h1', 0))} / {c(s.get('h2', 0))} fees x1.2 {c(s.get('stress', 0))}",
                  f"   kept minus skipped {c(s.get('diff', 0))} (day clustered z {s.get('diff_z', 0):+.2f}); gain {c(s.get('gain', 0))}; placebo 95th percentile {c(p95) if p95 is not None else 'n/a'}",
                  "   by month:"] + s.get("months", []) + [f"   VERDICT: {v if left == LEFT_S else '(information only) ' + v}"]
        kept = [rows[i] for i, sk in dec.items() if not sk]
        if kept:
            lines.append(f"   kept loss rate {100 * sum(r['lost'] for r in kept) / len(kept):.1f}%; skipped loss rate {100 * sum(rows[i]['lost'] for i, sk in dec.items() if sk) / max(1, sum(1 for sk in dec.values() if sk)):.1f}%; kept entries a day {len(kept) / max(1, s.get('days', 1)):.0f}")
        if left == LEFT_S:
            X = np.array([r["x"] for r in rows])
            model = fit_logit(X, np.array([r["lost"] for r in rows]))
            names = NUM + series
            wts = sorted(zip(names, model[2][1:]), key=lambda kv: -abs(kv[1]))[:10]
            lines.append("   weights on the standardised features, all days (information; positive raises the chance of a loss): " + ", ".join(f"{n} {w:+.2f}" for n, w in wts))
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
