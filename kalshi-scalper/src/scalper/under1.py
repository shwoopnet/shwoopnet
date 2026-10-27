"""UNDER1 (README, Pre-registration: UNDER1): is the cheap side of a 15 minute market underpriced in any series, time or price cell? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.under1 run   (once; a second run is refused)
"""
from __future__ import annotations

import collections
import random
import sys
from datetime import datetime, timezone

from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "under1_result.txt"
LEFTS = (120, 180, 240, 300, 360, 480, 600, 780)
BANDS = ((0.03, 0.10), (0.10, 0.20), (0.20, 0.30), (0.30, 0.45))
MIN_D, CAND_C, MIN_C, CONF_C, REPS, SEED = 150, 0.010, 60, 0.005, 100, 27102705


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def rows_for() -> list[dict]:
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = m
    out = []
    for tk, series, candles, close_ts, res in mk.values():
        if res not in ("yes", "no"):
            continue
        by = {c[0]: c for c in candles}
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        for ls in LEFTS:
            c = by.get(close_ts - ls)
            if c is None:
                continue
            for side, ask in (("yes", c[2]), ("no", round(1 - c[1], 4))):
                for bi, (lo, hi) in enumerate(BANDS):
                    if lo <= ask < hi:
                        out.append({"series": series, "day": day, "ls": ls, "bi": bi, "side": side, "net": (1.0 if res == side else 0.0) - ask - fee(ask)})
    return out


def cells(rows, nets, cut):
    d = collections.defaultdict(lambda: ([], []))
    for r, x in zip(rows, nets):
        d[(r["series"], r["ls"], r["bi"], r["side"])][0 if r["day"] < cut else 1].append(x)
    return d


def counts(d):
    cand = conf = 0
    for v in d.values():
        if len(v[0]) >= MIN_D and sum(v[0]) / len(v[0]) >= CAND_C:
            cand += 1
            if len(v[1]) >= MIN_C and sum(v[1]) / len(v[1]) >= CONF_C:
                conf += 1
    return cand, conf


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    rows = rows_for()
    days = sorted({r["day"] for r in rows}); cut = days[len(days) // 2]
    nets = [r["net"] for r in rows]
    d = cells(rows, nets, cut)
    cand, conf = counts(d)
    lines = [f"UNDER1: {len(rows)} observations, {len(days)} days, {len(d)} cells, {sum(1 for v in d.values() if len(v[0]) >= MIN_D)} with enough discovery entries"]
    shown = []
    for k, v in d.items():
        if len(v[0]) >= MIN_D and sum(v[0]) / len(v[0]) >= CAND_C:
            shown.append((sum(v[0]) / len(v[0]), k, len(v[0]), len(v[1]), (sum(v[1]) / len(v[1])) if v[1] else None))
    grp = collections.defaultdict(list)
    for i, r in enumerate(rows):
        grp[(r["series"], r["day"], r["ls"], r["bi"])].append(i)
    random.seed(SEED); nc, nf = [], []
    for _ in range(REPS):
        sh = list(nets)
        for idx in grp.values():
            v = [nets[i] for i in idx]; random.shuffle(v)
            for i, x in zip(idx, v): sh[i] = x
        a, b = counts(cells(rows, sh, cut)); nc.append(a); nf.append(b)
    nc.sort(); nf.sort()
    verdict = "NOT_YET_FALSIFIED" if conf > nf[95] and conf > 0 else "FALSIFIED"
    lines.append(f"VERDICT {verdict}: real candidates {cand}, confirmed {conf}; null candidates median {nc[50]} (95th {nc[95]}), null confirmed median {nf[50]} (95th {nf[95]})")
    for m, k, n1, n2, m2 in sorted(shown, reverse=True)[:20]:
        lines.append(f"  {k[0][2:-3]:7s} {k[1] // 60:2d}min band {BANDS[k[2]]} {k[3]:3s} disc n {n1:4d} {100 * m:+.2f}c | conf n {n2:4d} {'' if m2 is None else f'{100 * m2:+.2f}c'}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
