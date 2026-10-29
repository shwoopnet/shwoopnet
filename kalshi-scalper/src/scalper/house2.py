"""HOUSE2 (README, Pre-registration: HOUSE2): step the size up after wins, stop for the day after a loss. Research only.
Usage: python -m scalper.house2 run   (once)
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict

from .house1 import dstats
from .l1studies import fee
from .paths import DATA_DIR
from .tstop1 import LEFT, LIVE5, day, load

ACCTS = {500.0: 13, 1000.0: 23}


def pnl(r, c, m=1.0):
    return c * (r["won"] - r["price"]) - m * c * fee(r["price"], c)


def size_for(step, base, cap, wins, profit, price):
    if step is None:
        return base
    if step == "S1":
        c = base + wins
    elif step == "S2":
        c = int(base * 1.25 ** wins)
    else:
        c = base + (int(profit // price) if profit > 0 else 0)
    return min(cap, c)


def simulate(rows, base, step, stop, m=1.0):
    cap = base + base // 4
    byday = defaultdict(list)
    for r in rows:
        byday[day(r["close_ts"] - LEFT)].append(r)
    out, top_losses, losses = [], 0, 0
    for d, rs in byday.items():
        rs.sort(key=lambda r: r["close_ts"])
        taken = []   # (entry_t, close_t, dollars, contracts)
        for r in rs:
            t = r["close_ts"] - LEFT
            done = [x for x in taken if x[1] <= t]
            real = sum(x[2] for x in done)
            wins = sum(1 for x in done if x[2] > 0)
            nloss = sum(1 for x in done if x[2] < 0)
            if stop == "K1" and nloss >= 1:
                continue
            if stop == "K2" and nloss >= 2:
                continue
            if stop == "K3" and nloss >= 1:
                # stop once any settled loss has left the day's realised P&L at or below zero
                run, hit = 0.0, False
                for x in sorted(done, key=lambda x: x[1]):
                    run += x[2]
                    if x[2] < 0 and run <= 0:
                        hit = True
                if hit:
                    continue
            c = size_for(step, base, cap, wins, real, r["price"])
            v = pnl(r, c, m)
            taken.append((t, r["close_ts"], v, c))
            if v < 0:
                losses += 1
                top_losses += c >= cap and step is not None
        out += [(a, b, v) for a, b, v, _ in taken]
    return out, top_losses, losses


def first_loss_stats(rows, base):
    byday = defaultdict(list)
    for r in rows:
        byday[day(r["close_ts"] - LEFT)].append(r)
    zero, before = 0, []
    for d, rs in byday.items():
        rs.sort(key=lambda r: r["close_ts"])
        idx = next((i for i, r in enumerate(rs) if pnl(r, base) < 0), None)
        if idx is None:
            zero += 1
        else:
            before.append(idx)
    return zero / max(1, len(byday)), (st.median(before) if before else 0)


def main():
    if sys.argv[1:] != ["run"]:
        print(__doc__); return
    out = DATA_DIR / "house2_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    rows = [r for r in load() if r["series"] in LIVE5]
    thirds = [[r for r in rows if r["win"] == w] for w in range(3)]
    lines, passes = [], []
    for acct, base in ACCTS.items():
        lines.append(f"\n${acct:.0f} account, base {base}, cap {base + base // 4}")
        bases = [simulate(th, base, None, None)[0] for th in thirds]
        for w in range(3):
            b = dstats(bases[w]); z, med = first_loss_stats(thirds[w], base)
            lines.append(f"  third {w + 1} baseline: net ${b['net']:+.2f} PF {b['pf']:.3f} mean ${b['mean']:+.2f} worst ${b['worst']:+.2f} negative days {100 * b['neg']:.0f}% maxDD ${b['dd']:.2f}; days with no loss {100 * z:.0f}%, median trades before the first loss {med}")
        for step in ("S1", "S2", "S3"):
            for stop in ("K1", "K2", "K3"):
                ok, parts = True, []
                for w in range(3):
                    b = dstats(bases[w])
                    tr, top, nl = simulate(thirds[w], base, step, stop)
                    a = dstats(tr); s12 = dstats(simulate(thirds[w], base, step, stop, 1.2)[0])
                    net_ok = (a["net"] >= 0.7 * b["net"]) if b["net"] > 0 else (a["net"] >= b["net"])
                    worst_ok = b["worst"] < 0 and a["worst"] >= b["worst"] * (2 / 3)
                    ok = ok and net_ok and worst_ok
                    parts.append(f"t{w + 1}: net ${a['net']:+.2f} ({100 * a['net'] / b['net'] if b['net'] else 0:.0f}% kept) PF {a['pf']:.3f} mean ${a['mean']:+.2f} worst ${a['worst']:+.2f} neg {100 * a['neg']:.0f}% DD ${a['dd']:.2f}; losses at the top rung {top} of {nl}; fees x1.2 net ${s12['net']:+.2f} [{'net' if net_ok else '-'} {'worst' if worst_ok else '-'}]")
                if ok:
                    passes.append(f"${acct:.0f} {step}{stop}")
                lines.append(f"  {step} {stop} {'PASSES' if ok else 'fails'}")
                lines += ["      " + p for p in parts]
    lines.insert(0, "HOUSE2 VERDICT: " + (("meets the registered risk definition: " + "; ".join(passes)) if passes else "FALSIFIED (no rule keeps 70% of net and cuts the worst day by a third in all three thirds)"))
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
