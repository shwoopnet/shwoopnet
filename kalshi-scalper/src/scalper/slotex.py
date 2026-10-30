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


def entries(win, fill_mode, thresh=None, cond=True):
    """(window, side, raw fill, entry candle offset) for the pure core.
    cond=False drops the OI condition (side choice and fill only)."""
    thresh = F.THRESH if thresh is None else thresh
    out = []
    for t, w in win.items():
        sg = F.signal(w)
        if sg is None or (cond and not sg["doi"] > thresh):
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


def score(e, exit_, add=0.0, mult=1.0, C=C):
    """(net $, exit kind, sell price, fees $)."""
    w, side, fill, off = e
    name, tp, sl, early = exit_
    fill = min(0.99, round(fill + add, 6))
    cost = C * fill + F.fee(fill, C, mult)
    if not early:
        won = w["result"] == side
        return C * (1.0 if won else 0.0) - cost, "hold", None, F.fee(fill, C, mult)
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
        return -cost, how, 0, F.fee(fill, C, mult)
    return (C * px - F.fee(px, C, mult) - cost, how, px,
            F.fee(fill, C, mult) + F.fee(px, C, mult))


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


BUCKETS = [("<10c", 0, 0.10), ("10-20c", 0.10, 0.20), (">20c", 0.20, 1.0)]
SIZES = (1, 5, 10)


def stage_cells(es, ex, add, mult, c):
    out = {}
    for st in ("disc", "val"):
        nets = [score(e, ex, add, mult, c)[0] for e in es if F.stage(e[0]["close"]) == st]
        out[st] = (len(nets), F.pf(nets))
    return out


def by_size():
    """Amendment 1: every variant at C = 1, 5, 10."""
    win = F.load()
    print("| fill | exit | cost | n disc/val | " + " | ".join(f"C={c} PF disc | C={c} PF val" for c in SIZES) + " |")
    print("|---|---|---|---|" + "---|---|" * len(SIZES))
    for fm in ("N", "S"):
        es = entries(win, fm)
        for ex in EXITS:
            for cn, add, mult in (("base", 0, 1), ("x1.2", 0, 1.2), ("+2c", 0.02, 1)):
                cells = [stage_cells(es, ex, add, mult, c) for c in SIZES]
                n = cells[0]
                print(f"| {fm} | {ex[0]} | {cn} | {n['disc'][0]}/{n['val'][0]} | "
                      + " | ".join(f"{x['disc'][1]:.2f} | {x['val'][1]:.2f}" for x in cells) + " |")
    print()
    print("Entry price buckets, base cost (raw entry fill). fee/ct = mean entry+sell fees per contract, cents.")
    print()
    print("| fill | exit | bucket | n disc/val | " + " | ".join(f"C={c} PF disc/val | C={c} fee/ct disc/val" for c in SIZES) + " |")
    print("|---|---|---|---|" + "---|---|" * len(SIZES))
    for fm in ("N", "S"):
        es = entries(win, fm)
        for ex in EXITS:
            for bn, lo, hi in BUCKETS:
                sub = [e for e in es if lo <= e[2] < hi]
                ns, parts = None, []
                for c in SIZES:
                    pfs, fees, cnt = [], [], []
                    for st in ("disc", "val"):
                        r = [score(e, ex, 0, 1, c) for e in sub if F.stage(e[0]["close"]) == st]
                        cnt.append(len(r))
                        pfs.append(f"{F.pf([x[0] for x in r]):.2f}" if r else "-")
                        fees.append(f"{100 * sum(x[3] for x in r) / c / len(r):.2f}" if r else "-")
                    ns = cnt
                    parts.append(f"{pfs[0]}/{pfs[1]} | {fees[0]}/{fees[1]}")
                print(f"| {fm} | {ex[0]} | {bn} | {ns[0]}/{ns[1]} | " + " | ".join(parts) + " |")


def load_series(series):
    old = F.SERIES
    F.SERIES = series
    try:
        return F.load()
    finally:
        F.SERIES = old


EXITS2 = [EXITS[0], EXITS[1]]


