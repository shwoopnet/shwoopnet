"""HOUSE1 (README, Pre-registration: HOUSE1): trade only with the day's profit after a target. Research only.
Usage: python -m scalper.house1 run   (once)
"""
from __future__ import annotations

import sys
from collections import defaultdict

from .l1studies import fee, pf
from .paths import DATA_DIR
from .tstop1 import LEFT, LIVE5, day, load

TS = (10.0, 15.0, 25.0)
ACCTS = (500.0, 1000.0)


def per_contract(r, c):
    return r["won"] - r["price"] - fee(r["price"], c)


def simulate(rows, normal, variant, T):
    """rows of one third, sorted by entry time. Returns list of (entry_t, close_t, dollars) for orders taken."""
    byday = defaultdict(list)
    for r in rows:
        byday[day(r["close_ts"] - LEFT)].append(r)
    out = []
    for d, rs in byday.items():
        rs.sort(key=lambda r: r["close_ts"])
        taken, reached, stopped = [], False, False
        for r in rs:
            t = r["close_ts"] - LEFT
            real = sum(x[2] for x in taken if x[1] <= t)
            if variant is None:
                c = normal
            else:
                reached = reached or real >= T
                if not reached:
                    c = normal
                elif variant == "b":
                    open_after = sum(x[3] for x in taken if x[1] > t and x[4])
                    room = real - T - open_after
                    c = min(normal, int(room // r["price"])) if room > 0 else 0
                else:
                    stopped = stopped or real <= T
                    c = 0 if stopped else normal
            if c <= 0:
                continue
            taken.append((t, r["close_ts"], c * per_contract(r, c), c * r["price"], reached and variant == "b"))
        out += [(a, b, v) for a, b, v, *_ in taken]
    return out


def dstats(tr, T=None):
    bd = defaultdict(float)
    for t, c, v in tr:
        bd[day(t)] += v
    vals = [bd[k] for k in sorted(bd)]
    eq = peak = dd = 0.0
    for v in vals:
        eq += v; peak = max(peak, eq); dd = max(dd, peak - eq)
    return dict(net=sum(vals), pf=pf([v for *_, v in tr]), worst=min(vals) if vals else 0.0, neg=sum(1 for v in vals if v < 0) / max(1, len(vals)),
                mean=sum(vals) / max(1, len(vals)), dd=dd, days=len(vals))


def reached_stats(rows, normal, T, tr):
    """Days whose realised P&L reached T at some entry time, and how they finished (final day P&L)."""
    byday_all = defaultdict(list)
    for t, c, v in tr:
        byday_all[day(t)].append((t, c, v))
    n = below_t = below_0 = 0
    for d, xs in byday_all.items():
        xs.sort()
        hit = any(sum(v for t2, c2, v in xs if c2 <= t) >= T for t, _, _ in xs)
        if hit:
            n += 1; fin = sum(v for *_, v in xs)
            below_t += fin < T; below_0 += fin < 0
    return n, below_t, below_0


def main():
    if sys.argv[1:] != ["run"]:
        print(__doc__); return
    out = DATA_DIR / "house1_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    rows = [r for r in load() if r["series"] in LIVE5]
    lines, passes = [], []
    for acct in ACCTS:
        C = int(acct // 43)
        thirds = [[r for r in rows if r["win"] == w] for w in range(3)]
        base = [simulate(th, C, None, 0) for th in thirds]
        lines.append(f"\n${acct:.0f} account, {C} contracts")
        for w in range(3):
            b = dstats(base[w])
            lines.append(f"  third {w + 1} baseline: net ${b['net']:+.2f} PF {b['pf']:.3f} worst ${b['worst']:+.2f} negative days {100 * b['neg']:.0f}% mean ${b['mean']:+.2f} maxDD ${b['dd']:.2f} days {b['days']}")
        for var in ("b", "c"):
            for T in TS:
                ok, parts = True, []
                for w in range(3):
                    b = dstats(base[w]); tr = simulate(thirds[w], C, var, T); a = dstats(tr)
                    n, bt, b0 = reached_stats(thirds[w], C, T, base[w])
                    net_ok = (a["net"] >= 0.7 * b["net"]) if b["net"] > 0 else (a["net"] >= b["net"])
                    worst_ok = b["worst"] < 0 and a["worst"] >= b["worst"] * (2 / 3)
                    ok = ok and net_ok and worst_ok
                    parts.append(f"t{w + 1}: net ${a['net']:+.2f} ({100 * a['net'] / b['net'] if b['net'] else 0:.0f}% of base) PF {a['pf']:.3f} worst ${a['worst']:+.2f} neg {100 * a['neg']:.0f}% mean ${a['mean']:+.2f} DD ${a['dd']:.2f} | baseline days reaching T {n}: finished below T {bt}, below 0 {b0} [{'net' if net_ok else '-'} {'worst' if worst_ok else '-'}]")
                name = f"({var}) T=${T:.0f}"
                if ok:
                    passes.append(f"${acct:.0f} {name}")
                lines.append(f"  {name:12s} {'PASSES' if ok else 'fails'}")
                lines += ["      " + p for p in parts]
    lines.insert(0, "HOUSE1 VERDICT: " + (("meets the registered risk definition: " + "; ".join(passes)) if passes else "FALSIFIED (no rule keeps 70% of net and cuts the worst day by a third in all three thirds)"))
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
