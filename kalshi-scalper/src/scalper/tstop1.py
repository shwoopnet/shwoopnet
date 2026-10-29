"""TIMEX1 and DCAP1 (README, Pre-registration: TIMEX1 and DCAP1): the owner's time-stop questions on L1's history. Research only.
Usage: python -m scalper.tstop1 timex1 | dcap1   (each once)
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from .calibration import cluster_mean_z
from .l1studies import fee, pf
from .paths import DATA_DIR

LEFT = 360
CT = ZoneInfo("America/Chicago")
LIVE5 = {"KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M"}


def load():
    from . import feat1 as F
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load as hl
    mk = {}
    for m in hl() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), LEFT)
    for r in rows:
        cs = mk[r["ticker"]][2]
        r["won"] = round(r["net"] + r["price"] + 0.07 * r["price"] * (1 - r["price"]))
        r["path"] = [(e, b, a) for e, b, a, *_ in cs if r["close_ts"] - LEFT < e <= r["close_ts"] - 60]
        r["pre"] = [(e, b, a) for e, b, a, *_ in cs if r["close_ts"] - LEFT - 300 <= e <= r["close_ts"] - LEFT]
        r["entry_q"] = next(((b, a) for e, b, a, *_ in cs if e == r["close_ts"] - LEFT), None)
    closes = sorted({r["close_ts"] for r in rows})
    cut = (closes[len(closes) // 3], closes[2 * len(closes) // 3])
    for r in rows:
        r["win"] = 0 if r["close_ts"] < cut[0] else (1 if r["close_ts"] < cut[1] else 2)
    return rows


def sbid(r, b, a):
    return b if r["side"] == "yes" else round(1 - a, 4)


def hold(r, c=1):
    return r["won"] - r["price"] - fee(r["price"], c)


def sell(r, sb, c=1):
    return (sb - fee(sb, c) if sb > 0 else 0.0) - r["price"] - fee(r["price"], c)


def tx_at(r, secs, lvl):
    for e, b, a in r["path"]:
        if e == r["close_ts"] - secs:
            sb = sbid(r, b, a)
            return sell(r, sb) if sb <= lvl + 1e-9 else hold(r)
    return hold(r)


def tx3(r):
    for e, b, a in r["path"]:
        sb = sbid(r, b, a)
        if r["close_ts"] - e <= 180 and sb <= r["price"] - 0.15 + 1e-9:
            return sell(r, sb)
    return hold(r)


def tx4(r):
    pre = r["pre"]
    if len(pre) < 6:
        return hold(r)
    mids = [((b + a) / 2 if r["side"] == "yes" else 1 - (b + a) / 2) for e, b, a in pre[-6:]]
    vol = sum(abs(y - x) for x, y in zip(mids, mids[1:])) / 5
    line = r["price"] - max(0.05, 2 * vol)
    for e, b, a in r["path"]:
        sb = sbid(r, b, a)
        if sb <= line + 1e-9:
            return sell(r, sb)
    return hold(r)


def tx5(r):
    q = r["entry_q"]
    if not q or q[1] - q[0] < 0.02 - 1e-9:
        return hold(r)
    for e, b, a in r["path"]:
        sb = sbid(r, b, a)
        if sb <= r["price"] - 0.10 + 1e-9:
            return sell(r, sb)
    return hold(r)


RULES = {"TX1 late weak 2": lambda r: tx_at(r, 120, 0.70), "TX2 late weak 1": lambda r: tx_at(r, 60, 0.70), "TX3 late adverse": tx3, "TX4 own volatility": tx4, "TX5 spread keyed": tx5}
GROUPS = {"gold": {"KXGOLD15M"}, "Dogecoin": {"KXDOGE15M"}, "Bitcoin": {"KXBTC15M"}, "live five": LIVE5}


def timex1():
    p = DATA_DIR / "timex1_result.txt"
    if p.exists():
        print("Refusing to run again"); return
    rows = load()
    lines = [f"TIMEX1: {len(rows)} L1 entries; PF at 1 contract per third (disc / valid / third); better-than-hold needs +0.03 PF in all thirds and z >= 2"]
    verdict = []
    for g, ser in GROUPS.items():
        rs = [r for r in rows if r["series"] in ser]
        hp = [pf([hold(r) for r in rs if r["win"] == w]) for w in range(3)]
        lines.append(f"{g}: n={len(rs)}; hold PF " + " / ".join(f"{x:.3f}" for x in hp))
        for name, fn in RULES.items():
            v = [[fn(r) for r in rs if r["win"] == w] for w in range(3)]
            ps = [pf(x) for x in v]
            diffs = [(r["close_ts"] // 86400, fn(r) - hold(r)) for r in rs]
            changed = sum(1 for _, d in diffs if abs(d) > 1e-12)
            _, _, z = cluster_mean_z(diffs) if changed > 1 else (0, 0, 0.0)
            better = all(ps[w] >= hp[w] + 0.03 for w in range(3)) and z >= 2.0
            strat = all(x >= 1.5 for x in ps)
            if better or strat:
                verdict.append(f"{g} {name}")
            lines.append(f"  {name:20s} PF " + " / ".join(f"{x:.3f}" for x in ps) + f" | entries changed {changed} | diff z {z:+.2f} | {'BETTER THAN HOLD' if better else ''}{' STRATEGY BAR' if strat else ''}")
    lines.insert(0, "TIMEX1 VERDICT: " + (("meets a bar: " + ", ".join(verdict) + " (forward read only)") if verdict else "FALSIFIED (no rule beats hold in all thirds, none reaches 1.5)"))
    p.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def day(ts):
    return datetime.fromtimestamp(ts, CT).strftime("%Y-%m-%d")


def run_caps(ent, contracts, acct, up, down, spread_skip):
    """ent: list of (entry_t, close_t, pnl_per_contract, spread). Returns kept list, removed list, days triggered."""
    byday = defaultdict(list)
    for e in ent:
        byday[day(e[0])].append(e)
    kept, rem, trig = [], [], set()
    for d, es in byday.items():
        es.sort()
        taken = []
        for e in es:
            if spread_skip and e[3] is not None and e[3] >= 0.02 - 1e-9:
                rem.append(e); continue
            real = sum(contracts * x[2] for x in taken if x[1] <= e[0])
            if (up is not None and real >= up * acct) or (down is not None and real <= -down * acct):
                rem.append(e); trig.add(d); continue
            taken.append(e)
        kept += taken
    return kept, rem, trig


def dstats(ent, contracts):
    bd = defaultdict(float)
    for e in ent:
        bd[day(e[0])] += contracts * e[2]
    vals = [bd[k] for k in sorted(bd)]
    eq, peak, dd = 0.0, 0.0, 0.0
    for v in vals:
        eq += v; peak = max(peak, eq); dd = max(dd, peak - eq)
    pnl = [contracts * e[2] for e in ent]
    return dict(net=sum(pnl), pf=pf(pnl), worst=min(vals) if vals else 0.0, worst5=sum(sorted(vals)[:5]), dd=dd)


def dcap1():
    p = DATA_DIR / "dcap1_result.txt"
    if p.exists():
        print("Refusing to run again"); return
    rows = load()
    rules = [("profit cap +1%", 0.01, None, False), ("profit cap +2%", 0.02, None, False), ("profit cap +3%", 0.03, None, False),
             ("loss cap -2%", None, 0.02, False), ("loss cap -4%", None, 0.04, False), ("loss cap -6%", None, 0.06, False),
             ("combined +2% / -4%", 0.02, 0.04, False), ("SPREAD1 alone", None, None, True), ("SPREAD1 + combined", 0.02, 0.04, True)]
    lines = ["DCAP1: success = in all three thirds, worst day or max drawdown cut by >= 20% AND net given up <= 25% (or net not lower if baseline <= 0)"]
    meets = []
    for uname, flt in (("all 18 series", lambda r: True), ("live five", lambda r: r["series"] in LIVE5)):
        for acct in (500.0, 1000.0):
            C = int(acct // 43)
            lines.append(f"\n{uname}, ${acct:.0f} account ({C} contracts per entry)")
            for w in range(3):
                ent = [(r["close_ts"] - LEFT, r["close_ts"], hold(r, C), (r["entry_q"][1] - r["entry_q"][0]) if r["entry_q"] else None) for r in rows if flt(r) and r["win"] == w]
                b = dstats(ent, C)
                lines.append(f"  third {w + 1} baseline: n={len(ent)} net ${b['net']:+.2f} PF {b['pf']:.3f} worst day ${b['worst']:+.2f} worst5 ${b['worst5']:+.2f} maxDD ${b['dd']:.2f}")
            for name, up, down, sp in rules:
                ok_all, parts = True, []
                for w in range(3):
                    ent = [(r["close_ts"] - LEFT, r["close_ts"], hold(r, C), (r["entry_q"][1] - r["entry_q"][0]) if r["entry_q"] else None) for r in rows if flt(r) and r["win"] == w]
                    b = dstats(ent, C)
                    k, rm, trig = run_caps(ent, C, acct, up, down, sp)
                    a = dstats(k, C)
                    gw = sum(C * e[2] for e in rm if e[2] > 0); la = -sum(C * e[2] for e in rm if e[2] < 0)
                    risk_ok = (a["worst"] >= 0.8 * b["worst"]) or (a["dd"] <= 0.8 * b["dd"])
                    net_ok = (a["net"] >= 0.75 * b["net"]) if b["net"] > 0 else (a["net"] >= b["net"])
                    ok_all = ok_all and risk_ok and net_ok
                    parts.append(f"t{w + 1}: net ${a['net']:+.2f} PF {a['pf']:.3f} worst ${a['worst']:+.2f} worst5 ${a['worst5']:+.2f} DD ${a['dd']:.2f} days {len(trig)} wins given up ${gw:.2f} losses avoided ${la:.2f} [{'risk' if risk_ok else '-'}{' net' if net_ok else ' -'}]")
                if ok_all:
                    meets.append(f"{uname} ${acct:.0f} {name}")
                lines.append(f"  {name:20s} {'MEETS DEFINITION' if ok_all else 'fails'}")
                lines += ["      " + x for x in parts]
    lines.insert(0, "DCAP1 VERDICT: " + (("meets the registered definition (risk tool, not an edge; forward read only): " + "; ".join(meets)) if meets else "FALSIFIED (no rule meets the definition in all three thirds)"))
    p.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"timex1": timex1, "dcap1": dcap1}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
