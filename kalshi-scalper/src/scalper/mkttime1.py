"""MKTTIME1 (README, Pre-registration: MKTTIME1): per-market time-of-day and weekday stand-down rules for L1. Research only.
Usage: python -m scalper.mkttime1 ab        (windows A and B, once; writes the A-and-B survivors)
       python -m scalper.mkttime1 holdout   (window C, once, only for the A-and-B survivors)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from .calibration import cluster_mean_z
from .l1studies import pf
from .paths import DATA_DIR
from .tstop1 import LEFT, hold, load

CT = ZoneInfo("America/Chicago")
MARKETS = {"gold": "KXGOLD15M", "Bitcoin": "KXBTC15M", "Ethereum": "KXETH15M", "Dogecoin": "KXDOGE15M", "XRP": "KXXRP15M"}
DAYS = "Mon Tue Wed Thu Fri Sat Sun".split()
RULES = [(f"skip {h:02d}-{h + 4:02d} CT", lambda t, h=h: h <= t.hour < h + 4) for h in range(0, 24, 4)] + \
        [(f"skip {d}", lambda t, i=i: t.weekday() == i) for i, d in enumerate(DAYS)] + [("skip Sat+Sun", lambda t: t.weekday() >= 5)]
AB_OUT, C_OUT = DATA_DIR / "mkttime1_ab_result.txt", DATA_DIR / "mkttime1_c_result.txt"
SURV = DATA_DIR / "mkttime1_ab_survivors.json"


def rows_by_market():
    out = {}
    for r in load():
        for m, s in MARKETS.items():
            if r["series"] == s:
                r["t"] = datetime.fromtimestamp(r["close_ts"] - LEFT, CT)
                r["v"] = hold(r)
                out.setdefault(m, []).append(r)
    return out


def check(rs, fn):
    base = [r["v"] for r in rs]
    kept = [r["v"] for r in rs if not fn(r["t"])]
    skipped = [r for r in rs if fn(r["t"])]
    bn, kn = sum(base), sum(kept)
    net_ok = (kn >= 0.7 * bn) if bn > 0 else (kn >= bn)
    lift = pf(kept) - pf(base)
    return dict(ok=lift >= 0.10 and net_ok, lift=lift, pf0=pf(base), pf1=pf(kept), net0=bn, net1=kn, n_skip=len(skipped),
                losses_skip=sum(1 for r in skipped if r["v"] < 0))


def ab():
    if AB_OUT.exists():
        print("Refusing to run again"); return
    M = rows_by_market()
    lines, surv = [], []
    for m, rs in M.items():
        lines.append(f"{m}: n={len(rs)}; baseline PF A {pf([r['v'] for r in rs if r['win'] == 0]):.3f}, B {pf([r['v'] for r in rs if r['win'] == 1]):.3f}")
        for name, fn in RULES:
            a = check([r for r in rs if r["win"] == 0], fn); b = check([r for r in rs if r["win"] == 1], fn)
            enough = a["losses_skip"] + b["losses_skip"] >= 15
            ok = a["ok"] and b["ok"] and enough
            if ok:
                surv.append({"market": m, "rule": name})
            lines.append(f"  {'A+B PASS' if ok else '        '} {name:14s} A: PF {a['pf0']:.3f}->{a['pf1']:.3f} ({a['lift']:+.3f}) net {100 * a['net0']:+.0f}c->{100 * a['net1']:+.0f}c skip {a['n_skip']} ({a['losses_skip']} losses) | "
                         f"B: PF {b['pf0']:.3f}->{b['pf1']:.3f} ({b['lift']:+.3f}) net {100 * b['net0']:+.0f}c->{100 * b['net1']:+.0f}c skip {b['n_skip']} ({b['losses_skip']} losses){'' if enough else ' [under 15 losses]'}")
    SURV.write_text(json.dumps(surv))
    lines.insert(0, f"MKTTIME1 A and B: {len(RULES) * len(M)} rules tried; {len(surv)} pass A and B: " + (", ".join(f"{s['market']} {s['rule']}" for s in surv) or "none (FALSIFIED)"))
    AB_OUT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def holdout():
    if C_OUT.exists():
        print("Refusing to run again"); return
    surv = json.loads(SURV.read_text())
    if not surv:
        C_OUT.write_text("MKTTIME1 C: nothing passed A and B; FALSIFIED\n"); print("nothing to read"); return
    M = rows_by_market(); fns = dict(RULES)
    lines, ok_m = [], set()
    for s in surv:
        rs = [r for r in M[s["market"]] if r["win"] == 2]
        c = check(rs, fns[s["rule"]])
        allr = M[s["market"]]
        gain = [(r["close_ts"] // 86400, (0.0 if fns[s["rule"]](r["t"]) else r["v"]) - r["v"]) for r in allr]
        _, _, z = cluster_mean_z(gain)
        if c["ok"]:
            ok_m.add(s["market"])
        lines.append(f"  {'C PASS' if c['ok'] else 'C fail'} {s['market']} {s['rule']}: PF {c['pf0']:.3f}->{c['pf1']:.3f} ({c['lift']:+.3f}) net {100 * c['net0']:+.0f}c->{100 * c['net1']:+.0f}c skip {c['n_skip']} ({c['losses_skip']} losses); day-clustered z of the gain, all windows {z:+.2f} (deflated bar about 5.17)")
    v = "FALSIFIED" if len(ok_m) < 2 else "NOT_YET_FALSIFIED (forward test only)"
    lines.insert(0, f"MKTTIME1 C VERDICT: {v}; markets with a C pass: {sorted(ok_m) or 'none'}")
    C_OUT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"ab": ab, "holdout": holdout}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
