"""PULL1 (README, Pre-registration: PULL1): buy the pullback on Bitcoin and Ethereum 15 minute contracts and exit on a bounce or by the clock. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.pull1 run   (once; a second run is refused)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import numpy as np

from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "pull1_result.txt"
LS, DEPTHS, BANDS = (600, 480, 360, 240), (0.05, 0.10, 0.15), ((0.25, 0.50), (0.50, 0.75))
TS, STOPS, SELL_BEFORE, LOOK = (0.05, 0.10, 0.15), (None, 0.10), 120, 6
MIN_D, CAND_C, MIN_C, CONF_C, REPS, SEED = 150, 0.015, 60, 0.0075, 100, 27102706


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def exits():
    return [(T, S, fb) for T in TS for S in STOPS for fb in ("A", "B")]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1] in ("KXBTC15M", "KXETH15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = m
    ex = exits()
    recs = []  # one record per (market, L, side): features and the 12 outcomes
    for tk, series, candles, close_ts, res in mk.values():
        if res not in ("yes", "no"):
            continue
        by = {c[0]: (c[1], c[2]) for c in candles}
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        for L in LS:
            t = close_ts - L
            if t not in by or (t + 60) not in by:
                continue
            for side in ("yes", "no"):
                def bid(k):
                    q = by.get(k)
                    return None if q is None else (q[0] if side == "yes" else round(1 - q[1], 4))
                def ask(k):
                    q = by.get(k)
                    return None if q is None else (q[1] if side == "yes" else round(1 - q[0], 4))
                def mid(k):
                    q = by.get(k)
                    return None if q is None else ((q[0] + q[1]) / 2 if side == "yes" else 1 - (q[0] + q[1]) / 2)
                m_now = mid(t)
                hist = [mid(t - 60 * j) for j in range(0, LOOK + 1)]
                hist = [h for h in hist if h is not None]
                e = ask(t + 60)
                if m_now is None or e is None or len(hist) < 4 or not 0.25 <= e < 0.75:
                    continue
                pull = max(hist) - m_now
                payoff = 1.0 if res == side else 0.0
                outs = []
                for (T, S, fb) in ex:
                    val, done = None, False
                    for k in range(t + 120, close_ts - SELL_BEFORE + 1, 60):
                        b = bid(k)
                        if b is None:
                            continue
                        if b >= e + T - 1e-9 or (S is not None and b <= e - S + 1e-9):
                            val, done = b, True; break
                    if done:
                        outs.append(val - e - fee(e) - fee(val))
                    elif fb == "B":
                        b = bid(close_ts - SELL_BEFORE)
                        outs.append((b - e - fee(e) - fee(b)) if b is not None else (payoff - e - fee(e)))
                    else:
                        outs.append(payoff - e - fee(e))
                recs.append((series, day, L, e, pull, outs))
    days = sorted({r[1] for r in recs}); cut = days[len(days) // 2]
    out_lines = [f"PULL1: {len(recs)} candidate (market, time, side) records, {len(days)} days"]
    total_conf = 0
    rng = np.random.default_rng(SEED)
    rule_sets = []
    for series in ("KXBTC15M", "KXETH15M"):
        sub = [r for r in recs if r[0] == series]
        arr_out = np.array([r[5] for r in sub]); arr_day2 = np.array([r[1] >= cut for r in sub]); arr_L = np.array([r[2] for r in sub])
        arr_e = np.array([r[3] for r in sub]); arr_p = np.array([r[4] for r in sub])
        for L in LS:
            for bi, (lo, hi) in enumerate(BANDS):
                base = (arr_L == L) & (arr_e >= lo) & (arr_e < hi)
                for d in DEPTHS:
                    sel = np.where(base & (arr_p >= d - 1e-9))[0]
                    ctrl = np.where(base)[0]
                    for xi in range(len(ex)):
                        rule_sets.append((series, L, bi, d, xi, sel, ctrl, arr_out, arr_day2))
    def score(sel, xi, arr_out, d2):
        v = arr_out[sel, xi]; h = d2[sel]
        a, b = v[~h], v[h]
        cand = len(a) >= MIN_D and a.mean() >= CAND_C
        conf = cand and len(b) >= MIN_C and b.mean() >= CONF_C
        return cand, conf, a, b
    cand_n = conf_n = 0; confirmed = []
    for (series, L, bi, d, xi, sel, ctrl, arr_out, d2) in rule_sets:
        c, f, a, b = score(sel, xi, arr_out, d2)
        cand_n += c; conf_n += f
        if f: confirmed.append((series, L, bi, d, ex[xi], len(a), a.mean(), len(b), b.mean()))
    nc, nf = [], []
    for _ in range(REPS):
        c_t = f_t = 0
        for (series, L, bi, d, xi, sel, ctrl, arr_out, d2) in rule_sets:
            if len(sel) == 0 or len(ctrl) < len(sel):
                continue
            draw = rng.choice(ctrl, len(sel), replace=False)
            c, f, _, _ = score(draw, xi, arr_out, d2)
            c_t += c; f_t += f
        nc.append(c_t); nf.append(f_t)
    nc.sort(); nf.sort()
    verdict = "NOT_YET_FALSIFIED" if conf_n > nf[95] else "FALSIFIED"
    out_lines.append(f"VERDICT {verdict}: {len(rule_sets)} rules, candidates {cand_n}, confirmed {conf_n}; null candidates median {nc[50]} (95th {nc[95]}), null confirmed median {nf[50]} (95th {nf[95]})")
    for r in sorted(confirmed, key=lambda r: -r[6])[:15]:
        out_lines.append(f"  {r[0][2:-3]} L{r[1] // 60}min band{r[2]} pull>={100 * r[3]:.0f}c exit T{100 * r[4][0]:.0f}c S{r[4][1]} {r[4][2]} disc n {r[5]} {100 * r[6]:+.2f}c | conf n {r[7]} {100 * r[8]:+.2f}c")
    RESULT.write_text("\n".join(out_lines) + "\n"); print("\n".join(out_lines))


if __name__ == "__main__":
    main(sys.argv)
