"""SLOTEX: slot-legal (pre-settlement) exits for GEN6's pure OI core on KXBTC15M.

Research only. Reuses fals4's loader, signal and fee. See
workers/SLOTEX_REGISTRATION.md. Run: PYTHONPATH=src python -m scalper.slotex
"""
from scalper import fals4 as F

C = 10
EXITS = [("HOLD", None, None, False), ("X60", None, None, True),
         ("TP5", 0.05, None, True), ("TP8", 0.08, None, True),
         ("TP5/SL2", 0.05, 0.02, True), ("TP5/SL3", 0.05, 0.03, True),
         ("TP5/SL4", 0.05, 0.04, True)]


def entries(win, fill_mode):
    """(window, side, raw fill, entry candle offset) for the pure core."""
    out = []
    for t, w in win.items():
        sg = F.signal(w)
        if sg is None or not sg["doi"] > F.THRESH:
            continue
        side = F.cheap_side(sg["row"])
        if side is None:
            continue
        off = -120 if fill_mode == "N" else -180
        fr = w["c"].get(off)
        if fr is None:
            continue
        fill = F.side_ask(fr, side)
        if fill is None or fill <= 0 or fill >= 1:
            continue
        out.append((w, side, fill, off))
    return out


def score(e, exit_, add=0.0, mult=1.0):
    w, side, fill, off = e
    name, tp, sl, early = exit_
    fill = min(0.99, round(fill + add, 6))
    cost = C * fill + F.fee(fill, C, mult)
    if not early:
        won = w["result"] == side
        return C * (1.0 if won else 0.0) - cost, "hold", None
    how, px = None, None
    for o in range(off + 60, -59, 60):
        r = w["c"].get(o)
        b = F.side_bid(r, side) if r else None
        if o == -60:
            how, px = "x60", b
        if b is None or b <= 0:
            if o == -60:
                break
            continue
        if sl is not None and b <= fill - sl + 1e-9:
            how, px = "stop", b
            break
        if tp is not None and b >= fill + tp - 1e-9:
            how, px = "tp", b
            break
    if px is None or px <= 0:
        return -cost, how, 0
    return C * px - F.fee(px, C, mult) - cost, how, px


def main():
    win = F.load()
    rows = []
    for fm in ("N", "S"):
        es = entries(win, fm)
        for ex in EXITS:
            for cost_name, add, mult in (("base", 0, 1), ("x1.2", 0, 1.2), ("+2c", 0.02, 1)):
                cells = []
                for st in ("disc", "val"):
                    sub = [e for e in es if F.stage(e[0]["close"]) == st]
                    res = [score(e, ex, add, mult) for e in sub]
                    nets = [r[0] for r in res]
                    k = len(res) or 1
                    mix = {h: sum(1 for r in res if r[1] == h) / k for h in ("tp", "stop", "x60")}
                    nz = sum(1 for e in sub if (lambda r: r is not None and (F.side_bid(r, e[1]) or 0) > 0)(e[0]["c"].get(-60))) / k
                    cells.append((len(res), F.pf(nets), sum(nets), mix, nz))
                rows.append((fm, ex[0], cost_name, cells))
    print("| fill | exit | cost | disc n | disc PF | disc net $ | val n | val PF | val net $ | exit mix disc (tp/stop/60s) | exit mix val | nonzero bid@60s disc/val |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for fm, ex, cn, (d, v) in rows:
        mx = lambda c: "-" if ex == "HOLD" else f"{c[3]['tp']:.0%}/{c[3]['stop']:.0%}/{c[3]['x60']:.0%}"
        print(f"| {fm} | {ex} | {cn} | {d[0]} | {d[1]:.2f} | {d[2]:.2f} | {v[0]} | {v[1]:.2f} | {v[2]:.2f} | {mx(d)} | {mx(v)} | {d[4]:.1%}/{v[4]:.1%} |")


if __name__ == "__main__":
    main()
