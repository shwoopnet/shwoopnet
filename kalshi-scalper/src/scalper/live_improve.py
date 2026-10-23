"""Live fills by price improvement (README, "Slippage request" and FILLIMP1), INFORMATION ONLY: do fills cheaper than the quote seen at the decision lose more often?
YES order: improvement = seenAsk - avgFill; NO order: improvement = avgFill - seenBid (seenBid and seenAsk are YES-side quotes; avgFill is the YES-side fill price).
Usage: python -m scalper.live_improve [fills_with_quotes.csv]
"""
from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict

from .paths import DATA_DIR

EDGES = (0.0, 0.01, 0.03)
NAMES = ("improvement <= 0", "0 to 1c cheaper", "1c to 3c cheaper", "over 3c cheaper")
DEFAULT = DATA_DIR.parent / "studies" / "live_fills_with_quotes_2026-10-22.csv"


def improvement(side: str, seen_bid: float, seen_ask: float, fill: float) -> float:
    return (seen_ask - fill) if side == "y" else (fill - seen_bid)


def bucket(x: float) -> int:
    return 0 if x <= EDGES[0] + 1e-9 else 1 if x <= EDGES[1] + 1e-9 else 2 if x <= EDGES[2] + 1e-9 else 3


def binom_tail(k: int, n: int, p: float) -> float:
    if k <= 0:
        return 1.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq) for i in range(k, n + 1)))


def table(rows: list[dict], title: str) -> list[str]:
    n_all = len(rows)
    if n_all == 0:
        return [title + ": no rows"]
    loss_all = sum(1 for r in rows if r["pnl"] < 0) / n_all
    out = [f"{title}  (fills {n_all}, loss rate {100 * loss_all:.1f}%, P/L ${sum(r['pnl'] for r in rows):+.2f})"]
    g = defaultdict(list)
    for r in rows:
        g[bucket(r["imp"])].append(r)
    for i, name in enumerate(NAMES):
        v = g.get(i, [])
        if not v:
            continue
        k = sum(1 for r in v if r["pnl"] < 0)
        out.append(f"  {name:18s} fills {len(v):4d}  losses {k:3d} ({100 * k / len(v):5.1f}%)  P/L ${sum(r['pnl'] for r in v):+8.2f}  exited {sum(1 for r in v if r['exit'] == 'S'):2d}  tail p vs all {binom_tail(k, len(v), loss_all):.3f}")
    return out


def load(path) -> list[dict]:
    rows = []
    for r in csv.DictReader(open(path)):
        rows.append({"side": r["side"], "pnl": float(r["pnl"]), "exit": r["exit"], "lead": r["lead"], "count": float(r["count"]),
                     "imp": improvement(r["side"], float(r["seenBid"]), float(r["seenAsk"]), float(r["avgFill"]))})
    return rows


def main(argv: list[str]) -> None:
    rows = load(argv[1] if len(argv) > 1 else DEFAULT)
    out = table(rows, "ALL fills with a seen quote")
    for lead in ("6m", "10m"):
        sub = [r for r in rows if r["lead"] == lead]
        if len(sub) >= 20:
            out += table(sub, f"entryLead {lead}")
    since = [r for r in rows if r["count"] <= 6]
    out += table(since, "orders of 6 contracts or fewer (after the sizing change)")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
