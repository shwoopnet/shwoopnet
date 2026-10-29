"""ARB5 (README, Pre-registration: ARB5): crossed totals ladders in sports history. Research only.
Usage: python -m scalper.arb5 run (once)"""
from __future__ import annotations
import math, sqlite3, sys
from collections import defaultdict
from .paths import DATA_DIR

RESULT = DATA_DIR / "arb5_result.txt"


def fee(p, c=10):
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def main():
    if RESULT.exists():
        print("Refusing to run again"); return
    db = sqlite3.connect(DATA_DIR / "sports1.sqlite")
    ev = defaultdict(list)
    for t, s, k, c in db.execute("select ticker, series, strike, close_ts from market where series like '%TOTAL%' and strike is not null"):
        ev[t.rsplit("-", 1)[0]].append((k, t, c))
    q = defaultdict(dict)
    for t, e, b, a in db.execute("select ticker, end_ts, bid_c, ask_c from candle where series like '%TOTAL%' and bid_c is not null and ask_c is not null"):
        q[t][e] = (b, a)
    games = sorted(((min(c for _, _, c in v), e, v) for e, v in ev.items() if len(v) >= 2))
    n = len(games); cuts = (games[n // 3][0], games[2 * n // 3][0])
    win = lambda c: 0 if c < cuts[0] else (1 if c < cuts[1] else 2)
    W = [{"games": 0, "locked": 0, "best": -9.0, "locks": 0} for _ in range(3)]
    examples = []
    for c, e, v in games:
        w = W[win(c)]; w["games"] += 1
        v.sort()
        hit = False
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                lo, hi = q[v[i][1]], q[v[j][1]]
                for ts in set(lo) & set(hi):
                    ask_lo, bid_hi = lo[ts][1], hi[ts][0]
                    if not (0 < ask_lo < 1 and 0 < bid_hi < 1):
                        continue
                    lock = bid_hi - ask_lo - fee(ask_lo) - fee(1 - bid_hi)
                    w["best"] = max(w["best"], lock)
                    if lock >= 0.01:
                        w["locks"] += 1; hit = True
                        if len(examples) < 8: examples.append((e, v[i][0], v[j][0], ts, ask_lo, bid_hi, round(100 * lock, 2)))
        w["locked"] += hit
    ok = all(w["locked"] >= 3 and w["locked"] / max(w["games"], 1) >= 0.01 for w in W)
    lines = [f"ARB5 VERDICT {'NOT_YET_FALSIFIED (capacity unknown; forward check on recorder R5 only)' if ok else 'FALSIFIED'}"]
    for k, w in zip(("discovery", "validation", "holdout"), W):
        lines.append(f"  {k}: games {w['games']}, games with a lock >= 1c {w['locked']} ({100 * w['locked'] / max(w['games'], 1):.1f}%), lock-minutes {w['locks']}, best lock {100 * w['best']:+.2f}c")
    for x in examples:
        lines.append(f"  example {x}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main() if len(sys.argv) > 1 and sys.argv[1] == "run" else print(__doc__)
