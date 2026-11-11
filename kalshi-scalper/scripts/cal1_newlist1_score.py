"""CAL1 and NEWLIST1B scorer. Registration: workers/CAL1_NEWLIST1_PROTOCOL.md. One run."""
import sqlite3, json, os, re, math, datetime, sys
from collections import defaultdict
OUT = "data/cal1_newlist1_score.json"
if os.path.exists(OUT): sys.exit("already run")
def ro(f): return sqlite3.connect("file:data/%s.sqlite?mode=ro" % f, uri=True)
def fee(p): return 0.07 * p * (1 - p)
def strike(t):
    m = re.search(r"-[TB]([0-9.]+)$", t); return float(m.group(1)) if m else None
def split(dates):
    d = sorted(set(dates)); k = max(1, round(len(d) * 2 / 3)); return set(d[:k]), set(d[k:])
res = {}
# ---------- CAL1
def cand_map(c, tickers_sql, table="candle"):
    m = defaultdict(list)
    for t, e, b, a in c.execute("select ticker,end_ts,bid_c,ask_c from %s where %s" % (table, tickers_sql)):
        m[t].append((e, b, a))
    for t in m: m[t].sort()
    return m
def quote(cm, t, close, L, fresh=900):
    tt = close - L * 60; best = None
    for e, b, a in cm.get(t, ()):
        if tt - fresh < e <= tt and b is not None and a is not None: best = (b, a)
    return best
def yes_ok(q): return q is not None and 0.01 <= q[1] <= 0.99
def no_ok(q): return q is not None and q[0] >= 0.01
def ycost(q): return q[1] + fee(q[1])
def ncost(q): return (1 - q[0]) + fee(1 - q[0])
inx = ro("inx1"); xl = ro("xladder1")
U = {t: (cl, r) for t, cl, r in inx.execute("select ticker,close_ts,result from market where series='KXINXU'")}
X = {t: (cl, r) for t, cl, r in xl.execute("select ticker,close_ts,result from market")}
Ub = defaultdict(dict)
for t, (cl, r) in U.items(): Ub[cl][round(strike(t), 4)] = t
cmU = cand_map(inx, "series='KXINXU'"); cmX = cand_map(xl, "1=1")
br = {t: (k, lo, cap) for t, k, lo, cap in xl.execute("select ticker,kind,lo,cap from bracket")}
mism = 0; rows = defaultdict(list)  # (struct, L) -> (close, profit or None)
for t, (cl, r) in X.items():
    k, lo, cap = br[t]
    if cl not in Ub: continue
    for L in (60, 30, 10):
        if k == "greater":
            u = Ub[cl].get(round(strike(t), 4))
            if not u: continue
            if L == 60 and U[u][1] != r: mism += 1
            qa, qb = quote(cmX, t, cl, L), quote(cmU, u, cl, L)
            if qa is None or qb is None: rows[("I2", L)].append((cl, None)); continue
            best = None
            for A, B in ((qa, qb), (qb, qa)):
                if yes_ok(A) and no_ok(B):
                    p = 1 - ycost(A) - ncost(B); best = p if best is None or p > best else best
            rows[("I2", L)].append((cl, best))
        elif k == "between":
            ux = Ub[cl].get(round(lo - 0.0001, 4)); uh = Ub[cl].get(round(cap, 4))
            if not ux or not uh: continue
            qb, qx, qh = quote(cmX, t, cl, L), quote(cmU, ux, cl, L), quote(cmU, uh, cl, L)
            if None in (qb, qx, qh): rows[("I3", L)].append((cl, None)); continue
            best = None
            if yes_ok(qb) and yes_ok(qh) and no_ok(qx):
                best = 1 - ycost(qb) - ycost(qh) - ncost(qx)
            if yes_ok(qx) and no_ok(qb) and no_ok(qh):
                p = 2 - ycost(qx) - ncost(qb) - ncost(qh); best = p if best is None or p > best else best
            rows[("I3", L)].append((cl, best))
lc = ro("ladl1")
G = defaultdict(dict)
for t, s, cl, r in lc.execute("select ticker,series,close_ts,result from mk where series in('KXGOLDD','KXGOLDW')"):
    G[(cl, s, strike(t))] = (t, r)
Q = {(t, l): (b, a) for t, l, b, a in lc.execute("select ticker,look,bid,ask from q")}
gm = 0
for (cl, s, k), (t, r) in list(G.items()):
    if s != "KXGOLDW": continue
    d = G.get((cl, "KXGOLDD", k))
    if not d: continue
    if d[1] != r: gm += 1
    for L in (10, 6):
        qa, qb = Q.get((t, L * 60)), Q.get((d[0], L * 60))
        if qa is None or qb is None: rows[("G2", L)].append((cl, None)); continue
        best = None
        for A, B in ((qa, qb), (qb, qa)):
            if yes_ok(A) and no_ok(B):
                p = 1 - ycost(A) - ncost(B); best = p if best is None or p > best else best
        rows[("G2", L)].append((cl, best))
