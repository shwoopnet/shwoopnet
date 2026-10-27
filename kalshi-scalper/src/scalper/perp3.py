"""PERP3 (README, Pre-registration: PERP3): fast Bitcoin and Ethereum perpetual strategies with a stop and a target, on Deribit 1 minute bars. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.perp3 run   (once; a second run is refused)
"""
from __future__ import annotations

import sqlite3
import sys

import numpy as np

from .paths import DATA_DIR

RESULT = DATA_DIR / "perp3_result.txt"
COST, COST_INFO = 0.0014, 0.0008
NS, BNS, W = (15, 30, 60), (30, 60, 120), 60
TS, HOLDS = (0.003, 0.006, 0.010), (30, 60)
COOL, MIN_D, CAND, MIN_C, CONF, REPS, SEED = 30, 150, 0.0010, 60, 0.0005, 100, 27102710


def load(cur: str):
    db = sqlite3.connect(DATA_DIR / "search5k.sqlite")
    rows = db.execute("select ts, o, h, l, c, v from bar where cur=? order by ts", (cur,)).fetchall()
    t = np.array([r[0] // 60000 for r in rows]); full = np.arange(t[0], t[-1] + 1)
    arr = {k: np.full(len(full), np.nan) for k in "ohlcv"}
    for i, k in enumerate("ohlcv"):
        arr[k][t - t[0]] = [r[i + 1] for r in rows]
    for k in "ohlc":
        s = arr[k]; m = np.isnan(s)
        if m.any():
            idx = np.where(~m, np.arange(len(s)), 0); np.maximum.accumulate(idx, out=idx); arr[k] = s[idx]
    arr["v"] = np.nan_to_num(arr["v"])
    return full, arr


def outcomes(o, h, l, c, direction: int, T: float, S: float, hold: int):
    """Net-of-nothing gross return per entry minute i (entry at the open of bar i+1), vectorised; NaN where the window is incomplete."""
    n = len(o)
    win = np.lib.stride_tricks.sliding_window_view
    out = np.full(n, np.nan)
    m = n - hold - 2
    entry = o[1:1 + m]
    H = win(h[1:], hold)[:m]; L = win(l[1:], hold)[:m]; C = win(c[1:], hold)[:m]
    if direction > 0:
        tgt = H >= (entry * (1 + T))[:, None]; stp = L <= (entry * (1 - S))[:, None]
    else:
        tgt = L <= (entry * (1 - T))[:, None]; stp = H >= (entry * (1 + S))[:, None]
    ti = np.where(tgt.any(1), tgt.argmax(1), hold + 1); si = np.where(stp.any(1), stp.argmax(1), hold + 1)
    ret = np.where(si <= ti, np.where(si <= hold, -S, 0.0), np.where(ti <= hold, T, 0.0))
    none = (ti > hold) & (si > hold)
    last = (C[:, -1] / entry - 1) * direction
    ret = np.where(none, last, ret)
    out[:m] = ret
    return out


def signals(arr):
    c, h, l, v = arr["c"], arr["h"], arr["l"], arr["v"]
    n = len(c)
    r1 = np.zeros(n); r1[1:] = c[1:] / c[:-1] - 1
    sd = np.full(n, np.nan)
    cs = np.cumsum(np.insert(r1, 0, 0)); cs2 = np.cumsum(np.insert(r1 ** 2, 0, 0))
    k = 1440
    mean = (cs[k:] - cs[:-k]) / k
    var = (cs2[k:] - cs2[:-k]) / k - mean ** 2
    sd[k - 1:] = np.sqrt(np.maximum(var, 0))
    sig = {}
    for N in NS:
        rn = np.full(n, np.nan); rn[N:] = c[N:] / c[:-N] - 1
        z = rn / (sd * np.sqrt(N))
        sig[f"MOMO{N}"] = np.where(z >= 2, 1, np.where(z <= -2, -1, 0))
    for N in BNS:
        hi = np.full(n, np.nan); lo = np.full(n, np.nan)
        wh = np.lib.stride_tricks.sliding_window_view(h, N); wl = np.lib.stride_tricks.sliding_window_view(l, N)
        hi[N:] = wh[:-1].max(1)[:n - N]; lo[N:] = wl[:-1].min(1)[:n - N]
        sig[f"BREAK{N}"] = np.where(c > hi, 1, np.where(c < lo, -1, 0))
    v5 = np.convolve(v, np.ones(5), "full")[:n]
    r5 = np.zeros(n); r5[5:] = c[5:] / c[:-5] - 1
    med = np.full(n, np.nan)
    idx = np.arange(1440 + 5, n, 5)
    sample = v5[::5]
    # trailing 24h median of 5-minute volume, refreshed every 5 minutes
    for i in idx:
        med[i:i + 5] = np.median(v5[i - 1440:i:5])
    spike = v5 >= 3 * med
    sig["VOLSPIKE"] = np.where(spike & (r5 > 0), 1, np.where(spike & (r5 < 0), -1, 0))
    return sig


def pick(sig, cool=COOL):
    idx = np.where(sig != 0)[0]
    keep, last = [], -10 ** 9
    for i in idx:
        if i - last >= cool:
            keep.append(i); last = i
    return np.array(keep, dtype=int)


def zday(x, d):
    n = len(x)
    if n < 20: return 0.0
    r = x - x.mean(); s = np.bincount(d, weights=r); se = np.sqrt((s * s).sum()) / n
    return float(x.mean() / se) if se > 0 else 0.0


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    exits = [(T, S, hd) for T in TS for S in (T / 2, T) for hd in HOLDS]
    rules, per_asset = [], {}
    rng = np.random.default_rng(SEED)
    for cur in ("BTC", "ETH"):
        full, arr = load(cur)
        n = len(full); day = (full // 1440).astype(int); day -= day.min()
        half = day >= np.median(np.unique(day))
        sig = signals(arr)
        valid = np.arange(n) >= 1500
        out = {}
        for (T, S, hd) in exits:
            for d in (1, -1):
                out[(T, S, hd, d)] = outcomes(arr["o"], arr["h"], arr["l"], arr["c"], d, T, S, hd)
        per_asset[cur] = (full, day, half, sig, out, valid)
        for name, s in sig.items():
            for fol in (True, False):
                ids = pick(np.where(valid, s, 0))
                for ex in exits:
                    rules.append((cur, name, fol, ex, ids))
    results = []
    for (cur, name, fol, ex, ids) in rules:
        full, day, half, sig, out, valid = per_asset[cur]
        d = sig[name][ids] * (1 if fol else -1)
        x = np.array([out[(ex[0], ex[1], ex[2], int(dd))][i] for i, dd in zip(ids, d)])
        ok = ~np.isnan(x); x, ii = x[ok] - COST, ids[ok]
        h2 = half[ii]
        a, b = x[~h2], x[h2]
        cand = len(a) >= MIN_D and a.mean() >= CAND
        conf = bool(cand and len(b) >= MIN_C and b.mean() >= CONF)
        results.append({"cur": cur, "name": name, "fol": fol, "ex": ex, "n": len(x), "mean": float(x.mean()) if len(x) else 0.0, "z": zday(x, day[ii]) if len(x) else 0.0, "cand": cand, "conf": conf,
                        "disc": float(a.mean()) if len(a) else 0.0, "cf": float(b.mean()) if len(b) else 0.0, "n1": len(a), "n2": len(b)})
    cand_n = sum(r["cand"] for r in results); conf_n = sum(r["conf"] for r in results)
    nc, nf = [], []
    for _ in range(REPS):
        c_t = f_t = 0
        for (cur, name, fol, ex, ids), r in zip(rules, results):
            full, day, half, sig, out, valid = per_asset[cur]
            pool = np.where(valid)[0]
            draw = rng.choice(pool, len(ids), replace=False) if len(ids) else np.array([], dtype=int)
            dirs = rng.choice([1, -1], len(draw))
            x = np.array([out[(ex[0], ex[1], ex[2], int(dd))][i] for i, dd in zip(draw, dirs)]) if len(draw) else np.array([])
            ok = ~np.isnan(x); x, ii = x[ok] - COST, draw[ok]
            h2 = half[ii]
            a, b = x[~h2], x[h2]
            cd = len(a) >= MIN_D and a.mean() >= CAND
            c_t += cd; f_t += bool(cd and len(b) >= MIN_C and b.mean() >= CONF)
        nc.append(c_t); nf.append(f_t)
    nc.sort(); nf.sort()
    good = [r for r in results if r["conf"] and r["mean"] >= CAND and r["z"] >= 2.5]
    verdict = "NOT_YET_FALSIFIED" if (conf_n > nf[95] and good) else "FALSIFIED"
    lines = [f"PERP3 {verdict}: {len(results)} rules, candidates {cand_n}, confirmed {conf_n}; null candidates median {nc[50]} (95th {nc[95]}), null confirmed median {nf[50]} (95th {nf[95]})"]
    best = sorted(results, key=lambda r: -r["mean"])[:10]
    for r in best:
        lines.append(f"  {r['cur']} {r['name']} {'follow' if r['fol'] else 'fade'} T{100 * r['ex'][0]:.1f}% S{100 * r['ex'][1]:.2f}% hold{r['ex'][2]} n={r['n']} net {100 * r['mean']:+.3f}% z {r['z']:+.2f} disc {100 * r['disc']:+.3f}% ({r['n1']}) conf {100 * r['cf']:+.3f}% ({r['n2']})")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
