#!/usr/bin/env python3
"""CMD0 to CMD4 scorer (registered in workers/CMD_COMMON.md and CMD1..4_REGISTRATION.md before it was run).
Usage: python3 -I cmd.py KALSHI_DIR CASH_CSV_GZ   (KALSHI_DIR holds <TICKER>_1m.csv.gz from fetchk.py; sessions 11-04 and later are never used)"""
import sys, gzip, csv, math, statistics as st, collections, datetime as D
KD, CASH = sys.argv[1], sys.argv[2]
PAIRS = [("gold", "KXGOLDPERP", "GC=F"), ("silver", "KXSILVERPERP", "SI=F"), ("copper", "KXCOPPERPERP", "HG=F"),
         ("WTI", "KXWTIFUTURE", "CL=F"), ("US500", "KXUS500PERP", "ES=F"), ("Tech100", "KXUSTECH100PERP", "NQ=F")]
DEV = {"2026-10-30", "2026-11-02", "2026-11-03"}; D1 = {"2026-10-30"}
DST_END = 1793512800  # 2026-11-01T06:00Z
def off(T): return -4 * 3600 if T < DST_END else -5 * 3600
def coff(T): return -5 * 3600 if T < DST_END else -6 * 3600
def sess(T): return D.datetime.fromtimestamp(T + off(T) + 6 * 3600, D.UTC).strftime("%Y-%m-%d")
def et(T): return D.datetime.fromtimestamp(T + off(T), D.UTC).strftime("%m-%d %H:%M ET")
def ct(T): return D.datetime.fromtimestamp(T + coff(T), D.UTC).strftime("%m-%d %H:%M CT")
YB = collections.defaultdict(dict)
for r in csv.DictReader(gzip.open(CASH, "rt")):
    if r["close"]: YB[r["symbol"]][int(r["ts_unix"])] = float(r["close"])
P = {}
for n, k, f in PAIRS:
    d = {}
    for r in csv.DictReader(gzip.open("%s/%s_1m.csv.gz" % (KD, k), "rt")):
        if r["ok"] == "1":
            T = int(r["ts"])
            if sess(T) in DEV or sess(T) in ("2026-10-31", "2026-11-01"): d[T] = (float(r["bid_c"]), float(r["ask_c"]))   # weekend sessions hold only perp quotes; 11-04 on is never loaded
    P[n] = d
