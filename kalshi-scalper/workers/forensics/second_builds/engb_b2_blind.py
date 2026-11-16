#!/usr/bin/env python3
"""BATCH B2 (ENGB1TIMESTOP d0fa190e, ENGB2VSPIKE bcd53e01, ENGB3SPRW 653c4710), INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026).
Written from the three spec files and the conventions already confirmed with Desk A for ENGB4XBTC (SEARCH gate, VALIDATE bar, p, BH, order) ONLY. Desk A's code and prints for B2 were not opened before this file was committed.
Declared readings of the spec text (each can move a count, so each is printed in the header):
  A1 TA3/TA5: mark = the candle ending exactly e+180 / e+300; too late if that end is after close-60; no mark if absent or one sided; sell at side bid - h (floor 0.01), pays the exit fee.
  A2 VSPIKE: entry candle volume / mean volume of the 5 candles ending e-60..e-300; all 6 must exist with a volume; mean 0 = missing. Terciles per series and bucket over SEARCH markets whose entry candle is two sided AND the feature exists (cut v[ceil(n/3)-1], v[ceil(2n/3)-1]; low <= c1, mid <= c2, else high), as for spread.
  A3 SPRW: cents(ask-bid) at e minus the same at e-180, both candles two sided; class by sign.
  A4 TIMESTOP filters: none, plus up/flat/down of oi3 oi6 vol3 mom1 mom3 mom5 and low/mid/high spread (22 per bucket x band x side), exits TA3 TA5 only.
usage: python3 -I engb_b2_blind.py <TS|VS|SW> <archive_extract.sqlite> | python3 -I engb_b2_blind.py --selftest"""
import sys, os, math, sqlite3, collections, calendar, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
from shadow_rank_b2 import Mkt, cents, fee, two, side_ask, side_bid, LAST_SEARCH, klass
import engb4xbtc_b2 as E
BUCKETS = E.BUCKETS; SIDES = E.SIDES; CARRIED = 6290660
CFG = {"TS": {"exits": ("TA3", "TA5"), "tries": 782496}, "VS": {"exits": E.EXITS, "tries": 320112}, "SW": {"exits": E.EXITS, "tries": 320112}}
def vspike(m, e):
    ts = [e - 60 * i for i in range(6)]; v = [m.c.get(t) for t in ts]
    if any(x is None or x[3] is None for x in v): return None
    mean = sum(x[3] for x in v[1:]) / 5
    return None if mean == 0 else v[0][3] / mean
def swid(m, e):
    q, p = m.c.get(e), m.c.get(e - 180)
    if q is None or p is None or not two(q[0], q[1]) or not two(p[0], p[1]): return None
    return cents(q[1] - q[0]) - cents(p[1] - p[0])
def sign_class(x): return "up" if x > 0 else ("down" if x < 0 else "flat")
def tercile_cuts(vals):
    v = sorted(vals); n = len(v)
    return None if n == 0 else (v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1])
def tclass(x, cuts): return "low" if x <= cuts[0] else ("mid" if x <= cuts[1] else "high")
def nets_ta(m, B, side, h, exits):
    e = m.close - B; q = m.c[e]; b, a = q[0], q[1]
    raw = side_ask(side, b, a); paid = min(raw + h, 0.99); fin = fee(paid); out = {}
    for ex in exits:
        off = 180 if ex == "TA3" else 300; t = e + off
        if t > m.close - 60: out[ex] = None; continue
        k = m.c.get(t)
        if k is None or not two(k[0], k[1]): out[ex] = None; continue
        px = max(side_bid(side, k[0], k[1]) - h, 0.01); out[ex] = round(px * 10 - paid * 10 - fin - fee(px), 9)
    return out
def nets_gen(m, B, side, h, exits):
    if exits == ("TA3", "TA5"): return nets_ta(m, B, side, h, exits)
    return E.nets(m, B, side, h)
def work(args):
    mode, ser, mk, ls = args; exits = CFG[mode]["exits"]; res = {}
    sm = [m for m in mk if m.close < ls]
    cache = {}
    def cuts(B, kind):
        if (B, kind) not in cache:
            vals = []
            for m in sm:
                e = m.close - B; q = m.c.get(e)
                if q is None or not two(q[0], q[1]): continue
                x = cents(q[1] - q[0]) if kind == "spread" else vspike(m, e)
                if x is not None: vals.append(x)
            cache[(B, kind)] = tercile_cuts(vals)
        return cache[(B, kind)]
    for B in BUCKETS:
        cs = cuts(B, "spread") if mode == "TS" else (cuts(B, "vs") if False else None)
        cv = cuts(B, "vspike") if mode == "VS" else None
        for sr in SIDES:
            for m in mk:
                en = E.entries(m, B, sr)
                if en is None: continue
                side, ca = en; e = m.close - B; q = m.c[e]; band = ca // 5; ph = "S" if m.close < ls else "V"
                fl = []
                if mode == "TS":
                    fl.append(("none", "all"))
                    for kind in ("oi3", "oi6", "vol3", "mom1", "mom3", "mom5"):
                        x = P.feature(m, e, kind, side)
                        if x is not None: fl.append((kind, klass(x)))
                    if cs is not None: fl.append(("spread", tclass(cents(q[1] - q[0]), cs)))
                elif mode == "VS":
                    x = vspike(m, e)
                    if x is not None and cv is not None: fl.append(("vspike", tclass(x, cv)))
                else:
                    x = swid(m, e)
                    if x is not None: fl.append(("swid", sign_class(x)))
                if not fl: continue
                n1 = nets_gen(m, B, side, 0.01, exits); n2 = nets_gen(m, B, side, 0.02, exits)
                for f in fl:
                    key = (B, sr, band, f, ph); g = res.get(key)
                    if g is None: g = res[key] = {"n": 0, **{ex: ([], [], []) for ex in exits}}
                    g["n"] += 1
                    for ex in exits:
                        if n1[ex] is not None: g[ex][0].append(n1[ex]); g[ex][2].append((m.close, n1[ex]))
                        if n2[ex] is not None: g[ex][1].append(n2[ex])
    return ser, res
