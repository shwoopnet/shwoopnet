"""GROW1 (README, Pre-registration: GROW1): which sizing rule lets a $500 account grow on the L1 history. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.grow1 run   (once; a second run is refused)
"""
from __future__ import annotations

import random
import sys
from collections import defaultdict, deque

import numpy as np

from . import feat1 as F
from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "grow1_result.txt"
START, BURN_DAYS, REPS, SEED = 500.0, 30, 200, 27102801
PF_MIN, N_MIN, WIN_S = 1.10, 50, 30 * 86400
RULES = [("FIXED1", None, False, False), ("r0.5%", 0.005, False, False), ("r1%", 0.01, False, False), ("r2%", 0.02, False, False),
         ("r1% WF", 0.01, True, False), ("r2% WF", 0.02, True, False), ("r1% WF+HALF", 0.01, True, True)]


def simulate(entries, days_scored, rule):
    name, r, wf, half = rule
    bal, peak, mdd = START, START, 0.0
    wins = losses = 0.0
    hist = defaultdict(deque)   # series -> deque of (ts, net) of ALL entries (shadow)
    last100 = defaultdict(deque)
    for ts, day, ser, price, net in entries:
        h = hist[ser]
        while h and h[0][0] < ts - WIN_S:
            h.popleft()
        trade = day in days_scored
        if trade:
            ok = True
            if wf:
                w = sum(x for _, x in h if x > 0); l = -sum(x for _, x in h if x < 0)
                ok = len(h) >= N_MIN and l > 0 and w / l >= PF_MIN
            if ok and bal > 1:
                size = 1 if r is None else max(1, int(r * bal / price))
                if half and len(last100[ser]) >= 100 and sum(last100[ser]) / 100 < 0:
                    size = max(1, size // 2)
                d = size * net
                bal += d
                if d > 0: wins += d
                else: losses -= d
                peak = max(peak, bal); mdd = max(mdd, (peak - bal) / peak)
        h.append((ts, net))
        l100 = last100[ser]; l100.append(net)
        if len(l100) > 100: l100.popleft()
    return bal, mdd, (wins / losses if losses else float("inf"))


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
    rows.sort(key=lambda r: r["close_ts"])
    days = sorted({r["day"] for r in rows}); scored = set(days[BURN_DAYS:])
    ent = [(r["close_ts"], r["day"], r["series"], r["price"], r["net"]) for r in rows]
    lines = [f"GROW1: {len(ent)} L1 entries, {len(days)} days, burn-in {BURN_DAYS} days, scored {len(scored)} days"]
    byday = defaultdict(list)
    for e in ent: byday[e[1]].append(e)
    random.seed(SEED)
    passed = []
    for rule in RULES:
        bal, mdd, pf = simulate(ent, scored, rule)
        finals = []
        sd = sorted(scored)
        for _ in range(REPS):
            pick = [random.choice(sd) for _ in sd]
            ent2 = [e for e in ent if e[1] not in scored]  # burn-in entries stay as they are (history statistic)
            for d in pick:
                ent2.extend((e[0], "S", *e[2:]) for e in byday[d])
            # resampled days keep their intra-day order; assign synthetic increasing timestamps by position
            ts0 = max(e[0] for e in ent if e[1] not in scored)
            res, last_ts = [], ts0
            for d in pick:
                base = byday[d][0][0] if byday[d] else 0
                for e in byday[d]:
                    last_ts = last_ts + max(1, e[0] - base) if False else last_ts
                res.extend(byday[d])
            seq, t = [e for e in ent if e[1] not in scored], ts0
            for d in pick:
                if not byday[d]: continue
                b0 = byday[d][0][0]
                for e in byday[d]:
                    seq.append((ts0 + 86400 * (pick.index(d) if False else 0) + (e[0] - b0), "S", e[2], e[3], e[4]))
                ts0 += 86400
            fb, _, _ = simulate(seq, {"S"}, rule)
            finals.append(fb)
        finals.sort()
        p5, p50, below = finals[int(0.05 * REPS)], finals[REPS // 2], sum(f < START for f in finals) / REPS
        ok = p5 >= START and pf >= 1.15
        if ok: passed.append(rule[0])
        lines.append(f"{rule[0]:12s} final ${bal:8.2f}  max drawdown {100 * mdd:5.1f}%  PF {pf:5.2f} | bootstrap: median ${p50:8.2f}, 5th pct ${p5:8.2f}, share below $500 {100 * below:4.0f}% {'PASS' if ok else ''}")
    lines.insert(0, f"GROW1 {'NOT_YET_FALSIFIED' if passed else 'FALSIFIED'}; passing {passed}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