def mid(q): return (q[0] + q[1]) / 2
def fut(f, T, s): return YB[f].get(T - 60 + 60 * s)
out = []
def pr(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
def corr(x, y):
    if len(x) < 10: return None
    mx, my = st.mean(x), st.mean(y); sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx > 0 and sy > 0 else None
# ---------------- CMD0 alignment
EV = [1793363400, 1793631600, 1793718000]  # 12:30Z 10-30, 15:00Z 11-02, 15:00Z 11-03
def argmax_T(ser, E):
    best = None
    for T in range(E - 5 * 60, E + 10 * 60 + 1, 60):
        v = ser(T)
        if v is not None and (best is None or abs(v) > best[0]): best = (abs(v), T)
    return best[1] if best else None
pmax = {}
for n, k, f in PAIRS:
    for E in EV:
        pmax[(n, E)] = argmax_T(lambda T: math.log(mid(P[n][T]) / mid(P[n][T - 60])) if T in P[n] and T - 60 in P[n] else None, E)
match = {}
for s in (-1, 0, 1):
    c = 0
    for n, k, f in PAIRS:
        for E in EV:
            fm = argmax_T(lambda T: math.log(fut(f, T, s) / fut(f, T - 60, s)) if fut(f, T, s) and fut(f, T - 60, s) else None, E)
            c += (fm is not None and fm == pmax[(n, E)])
    match[s] = c
S = 0
best = max(match.values()); cand = [s for s in (0, -1, 1) if match[s] == best]; S = cand[0]
pr("CMD0 alignment: coincident argmax minutes of 18 (pair x event) by shift s (futures bar end shifted s minutes later than the perp T):", match, "-> s =", S,
   "UNCONFIRMED" if match[S] < 9 else "confirmed")
for n, k, f in PAIRS:
    pr("  ", n, [(et(E), (pmax[(n, E)] - E) // 60 if pmax[(n, E)] else None) for E in EV], "perp argmax minute minus event, minutes")
# ---------------- lag profile
def rets(n, f):
    rp, rf = {}, {}
    for T in P[n]:
        if T - 60 in P[n]: rp[T] = math.log(mid(P[n][T]) / mid(P[n][T - 60]))
        a, b = fut(f, T, S), fut(f, T - 60, S)
        if a and b: rf[T] = math.log(a / b)
    return rp, rf
pr("\nLag profile: corr(futures return at T-k, perp return at T), k = -3..3 (k>0: futures earlier). halves D1 / D2, all")
LEADSTAT = {}
for n, k, f in PAIRS:
    rp, rf = rets(n, f)
    for lab, sel in (("D1", lambda T: sess(T) in D1), ("D2", lambda T: sess(T) not in D1), ("all", lambda T: True)):
        row = []
        for kk in range(-3, 4):
            xs = [(rf[T - 60 * kk], rp[T]) for T in rp if sel(T) and (T - 60 * kk) in rf]
            c = corr([a for a, b in xs], [b for a, b in xs]); row.append(None if c is None else round(c, 3))
        pr("  %-8s %-3s n %5d" % (n, lab, len([T for T in rp if sel(T)])), row)
        if row[3] is not None and row[4] is not None and row[2] is not None:
            LEADSTAT[(n, lab)] = row[4] - row[2]   # corr(fut T-1, perp T) - corr(fut T+1, perp T)
pr("LEAD statistic (corr futures T-1 vs perp T, minus perp T-1 vs futures T):", {k: round(v, 3) for k, v in LEADSTAT.items()})
cnt = {lab: sum(1 for n, *_ in PAIRS if LEADSTAT.get((n, lab), -1) >= 0.03) for lab in ("D1", "D2", "all")}
pr("pairs with statistic >= 0.03 of 6:", cnt)
# cash lag
pr("\nCash index lead-lag (cash hours 09:30-16:00 ET), corr(cash return at T-k, perp return at T), k=-2..2 (information only)")
for cash, n in (("^GSPC", "US500"), ("^NDX", "Tech100")):
    row = []
    for kk in range(-2, 3):
        xs = []
        for T in P[n]:
            h = D.datetime.fromtimestamp(T + off(T), D.UTC); m = h.hour * 60 + h.minute
            if not (9 * 60 + 35 <= m <= 16 * 60): continue
            a, b, c2, d2 = YB[cash].get(T - 60 - 60 * kk), YB[cash].get(T - 120 - 60 * kk), (P[n].get(T)), (P[n].get(T - 60))
            if a and b and c2 and d2: xs.append((math.log(a / b), math.log(mid(c2) / mid(d2))))
        c = corr([a for a, b in xs], [b for a, b in xs]); row.append((len(xs), None if c is None else round(c, 3)))
    pr("  ", cash, n, row)
# ---------------- basis, flags
X, DV, FLAG = {}, {}, {}
for n, k, f in PAIRS:
    x = {}
    for T, q in P[n].items():
        a = fut(f, T, S)
        if a: x[T] = math.log(mid(q) / a)
    X[n] = x; dv = {}
    for T in sorted(x):
        w = [x[T - 60 * j] for j in range(1, 61) if (T - 60 * j) in x and sess(T - 60 * j) == sess(T)]
        if len(w) >= 30: dv[T] = x[T] - st.median(w)
    DV[n] = dv; fl = set()
    for T in P[n]:
        a, b = fut(f, T, S), fut(f, T - 60, S)
        if a and b and T - 60 in P[n]:
            rf_ = math.log(a / b); rp_ = math.log(mid(P[n][T]) / mid(P[n][T - 60]))
            if abs(rf_) >= 0.003 and abs(rp_) < 0.2 * abs(rf_): fl.add(T)
    FLAG[n] = fl
def flagged(n, a, b): return any((T in FLAG[n]) for T in range(a - 3600, b + 1, 60))
def exit_q(n, T1):
    for j in range(0, 4):
        q = P[n].get(T1 + 60 * j)
        if q: return T1 + 60 * j, q
    return None
def trade(n, T, sgn, H, mintime=None):
    e = P[n].get(T); xq = exit_q(n, T + 60 * H)
    if not e or not xq: return None
    Tx, q = xq
    if sess(Tx) not in DEV: return None
    g = (q[0] / e[1] - 1) if sgn > 0 else (1 - q[1] / e[0])
    return dict(n=n, T=T, Tx=Tx, sgn=sgn, gross=g, sess=sess(Tx if False else T))
FEES = (0.0005, 0.0012, 0.0024)
def summarize(label, tr, bars=True):
    k = len(tr); cl = collections.defaultdict(list)
    for t in tr: cl[t["sess"]].append(t["gross"] - 0.0024)
    pr("==", label, "trades", k, "session clusters", len(cl))
    if not k: return
    pr("  gross after spread, before fee: mean %.2f bp, hit %.2f, break-even fee/side %.2f bp" % (st.mean(t["gross"] for t in tr) * 1e4, sum(t["gross"] > 0 for t in tr) / k, st.mean(t["gross"] for t in tr) * 1e4 / 2))
    for f in FEES: pr("  net at %2.0f bp a side: mean %.1f bp" % (f * 1e4, (st.mean(t["gross"] for t in tr) - 2 * f) * 1e4))
    for lab, sel in (("D1", lambda t: t["sess"] in D1), ("D2", lambda t: t["sess"] not in D1)):
        v = [t["gross"] - 0.0024 for t in tr if sel(t)]
        pr("  %s n %d net12 %s" % (lab, len(v), "%.1f bp" % (st.mean(v) * 1e4) if v else "-"))
    ds = [st.mean(v) for v in cl.values()]
    pr("  per-session net12 bp:", {s: round(st.mean(v) * 1e4, 1) for s, v in sorted(cl.items())}, "z", ("%.2f" % (st.mean(ds) / (st.stdev(ds) / math.sqrt(len(ds))))) if len(ds) >= 3 and st.stdev(ds) > 0 else "n/a (under 3 clusters or no variance)")
def run_r1(H, n):
    tr, skip, big, last = [], 0, 0, 0
    for T in sorted(DV[n]):
        if T < last: continue
        d = DV[n][T]
        if abs(d) > 0.01: big += 1; continue
        if abs(d) < 0.001: continue
        if sess(T) not in DEV: continue
        t = trade(n, T, -1 if d > 0 else +1, H)
        if not t: skip += 1; continue
        if flagged(n, T, t["Tx"]): skip += 1; continue
        tr.append(t); last = t["Tx"]
    return tr, skip, big
def run_r2(H, n, f):
    tr, skip, last = [], 0, 0
    for T in sorted(P[n]):
        if T < last: continue
        a, b = fut(f, T, S), fut(f, T - 60, S)
        if not (a and b and T - 60 in P[n]): continue
        rf_ = math.log(a / b)
        if abs(rf_) < 0.0005 or sess(T) not in DEV: continue
        sg = 1 if rf_ > 0 else -1; rp_ = math.log(mid(P[n][T]) / mid(P[n][T - 60]))
        if sg * rp_ >= 0.5 * abs(rf_): continue
        t = trade(n, T, sg, H)
        if not t: skip += 1; continue
        if flagged(n, T, t["Tx"]): skip += 1; continue
        tr.append(t); last = t["Tx"]
    return tr, skip
pr("\n--- CMD1 R1 basis reversion (|d| >= 10 bp, skip > 100 bp), pooled over six pairs, hold H")
CELLS = {}
for H in (5, 15, 30):
    allt, sk, bg = [], 0, 0
    for n, k, f in PAIRS:
        tr, s_, b_ = run_r1(H, n); allt += tr; sk += s_; bg += b_; CELLS[("R1", H, n)] = tr
    summarize("R1 H=%d%s" % (H, " (PRIMARY)" if H == 15 else ""), allt); pr("  skipped", sk, "bad pairs >100bp", bg)
pr("\n--- CMD1 R2 follow the futures (|futures 1m return| >= 5 bp, perp caught up < 50 percent)")
for H in (1, 5, 15):
    allt, sk = [], 0
    for n, k, f in PAIRS:
        tr, s_ = run_r2(H, n, f); allt += tr; sk += s_; CELLS[("R2", H, n)] = tr
    summarize("R2 H=%d%s" % (H, " (PRIMARY)" if H == 5 else ""), allt); pr("  skipped", sk)
# ---------------- CMD2
pr("\n--- CMD2 daily break and weekend (times ET and CT)")
def asof(n, T): return P[n].get(T)
b1 = []
for n, k, f in PAIRS:
    for T0, T1, Tx in ((1793656800, 1793660340, 1793661300),):   # Mon 11-02 17:00 ET = 22:00Z; 17:59 = 22:59Z; 18:15 = 23:15Z
        q0, q1 = asof(n, T0), asof(n, T1)
        if not (q0 and q1): pr("  B1", n, "no quote at 17:00 or 17:59 ET"); continue
        Mb = math.log(mid(q1) / mid(q0)); pass
        pr("  B1 %s break %s perp drift Mb %.1f bp" % (n, et(T0), Mb * 1e4), "TRIGGER" if abs(Mb) >= 0.001 else "below 10 bp")
        if abs(Mb) >= 0.001:
            xq = exit_q(n, Tx)
            if xq and sess(xq[0]) in DEV:
                sg = -1 if Mb > 0 else 1; e = q1; q = xq[1]
                g = (q[0] / e[1] - 1) if sg > 0 else (1 - q[1] / e[0]); b1.append(dict(n=n, T=T1, Tx=xq[0], sgn=sg, gross=g, sess=sess(xq[0])))
pr("  B1 note: Tue 11-03 break not scoreable (its 18:15 ET exit is in held-out session 11-04); Fri 10-30 17:00 is the weekend close.")
summarize("B1", b1)
b2 = []
for n, k, f in PAIRS:
    T0, T1, Tx = 1793394000, 1793573940, 1793575800   # Fri 10-30 17:00 ET = 21:00Z; Sun 11-01 17:59 ET = 22:59Z; 18:30 ET = 23:30Z
    q0, q1 = asof(n, T0), asof(n, T1)
    if not (q0 and q1): pr("  B2", n, "no quote at Fri 17:00 or Sun 17:59 ET", et(T0), et(T1)); continue
    W = math.log(mid(q1) / mid(q0)); pr("  B2 %s weekend drift W %.1f bp" % (n, W * 1e4), "TRIGGER" if abs(W) >= 0.0015 else "below 15 bp")
    if abs(W) >= 0.0015:
        xq = exit_q(n, Tx)
        if xq and sess(xq[0]) in DEV:
            sg = -1 if W > 0 else 1; e = q1; q = xq[1]
            g = (q[0] / e[1] - 1) if sg > 0 else (1 - q[1] / e[0]); b2.append(dict(n=n, T=T1, Tx=xq[0], sgn=sg, gross=g, sess=sess(xq[0])))
summarize("B2", b2)
# ---------------- CMD3
pr("\n--- CMD3 roll screen: flagged minutes (futures |1m change| >= 30 bp, perp under 20 percent of it), development")
for n, k, f in PAIRS:
    pr("  ", n, "flagged minutes", len(FLAG[n]), [ (et(T), "%.1f bp" % (math.log(fut(f, T, S) / fut(f, T - 60, S)) * 1e4)) for T in sorted(FLAG[n])][:8])
# ---------------- CMD4
pr("\n--- CMD4 break-even fee map (development only; cells under 10 trades print n only)")
pr("  %-8s %-18s %6s %12s %10s %8s %8s %8s %6s" % ("pair", "rule", "n", "gross bp", "BE fee bp", "net5", "net12", "net24", "hit"))
for n, k, f in PAIRS:
    for lab, key in (("R1 H=15", ("R1", 15, n)), ("R2 H=5", ("R2", 5, n))):
        tr = CELLS[key]; m = len(tr)
        if m < 10: pr("  %-8s %-18s %6d  (under 10 trades, no map)" % (n, lab, m)); continue
        g = st.mean(t["gross"] for t in tr) * 1e4
        pr("  %-8s %-18s %6d %12.2f %10.2f %8.1f %8.1f %8.1f %6.2f" % (n, lab, m, g, g / 2, g - 10, g - 24, g - 48, sum(t["gross"] > 0 for t in tr) / m))
open(sys.argv[0].rsplit("/", 1)[0] + "/cmd_output.txt", "w").write("\n".join(out) + "\n")