cal = {}
for key, rs in sorted(rows.items()):
    dev, held = split([c for c, _ in rs])
    drs = [(c, p) for c, p in rs if c in dev]
    sc = [(c, p) for c, p in drs if p is not None]
    pos = [(c, p) for c, p in sc if p > 0]
    mean_pos = sum(p for _, p in pos) / len(pos) if pos else 0
    allbest = max([p for _, p in sc], default=None)
    surv = len(sc) >= 100 and len(pos) >= 30 and len({c for c, _ in pos}) >= 10 and mean_pos >= 0.01
    verdict = "SURVIVOR_READ_HELDOUT" if surv else ("NOT_ENOUGH_DATA" if len(sc) < 100 else "FALSIFIED")
    cal["%s_L%d" % key] = dict(pairs_listed=len(rs), dev_listed=len(drs), dev_scored=len(sc), dev_positive=len(pos),
        dev_dates=len({c for c, _ in drs}), best_dev_lock_c=None if allbest is None else round(allbest * 100, 2),
        mean_pos_c=round(mean_pos * 100, 2), verdict=verdict,
        all_scored_incl_heldout_count_only=sum(1 for _, p in rs if p is not None))
cal["settle_mismatch_index"] = mism; cal["settle_mismatch_gold"] = gm
# ---------- NEWLIST1B
nl = ro("newlist1")
CUT = 1792382340  # 2026-10-19 03:59 UTC
mk = {t: (o, c, cat) for t, o, c, cat in nl.execute("select ticker,open_ts,close_ts,category from mk")}
rs_ = {t: r for t, r in nl.execute("select ticker,result from res")}
cd = defaultdict(list)
for t, e, b, a in nl.execute("select ticker,end_ts,bid,ask from cd"): cd[t].append((e, b, a))
for t in cd: cd[t].sort()
H = 3600
def priced(b, a): return b is not None and a is not None and b >= 0.01 and a <= 0.99 and a > b
def sides(b, a): return [("Y", a, b), ("N", 1 - b, 1 - a)]  # side, ask, bid
ent = defaultdict(list)  # test -> (day, net, cat, close)
for t, c in cd.items():
    if t not in mk or t not in rs_ or rs_[t] not in ("yes", "no"): continue
    o, cl, cat = mk[t]
    if cl - o < 12 * H: continue
    for T in (1, 3, 6):
        e0 = next(((e, b, a) for e, b, a in c if o + T * H <= e < o + (T + 1) * H and priced(b, a)), None)
        if not e0: continue
        e, b, a = e0
        cands = {}
        for s, ask, bid in sides(b, a):
            if 0.04 <= ask <= 0.30: cands.setdefault("C", (s, ask))
            if 0.30 < ask <= 0.88: cands.setdefault("M", (s, ask))
        for band, (s, ask) in cands.items():
            def bidof(row): return row[1] if s == "Y" else 1 - row[2]
            win = 1.0 if rs_[t] == ("yes" if s == "Y" else "no") else 0.0
            later = [row for row in c if row[0] > e and priced(row[1], row[2]) and row[0] <= cl]
            # X1
            x = next((r for r in later if r[0] >= e + 3 * H), None)
            n1 = (bidof(x) - fee(bidof(x))) if x else win
            ent[(band, T, "X1")].append((datetime.datetime.utcfromtimestamp(o).strftime("%Y-%m-%d"), n1 - ask - fee(ask), cat, cl))
            # X2
            out = None
            for r in later:
                if r[0] > e + 6 * H: break
                if bidof(r) >= ask + 0.10: out = bidof(r) - fee(bidof(r)); break
            if out is None:
                x6 = [r for r in later if e + 6 * H <= r[0]]
                out = (bidof(x6[0]) - fee(bidof(x6[0]))) if x6 else win
            ent[(band, T, "X2")].append((datetime.datetime.utcfromtimestamp(o).strftime("%Y-%m-%d"), out - ask - fee(ask), cat, cl))
def stats(rows):
    n = len(rows)
    if n < 2: return dict(n=n)
    nets = [r[1] for r in rows]; mean = sum(nets) / n
    by = defaultdict(float)
    for d, x, _, _ in rows: by[d] += x - mean
    se = math.sqrt(sum(v * v for v in by.values())) / n
    gw = sum(x for x in nets if x > 0); gl = -sum(x for x in nets if x < 0)
    return dict(n=n, mean_c=round(mean * 100, 2), pf=round(gw / gl, 2) if gl > 0 else None, z=round(mean / se, 2) if se > 0 else 0)
nlr = {}
for key, rows in sorted(ent.items()):
    dev = [r for r in rows if r[3] < CUT]
    s = stats(dev)
    ok = s["n"] >= 100 and s.get("mean_c", -1) > 0 and (s.get("pf") or 0) >= 1.5 and s.get("z", 0) >= 5.34
    s["verdict"] = "SURVIVOR_READ_HELDOUT" if ok else ("NOT_ENOUGH_DATA" if s["n"] < 100 else "FALSIFIED")
    s["held_n_count_only"] = len(rows) - len(dev)
    cats = defaultdict(list)
    for r in dev: cats[r[2]].append(r)
    s["cats_info"] = {c: stats(v) for c, v in cats.items() if len(v) >= 20}
    nlr["%s_T%d_%s" % key] = s
json.dump(dict(cal1=cal, newlist1b=nlr), open(OUT, "w"), indent=1)
print(json.dumps(cal, indent=1))
for k, v in nlr.items(): print(k, {a: b for a, b in v.items() if a != "cats_info"})