def eth():
    """SLOTEX-ETH (workers/SLOTEX_ETH_REGISTRATION.md)."""
    btc, eth_ = load_series("KXBTC15M"), load_series("KXETH15M")
    dv = sorted(sg["doi"] for w in eth_.values() if F.stage(w["close"]) == "disc"
                for sg in [F.signal(w)] if sg is not None)
    p90 = dv[int(0.9 * (len(dv) - 1))]
    print(f"ETH windows {len(eth_)}; discovery doi values {len(dv)}; ETH-P90 = {p90:.0f} contracts")
    ths = [("ETH-P90", p90), ("ABS", F.THRESH)]
    print()
    print("| threshold | exit | cost | n disc/val | C=5 PF disc | C=5 PF val | C=10 PF disc | C=10 PF val | C=10 net $ disc/val | nonzero bid@60s disc/val |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for tn, th in ths:
        es = entries(eth_, "N", th)
        for ex in EXITS2:
            for cn, add, mult in (("base", 0, 1), ("x1.2", 0, 1.2), ("+2c", 0.02, 1)):
                c5, c10 = stage_cells(es, ex, add, mult, 5), stage_cells(es, ex, add, mult, 10)
                nets = {st: sum(score(e, ex, add, mult, 10)[0] for e in es if F.stage(e[0]["close"]) == st) for st in ("disc", "val")}
                nz = []
                for st in ("disc", "val"):
                    sub = [e for e in es if F.stage(e[0]["close"]) == st]
                    ok = sum(1 for e in sub if e[0]["c"].get(-60) and (F.side_bid(e[0]["c"][-60], e[1]) or 0) > 0)
                    nz.append(f"{ok / len(sub):.1%}" if sub else "-")
                print(f"| {tn} | {ex[0]} | {cn} | {c5['disc'][0]}/{c5['val'][0]} | {c5['disc'][1]:.2f} | {c5['val'][1]:.2f} | "
                      f"{c10['disc'][1]:.2f} | {c10['val'][1]:.2f} | {nets['disc']:.2f}/{nets['val']:.2f} | {nz[0]}/{nz[1]} |")
    # co-loss
    bes = {e[0]["close"]: e for e in entries(btc, "N")}
    eall = {e[0]["close"]: e for e in entries(eth_, "N", cond=False)}
    print()
    print("Co-loss, C = 10 base. lost = net < 0. exp = n x pB x pE (rates within the same windows).")
    print()
    print("| pair | ETH threshold | exit | stage | n windows | BTC lost | ETH lost | both lost | exp both (indep.) | ratio | one lost | neither |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for tn, th in ths:
        efire = {e[0]["close"]: e for e in entries(eth_, "N", th)}
        for pair in ("both fired", "BTC only, ETH same side choice"):
            for ex in EXITS2:
                for st in ("disc", "val"):
                    if pair == "both fired":
                        ks = [k for k in bes if k in efire and F.stage(k) == st]
                        src = efire
                    else:
                        ks = [k for k in bes if k not in efire and k in eall and F.stage(k) == st]
                        src = eall
                    lb = [score(bes[k], ex)[0] < 0 for k in ks]
                    le = [score(src[k], ex)[0] < 0 for k in ks]
                    n = len(ks)
                    if not n:
                        print(f"| {pair} | {tn} | {ex[0]} | {st} | 0 | | | | | | | |")
                        continue
                    both = sum(a and b for a, b in zip(lb, le))
                    one = sum(a != b for a, b in zip(lb, le))
                    exp = n * (sum(lb) / n) * (sum(le) / n)
                    ratio = f"{both / exp:.2f}" if exp else "-"
                    print(f"| {pair} | {tn} | {ex[0]} | {st} | {n} | {sum(lb)} | {sum(le)} | {both} | {exp:.1f} | {ratio} | {one} | {n - both - one} |")


if __name__ == "__main__":
    import sys
    if "--eth" in sys.argv:
        eth()
    elif "--sizes" in sys.argv:
        by_size()
    else:
        main()
