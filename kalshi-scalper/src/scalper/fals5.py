"""FALS5: is the Bitcoin open interest core's edge the OI JUMP or the OI LEVEL regime? (research only)

Registration: workers/FALS5_REGISTRATION.md. Uses fals4's loader and trade function unchanged (same windows, same fill at the
-120 s candle's ask, same fee rounded up per order). Nothing closing on or after 2026-10-28 00:00 UTC has an outcome read;
check 4 counts signals from candles only (no result column) for the days after Oct 27.

Run: PYTHONPATH=src python -m scalper.fals5
"""
import math
import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timezone

from scalper import fals4
from scalper.fals4 import THRESH, cheap_side, dayz, pf, side_ask, signal, stage, trades
from scalper.paths import DATA_DIR

LEVEL_OFF = -360


def level(w):
    r = w["c"].get(LEVEL_OFF)
    return None if r is None else r[3]


def month(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")


def isoweek(ts):
    y, wk, _ = datetime.fromtimestamp(ts, timezone.utc).isocalendar()
    return f"{y}-W{wk:02d}"


def week_start(label):
    y, wk = label.split("-W")
    return datetime.fromisocalendar(int(y), int(wk), 1).strftime("%b %d")


def fmt_pf(nets, n_min=1):
    if len(nets) < n_min:
        return "."
    v = pf(nets)
    return "inf" if v == float("inf") else f"{v:.2f}"


def row(tr):
    """n, PF, win rate, day z for one list of trades."""
    if not tr:
        return "n 0"
    n = [t["net"] for t in tr]
    return f"n {len(tr)} PF {fmt_pf(n)} win {sum(t['won'] for t in tr)/len(tr):.0%} z {dayz(tr):.2f}"


def candidates(win):
    """{ticker: (level, doi, stage, close)} over candidate windows (valid doi, cheap side, fill candle present)."""
    out = {}
    for t, w in win.items():
        sg = signal(w)
        if sg is None or -120 not in w["c"] or cheap_side(sg["row"]) is None:
            continue
        lv = level(w)
        if lv is None:
            continue
        out[t] = (lv, sg["doi"], stage(w["close"]), w["close"])
    return out


def terciles(cand):
    """{ticker: tercile 0/1/2} by level within each UTC month of the candidate windows."""
    by_m = defaultdict(list)
    for t, (lv, _, _, close) in cand.items():
        by_m[month(close)].append((lv, t))
    out, cuts = {}, {}
    for m, xs in by_m.items():
        xs.sort()
        n = len(xs)
        c1, c2 = xs[n // 3][0], xs[(2 * n) // 3][0]
        cuts[m] = (c1, c2, n)
        for i, (lv, t) in enumerate(xs):
            out[t] = 0 if i < n // 3 else (1 if i < (2 * n) // 3 else 2)
    return out, cuts


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    if len(xs) < 3:
        return float("nan")
    return statistics.correlation(ranks(xs), ranks(ys))


def check1(win, core, base, cand):
    print("\n## Check 1: level (oi at -360 s) terciles by month")
    terc, cuts = terciles(cand)
    for m in sorted(cuts):
        c1, c2, n = cuts[m]
        print(f"{m}: {n} candidate windows, tercile cuts at level {c1:,.0f} and {c2:,.0f}")
    for st in ("disc", "val"):
        xs = [(cand[t][0], cand[t][1]) for t in cand if cand[t][2] == st]
        print(f"corr(level, doi) over {st} candidate windows: {statistics.correlation(*zip(*xs)):.2f} (n {len(xs)})")
    core_t = {t["t"] for t in core}
    names = ("bottom", "middle", "top")
    print("\n| tercile | stage | core | base (all candidates) | fire share | share of core trades | top tercile, core does NOT fire |")
    print("|---|---|---|---|---|---|---|")
    res = {}
    for k in (0, 1, 2):
        for st in ("disc", "val"):
            c = [t for t in core if t["stage"] == st and terc.get(t["t"]) == k]
            b = [t for t in base if t["stage"] == st and terc.get(t["t"]) == k]
            nc = sum(1 for t in cand if cand[t][2] == st and terc[t] == k)
            allc = sum(1 for t in core if t["stage"] == st)
            nf = [t for t in b if t["t"] not in core_t] if k == 2 else []
            res[(k, st)] = (c, b, nf)
            print(f"| {names[k]} | {st} | {row(c)} | {row(b)} | {len(c)}/{nc} = {len(c)/max(nc,1):.0%} | "
                  f"{len(c)/max(allc,1):.0%} | {row(nf) if k == 2 else ''} |")
    print("\n| non-top terciles pooled | stage | core | base |")
    print("|---|---|---|---|")
    for st in ("disc", "val"):
        c = res[(0, st)][0] + res[(1, st)][0]
        b = res[(0, st)][1] + res[(1, st)][1]
        print(f"| bottom + middle | {st} | {row(c)} | {row(b)} |")
    # reading rule
    verdict = "MIXED"
    def pfof(tr):
        return pf([t["net"] for t in tr]) if tr else float("nan")
    lvl = all(pfof(res[(2, st)][0]) >= 1.5 and len(res[(0, st)][0] + res[(1, st)][0]) >= 30
              and pfof(res[(0, st)][0] + res[(1, st)][0]) < 1.2 and pfof(res[(2, st)][2]) >= 1.4 for st in ("disc", "val"))
    jmp = all(pfof(res[(0, st)][0] + res[(1, st)][0]) >= 1.5 and pfof(res[(2, st)][2]) < 1.3 for st in ("disc", "val"))
    if lvl:
        verdict = "LEVEL"
    elif jmp:
        verdict = "JUMP"
    print(f"\nCheck 1 reading by the registered rule: **{verdict}**")
    return terc


def check2(win, core, cand):
    print("\n## Check 2: relative jump (doi / level) at the matched discovery quantile")
    allv = []   # every settled window with a valid doi, discovery
    for t, w in win.items():
        sg = signal(w)
        if sg is None or stage(w["close"]) != "disc":
            continue
        lv = level(w)
        allv.append((sg["doi"], lv))
    k = sum(1 for d, _ in allv if d > THRESH)
    rd = sorted((d / lv for d, lv in allv if lv and lv > 0), reverse=True)
    rthr = rd[k]            # exactly k discovery windows have rdoi strictly above it (bar ties)
    above = sum(1 for x in rd if x > rthr)
    print(f"discovery windows with a valid doi {len(allv)}; above 86,300: {k} ({k/len(allv):.1%}); "
          f"relative threshold {rthr:.4f} ({rthr:.1%} of oi at -360 s); above it: {above} (ties kept out)")

    def cond(w, sg):
        lv = level(w)
        return bool(lv and lv > 0 and sg["doi"] / lv > rthr)
    rel = trades(win, cond=cond)
    rel1 = trades(win, cond=cond, c=1)
    rel12 = trades(win, cond=cond, mult=1.2)
    core_t = {t["t"] for t in core}
    print("\n| relative jump | discovery | validation |")
    print("|---|---|---|")
    for lab, tr in (("C = 10", rel), ("C = 1", rel1), ("C = 10, fees x1.2", rel12)):
        print(f"| {lab} | {row([t for t in tr if t['stage']=='disc'])} | {row([t for t in tr if t['stage']=='val'])} |")
    for st in ("disc", "val"):
        x = [t for t in rel if t["stage"] == st]
        ov = sum(t["t"] in core_t for t in x)
        cst = sum(1 for t in core if t["stage"] == st)
        n = [t["net"] for t in x]
        print(f"{st}: overlap with the core {ov} of {len(x)} relative trades ({ov/max(len(x),1):.0%}); "
              f"the core's {cst} trades: {ov/max(cst,1):.0%} also relative; net ${sum(n):.2f} at C = 10; "
              f"x1.2 net ${sum(t['net'] for t in rel12 if t['stage']==st):.2f}")
        only_rel = [t for t in x if t["t"] not in core_t]
        only_core = [t for t in core if t["stage"] == st and t["t"] not in {u["t"] for u in x}]
        print(f"   only relative: {row(only_rel)}; only core: {row(only_core)}")
    # weekly firing share, relative vs absolute, over candidate windows
    wk = defaultdict(lambda: [0, 0, 0])
    rel_t = {t["t"] for t in rel}
    for t, (lv, d, st, close) in cand.items():
        w = wk[isoweek(close)]
        w[0] += 1
        w[1] += d > THRESH
        w[2] += t in rel_t
    print("\n| ISO week (Mon) | candidate windows | absolute fires | relative fires |")
    print("|---|---|---|---|")
    for k_ in sorted(wk):
        n, a, r = wk[k_]
        print(f"| {k_} ({week_start(k_)}) | {n} | {a} ({a/n:.0%}) | {r} ({r/n:.0%}) |")
    pfs = {st: pf([t["net"] for t in rel if t["stage"] == st]) for st in ("disc", "val")}
    ns = {st: sum(1 for t in rel if t["stage"] == st) for st in ("disc", "val")}
    pos12 = all(sum(t["net"] for t in rel12 if t["stage"] == st) > 0 for st in ("disc", "val"))
    killed = any(pfs[st] < 1.5 or ns[st] < 60 for st in ("disc", "val")) or not pos12
    print(f"\nCheck 2 verdict by the registered kill line: **{'FALSIFIED' if killed else 'NOT_YET_FALSIFIED'}** "
          f"(PF {pfs['disc']:.2f} / {pfs['val']:.2f}, n {ns['disc']} / {ns['val']}, positive at x1.2 in both: {pos12})")
    return rthr, rel


def check3(core, cand):
    print("\n## Check 3: per ISO week, share of candidate windows above 86,300 and the core's PF")
    wk = defaultdict(lambda: {"cand": 0, "above": 0, "lv": [], "tr": []})
    for t, (lv, d, st, close) in cand.items():
        w = wk[isoweek(close)]
        w["cand"] += 1
        w["above"] += d > THRESH
        w["lv"].append(lv)
    for t in core:
        wk[isoweek(t["close"])]["tr"].append(t)
    print("\n| ISO week (Mon) | stage | candidate windows | share above 86,300 | median level | core n | core PF | core net C = 10 |")
    print("|---|---|---|---|---|---|---|---|")
    xs, ys = [], []
    last = []
    for k in sorted(wk):
        w = wk[k]
        share = w["above"] / w["cand"]
        n = [t["net"] for t in w["tr"]]
        st = "/".join(sorted({t["stage"] for t in w["tr"]})) or "."
        p = fmt_pf(n, 10)
        if len(n) >= 10:
            xs.append(share)
            ys.append(pf(n))
            last.append(pf(n))
        print(f"| {k} ({week_start(k)}) | {st} | {w['cand']} | {share:.0%} | {statistics.median(w['lv']):,.0f} | {len(n)} | {p} | ${sum(n):.0f} |")
    rho = spearman(xs, ys)
    l3 = last[-3:]
    print(f"\nSpearman(share above, weekly PF) over {len(xs)} weeks with n >= 10: {rho:.2f}; last 3 such weeks PF {', '.join(f'{v:.2f}' for v in l3)}")
    stopped = rho < -0.6 and all(v < 1.3 for v in l3)
    print(f"Registered reading 'the fixed threshold has stopped selecting': {'YES' if stopped else 'NO'}")


def check4():
    """Signal counts per ISO week from candles only. No result column is loaded; days after Oct 27 are counted the same way."""
    print("\n## Check 4: signal rate per ISO week since Aug 4 (candles only, no outcome read)")
    start = int(datetime(2026, 8, 4, tzinfo=timezone.utc).timestamp())
    win = {}
    for f in fals4.FILES:
        con = sqlite3.connect(DATA_DIR / f)
        for t, close in con.execute("select ticker, close_ts from market where series=? and close_ts>=?", (fals4.SERIES, start)):
            if t not in win:
                win[t] = {"close": close, "c": {}, "file": f}
        for t, end, bid, ask, oi in con.execute("select ticker, end_ts, bid_c, ask_c, oi from candle where series=?", (fals4.SERIES,)):
            w = win.get(t)
            if w is None or w["file"] != f:
                continue
            off = end - w["close"]
            if off in (-360, -180, -120):
                w["c"][off] = (bid, ask, None, oi)
        con.close()
    now = max(w["close"] for w in win.values())
    print(f"windows loaded {len(win)} (settled or not; last close on file {datetime.fromtimestamp(now, timezone.utc):%Y-%m-%d %H:%M} UTC)")
    wk = defaultdict(lambda: [0, 0, 0, 0, []])
    for t, w in win.items():
        s, p = w["c"].get(-180), w["c"].get(-360)
        if s is None or p is None or s[3] is None or p[3] is None:
            continue
        d = s[3] - p[3]
        a = wk[isoweek(w["close"])]
        a[0] += 1
        a[1] += d > THRESH
        cs = cheap_side(s)
        if cs is not None and -120 in w["c"]:
            a[2] += 1
            a[3] += d > THRESH
        a[4].append(d)
    print("\n| ISO week (Mon) | windows with doi | share above 86,300 | median doi | candidate windows | signals (cheap side and above) |")
    print("|---|---|---|---|---|---|")
    for k in sorted(wk):
        n, ab, c, sg, ds = wk[k]
        note = " (part week, to the last candle on file)" if k == max(wk) else ""
        print(f"| {k} ({week_start(k)}){note} | {n} | {ab/n:.0%} | {statistics.median(ds):,.0f} | {c} | {sg} |")


def check5(win, core):
    print("\n## Check 5: same-fill honesty (reproduction and per-trade assertions)")
    for st, n_exp, pf_exp in (("disc", 222, 2.28), ("val", 333, 1.85)):
        x = [t for t in core if t["stage"] == st]
        p = pf([t["net"] for t in x])
        print(f"{st}: n {len(x)} (expected {n_exp}) PF {p:.2f} (expected {pf_exp}) -> {'ok' if len(x)==n_exp and round(p,2)==pf_exp else 'MISMATCH'}")
    bad_fill = bad_fee = zero_vol = 0
    for t in core:
        w = win[t["t"]]
        fr = w["c"][-120]
        if abs(side_ask(fr, t["side"]) - t["fill"]) > 1e-9:
            bad_fill += 1
        expected_fee = math.ceil(round(0.07 * 10 * t["fill"] * (1 - t["fill"]) * 100, 9)) / 100
        implied_fee = 10 * ((1.0 if t["won"] else 0.0) - t["fill"]) - t["net"]
        if abs(expected_fee - implied_fee) > 1e-9:
            bad_fee += 1
        if (fr[2] or 0) == 0 or (w["c"][-180][2] or 0) == 0:
            zero_vol += 1
    print(f"fill != the -120 s candle's ask of the bought side: {bad_fill} of {len(core)}; "
          f"fee != ceil(0.07 x 10 x p x (1-p)) per order: {bad_fee} of {len(core)}; zero-volume signal or fill candle: {zero_vol}")
    print("gen6.py (read for confirmation only): fee = ceil(m x 0.07 x c x p x (1-p) x 100 - 1e-9) / 100 / c (line 48); "
          "fill = _sq(nq, yes)[1], the NEXT candle's ask (line 113). Same definitions; nothing changed.")


def main():
    win = fals4.load()
    core = trades(win)
    base = trades(win, cond=lambda w, sg: True)
    cand = candidates(win)
    print(f"windows {len(win)}; candidate windows {len(cand)} "
          f"(disc {sum(v[2]=='disc' for v in cand.values())}, val {sum(v[2]=='val' for v in cand.values())}); "
          f"core trades {len(core)}; base trades {len(base)}")
    check5(win, core)
    check1(win, core, base, cand)
    check2(win, core, cand)
    check3(core, cand)
    check4()


if __name__ == "__main__":
    main()
