"""PERPFLOW1 (README, Pre-registration: PERPFLOW1): signed taker flow signals on the Binance BTC and ETH USD-M perpetuals. Discovery lane, research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.perpflow1 run   (once; a second run is refused). Klines: data/binance/futures_um_*.zip.
"""
from __future__ import annotations

import csv
import io
import sys
import zipfile

import numpy as np

from .paths import DATA_DIR
from .perp3 import outcomes, pick, zday

RESULT = DATA_DIR / "perpflow1_result.txt"
KD = DATA_DIR / "binance"
COST, COST_INFO = 0.0012, 0.0008
TS, HOLDS = (0.003, 0.006, 0.010), (30, 60)
COOL, MIN_D, CAND, MIN_C, CONF, REPS, SEED = 30, 150, 0.0010, 60, 0.0005, 100, 27102812


def load(sym: str):
    rows = {}
    for f in sorted(KD.glob(f"futures_um_{sym}-*.zip")):
        z = zipfile.ZipFile(f)
        for line in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
            try:
                ts = int(line[0])
            except ValueError:
                continue
            ts = ts // 1_000_000 if ts > 10 ** 14 else ts // 1000
            rows[ts // 60] = (float(line[1]), float(line[2]), float(line[3]), float(line[4]), float(line[5]), float(line[9]))
    ks = sorted(rows); full = np.arange(ks[0], ks[-1] + 1)
    arr = {k: np.full(len(full), np.nan) for k in ("o", "h", "l", "c", "v", "tb")}
    for m, r in rows.items():
        i = m - full[0]
        for j, k in enumerate(("o", "h", "l", "c", "v", "tb")):
            arr[k][i] = r[j]
    for k in ("o", "h", "l", "c"):
        s = arr[k]; m = np.isnan(s)
        if m.any():
            idx = np.where(~m, np.arange(len(s)), 0); np.maximum.accumulate(idx, out=idx); arr[k] = s[idx]
    arr["v"] = np.nan_to_num(arr["v"]); arr["tb"] = np.nan_to_num(arr["tb"])
    return full, arr


def rolling_sum(x, k):
    cs = np.cumsum(np.insert(x, 0, 0.0)); out = np.full(len(x), np.nan); out[k - 1:] = cs[k:] - cs[:-k]; return out


def signals(arr):
    o, h, l, c, v, tb = (arr[k] for k in ("o", "h", "l", "c", "v", "tb"))
    n = len(c); net = 2 * tb - v
    sig = {}
    for k in (5, 15, 30):
        sh = rolling_sum(net, k) / np.maximum(rolling_sum(v, k), 1e-9)
        # trailing 24h mean and sd of the share (computed every minute with cumulative sums)
        W = 1440
        cs = np.cumsum(np.insert(np.nan_to_num(sh), 0, 0)); cs2 = np.cumsum(np.insert(np.nan_to_num(sh) ** 2, 0, 0))
        mu = np.full(n, np.nan); sd = np.full(n, np.nan)
        mu[W:] = (cs[W:n] - cs[:n - W]) / W
        sd[W:] = np.sqrt(np.maximum((cs2[W:n] - cs2[:n - W]) / W - mu[W:] ** 2, 0))
        z = (sh - mu) / sd
        sig[f"FLOW{k}"] = np.where(z >= 2, 1, np.where(z <= -2, -1, 0))
    for N in (15, 30):
        wh = np.lib.stride_tricks.sliding_window_view(h, N); wl = np.lib.stride_tricks.sliding_window_view(l, N)
        hi = np.full(n, np.nan); lo = np.full(n, np.nan)
        hi[N - 1:] = wh.max(1); lo[N - 1:] = wl.min(1)
        fl = rolling_sum(net, N)
        price_dir = np.where(c >= hi, 1, np.where(c <= lo, -1, 0))
        flow_dir = np.sign(fl)
        div = (price_dir != 0) & (flow_dir == -price_dir)
        sig[f"DIV{N}"] = np.where(div, price_dir, 0)  # direction of the price move; follow = with it, fade = with the flow
    v5 = rolling_sum(v, 5); r5 = np.zeros(n); r5[5:] = np.abs(c[5:] / c[:-5] - 1)
    med = np.full(n, np.nan)
    for i in range(1445, n, 5):
        med[i:i + 5] = np.median(v5[i - 1440:i:5])
    sh5 = rolling_sum(net, 5) / np.maximum(v5, 1e-9)
    ab = (v5 >= 3 * med) & (r5 < 0.0005) & (np.abs(sh5) > 0.1)
    sig["ABSORB"] = np.where(ab, np.sign(sh5), 0)
    return sig


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    exits = [(T, S, hd) for T in TS for S in (T / 2, T) for hd in HOLDS]
    rules, per = [], {}
    rng = np.random.default_rng(SEED)
    for sym in ("BTCUSDT", "ETHUSDT"):
        full, arr = load(sym)
        n = len(full); day = ((full - full[0]) // 1440).astype(int)
        half = day >= np.median(np.unique(day))
        sig = signals(arr)
        valid = np.arange(n) >= 1500
        out = {(T, S, hd, d): outcomes(arr["o"], arr["h"], arr["l"], arr["c"], d, T, S, hd) for (T, S, hd) in exits for d in (1, -1)}
        per[sym] = (day, half, sig, out, valid)
        for name, s in sig.items():
            ids = pick(np.where(valid, s, 0))
            for fol in (True, False):
                for ex in exits:
                    rules.append((sym, name, fol, ex, ids))
    def trade_dirs(sig_arr, ids, fol):
        d = sig_arr[ids] * (1 if fol else -1)
        return d
    results = []
    for (sym, name, fol, ex, ids) in rules:
        day, half, sig, out, valid = per[sym]
        d = trade_dirs(sig[name], ids, fol)
        x = np.array([out[(ex[0], ex[1], ex[2], int(dd))][i] for i, dd in zip(ids, d)]) if len(ids) else np.array([])
        ok = ~np.isnan(x); x, ii = x[ok] - COST, ids[ok]
        h2 = half[ii]; a, b = x[~h2], x[h2]
        cand = len(a) >= MIN_D and a.mean() >= CAND
        conf = bool(cand and len(b) >= MIN_C and b.mean() >= CONF)
        w = x[x > 0].sum(); lo_ = -x[x < 0].sum()
        results.append({"sym": sym, "name": name, "fol": fol, "ex": ex, "n": len(x), "mean": float(x.mean()) if len(x) else 0.0, "pf": float(w / lo_) if lo_ > 0 else float("inf"), "lr": float((x < 0).mean()) if len(x) else 0.0,
                        "z": zday(x, day[ii]) if len(x) else 0.0, "cand": cand, "conf": conf, "disc": float(a.mean()) if len(a) else 0.0, "cf": float(b.mean()) if len(b) else 0.0, "n1": len(a), "n2": len(b)})
    cand_n = sum(r["cand"] for r in results); conf_n = sum(r["conf"] for r in results)
    nc, nf = [], []
    for _ in range(REPS):
        c_t = f_t = 0
        for (sym, name, fol, ex, ids) in rules:
            day, half, sig, out, valid = per[sym]
            pool = np.where(valid)[0]
            draw = rng.choice(pool, len(ids), replace=False) if len(ids) else np.array([], dtype=int)
            dirs = rng.choice([1, -1], len(draw))
            x = np.array([out[(ex[0], ex[1], ex[2], int(dd))][i] for i, dd in zip(draw, dirs)]) if len(draw) else np.array([])
            ok = ~np.isnan(x); x, ii = x[ok] - COST, draw[ok]
            h2 = half[ii]; a, b = x[~h2], x[h2]
            cd = len(a) >= MIN_D and a.mean() >= CAND
            c_t += cd; f_t += bool(cd and len(b) >= MIN_C and b.mean() >= CONF)
        nc.append(c_t); nf.append(f_t)
    nc.sort(); nf.sort()
    good = [r for r in results if r["conf"] and r["pf"] >= 1.5 and r["z"] >= 2.5]
    verdict = "NOT_YET_FALSIFIED" if (conf_n > nf[95] and good) else "FALSIFIED"
    lines = [f"PERPFLOW1 {verdict}: {len(results)} rules, candidates {cand_n}, confirmed {conf_n}; null candidates median {nc[50]} (95th {nc[95]}), null confirmed median {nf[50]} (95th {nf[95]}); cost {100 * COST:.2f}% a round trip"]
    for r in sorted(results, key=lambda r: -r["pf"] if np.isfinite(r["pf"]) else 0)[:10]:
        lines.append(f"  {r['sym']} {r['name']} {'follow' if r['fol'] else 'fade'} T{100 * r['ex'][0]:.1f}% S{100 * r['ex'][1]:.2f}% hold{r['ex'][2]}: PF {r['pf']:.2f}, loss rate {100 * r['lr']:.0f}%, n={r['n']}, net {100 * r['mean']:+.3f}%, z {r['z']:+.2f}, disc {100 * r['disc']:+.3f}% ({r['n1']}) conf {100 * r['cf']:+.3f}% ({r['n2']})")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
