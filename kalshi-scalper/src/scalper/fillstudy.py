"""Does the bot's IOC order miss the signals that would have won? Information only (no hypothesis, no verdict, nothing here means trade).

Reads studies/fills_2026-10-08.csv: every L1 order from the owner's own diagnostics export on 2026-10-07 and 2026-10-08 (decision price, whether it filled, and how the market settled,
taken from Kalshi's public market data afterwards). For each order, the profit per contract it WOULD have made at the decision price is worked out whether or not it filled,
so the missed signals are scored on what the bot saw, not on a fill it never got. The test is whether losses are concentrated among the misses (one sided Fisher exact test).

Usage: python -m scalper.fillstudy
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .scalps import fee

PATH = Path(__file__).resolve().parents[2] / "studies" / "fills_2026-10-08.csv"


def load(path: Path = PATH) -> list[dict]:
    out = []
    for r in csv.DictReader(open(path)):
        d = float(r["decision_price"])
        won = r["result"] == r["side"]
        out.append({"ticker": r["ticker"], "side": r["side"], "price": d, "filled": r["status"] == "filled", "won": won, "pnl": (1.0 if won else 0.0) - d - fee(d)})
    return out


def fisher_one_sided(losses_missed: int, n_missed: int, losses_filled: int, n_filled: int) -> float:
    """P(at least this many losses among the missed | the same total losses, drawn at random from all orders)."""
    tot, n = losses_missed + losses_filled, n_missed + n_filled
    if tot == 0:
        return 1.0
    return sum(math.comb(n_missed, k) * math.comb(n_filled, tot - k) for k in range(losses_missed, min(n_missed, tot) + 1)) / math.comb(n, tot)


def summarize(rows: list[dict]) -> dict:
    f = [r for r in rows if r["filled"]]
    m = [r for r in rows if not r["filled"]]
    lf, lm = sum(1 for r in f if not r["won"]), sum(1 for r in m if not r["won"])
    mean = lambda xs: sum(r["pnl"] for r in xs) / len(xs) if xs else 0.0
    return {"filled": len(f), "missed": len(m), "lost_filled": lf, "lost_missed": lm, "mean_filled": mean(f), "mean_missed": mean(m), "p": fisher_one_sided(lm, len(m), lf, len(f))}


def main() -> None:
    rows = load()
    s = summarize(rows)
    print(f"{len(rows)} L1 orders. Profit per contract at the decision price, cents.\n")
    print(f"  filled: {s['filled']:>2} orders, {s['lost_filled']} lost, mean {s['mean_filled'] * 100:+.2f}c")
    print(f"  missed: {s['missed']:>2} orders, {s['lost_missed']} would have lost, mean {s['mean_missed'] * 100:+.2f}c")
    print(f"  losses among misses against fills: one sided Fisher exact p = {s['p']:.3f}")
    for series, name in (("KXBTC15M", "Bitcoin"), ("KXGOLD15M", "gold")):
        sub = summarize([r for r in rows if r["ticker"].startswith(series)])
        print(f"  {name}: filled {sub['filled']} ({sub['lost_filled']} lost), missed {sub['missed']} ({sub['lost_missed']} would have lost)")
    print("\nInformation only. One look at one sample, found after the fact: not a pre-registered test.")


if __name__ == "__main__":
    main()
