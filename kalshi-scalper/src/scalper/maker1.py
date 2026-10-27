"""MAKER1 (README, Pre-registration: MAKER1): resting-order spread capture on deep tennis markets, replayed on the real trade tape. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.maker1 run   (once; a second run is refused)
"""
from __future__ import annotations

import bisect
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from .calibration import cluster_mean_z
from .paths import DATA_DIR

SC1, RESULT = DATA_DIR / "sc1.sqlite", DATA_DIR / "maker1_result.txt"
MIN_VOL, SPREAD_LO, SPREAD_HI, MID_LO, MID_HI = 100.0, 0.02, 0.04, 0.15, 0.85
ENTRY_S, EXIT_S = 180, 300
QS = (1.0, 100.0, 300.0)
BAR_C, BAR_Z, MIN_FILLS, MIN_DAYS, FALSIFY_C = 0.005, 2.0, 300, 12, 0.001


def fee(p: float, on: bool = True) -> float:
    return 0.07 * p * (1 - p) if on else 0.0


def first_fill(ts, px, sd, i0: int, t_end: float, want_side: int, price: float, below: bool, q: float):
    """Index and time at which cumulative taker contracts on want_side at or through price reach q, scanning trades from i0 until t_end."""
    cum = 0.0
    for k in range(i0, len(ts)):
        if ts[k] > t_end:
            return None
        if sd[k][0] == want_side and ((px[k] <= price + 1e-9) if below else (px[k] >= price - 1e-9)):
            cum += sd[k][1]
            if cum >= q:
                return k, ts[k]
    return None


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    src = sqlite3.connect(SC1)
    where = {}
    for f in sorted(DATA_DIR.glob("fp3*.sqlite")):
        d = sqlite3.connect(f)
        for (t,) in d.execute("SELECT ticker FROM done"):
            where[t] = d
    res = {(q, fa): [] for q in QS for fa in (True, False)}  # (day, net) per filled entry
    posted = {q: 0 for q in QS}
    for tk, d in where.items():
        cd = src.execute("SELECT end_ts, bid_c, ask_c, volume FROM candle WHERE ticker=? ORDER BY end_ts", (tk,)).fetchall()
        tr = d.execute("SELECT ts, price, size, side FROM trade WHERE ticker=? ORDER BY ts", (tk,)).fetchall()
        if len(cd) < 60 or len(tr) < 200:
            continue
        ts = [t[0] for t in tr]; px = [t[1] / 100 for t in tr]; sd = [(t[3], t[2]) for t in tr]
        qt = {c[0]: c for c in cd if c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1}
        for q in QS:
            busy_until = 0.0
            for end in sorted(qt):
                c = qt[end]
                b, a = c[1], c[2]
                if end < busy_until or (c[3] or 0) < MIN_VOL or not (SPREAD_LO - 1e-9 <= a - b <= SPREAD_HI + 1e-9) or not (MID_LO <= (a + b) / 2 <= MID_HI):
                    continue
                posted[q] += 1
                i0 = bisect.bisect_left(ts, end)
                f1 = first_fill(ts, px, sd, i0, end + ENTRY_S, -1, b, True, q)  # taker sells hit our bid
                if f1 is None:
                    continue
                k1, t1 = f1
                f2 = first_fill(ts, px, sd, k1 + 1, t1 + EXIT_S, +1, a, False, q)  # taker buys lift our offer
                if f2 is not None:
                    sell, t2, maker_exit = a, f2[1], True
                else:
                    t2 = t1 + EXIT_S
                    x = qt.get(((int(t2) // 60) + 1) * 60) or qt.get((int(t2) // 60) * 60)
                    if x is None:
                        continue
                    sell, maker_exit = x[1], False  # cross at the closing bid
                day = datetime.fromtimestamp(end, timezone.utc).strftime("%Y-%m-%d")
                for fa in (True, False):
                    res[(q, fa)].append((day, sell - b - fee(b, fa) - fee(sell, fa)))
                busy_until = t2
    days = sorted({d for v in res.values() for d, _ in v}); cut = days[len(days) // 2] if days else ""
    lines, verdicts = [], {}
    for q in QS:
        for fa in (True, False):
            v = res[(q, fa)]
            if not v:
                lines.append(f"Q={q:.0f} fee={'taker-equal' if fa else 'zero'}: no fills"); continue
            m, se, z = cluster_mean_z(v)
            h1 = [x for dd, x in v if dd < cut]; h2 = [x for dd, x in v if dd >= cut]
            nd = len({dd for dd, _ in v})
            ok = len(v) >= MIN_FILLS and nd >= MIN_DAYS and m >= BAR_C and z >= BAR_Z and np.mean(h1) > 0 and np.mean(h2) > 0
            verdicts[(q, fa)] = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if m < FALSIFY_C and q == 1.0 else "NOT_ENOUGH_DATA" if len(v) < MIN_FILLS else "FALSIFIED")
            lines.append(f"Q={q:5.0f} fee={'taker-equal' if fa else 'zero      '} postings {posted[q]:6d} fills {len(v):5d} ({100 * len(v) / max(posted[q], 1):.1f}%) days {nd:3d} net/fill {100 * m:+.2f}c z {z:+.2f} halves {100 * np.mean(h1):+.2f}/{100 * np.mean(h2):+.2f}c  {verdicts[(q, fa)]}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
