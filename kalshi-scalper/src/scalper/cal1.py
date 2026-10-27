"""CAL1 (README, Pre-registration: CAL1): weekday effects on the 6 minute L1 trade, per series. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.cal1 run   (once; a second run is refused)
"""
from __future__ import annotations

import collections
import random
import sys
from datetime import datetime, timezone

from . import feat1 as F
from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "cal1_result.txt"
MIN_D, CAND_C, MIN_C, CONF_C, REPS, SEED = 100, 0.015, 40, 0.0075, 100, 27102708


def cells(rows, nets, cut):
    d = collections.defaultdict(lambda: ([], []))
    for r, x in zip(rows, nets):
        d[(r["series"], r["wd"])][0 if r["day"] < cut else 1].append(x)
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
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    for r in rows:
        r["wd"] = datetime.fromtimestamp(r["close_ts"], timezone.utc).weekday()
    days = sorted({r["day"] for r in rows}); cut = days[len(days) // 2]
    nets = [r["net"] for r in rows]
    d = cells(rows, nets, cut)
    cand, conf = counts(d)
    grp = collections.defaultdict(list)
    for i, r in enumerate(rows):
        grp[(r["series"], r["day"])].append(i)
    random.seed(SEED); nc, nf = [], []
    for _ in range(REPS):
        sh = list(nets)
        for idx in grp.values():
            v = [nets[i] for i in idx]; random.shuffle(v)
            for i, x in zip(idx, v): sh[i] = x
        a, b = counts(cells(rows, sh, cut)); nc.append(a); nf.append(b)
    nc.sort(); nf.sort()
    verdict = "NOT_YET_FALSIFIED" if conf > nf[95] and conf > 0 else "FALSIFIED"
    lines = [f"CAL1 {verdict}: {len(rows)} entries, {len(d)} cells, real candidates {cand}, confirmed {conf}; null candidates median {nc[50]} (95th {nc[95]}), null confirmed median {nf[50]} (95th {nf[95]})"]
    allwd = collections.defaultdict(list)
    for r in rows:
        allwd[r["wd"]].append(r["net"])
    lines.append("all series by weekday (Mon=0): " + ", ".join(f"{k}: n {len(v)} {100 * sum(v) / len(v):+.2f}c" for k, v in sorted(allwd.items())))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
