"""THROTTLE1 (README, Pre-registration: THROTTLE1): does sizing down when the trailing 100-trade edge of a series is poor improve the L1 record? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.throttle1 run   (once; a second run is refused)
"""
from __future__ import annotations

import random
import sys
from collections import defaultdict

import numpy as np

from . import feat1 as F
from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "throttle1_result.txt"
LOOK, REPS, SEED = 100, 200, 27102711
VARIANTS = {"HALF<0c": (0.0, 0.5), "HALF<-2c": (-0.02, 0.5), "PAUSE<-3c": (-0.03, 0.0)}


def run_series(nets, thr, size):
    """Sizes from the trailing LOOK mean of the previous entries; returns the array of size x net."""
    out = np.empty(len(nets)); run = 0.0
    for i, x in enumerate(nets):
        if i >= LOOK:
            tm = run / LOOK
            s = size if tm < thr else 1.0
        else:
            s = 1.0
        out[i] = s * x
        run += x
        if i >= LOOK:
            run -= nets[i - LOOK]
    return out


def evaluate(streams, thr=None, size=1.0):
    parts = []
    for ser, (ts, nets) in streams.items():
        parts.append((ts, run_series(nets, thr, size) if thr is not None else np.array(nets)))
    ts_all = np.concatenate([p[0] for p in parts]); v = np.concatenate([p[1] for p in parts])
    v = v[np.argsort(ts_all, kind="stable")]
    cum = np.cumsum(v); peak = np.maximum.accumulate(np.maximum(cum, 0)); dd = float((peak - cum).max())
    return float(cum[-1]), dd


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    by = defaultdict(list)
    for r in rows:
        by[r["series"]].append((r["close_ts"], r["net"]))
    streams = {}
    for s, v in by.items():
        v.sort()
        if len(v) > LOOK + 50:
            streams[s] = (np.array([t for t, _ in v], dtype=float), [x for _, x in v])
    base_tot, base_dd = evaluate(streams)
    lines = [f"THROTTLE1: {sum(len(v[1]) for v in streams.values())} entries, {len(streams)} series; always-on total {100 * base_tot:+.0f}c-contracts, max drawdown {100 * base_dd:.0f}, ratio {base_tot / base_dd:.2f}"]
    random.seed(SEED)
    null = {k: [] for k in VARIANTS}; null_dd = {k: [] for k in VARIANTS}
    for _ in range(REPS):
        sh = {}
        for s, (ts, nets) in streams.items():
            n2 = list(nets); random.shuffle(n2); sh[s] = (ts, n2)
        b_tot, b_dd = evaluate(sh)
        for k, (thr, size) in VARIANTS.items():
            t, d = evaluate(sh, thr, size)
            null[k].append(t - b_tot); null_dd[k].append((t / d) / (b_tot / b_dd) if d > 0 and b_dd > 0 and b_tot > 0 else 1.0)
    passed = False
    for k, (thr, size) in VARIANTS.items():
        t, d = evaluate(streams, thr, size)
        dtot = t - base_tot
        p95 = float(np.quantile(null[k], 0.95))
        ratio_gain = (t / d) / (base_tot / base_dd) - 1 if base_tot > 0 and d > 0 else float("nan")
        ok = ratio_gain >= 0.20 and dtot > p95
        passed = passed or ok
        lines.append(f"{k:10s} total {100 * t:+.0f} (change {100 * dtot:+.0f}; null 95th pct of change {100 * p95:+.0f}), drawdown {100 * d:.0f}, net/drawdown {t / d:.2f} ({100 * ratio_gain:+.0f}% vs always-on) {'PASS' if ok else ''}")
    lines.insert(0, f"THROTTLE1 {'NOT_YET_FALSIFIED' if passed else 'FALSIFIED'}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
