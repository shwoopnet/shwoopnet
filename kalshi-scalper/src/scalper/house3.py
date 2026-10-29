"""HOUSE3 (README, Pre-registration: HOUSE3): loss timing gate, then a cooldown after a loss. Research only.
Usage: python -m scalper.house3 run   (once)
"""
from __future__ import annotations

import math
import sys
from bisect import bisect_right
from collections import defaultdict

from .house1 import dstats
from .house2 import ACCTS, pnl
from .paths import DATA_DIR
from .tstop1 import LEFT, LIVE5, day, load

NS = (15, 30, 60, 120, 240)
NAMES = {"KXGOLD15M": "gold", "KXBTC15M": "Bitcoin", "KXETH15M": "Ethereum", "KXDOGE15M": "Dogecoin", "KXXRP15M": "XRP"}


def z2(a, n1, b, n2):
    if n1 == 0 or n2 == 0:
        return 0.0
    p1, p2 = a / n1, b / n2
    p = (a + b) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else 0
    return (p1 - p2) / se if se else 0.0


def timing(rows):
    lost = lambda r: r["won"] < 0.5
    rows = sorted(rows, key=lambda r: r["close_ts"] - LEFT)
    ent = [r["close_ts"] - LEFT for r in rows]
    U = sum(lost(r) for r in rows); n = len(rows)
    lines, zmax = [f"  unconditional loss rate {100 * U / n:.2f}% (n {n})"], -9.0
    for scope in ("any market", "same market"):
        for N in NS:
            hit = tot = 0
            for r in rows:
                if not lost(r):
                    continue
                c = r["close_ts"]
                i = bisect_right(ent, c)   # entered strictly after the loss settled
                for q in rows[i:]:
                    if q["close_ts"] > c + N * 60:
                        if q["close_ts"] - LEFT > c + N * 60:
                            break
                        continue
                    if scope == "same market" and q["series"] != r["series"]:
                        continue
                    tot += 1; hit += lost(q)
            z = z2(hit, tot, U, n)
            if scope == "any market":
                zmax = max(zmax, z)
            lines.append(f"  {scope:11s} within {N:3d} min after a loss: loss rate {100 * hit / max(1, tot):.2f}% (n {tot}), z {z:+.2f}")
    by_w = defaultdict(list)
    for r in rows:
        by_w[r["close_ts"]].append(r)
    co = cn = 0
    for c, rs in by_w.items():
        if len(rs) < 2:
            continue
        for r in rs:
            if lost(r):
                others = [q for q in rs if q is not r]
                cn += len(others); co += sum(lost(q) for q in others)
    lines.append(f"  same window (entered before the loss was known): others lost {100 * co / max(1, cn):.2f}% (n {cn}) against {100 * U / n:.2f}%, z {z2(co, cn, U, n):+.2f}")
    return lines, zmax


def simulate(rows, base, N, scope, ladder, m=1.0):
    cap = base + base // 4
    byday = defaultdict(list)
    for r in rows:
        byday[day(r["close_ts"] - LEFT)].append(r)
    out, skipped = [], []
    for d, rs in byday.items():
        rs.sort(key=lambda r: r["close_ts"])
        taken = []   # (entry_t, close_t, dollars, series)
        for r in rs:
            t = r["close_ts"] - LEFT
            done = [x for x in taken if x[1] <= t]
            losses = [x for x in done if x[2] < 0 and (scope == "a" or x[3] == r["series"])]
            if N is not None and any(t < x[1] + N * 60 for x in losses):
                skipped.append((t, r["close_ts"], pnl(r, base, m)))
                continue
            c = base
            if ladder:
                last_end = max((x[1] + N * 60 for x in done if x[2] < 0), default=-1)
                wins = sum(1 for x in done if x[2] > 0 and x[1] > last_end)
                c = min(cap, base + wins)
            taken.append((t, r["close_ts"], pnl(r, c, m), r["series"]))
        out += [(a, b, v) for a, b, v, _ in taken]
    return out, skipped


def main():
    if sys.argv[1:] != ["run"]:
        print(__doc__); return
    out = DATA_DIR / "house3_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    rows = [r for r in load() if r["series"] in LIVE5]
    lines = ["Part 1, loss timing, live five pooled:"]
    tl, zmax = timing(rows); lines += tl
    for s, nm in NAMES.items():
        sub, _ = timing([r for r in rows if r["series"] == s])
        lines.append(f" {nm}:"); lines += sub
    gate = zmax >= 2.0
    lines.append(f"GATE: max pooled any-market z {zmax:+.2f}: " + ("conditional loss rate is higher, cooldown can help in principle" if gate else "no conditional loss rate above the unconditional one by z 2: every cooldown is FALSIFIED by the registered gate"))
    thirds = [[r for r in rows if r["win"] == w] for w in range(3)]
    passes = []
    for acct, base in ACCTS.items():
        lines.append(f"\n${acct:.0f}, base {base}")
        bases = [dstats(simulate(th, base, None, "a", False)[0]) for th in thirds]
        for w, b in enumerate(bases):
            lines.append(f"  third {w + 1} baseline net ${b['net']:+.2f} worst ${b['worst']:+.2f} neg {100 * b['neg']:.0f}% DD ${b['dd']:.2f}")
        for scope in ("a", "b"):
            for ladder in (False, True):
                for N in NS:
                    ok, parts = True, []
                    for w in range(3):
                        b = bases[w]; tr, sk = simulate(thirds[w], base, N, scope, ladder); a = dstats(tr)
                        net_ok = (a["net"] >= 0.7 * b["net"]) if b["net"] > 0 else (a["net"] >= b["net"])
                        worst_ok = b["worst"] < 0 and a["worst"] >= b["worst"] * (2 / 3)
                        ok = ok and net_ok and worst_ok
                        parts.append(f"t{w + 1} kept {100 * a['net'] / b['net'] if b['net'] else 0:.0f}% worst ${a['worst']:+.2f} neg {100 * a['neg']:.0f}% DD ${a['dd']:.2f} skipped {len(sk)} worth ${sum(v for *_, v in sk):+.2f}")
                    ok = ok and gate
                    name = f"scope {scope} {'ladder' if ladder else 'base'} {N:3d} min"
                    if ok:
                        passes.append(f"${acct:.0f} {name}")
                    lines.append(f"  {name}: {'PASSES' if ok else 'fails'} | " + " | ".join(parts))
    lines.insert(0, "HOUSE3 VERDICT: " + (("meets the registered risk definition: " + "; ".join(passes)) if passes else "FALSIFIED"))
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
