"""STALE1 (workers/STALE1_PROTOCOL.md). Development only; held-out read only for survivors."""
import sqlite3, math, collections, sys, datetime
def fee(p): return 0.07 * p * (1 - p)
SER = {"KXSILVER15M","KXWTI15M","KXCOPPER15M","KXNATGAS15M","KXPLATINUM15M","KXPALLADIUM15M","KXEURUSD15M","KXGBPUSD15M","KXUSDJPY15M","KXAUDUSD15M","KXUSDCAD15M"}
FILES = ["data/alts2.sqlite","data/alts3.sqlite","data/alts4.sqlite","data/fresh.sqlite","data/rep.sqlite"]
mk = {}; cand = {}
for db in FILES:
    c = sqlite3.connect(db); new = {}
    for t, s, o, ct, r in c.execute("select ticker,series,open_ts,close_ts,result from market where result in ('yes','no')"):
        if s in SER and t not in mk: new[t] = (s, o, ct, r)
    if not new: continue
    for t, ts, bo, bc, ao, ac, v in c.execute("select ticker,end_ts,bid_o,bid_c,ask_o,ask_c,volume from candle"):
        if t in new: cand.setdefault(t, {})[ts] = (bo, bc, ao, ac, v or 0)
    for t, m in new.items():
        if t in cand: mk[t] = m
# PINNED per-series cuts (Nov 12, 2026): close_ts (epoch s) of the first held-out market per series, the values the Nov 11 development run
# used (two thirds of each series' 39,126-market list then). The old rule recomputed two thirds of whatever markets existed at run time.
# Held-out = ct >= cut. A series not listed has no cut and is refused.
CUTS = {"KXAUDUSD15M": 1792376100, "KXCOPPER15M": 1791865800, "KXEURUSD15M": 1792662300, "KXGBPUSD15M": 1792662300,
        "KXNATGAS15M": 1791925200, "KXPALLADIUM15M": 1792540800, "KXPLATINUM15M": 1792540800, "KXSILVER15M": 1791197100,
        "KXUSDCAD15M": 1792376100, "KXUSDJPY15M": 1792662300, "KXWTI15M": 1791305100}
bys = collections.defaultdict(list)
for t, (s, o, ct, r) in mk.items(): bys[s].append((ct, o, t))
rows = []  # one per market: (series, ct, ticker, gapclass or None)
for s, v in bys.items():
    v.sort(); cut = CUTS[s]
    for i, (ct, o, t) in enumerate(v):
        g = None
        if i > 0:
            gap = o - v[i-1][0]
            if gap >= 86400: g = "W"
            elif gap >= 1800: g = "D"
        rows.append((s, ct, t, g, ct >= cut))
print("markets", len(rows), "gap events", collections.Counter(r[3] for r in rows))
def trade(t, ct, look, band, exit_):
    c = cand[t]; o = mk[t][1]
    sig = c.get(o + look)
    nxt = c.get(o + look + 60)
    if not sig or not nxt: return None
    bo, bc, ao, ac, v = sig
    if bc is None or ac is None or bc <= 0 or ac >= 1 or ac < bc: return None
    sp = ac - bc
    if sp > 0.06: return None
    lo, hi = (0.04, 0.30) if band == "CHEAP" else (0.30, 0.88)
    if lo <= ac <= hi: side = "yes"
    elif lo <= 1 - bc <= hi: side = "no"
    else: return None
    nbo, nbc, nao, nac, nv = nxt
    if side == "yes": e = nao if nao is not None else None
    else: e = (1 - nbo) if nbo is not None else None
    if e is None or not (0 < e < 1) or e > 0.88: return None
    stale = sum(1 for k in range(60, look + 1, 60) if o + k in c and c[o + k][4] == 0)
    res = mk[t][3]
    if exit_ == "HOLD":
        net = (1.0 if res == side else 0.0) - e - fee(e)
    else:
        x = c.get(o + look + 60 + 300)
        if x is None: return None
        sell = x[1] if side == "yes" else (1 - x[3] if x[3] is not None else None)
        if sell is None: return None
        sell = max(0.0, min(1.0, sell))
        net = sell - e - fee(e) - (fee(sell) if sell > 0 else 0)
    return net, e, sp, stale
def stats(xs):
    # xs: [(day, net)] ; day-clustered z; PF
    n = len(xs)
    if n == 0: return None
    w = sum(x for _, x in xs if x > 0); l = -sum(x for _, x in xs if x < 0)
    pf = w / l if l > 0 else float("inf")
    cl = collections.defaultdict(float)
    for d, x in xs: cl[d] += x
    k = len(cl); m = sum(cl.values()) / k if k else 0
    sd = (sum((v - m) ** 2 for v in cl.values()) / (k - 1)) ** 0.5 if k > 1 else float("nan")
    z = m / (sd / k ** 0.5) if k > 1 and sd > 0 else float("nan")
    return dict(n=n, pf=round(pf, 3), mean_c=round(100 * sum(x for _, x in xs) / n, 2), z=round(z, 2), days=k)
def day(ct): return ct // 86400
SLICES = {"ALL": lambda r: True, "STALE": lambda r: r[3] >= 1, "FRESH": lambda r: r[3] == 0, "TIGHT": lambda r: r[2] <= 0.02, "WIDE": lambda r: r[2] > 0.02}
out = []
for held in (False,) if "--held" not in sys.argv else (True,):
    for cls in ("W", "D"):
        for look in (180, 300):
            for band in ("CHEAP", "MID"):
                for ex in ("HOLD", "TIME"):
                    ev = []
                    for s, ct, t, g, h in rows:
                        if g != cls or h != held: continue
                        r = trade(t, ct, look, band, ex)
                        if r: ev.append((ct, r))
                    for sl, f in SLICES.items():
                        xs = [(day(ct), r[0]) for ct, r in ev if f(r)]
                        st = stats(xs)
                        out.append((cls, look, band, ex, sl, st))
for o in out: print(*o[:5], o[5])
# control: non-gap markets, dev only, ALL slice
print("CONTROL (non-gap, dev)")
for look in (180, 300):
    for band in ("CHEAP", "MID"):
        for ex in ("HOLD", "TIME"):
            xs = []
            for s, ct, t, g, h in rows:
                if g is None and not h:
                    r = trade(t, ct, look, band, ex)
                    if r: xs.append((day(ct), r[0]))
            print(look, band, ex, stats(xs))
