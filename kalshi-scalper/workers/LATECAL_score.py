"""LATECAL scorer (research only). Registration: workers/LATECAL_REGISTRATION.md.

Usage: python -I LATECAL_score.py <data_dir> stageA|stageB
stageA: builds the poll table, reads outcomes, prints the 32 cells on T1+T2 and the chosen cells.
stageB: prints T3 for every cell and the rule's verdict figures.
"""
import csv, glob, gzip, math, os, sys
from datetime import datetime, timedelta, timezone

MARKETS = {"KXGOLD15M": "gold", "KXBTC15M": "bitcoin"}
TIMES = [(120, 90), (90, 60), (60, 30), (30, 10)]
BANDS = [(0.50, 0.80), (0.80, 0.90), (0.90, 0.95), (0.95, 0.98)]
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def close_ts(ticker):
    part = ticker.split("-")[1]  # 26OCT291345
    y, mon, d, hh, mm = 2000 + int(part[:2]), MON[part[2:5]], int(part[5:7]), int(part[7:9]), int(part[9:11])
    et = datetime(y, mon, d, hh, mm, tzinfo=timezone(timedelta(hours=-4)))  # EDT through 2026-10-31
    return et.timestamp()


def fee_cents(p, c):
    return math.ceil(round(7 * c * p * (1 - p), 9))  # cents per order, rounded up


def load_polls(ddir):
    polls = {}
    for f in sorted(glob.glob(os.path.join(ddir, "*quotes.csv.gz"))):
        with gzip.open(f, "rt") as fh:
            for r in csv.DictReader(fh):
                t = r["ticker"]
                pre = t.split("-")[0]
                if pre not in MARKETS:
                    continue
                polls.setdefault(t, {})[int(r["t_recv_ms"])] = r
    return {t: [v[k] for k in sorted(v)] for t, v in polls.items()}


def usable(r, side):
    if r["status"] != "active":
        return None
    try:
        b, a = float(r["yes_bid"]), float(r["yes_ask"])
        bs, asz = float(r["bid_size"] or 0), float(r["ask_size"] or 0)
    except ValueError:
        return None
    if not (0 < b < a < 1):
        return None
    if side == "yes":
        return a if asz >= 1 else None
    return round(1 - b, 6) if bs >= 1 else None


def observations(polls):
    """(ticker, cell (ti, bi), side, ask, next_ask or None)."""
    out = []
    for t, rows in polls.items():
        ct = close_ts(t)
        for side in ("yes", "no"):
            for ti, (hi, lo) in enumerate(TIMES):
                done = set()
                for i, r in enumerate(rows):
                    s = ct - int(r["t_recv_ms"]) / 1000
                    if not (hi >= s > lo):
                        continue
                    p = usable(r, side)
                    if p is None:
                        continue
                    for bi, (bl, bh) in enumerate(BANDS):
                        if bi in done or not (bl <= p < bh):
                            continue
                        done.add(bi)
                        nxt = None
                        for r2 in rows[i + 1:]:
                            if ct - int(r2["t_recv_ms"]) / 1000 <= 0:
                                break
                            q = usable(r2, side)
                            if q is not None:
                                nxt = q
                                break
                        out.append((t, (ti, bi), side, p, nxt))
    return out


def load_results(ddir):
    res = {}
    for f in sorted(glob.glob(os.path.join(ddir, "*results.csv.gz"))):
        with gzip.open(f, "rt") as fh:
            for r in csv.DictReader(fh):
                if r["result"] in ("yes", "no"):
                    res[r["ticker"]] = r["result"]
    return res


def stats(obs, fill="now", stress=1.0):
    n = len(obs)
    if n == 0:
        return dict(n=0)
    wins = sum(o["win"] for o in obs)
    ps = [o["p"] for o in obs]
    sp = sum(ps)
    var = sum(p * (1 - p) for p in ps)
    z = (wins - sp) / math.sqrt(var) if var > 0 else float("nan")
    out = dict(n=n, win=wins / n, ask=sp / n, gap=(wins - sp) / n, z=z)
    for c in (1, 10):
        g = l = net = 0.0
        m = 0
        for o in obs:
            p = o["p"] if fill == "now" else o["nxt"]
            if p is None:
                continue
            m += 1
            fee = fee_cents(p, c) / 100 / c * stress
            pnl = (1 - p - fee) if o["win"] else (-p - fee)
            net += pnl
            if pnl > 0:
                g += pnl
            else:
                l -= pnl
        out[f"pf{c}"] = g / l if l > 0 else float("inf")
        out[f"net{c}"] = net / m * 100 if m else float("nan")
        out[f"m{c}"] = m
    return out


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    return (f"n {s['n']:4d} win {s['win']:.3f} ask {s['ask']:.3f} gap {s['gap']*100:+6.2f}pt z {s['z']:+5.2f} "
            f"PF1 {s['pf1']:5.2f} net1 {s['net1']:+6.2f}c PF10 {s['pf10']:5.2f} net10 {s['net10']:+6.2f}c")


