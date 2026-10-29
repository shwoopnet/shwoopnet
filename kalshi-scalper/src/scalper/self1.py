"""Self-guide round 1 (README): LOOK1, BAND1, ROUND1 on L1's history, LIVELOSS on the live export. Research only.
Usage: python -m scalper.self1 run (once)
"""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict

from .calibration import cluster_mean_z
from .gen1 import _norm_ppf
from .l1studies import load
from .paths import DATA_DIR

SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M", "KXDOGE15M", "KXXRP15M")
LOOKS = (600, 480, 360, 240, 180)
BANDS = ((0.88, 0.91), (0.91, 0.94), (0.94, 0.97), (0.88, 0.97))
RESULT = DATA_DIR / "self1_result.txt"
LIVE = "/tmp/claude-0/-home-user-shwoopnet/cbbea649-50b2-5b08-81d5-2b9a4664b7f3/scratchpad/orders_export4.csv"
N = 438_620 + 46


def fee(p, c=1, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def net(r, c=1, m=1.0):
    return r["won"] - r["price"] - fee(r["price"], c, m)


def summ(rs, c=1):
    v = [net(r, c) for r in rs]; s = [net(r, c, 1.2) for r in rs]
    _, _, z = cluster_mean_z([(r["day"], x) for r, x in zip(rs, v)]) if len(v) > 1 else (0, 0, 0.0)
    return {"pf": pf(v), "pfs": pf(s), "n": len(v), "closes": len({r["close_ts"] for r in rs}), "z": z}


def gate(ws):
    return all(w["pf"] >= 1.5 and w["pfs"] >= 1.2 and w["closes"] >= 30 for w in ws) and ws[1]["z"] >= _norm_ppf(1 - 0.05 / N)


def main():
    if RESULT.exists():
        print("Refusing to run again"); return
    by_look = {L: [r for r in load(L) if r["series"] in SERIES] for L in LOOKS}
    # one shared window cut across looks
    closes = sorted({r["close_ts"] for rs in by_look.values() for r in rs}); cut = (closes[len(closes) // 3], closes[2 * len(closes) // 3])
    for rs in by_look.values():
        for r in rs:
            r["win"] = 0 if r["close_ts"] < cut[0] else (1 if r["close_ts"] < cut[1] else 2)
    lines = [f"SELF1: series {', '.join(s.replace('KX', '').replace('15M', '') for s in SERIES)}; Bonferroni z bar {_norm_ppf(1 - 0.05 / N):.2f}"]
    # LOOK1
    lines.append("LOOK1 (look time per series chosen on discovery):")
    for s in SERIES:
        disc = {L: summ([r for r in by_look[L] if r["series"] == s and r["win"] == 0]) for L in LOOKS}
        ok = {L: d for L, d in disc.items() if d["n"] >= 100}
        if not ok:
            lines.append(f"  {s}: no look with 100 discovery entries"); continue
        L = max(ok, key=lambda k: ok[k]["pf"])
        ws = [summ([r for r in by_look[L] if r["series"] == s and r["win"] == w]) for w in range(3)]
        lines.append(f"  {s}: chosen {L // 60} min (discovery PFs " + ", ".join(f"{k // 60}m {v['pf']:.2f}" for k, v in disc.items()) + ") | " +
                     " | ".join(f"{['disc', 'valid', 'HOLD'][i]} PF {w['pf']:.2f} stress {w['pfs']:.2f} n={w['n']} closes {w['closes']} z {w['z']:+.2f}" for i, w in enumerate(ws)) +
                     f" => {'NOT_YET_FALSIFIED' if gate(ws) else 'FALSIFIED'}")
    # BAND1
    lines.append("BAND1 (price sub-band per series at 6 min, chosen on discovery):")
    base = by_look[360]
    for s in SERIES:
        disc = {b: summ([r for r in base if r["series"] == s and r["win"] == 0 and b[0] - 1e-9 <= r["price"] <= b[1] + 1e-9]) for b in BANDS}
        ok = {b: d for b, d in disc.items() if d["n"] >= 100}
        if not ok:
            lines.append(f"  {s}: no band with 100 discovery entries"); continue
        b = max(ok, key=lambda k: ok[k]["pf"])
        ws = [summ([r for r in base if r["series"] == s and r["win"] == w and b[0] - 1e-9 <= r["price"] <= b[1] + 1e-9]) for w in range(3)]
        lines.append(f"  {s}: chosen {int(b[0] * 100)}c-{int(b[1] * 100)}c (discovery PFs " + ", ".join(f"{int(k[0] * 100)}-{int(k[1] * 100)} {v['pf']:.2f}" for k, v in disc.items()) + ") | " +
                     " | ".join(f"{['disc', 'valid', 'HOLD'][i]} PF {w['pf']:.2f} stress {w['pfs']:.2f} n={w['n']} closes {w['closes']}" for i, w in enumerate(ws)) +
                     f" => {'NOT_YET_FALSIFIED' if gate(ws) else 'FALSIFIED'}")
    # ROUND1
    lines.append("ROUND1 (size chosen per entry to minimise the rounded fee per contract, vs fixed 6 contracts), 6 minute look, 5 series:")
    for w in range(3):
        rs = [r for r in base if r["win"] == w]
        fixed = [net(r, 6) for r in rs]
        best = [r["won"] - r["price"] - min(fee(r["price"], c) for c in (3, 4, 5, 6, 8, 10)) for r in rs]
        lines.append(f"  {['disc', 'valid', 'HOLD'][w]}: fixed 6 PF {pf(fixed):.3f} mean {100 * sum(fixed) / len(fixed):+.3f}c | chosen size PF {pf(best):.3f} mean {100 * sum(best) / len(best):+.3f}c | n={len(rs)}")
    lines.append("  ROUND1 => FALSIFIED on the 1.5 bar (see the saving above for the upkeep lane)")
    # LIVELOSS
    lines.append("LIVELOSS (information): live export, filled orders with a result, by group: net $, PF, n")
    g = defaultdict(list)
    for r in csv.DictReader(open(LIVE)):
        try:
            n_ = float(r["fillCount"] or 0)
            if n_ <= 0 or r["pnl"] == "" or r["series"] not in SERIES:
                continue
            pnl = float(r["pnl"]); p = float(r["price"]); spread = (float(r["seenAsk"]) - float(r["seenBid"])) if r["seenAsk"] and r["seenBid"] else None
            g[("series", r["series"])].append(pnl)
            g[("lead", r["entryLead"] or "?")].append(pnl)
            g[("price", "88-91" if p < 0.91 else ("91-94" if p < 0.94 else "94-97"))].append(pnl)
            if spread is not None:
                g[("spread", "1c" if spread <= 0.011 else "2c+")].append(pnl)
            if r["depthAtLimit"]:
                g[("depth", float(r["depthAtLimit"]))].append(pnl)
        except (ValueError, KeyError):
            continue
    depth = sorted(k[1] for k in g if k[0] == "depth")
    if depth:
        med = statistics.median(depth)
        lo = [x for k, v in g.items() if k[0] == "depth" and k[1] <= med for x in v]; hi = [x for k, v in g.items() if k[0] == "depth" and k[1] > med for x in v]
        g = {k: v for k, v in g.items() if k[0] != "depth"}; g[("depth", f"<= {med:.0f}")] = lo; g[("depth", f"> {med:.0f}")] = hi
    for k in sorted(g, key=str):
        v = g[k]
        lines.append(f"  {k[0]:7s} {str(k[1]):14s} net ${sum(v):+7.2f} PF {pf(v):5.2f} n={len(v)}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
