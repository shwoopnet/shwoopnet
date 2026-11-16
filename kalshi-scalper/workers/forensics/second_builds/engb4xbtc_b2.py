#!/usr/bin/env python3
"""ENGB4XBTC, INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from the spec ENGB4XBTC.spec.json (sha256 fd5b5b2b...) and Desk A's convention text of 2026-11-16 18:28Z (btcmom3, SEARCH gate, VALIDATE bar, p, BH, order) ONLY.
Desk A's driver and enumerator code and prints were not opened before this file was committed. Reuses the primitives of shadow_rank_b2.py (already reproduced 190 of 190 rules exactly).
usage: python3 -I engb4xbtc_b2.py <archive_extract.sqlite> [--selftest]"""
import sys, os, math, sqlite3, collections, calendar, datetime, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
from shadow_rank_b2 import Mkt, cents, fee, two, side_ask, side_bid, LAST_SEARCH
BUCKETS = list(range(120, 841, 60)); SIDES = ("yes", "no", "cheap", "favourite"); EXITS = ("H", "T", "S", "B", "M180", "M60"); CLASSES = ("up", "flat", "down")
M_PRIOR = 2347488; BTC = "KXBTC15M"
def klass(x): return P.klass(x)
def btcmom3(btc, e):
    if btc is None: return None
    q, p = btc.c.get(e), btc.c.get(e - 180)
    if q is None or p is None or None in (q[0], q[1], p[0], p[1]): return None
    return (q[0] + q[1]) / 2 - (p[0] + p[1]) / 2
def entries(m, B, side_rule):
    """(side, ca) at the entry candle or None."""
    e = m.close - B; q = m.c.get(e)
    if q is None or not two(q[0], q[1]): return None
    b, a = q[0], q[1]; ya, na = cents(a), cents(1 - b)
    side = "yes" if side_rule == "yes" else "no" if side_rule == "no" else (("yes" if ya <= na else "no") if side_rule == "cheap" else ("yes" if ya >= na else "no"))
    ca = ya if side == "yes" else na
    return (side, ca) if 5 <= ca <= 94 else None
def nets(m, B, side, h):
    """dict exit -> net or None (10 contracts). One scan for T, S, B."""
    e = m.close - B; q = m.c[e]; b, a = q[0], q[1]
    raw = side_ask(side, b, a); paid = min(raw + h, 0.99); fin = fee(paid); out = {}
    if m.res not in ("yes", "no"): st = round(-fin, 9)
    else: st = round((10 if m.res == side else 0) - paid * 10 - fin, 9)
    out["H"] = st
    for ex, off in (("M180", 180), ("M60", 60)):
        mark = m.close - off
        if e > mark: out[ex] = None; continue
        k = m.c.get(mark)
        if k is None or not two(k[0], k[1]): out[ex] = None; continue
        px = max(side_bid(side, k[0], k[1]) - h, 0.01); out[ex] = round(px * 10 - paid * 10 - fin - fee(px), 9)
    tgt, stp = min(2 * paid, 0.99), paid / 2; ht = hs = None
    for t in sorted(t for t in m.c if e < t <= m.close - 60):
        k = m.c[t]
        if not two(k[0], k[1]): continue
        sb = side_bid(side, k[0], k[1]); it = sb >= tgt - 1e-12; is_ = sb <= stp + 1e-12
        def sell(sb=sb): px = max(sb - h, 0.01); return round(px * 10 - paid * 10 - fin - fee(px), 9)
        if it and ht is None: ht = sell()
        if is_ and hs is None: hs = sell()
        if ht is not None and hs is not None: break
    # first hit of either, in time order, for B: recompute cheaply
    first = None
    for t in sorted(t for t in m.c if e < t <= m.close - 60):
        k = m.c[t]
        if not two(k[0], k[1]): continue
        sb = side_bid(side, k[0], k[1])
        if sb >= tgt - 1e-12 or sb <= stp + 1e-12:
            px = max(sb - h, 0.01); first = round(px * 10 - paid * 10 - fin - fee(px), 9); break
    out["T"] = ht if ht is not None else st; out["S"] = hs if hs is not None else st; out["B"] = first if first is not None else st
    return out
def work(args):
    ser, markets_by_close, btc_by_close, ls = args
    mk = markets_by_close[ser]; res = {}   # key (B, side, band, cls, phase) -> {"n": entries, ex: ([h1 nets],[h2 nets], [(close,net1)])}
    for B in BUCKETS:
        for sr in SIDES:
            for m in mk:
                en = entries(m, B, sr)
                if en is None: continue
                side, ca = en; e = m.close - B
                x = btcmom3(btc_by_close.get(m.close), e)
                if x is None: continue
                ph = "S" if m.close < ls else "V"; key = (B, sr, ca // 5, klass(x), ph); g = res.get(key)
                if g is None: g = res[key] = {"n": 0, **{ex: ([], [], []) for ex in EXITS}}
                g["n"] += 1; n1 = nets(m, B, side, 0.01); n2 = nets(m, B, side, 0.02)
                for ex in EXITS:
                    if n1[ex] is not None: g[ex][0].append(n1[ex]); g[ex][2].append((m.close, n1[ex]))
                    if n2[ex] is not None: g[ex][1].append(n2[ex])
    return ser, res
def pfv(x):
    g = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0)
    return g / l if l else float("inf")
