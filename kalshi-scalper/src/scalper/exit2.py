"""EXIT2 (README, Pre-registration: EXIT2): where should the L1 exit line sit? L1 upkeep lane. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.exit2 run   (once; a second run is refused)
"""
from __future__ import annotations

import sys
from collections import defaultdict

from . import feat1 as F
from .calibration import cluster_mean_z
from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "exit2_result.txt"
LINES = (None, 0.15, 0.25, 0.40, 0.55, 0.70)


def fee(p):
    return 0.07 * p * (1 - p)


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
    cand = {r["ticker"]: r for r in rows}
    out = {X: [] for X in LINES}; would_win = {X: [0, 0] for X in LINES}
    for tk, (t, series, candles, close_ts, res) in mk.items():
        r = cand.get(tk)
        if r is None:
            continue
        side, price, day = r["side"], r["price"], r["day"]
        win = 1.0 if res == side else 0.0
        by = sorted((c for c in candles if r["close_ts"] - 360 < c[0] <= close_ts), key=lambda c: c[0])
        hold = win - price - fee(price)
        for X in LINES:
            if X is None:
                out[X].append((day, hold)); continue
            sold = None
            for c in by:
                bid = c[1] if side == "yes" else round(1 - c[2], 4)
                if bid <= X:
                    sold = bid; break
            if sold is None:
                out[X].append((day, hold))
            else:
                out[X].append((day, sold - price - fee(price) - fee(sold)))
                would_win[X][0] += 1; would_win[X][1] += int(win == 1.0)
    days = sorted({d for d, _ in out[None]}); cut = days[len(days) // 2]
    def pf(xs):
        w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else float("inf")
    lines = [f"EXIT2: {len(out[None])} L1 entries, {len(days)} days"]
    base = {d_: None for d_ in days}
    b = out[0.25]
    res = {}
    for X in LINES:
        v = out[X]; xs = [x for _, x in v]; h1 = [x for d, x in v if d < cut]; h2 = [x for d, x in v if d >= cut]
        nsold, nwin = would_win[X]
        res[X] = (pf(xs), pf(h1), pf(h2))
        diff = cluster_mean_z([(d, x - y) for (d, x), (_, y) in zip(v, b)]) if X != 0.25 else (0, 0, 0)
        lines.append(f"line {'hold' if X is None else f'{100 * X:.0f}c':5s} PF {pf(xs):.3f} (halves {pf(h1):.3f} / {pf(h2):.3f}), loss rate {100 * sum(1 for x in xs if x < 0) / len(xs):.2f}%, mean {100 * sum(xs) / len(xs):+.2f}c, sold {nsold}, of which would have settled a win {nwin} ({100 * nwin / max(nsold, 1):.0f}%), difference vs 25c per entry {100 * diff[0]:+.3f}c z {diff[2]:+.2f}")
    better = [X for X in LINES if X not in (0.25,) and res[X][1] > res[0.25][1] and res[X][2] > res[0.25][2] and res[X][0] - res[0.25][0] >= 0.03]
    lines.insert(0, f"EXIT2 {'NOT_YET_FALSIFIED' if better else 'FALSIFIED'}; lines beating 25c on both halves by 0.03 PF: {better}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