def selftest():
    C = 43200; e = C - 360
    m = Mkt("T", "X", C, "yes", {e: (0.88, 0.90, 0, 0, 0), e + 180: (0.93, 0.95, 0, 0, 0)})
    assert nets_ta(m, 360, "yes", 0.01, ("TA3", "TA5"))["TA3"] == round((0.92 * 10) - 0.91 * 10 - fee(0.91) - fee(0.92), 9)
    assert nets_ta(m, 360, "yes", 0.01, ("TA3", "TA5"))["TA5"] is None
    m2 = Mkt("T", "X", C, "yes", {C - 120: (0.88, 0.90, 0, 0, 0), C + 60: (0.9, 0.91, 0, 0, 0)}); assert nets_ta(m2, 120, "yes", 0.01, ("TA3",))["TA3"] is None   # e = C-120, e+180 = C+60 > close - 60
    vs = Mkt("V", "X", C, "no", {e - 60 * i: (0.5, 0.52, 0, v, 0) for i, v in enumerate([30, 10, 10, 10, 10, 10])}); assert abs(vspike(vs, e) - 3.0) < 1e-12
    vz = Mkt("V", "X", C, "no", {e - 60 * i: (0.5, 0.52, 0, v, 0) for i, v in enumerate([5, 0, 0, 0, 0, 0])}); assert vspike(vz, e) is None
    sw = Mkt("W", "X", C, "no", {e: (0.50, 0.54, 0, 0, 0), e - 180: (0.50, 0.52, 0, 0, 0)}); assert swid(sw, e) == 2 and sign_class(2) == "up" and sign_class(0) == "flat"
    assert tercile_cuts([1, 1, 2, 2, 3, 3, 4, 4, 5]) == (2, 3) and tclass(2, (2, 3)) == "low" and tclass(3, (2, 3)) == "mid" and tclass(4, (2, 3)) == "high"
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    mode = a[0]; db = sqlite3.connect("file:%s?mode=ro" % a[1], uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"): ms[tk] = Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    mk = collections.defaultdict(list)
    for m in sorted(ms.values(), key=lambda m: (m.close, m.tk)): mk[m.ser].append(m)
    sers = [s for s in sorted(LAST_SEARCH) if s in mk]; ls_of = {s: calendar.timegm(tuple(int(x) for x in LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in sers}
    exits = CFG[mode]["exits"]; tries = CFG[mode]["tries"]; m_all = CARRIED + tries
    print("mode", mode, "series scored", len(sers), "tries (spec)", tries, "carried", CARRIED, "m", m_all, flush=True)
    with multiprocessing.Pool(min(8, os.cpu_count() or 2)) as pool:
        out = dict(pool.map(work, [(mode, s, mk[s], ls_of[s]) for s in sers], chunksize=1))
    rows = []; ns = 0
    for s in sers:
        sc = [m.close for m in mk[s] if m.close < ls_of[s]]; vc = [m.close for m in mk[s] if m.close >= ls_of[s]]
        sdays = (max(sc) - min(sc)) / 86400 + 1; vdays = (max(vc) - ls_of[s]) / 86400; res = out[s]
        for (B, sr, band, f, ph), g in res.items():
            if ph != "S" or g["n"] < 100: continue
            v = res.get((B, sr, band, f, "V"))
            for ex in exits:
                x1, x2, _ = g[ex]
                if len(x1) < 100 or E.pfv(x1) < 1.3 or E.pfv(x2) < 1.0 or len(x1) / sdays < 3: continue
                ns += 1
                if v is None or v["n"] < 100: continue
                y1, y2, cn = v[ex]
                if len(y1) < 100 or E.pfv(y1) < 1.3 or E.pfv(y2) < 1.0: continue
                z, p, k = E.pval(cn); n = len(y1); spd = n / vdays; e1 = sum(y1) / (n * 10) * 100
                rows.append({"series": s, "bucket": B, "side": sr, "band": band, "filter": "%s:%s" % f, "exit": ex, "n": n, "pf1": E.pfv(y1), "pf2": E.pfv(y2), "days": k, "p": p, "spd": spd, "edge1c": e1})
    print("SEARCH passes (bar + 3 a day)", ns, "VALIDATE passes", len(rows))
    k, o = E.bh([r["p"] for r in rows], m_all); print("BH m", m_all, "survivors", k)
    rows.sort(key=lambda r: (r["series"], r["bucket"], r["band"], r["side"], r["filter"], r["exit"]))
    lines = ["series bucket band side filter exit n pf1 pf2 days p"] + ["%s %d %d %s %s %s %d %.12f %.12f %d %.12e" % (r["series"], r["bucket"], r["band"], r["side"], r["filter"], r["exit"], r["n"], r["pf1"], r["pf2"], r["days"], r["p"]) for r in rows]
    open(os.environ.get("OUTLIST", "/dev/null"), "w").write("\n".join(lines) + "\n")
if __name__ == "__main__": main(sys.argv[1:])