def pval(closes_nets):
    d = collections.defaultdict(float)
    for c, v in closes_nets: d[P.day(c)] += v
    k = len(d)
    if k < 2: return None, 1.0, k
    s = list(d.values()); mu = sum(s) / k; sd = math.sqrt(sum((v - mu) ** 2 for v in s) / (k - 1))
    if sd == 0: return None, 1.0, k
    z = mu / (sd / math.sqrt(k)); return z, 0.5 * math.erfc(z / math.sqrt(2)), k
def bh(ps, m):
    """ps: list of p values (rules passing VALIDATE); returns number of survivors (first k in ascending order)."""
    o = sorted(range(len(ps)), key=lambda i: (ps[i], i)); k = 0
    for r, i in enumerate(o, 1):
        if ps[i] <= 0.05 * r / m: k = r
    return k, o
def selftest():
    z, p, k = pval([(0, 3.0), (86400, 1.0), (172800, -0.5)]); assert k == 3 and abs(z - 1.15079) < 1e-4 and abs(p - 0.12491) < 1e-4, (z, p)
    assert pval([(0, 1.0)])[1] == 1.0
    assert bh([0.01, 0.5, 0.0001], 100)[0] == 1 and bh([0.0004, 0.0009, 0.5], 100)[0] == 2 and bh([0.9], 10)[0] == 0
    C = 43200; e = C - 360
    a = Mkt("A", "KXTST15M", C, "yes", {e: (0.88, 0.90, 0, 0, 0)}); bt = Mkt("B", BTC, C, "no", {e: (0.50, 0.54, 0, 0, 0), e - 180: (0.50, 0.52, 0, 0, 0)})
    assert abs(btcmom3(bt, e) - 0.01) < 1e-12 and klass(0.01) == "up" and btcmom3(None, e) is None
    assert nets(a, 360, "yes", 0.01)["H"] == 0.84 and entries(a, 360, "favourite") == ("yes", 90)
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    db = sqlite3.connect("file:%s?mode=ro" % a[0], uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"): ms[tk] = Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    ser_all = sorted({m.ser for m in ms.values()}); mk = collections.defaultdict(list)
    for m in sorted(ms.values(), key=lambda m: (m.close, m.tk)): mk[m.ser].append(m)
    btc_by_close = {m.close: m for m in mk[BTC]}
    alts = [s for s in sorted(LAST_SEARCH) if s != BTC and s in mk]; skipped = [s for s in ser_all if s not in LAST_SEARCH]
    ls_of = {s: calendar.timegm(tuple(int(x) for x in LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in alts}
    print("series in extract", len(ser_all), "alts scored", len(alts), "skipped (no split constant)", skipped, "rules", len(alts) * len(BUCKETS) * 18 * 4 * 3 * 6, flush=True)
    m_all = M_PRIOR + len(alts) * len(BUCKETS) * 18 * 4 * 3 * 6; print("m", m_all, "batch line 4,073,472", flush=True)
    with multiprocessing.Pool(min(8, os.cpu_count() or 2)) as pool:
        out = dict(pool.map(work, [(s, mk, btc_by_close, ls_of[s]) for s in alts], chunksize=1))
    rows = []; ns = 0
    for s in alts:
        sc = [m.close for m in mk[s] if m.close < ls_of[s]]; vc = [m.close for m in mk[s] if m.close >= ls_of[s]]
        sdays = (max(sc) - min(sc)) / 86400 + 1; vdays = (max(vc) - ls_of[s]) / 86400
        res = out[s]
        for (B, sr, band, cls, ph), g in res.items():
            if ph != "S" or g["n"] < 100: continue
            v = res.get((B, sr, band, cls, "V"))
            for ex in EXITS:
                x1, x2, _ = g[ex]
                if len(x1) < 100 or pfv(x1) < 1.3 or pfv(x2) < 1.0 or len(x1) / sdays < 3: continue
                ns += 1
                if v is None or v["n"] < 100: continue
                y1, y2, cn = v[ex]
                if len(y1) < 100 or pfv(y1) < 1.3 or pfv(y2) < 1.0: continue
                z, p, k = pval(cn); n = len(y1); spd = n / vdays; e1 = sum(y1) / (n * 10) * 100
                rows.append({"series": s, "bucket": B, "side": sr, "band": band, "class": cls, "exit": ex, "n": n, "pf1": pfv(y1), "pf2": pfv(y2), "days": k, "p": p, "spd": spd, "edge1c": e1, "dollars_week": spd * e1 / 100 * 35})
    print("SEARCH passes (bar + 3 a day)", ns, "VALIDATE passes", len(rows))
    for m_ in (m_all, 4073472):
        k, o = bh([r["p"] for r in rows], m_); print("BH m", m_, "survivors", k)
        if m_ == m_all:
            for i in o[:k]: r = rows[i]; print("  %s b%d %s band%d btc_%s %s n%d pf1 %.4f pf2 %.4f days%d p %.3e spd %.3f edge %.3fc $/wk %.2f" % (r["series"], r["bucket"], r["side"], r["band"], r["class"], r["exit"], r["n"], r["pf1"], r["pf2"], r["days"], r["p"], r["spd"], r["edge1c"], r["dollars_week"]))
    import json; json.dump(rows, open("/tmp/claude-0/-home-user-shwoopnet/f20c51d9-20ce-51d5-8d30-102a6cd95c3f/scratchpad/engb4xbtc_b2_validate_pass.json", "w"))
if __name__ == "__main__": main(sys.argv[1:])