def main():
    ddir, stage = sys.argv[1], sys.argv[2]
    polls = load_polls(ddir)
    res = load_results(ddir)
    third = {}
    nwin = {}
    for pre, name in MARKETS.items():
        ws = sorted([t for t in polls if t.startswith(pre + "-") and t in res], key=close_ts)
        nwin[name] = (len([t for t in polls if t.startswith(pre + "-")]), len(ws))
        k = len(ws)
        for i, t in enumerate(ws):
            third[t] = 1 + min(2, i * 3 // k)
        print(f"{name}: windows with polls {nwin[name][0]}, with result {nwin[name][1]}; "
              f"T1 {sum(1 for t in ws if third[t]==1)} T2 {sum(1 for t in ws if third[t]==2)} T3 {sum(1 for t in ws if third[t]==3)}; "
              f"T3 starts {datetime.fromtimestamp(close_ts([t for t in ws if third[t]==3][0]), timezone.utc).isoformat()}")
    raw = observations(polls)
    obs = []
    for t, cell, side, p, nxt in raw:
        if t not in res:
            continue
        obs.append(dict(t=t, m=MARKETS[t.split("-")[0]], cell=cell, side=side, p=p, nxt=nxt,
                        win=int(res[t] == side), th=third[t]))
    def sel(m, cell, ths):
        return [o for o in obs if o["m"] == m and o["cell"] == cell and o["th"] in ths]
    def label(cell):
        (hi, lo), (bl, bh) = TIMES[cell[0]], BANDS[cell[1]]
        return f"{hi:3d}-{lo:3d}s ask {bl:.2f}-{bh:.2f}"
    chosen = []
    print("\n== T1+T2 (selection set) ==")
    for m in MARKETS.values():
        for ti in range(4):
            for bi in range(4):
                c = (ti, bi)
                a = sel(m, c, {1, 2}); s1 = stats(sel(m, c, {1})); s2 = stats(sel(m, c, {2})); s = stats(a)
                ok = s["n"] >= 30 and s["gap"] >= 0.03 and s1.get("gap", -1) > 0 and s2.get("gap", -1) > 0
                tag = " CHOSEN" if ok else (" NOT_ENOUGH_DATA" if s["n"] < 30 else "")
                print(f"{m:7s} {label(c)}  {fmt(s)}  T1gap {s1.get('gap',float('nan'))*100:+.2f} T2gap {s2.get('gap',float('nan'))*100:+.2f}{tag}")
                if ok:
                    chosen.append((m, c))
    print("\nchosen:", [(m, label(c)) for m, c in chosen])
    if stage != "stageB":
        return
    print("\n== T3 (holdout) all cells, information ==")
    for m in MARKETS.values():
        for ti in range(4):
            for bi in range(4):
                c = (ti, bi)
                s = stats(sel(m, c, {3}))
                tag = " NOT_ENOUGH_DATA" if s["n"] < 30 else ""
                print(f"{m:7s} {label(c)}  {fmt(s)}{tag}")
    print("\n== all thirds pooled, per cell (information) ==")
    for m in MARKETS.values():
        for ti in range(4):
            for bi in range(4):
                c = (ti, bi)
                s = stats(sel(m, c, {1, 2, 3})); sn = stats(sel(m, c, {1, 2, 3}), fill="next")
                print(f"{m:7s} {label(c)}  {fmt(s)}  | next-poll PF1 {sn.get('pf1',float('nan')):5.2f} net1 {sn.get('net1',float('nan')):+.2f}c")
    print("\n== rule ==")
    for th in ({1}, {2}, {3}, {1, 2, 3}):
        r = [o for m, c in chosen for o in sel(m, c, th)]
        s = stats(r); sn = stats(r, fill="next"); ss = stats(r, stress=1.2)
        print(f"thirds {sorted(th)}: {fmt(s)} | next PF1 {sn.get('pf1',float('nan')):.2f} | x1.2 net1 {ss.get('net1',float('nan')):+.2f}c")


if __name__ == "__main__":
    main()
