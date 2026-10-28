"""HIST1 (README, Pre-registration: HIST1). Research only. Usage: python -m scalper.hist1 run (once)."""
from __future__ import annotations
import random, sys
from datetime import datetime, timezone
from itertools import product
from .scalp12 import load, side_quotes, fee, FLAT
from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT = DATA_DIR / "hist1_result.txt"
LEFTS = (840, 600, 420, 300)
TRIGS = ("cheap", "mid", "up", "down")
TARGETS = (0.10, 0.15, 0.20)
STOPS = (None, 0.10, 0.15, 0.20)


def pick(cs, t, trig):
    q = cs.get(t); p = cs.get(t - 120)
    if q is None:
        return None
    best = None
    for side in ("yes", "no"):
        ask = side_quotes(q, side)[1]; bid = side_quotes(q, side)[0]
        if trig == "cheap" and 0.15 <= ask <= 0.30: sc = -ask
        elif trig == "mid" and 0.30 < ask <= 0.50: sc = -ask
        elif p is not None and trig == "up" and bid - side_quotes(p, side)[0] >= 0.10 and 0.20 <= ask <= 0.70: sc = bid - side_quotes(p, side)[0]
        elif p is not None and trig == "down" and side_quotes(p, side)[0] - bid >= 0.10 and 0.15 <= ask <= 0.50: sc = side_quotes(p, side)[0] - bid
        else: continue
        if best is None or sc > best[0]: best = (sc, side, ask)
    return best


def sim(cs, side, e, t, close_ts, tg, st):
    last = None
    for k in sorted(k for k in cs if t < k <= close_ts - FLAT):
        b = side_quotes(cs[k], side)[0]; last = b
        if b >= e + tg - 1e-9 or (st is not None and b <= e - st + 1e-9):
            return b
    return last


def main(argv):
    if len(argv) < 2 or argv[1] != "run": print(__doc__); return
    if RESULT.exists(): print("Refusing to run again"); return
    M, _ = load()
    res = {}  # cell -> list of (day, net, net_stress)
    for tk, (series, strike, close_ts, cs) in M.items():
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        for L, trig in product(LEFTS, TRIGS):
            t = close_ts - L; pk = pick(cs, t, trig)
            if not pk: continue
            _, side, e = pk
            for tg, st in product(TARGETS, STOPS):
                b = sim(cs, side, e, t, close_ts, tg, st)
                if b is None: continue
                res.setdefault((series, L, trig, tg, st), []).append((day, b - e - fee(e) - fee(b), b - e - fee(e, 1.2) - fee(b, 1.2)))
    days = sorted({d for v in res.values() for d, _, _ in v}); cut = days[len(days) // 2]
    def pf(xs):
        w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else 99.0
    train = []
    for c, v in res.items():
        a = [x for d, x, _ in v if d < cut]
        if len(a) >= 300: train.append((pf(a), c, len(a)))
    train.sort(reverse=True)
    lines = [f"HIST1: {len(M)} markets, {len(res)} cells with trades, {len(train)} with 300+ train trades, split {cut}"]
    passed = []
    for p, c, n in train[:10]:
        v = res[c]; b = [x for d, x, _ in v if d >= cut]; bs = [x for d, _, x in v if d >= cut]
        cp = pf(b) if b else 0; sp = pf(bs) if bs else 0
        _, _, z = cluster_mean_z([(d, x) for d, x, _ in v if d >= cut])
        ok = len(b) >= 300 and cp >= 1.2 and sp >= 1.0
        if ok: passed.append(c)
        lines.append(f"{c} train PF {p:.2f} n={n} | confirm PF {cp:.2f} stressed {sp:.2f} n={len(b)} loss {100*sum(1 for x in b if x<0)/max(len(b),1):.0f}% z {z:+.2f} {'PASS' if ok else ''}")
    allconf = [pf([x for d, x, _ in res[c] if d >= cut]) for _, c, _ in train if sum(1 for d, _, _ in res[c] if d >= cut) >= 300]
    best_all = max(allconf) if allconf else 0
    lines.append(f"best confirm PF over all {len(allconf)} cells with 300+ confirm trades (information only, picks by hindsight): {best_all:.2f}; cells with confirm PF over 1.0: {sum(1 for x in allconf if x > 1.0)}")
    lines.insert(1, f"VERDICT {'NOT_YET_FALSIFIED' if passed else 'FALSIFIED'}; passing: {passed}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))

if __name__ == "__main__": main(sys.argv)
