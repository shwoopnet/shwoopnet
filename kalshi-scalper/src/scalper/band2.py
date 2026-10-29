"""BAND2 (README, Pre-registration: BAND2): calibration of L1 by price paid, history and live aggregates. Research only.
Usage: python -m scalper.band2 run [live_report.json]   (once)
"""
from __future__ import annotations

import json
import math
import sys

from .l1studies import fee, pf
from .paths import DATA_DIR
from .tstop1 import LIVE5, load

BANDS = [(88, 90), (91, 92), (93, 94), (95, 97)]
GROUPS = {"gold": {"KXGOLD15M"}, "Dogecoin": {"KXDOGE15M"}, "Ethereum": {"KXETH15M"}, "Bitcoin": {"KXBTC15M"}, "XRP": {"KXXRP15M"}, "live five": LIVE5}


def cell(rs):
    n = len(rs)
    if n == 0:
        return "n 0"
    w = sum(1 for r in rs if r["won"] > 0.5); p = sum(r["price"] for r in rs) / n
    z = (w / n - p) / math.sqrt(p * (1 - p) / n)
    net = [r["won"] - r["price"] - fee(r["price"]) for r in rs]
    return f"n {n} losses {n - w} won {100 * w / n:.1f}% paid {100 * p:.1f}c gap {100 * (w / n - p):+.1f} pts z {z:+.2f} PF {pf(net):.2f}"


def band_of(price):
    c = round(price * 100)
    return next((b for b in BANDS if b[0] <= c <= b[1]), None)


def main():
    if sys.argv[1:2] != ["run"]:
        print(__doc__); return
    out = DATA_DIR / "band2_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    rows = [r for r in load() if r["series"] in LIVE5]
    lines = ["BAND2 history (6 minute look, 1 contract fee); per third t1 / t2 / t3 and pooled"]
    for g, ser in GROUPS.items():
        lines.append(f"{g}:")
        for b in BANDS:
            rs = [r for r in rows if r["series"] in ser and band_of(r["price"]) == b]
            lines.append(f"  {b[0]}-{b[1]}c pooled: {cell(rs)}")
            for w in range(3):
                lines.append(f"      t{w + 1}: {cell([r for r in rs if r['win'] == w])}")
    if len(sys.argv) > 2:
        d = json.load(open(sys.argv[2]))
        lines.append("\nLIVE (owner's settled orders, held and exits, from the report endpoint; price paid = avgFill when present)")
        o = [x for x in d["orders"] if x.get("status") != "no fill" and x.get("avgFill") and x.get("result") in ("yes", "no", "win", "loss", "exit") or (x.get("settledPnl") is not None and x.get("avgFill"))]
        lines.append(f"  orders with a price paid: {len(o)} of {len(d['orders'])}")
        for k in ("ticker", "entryLead"):
            pass
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
