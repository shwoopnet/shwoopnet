"""SIZE2 (README, Pre-registration: SIZE2): per-market order size for L1. Analysis only."""
from __future__ import annotations
import csv, math, statistics
from collections import defaultdict
from datetime import datetime
from .daycut1 import LIVE, CT, close_of
from .paths import DATA_DIR

RESULT = DATA_DIR / "size2_result.txt"
SERIES = ("KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M")
SIZES = (1, 3, 5, 10)


def fo(p, c):
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def fx(p):
    return 0.07 * p * (1 - p)


def summary(trades):
    """trades: (day, dollars)"""
    w = sum(x for _, x in trades if x > 0); l = -sum(x for _, x in trades if x < 0)
    bd = defaultdict(float)
    for d, x in trades: bd[d] += x
    return f"net ${w - l:+8.2f}, PF {w / l if l else 99:5.2f}, worst trade ${min(x for _, x in trades):+7.2f}, worst day ${min(bd.values()):+7.2f}"


def main():
    L = defaultdict(list)
    for r in csv.DictReader(open(LIVE)):
        try:
            n = float(r["fillCount"] or 0)
            if n <= 0 or r["pnl"] == "" or r["series"] not in SERIES: continue
            p = float(r["price"]); fee_e = float(r["avgFee"] or 0)
            ex = r["exitStatus"] == "sold" and r["exitAvg"]
            e = float(r["exitAvg"]) if ex else None
            g = float(r["pnl"]) / n + fee_e + (fx(e) if ex else 0.0)
            day = datetime.fromtimestamp(datetime.fromisoformat(r["time"].replace("Z", "+00:00")).timestamp(), CT).strftime("%Y-%m-%d")
            L[r["series"]].append((day, n, p, e, g, float(r["pnl"])))
        except (ValueError, KeyError):
            continue
    from . import feat1 as F
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1] in SERIES and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    H = defaultdict(list)
    for r in rows:
        H[r["series"]].append((datetime.fromtimestamp(r["close_ts"], CT).strftime("%Y-%m-%d"), r["price"], r["net"] + r["price"] + fx(r["price"])))
    lines = []
    for s in SERIES:
        lv = L[s]; hv = H[s]
        lines.append(f"== {s}")
        if lv:
            days = sorted({d for d, *_ in lv})
            lines.append(f"  LIVE {days[0]} to {days[-1]}, {len(days)} days, {len(lv)} orders, median size {statistics.median(n for _, n, *_ in lv):.0f}")
            lines.append(f"    today's size (actual P&L):  {summary([(d, pn) for d, n, p, e, g, pn in lv])}")
            for c in SIZES:
                t = [(d, c * (g - fo(p, c) - (fo(e, c) if e is not None else 0))) for d, n, p, e, g, pn in lv]
                lines.append(f"    {c:2d} contracts every order:   {summary(t)}")
        if hv:
            days = sorted({d for d, *_ in hv})
            lines.append(f"  HISTORY {days[0]} to {days[-1]}, {len(days)} days, {len(hv)} entries (held to settlement; no 25c exit modelled)")
            for c in SIZES:
                lines.append(f"    {c:2d} contracts every order:   {summary([(d, c * (g - p - fo(p, c))) for d, p, g in hv])}")
        lines.append("    drop the market:            net $0.00")
    lines.append("== one 90c position lost: to zero | sold at the 25c exit")
    for c in SIZES:
        lines.append(f"  {c:2d} contracts: ${c * (0.90 + fo(0.90, c)):.2f} | ${c * (0.90 + fo(0.90, c) - 0.25 + fo(0.25, c)):.2f}")
    d = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(LIVE)):
        if r["series"] in SERIES:
            for f in ("bidSize", "askSize", "depthAtLimit", "shareOfDepth"):
                try:
                    if r[f]: d[r["series"]][f].append(float(r[f]))
                except ValueError:
                    pass
    lines.append("== top-of-book depth at entry (live export; only the top level exists)")
    for s in SERIES:
        lines.append(f"  {s}: " + "; ".join(f"{k} median {statistics.median(v):.3g} (n={len(v)})" for k, v in d[s].items() if v))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
