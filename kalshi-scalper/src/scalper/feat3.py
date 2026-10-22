"""FEAT3 (README, Pre-registration: FEAT3): a calibration-correction model (logistic with an offset of logit(price)) over every side and price from 0.50 to 0.97 at 360 and 600 seconds,
walk-forward, top 3% by predicted expected net, one entry per market. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.feat3 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
LEFTS, PRICE_LO, PRICE_HI, BURN_DAYS, REFIT_DAYS, KEEP_Q, LAM, NEWTON = (360, 600), 0.50, 0.97, 14, 7, 0.97, 1.0, 30
Z_BAR, MIN_N, MIN_DAYS, MONTH_MIN, PLACEBO_REPS, SEED, STRESS = 3.0, 1500, 10, 300, 50, 37, 1.2
NUM = ["price", "price2", "spread", "rise3", "d1", "tib", "stab", "dip", "rng5", "is600"]
RESULT = DATA_DIR / "feat3_result.txt"


def fee(p):
    return 0.07 * p * (1 - p)


def build(markets: list[tuple]):
    series = sorted({m[1] for m in markets})
    rows = []
    for tk, s, cs, close, res in markets:
        if res not in ("yes", "no"):
            continue
        byt = {c[0]: c for c in cs}
        day = datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d")
        for left in LEFTS:
            t = close - left
            now, m1, m3 = byt.get(t), byt.get(t - 60), byt.get(t - 180)
            if now is None or m1 is None or m3 is None or not valid_quote(now[1], now[2]):
                continue
            earlier = [c for c in cs if c[0] < t]
            for side in ("yes", "no"):
                ask = lambda x: x[2] if side == "yes" else 1 - x[1]
                mid = lambda x: (x[1] + x[2]) / 2 if side == "yes" else 1 - (x[1] + x[2]) / 2
                price = ask(now)
                if not (PRICE_LO <= price <= PRICE_HI) or not earlier:
                    continue
                tib = stab = 0
                k = t - 60
                while k in byt and ask(byt[k]) >= 0.88 and tib < 8:
                    tib += 1
                    k -= 60
                k = t - 60
                while k in byt and abs(ask(byt[k]) - price) <= 0.03 and stab < 8:
                    stab += 1
                    k -= 60
                win = [mid(byt[j]) for j in range(t - 300, t + 1, 60) if j in byt]
                x = [price, price * price, now[2] - now[1], mid(now) - mid(m3), mid(now) - mid(m1), float(tib), float(stab), min(mid(c) for c in earlier), max(win) - min(win),
                     1.0 if left == 600 else 0.0] + [1.0 if s == t_ else 0.0 for t_ in series]
                rows.append({"ticker": tk, "series": s, "day": day, "close_ts": close, "left": left, "side": side, "price": price, "won": 1.0 if res == side else 0.0, "x": x})
    return rows, series


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_offset_logit(X: np.ndarray, y: np.ndarray, offset: np.ndarray, lam: float = LAM, iters: int = NEWTON):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = np.hstack([np.ones((len(X), 1)), (X - mu) / sd])
    w = np.zeros(Z.shape[1])
    pen = np.full(Z.shape[1], lam)
    pen[0] = 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(offset + Z @ w, -30, 30)))
        g = Z.T @ (p - y) + pen * w
        H = (Z * (p * (1 - p))[:, None]).T @ Z + np.diag(pen) + 1e-9 * np.eye(Z.shape[1])
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return mu, sd, w


def predict_p(model, X: np.ndarray, offset: np.ndarray) -> np.ndarray:
    mu, sd, w = model
    Z = np.hstack([np.ones((len(X), 1)), (X - mu) / sd])
    return 1 / (1 + np.exp(-np.clip(offset + Z @ w, -30, 30)))


def expected_net(p: np.ndarray, price: np.ndarray) -> np.ndarray:
    return p - price - fee(price)


def walk(rows: list[dict], won: np.ndarray, X: np.ndarray, price: np.ndarray, off: np.ndarray) -> list[int]:
    """Indices of the entries taken: for each block of days a model fitted on strictly earlier days, the keep threshold the KEEP_Q quantile of its predicted EV on those
    training rows, one entry per market (the highest predicted EV)."""
    days = sorted({r["day"] for r in rows})
    day_arr = np.array([r["day"] for r in rows])
    taken = []
    for b in range(BURN_DAYS, len(days), REFIT_DAYS):
        start = days[b]
        block = days[b:b + REFIT_DAYS]
        tr = day_arr < start
        te = np.where(np.isin(day_arr, block))[0]
        if tr.sum() < 2000 or len(te) == 0:
            continue
        model = fit_offset_logit(X[tr], won[tr], off[tr])
        thr = np.quantile(expected_net(predict_p(model, X[tr], off[tr]), price[tr]), KEEP_Q)
        ev = expected_net(predict_p(model, X[te], off[te]), price[te])
        best = {}
        for i, e in zip(te, ev):
            if e >= thr and (rows[i]["ticker"] not in best or e > best[rows[i]["ticker"]][0]):
                best[rows[i]["ticker"]] = (e, i)
        taken += [i for _, i in best.values()]
    return taken


def nets(rows, idx, won, mult=1.0):
    return [(rows[i]["day"], rows[i]["close_ts"], won[i] - rows[i]["price"] - fee(rows[i]["price"]) * mult) for i in idx]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, series = build(full)
    rows.sort(key=lambda r: r["close_ts"])
    X = np.array([r["x"] for r in rows])
    won = np.array([r["won"] for r in rows])
    price = X[:, 0]
    off = logit(price)
    taken = walk(rows, won, X, price, off)
    n_ = nets(rows, taken, won)
    n = len(n_)
    days = len({d for d, _, _ in n_})
    m, _, z = cluster_mean_z([(d, v) for d, _, v in n_]) if n > 1 else (0.0, 0.0, 0.0)
    ordered = sorted(n_, key=lambda x: x[1])
    h = n // 2
    h1, h2 = st.mean(v for _, _, v in ordered[:h]), st.mean(v for _, _, v in ordered[h:])
    stress = st.mean(v for _, _, v in nets(rows, taken, won, STRESS))
    months = defaultdict(list)
    for d, _, v in n_:
        months[d[:7]].append(v)
    month_ok, month_lines = True, []
    for mo in sorted(months):
        vals = months[mo]
        if len(vals) < MONTH_MIN:
            month_lines.append(f"   {mo}: {len(vals)} entries (under {MONTH_MIN}, not judged)")
            continue
        mm = st.mean(vals)
        month_lines.append(f"   {mo}: {len(vals)} entries at {mm * 100:+.2f}c")
        month_ok = month_ok and mm > 0
    # placebo: shuffle win labels among candidates of the same day and time, rerun the whole walk-forward
    rng = random.Random(SEED)
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[(r["day"], r["left"])].append(i)
    placebo = []
    for _ in range(PLACEBO_REPS):
        w2 = won.copy()
        for ix in groups.values():
            v = won[ix].copy()
            rng_np = np.random.default_rng(rng.randrange(1 << 30))
            rng_np.shuffle(v)
            w2[ix] = v
        t2 = walk(rows, w2, X, price, off)
        v2 = [x for _, _, x in nets(rows, t2, w2)]
        placebo.append(sum(v2) / len(v2) if v2 else 0.0)
    placebo.sort()
    p95 = placebo[int(0.95 * (len(placebo) - 1))]
    ok = n >= MIN_N and days >= MIN_DAYS and m > 0 and z >= Z_BAR and h1 > 0 and h2 > 0 and stress > 0 and m > p95 and month_ok
    verdict = "NOT_ENOUGH_DATA" if (n < MIN_N or days < MIN_DAYS) else ("NOT_YET_FALSIFIED" if ok else "FALSIFIED")
    c = lambda x: f"{x * 100:+.2f}c"
    lines = [f"FEAT3: {len(rows)} candidate rows over {len({r['day'] for r in rows})} days; entries taken {n} on {days} days ({n / max(1, days):.0f} a day); net {c(m)} (z {z:+.2f}); halves {c(h1)} / {c(h2)}; fees x{STRESS} {c(stress)}; placebo 95th percentile {c(p95)}",
             "   by month:"] + month_lines + [f"   VERDICT: {verdict}"]
    def band(lo, hi):
        g = [i for i in taken if lo <= rows[i]["price"] < hi]
        return f"price {lo:.2f}-{hi:.2f}: {len(g)} entries at {c(st.mean(won[i] - rows[i]['price'] - fee(rows[i]['price']) for i in g)) if g else 'n/a'}"
    lines.append("   kept by price band (information): " + "; ".join(band(lo, hi) for lo, hi in ((0.5, 0.8), (0.8, 0.88), (0.88, 0.94), (0.94, 0.98))))
    for name, sel in (("YES", lambda r: r["side"] == "yes"), ("NO", lambda r: r["side"] == "no"), ("360 s", lambda r: r["left"] == 360), ("600 s", lambda r: r["left"] == 600)):
        g = [i for i in taken if sel(rows[i])]
        lines.append(f"   kept {name}: {len(g)} entries at {c(st.mean(won[i] - rows[i]['price'] - fee(rows[i]['price']) for i in g)) if g else 'n/a'}")
    per = defaultdict(list)
    for i in taken:
        per[rows[i]["series"]].append(won[i] - rows[i]["price"] - fee(rows[i]["price"]))
    lines.append("   kept by series: " + ", ".join(f"{k[2:-3]} {len(v)} at {st.mean(v) * 100:+.2f}c" for k, v in sorted(per.items())))
    model = fit_offset_logit(X, won, off)
    wts = sorted(zip(NUM + series, model[2][1:]), key=lambda kv: -abs(kv[1]))[:10]
    lines.append("   weights on all days (information; positive raises the chance of a WIN above the price): " + ", ".join(f"{k} {w:+.2f}" for k, w in wts))
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
