"""FILLIMP1 (README), INFORMATION ONLY: do favourites that got cheaper between the decision and the fill lose more often? No claim, no verdict.
Usage: python -m scalper.fillimp
"""
from __future__ import annotations

import math
import statistics as st
import sys
from collections import defaultdict

from . import feat1 as F
from .hs1 import load

GAP_S, EPS = 60, 1e-9
BUCKETS = (("no fill (ask rose)", None, None), ("equal (0)", 0.0, 0.0), ("0 to 1c cheaper", 0.0, 0.01), ("1c to 3c cheaper", 0.01, 0.03), ("over 3c cheaper", 0.03, 1.0))


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def net_at(price: float, win: bool) -> float:
    return (1 - price - fee(price)) if win else -(price + fee(price))


def binom_tail(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def bucket(improvement: float | None) -> int:
    """Index into BUCKETS: None (ask rose above the limit, no fill), or the improvement bucket."""
    if improvement is None:
        return 0
    if improvement <= EPS:
        return 1
    return 2 if improvement <= 0.01 else 3 if improvement <= 0.03 else 4


def next_ask(c_next: tuple, side: str):
    return c_next[2] if side == "yes" else 1 - c_next[1]


def main() -> None:
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    by_t = {m[0]: {c[0]: c for c in m[2]} for m in full}
    rows, _, _ = F.build(full, 360)
    groups = defaultdict(list)
    for r in rows:
        nxt = by_t[r["ticker"]].get(r["close_ts"] - 360 + GAP_S)
        if nxt is None or nxt[1] is None or nxt[2] is None:
            continue
        na = next_ask(nxt, r["side"])
        win = r["gross"] > 0
        if na > r["price"] + EPS:
            groups[0].append((net_at(r["price"], win), not win))
        else:
            groups[bucket(r["price"] - na)].append((net_at(na, win), not win))
    filled = [x for i in (1, 2, 3, 4) for x in groups[i]]
    base = sum(1 for _, l in filled if l) / len(filled)
    print(f"entries with a next-minute candle: {sum(len(v) for v in groups.values())}; filled {len(filled)} (loss rate {100 * base:.2f}%, mean net {100 * st.mean(n for n, _ in filled):+.2f}c)")
    for i, (name, _, _) in enumerate(BUCKETS):
        v = groups[i]
        if not v:
            continue
        k = sum(1 for _, l in v if l)
        tail = binom_tail(k, len(v), base) if i else float("nan")
        print(f"  {name:20s} n={len(v):6d}  loss {100 * k / len(v):5.2f}%  net {100 * st.mean(n for n, _ in v):+6.2f}c" + (f"  (tail p vs filled pool {tail:.3f})" if i else "  (net had it filled at the decision ask)"))


if __name__ == "__main__":
    main()
