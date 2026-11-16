#!/usr/bin/env python3
"""SHADOW RANKING, INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from Desk A's SHADOW_RANKING_SPEC_NOV16.md (sha256 45dd2ca7...) and ENGINE1_SCORING_CONVENTIONS_NOV16.md (sha256 3b6f169b...) ONLY. Desk A's engine code, rescore table and shadow list were not opened before this file was committed.
Inputs: the 190-rule listing (ENGINE1_RUN2_BARLIST_NOV16.json, sha256 16049fec...) and the archive extract (ENGINE1_archive_extract.sqlite). Steps: (1) reproduce each rule's validate n, pf_1c, pf_2c from the extract (printed difference to the listing), (2) rank by the spec: signals per day, edge, dollars a week at 5 contracts, admission, family, clusters, picks.
usage: python3 -I shadow_rank_b2.py <barlist.json> <archive_extract.sqlite> | python3 -I shadow_rank_b2.py --selftest"""
import sys, json, sqlite3, math, collections, calendar, datetime
LAST_SEARCH = {"KXBNB15M": "2026-09-03", "KXBTC15M": "2026-09-03", "KXDOGE15M": "2026-09-03", "KXETH15M": "2026-09-03", "KXGOLD15M": "2026-09-03", "KXHYPE15M": "2026-09-03", "KXNEAR15M": "2026-09-03", "KXSILVER15M": "2026-09-03",
               "KXXRP15M": "2026-09-03", "KXZEC15M": "2026-09-03", "KXSOL15M": "2026-09-07", "KXWTI15M": "2026-09-04", "KXCOPPER15M": "2026-09-13", "KXNATGAS15M": "2026-09-14", "KXEURUSD15M": "2026-09-27",
               "KXGBPUSD15M": "2026-09-27", "KXUSDJPY15M": "2026-09-27", "KXPALLADIUM15M": "2026-09-24", "KXPLATINUM15M": "2026-09-24"}
def cents(x): return math.ceil(round(100 * x, 6))
def fee(p, n=10): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100
def two(b, a): return b is not None and a is not None and 0 < b < a < 1
def day(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
class Mkt:
    def __init__(s, tk, ser, close, res, cs): s.tk, s.ser, s.close, s.res, s.c = tk, ser, close, res, cs   # cs: {end_ts: (bid, ask, last, vol, oi)}
def side_ask(side, b, a): return a if side == "yes" else 1 - b          # raw ask of the side
def side_bid(side, b, a): return b if side == "yes" else 1 - a
def side_mid(side, b, a):
    m = (b + a) / 2
    return m if side == "yes" else 1 - m
def feature(m, e, kind, side):
    c = m.c; q = c.get(e)
    if kind in ("oi3", "oi6"):
        k = 180 if kind == "oi3" else 360; p = c.get(e - k)
        if q is None or p is None or q[4] is None or p[4] is None: return None
        return q[4] - p[4]
    if kind == "vol3":
        ts = [e, e - 60, e - 120, e - 180, e - 240, e - 300]; v = [c.get(t) for t in ts]
        if any(x is None or x[3] is None for x in v): return None
        return (v[0][3] + v[1][3] + v[2][3]) - (v[3][3] + v[4][3] + v[5][3])
    if kind in ("mom1", "mom3", "mom5"):
        k = 60 * int(kind[3]); p = c.get(e - k)
        if q is None or p is None or q[0] is None or q[1] is None or p[0] is None or p[1] is None: return None
        return side_mid(side, q[0], q[1]) - side_mid(side, p[0], p[1])
    raise ValueError(kind)
def klass(x): return "up" if x > 1e-12 else ("down" if x < -1e-12 else "flat")
def terciles(markets, ser, bucket):
    v = sorted(cents(m.c[m.close - bucket][1] - m.c[m.close - bucket][0]) for m in markets if m.ser == ser and (m.close - bucket) in m.c and two(m.c[m.close - bucket][0], m.c[m.close - bucket][1]))
    n = len(v)
    if n == 0: return None
    return v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1]
def score(m, rule, h, cuts):
    """Net in dollars for 10 contracts of one market under one rule, or (None, reason)."""
    B = rule["bucket"]; e = m.close - B; q = m.c.get(e)
    if q is None or not two(q[0], q[1]): return None, "no entry candle"
    b, a = q[0], q[1]; ya, na = cents(a), cents(1 - b); sr = rule["side"]
    side = "yes" if sr == "yes" else "no" if sr == "no" else (("yes" if ya <= na else "no") if sr == "cheap" else ("yes" if ya >= na else "no"))
    ca = ya if side == "yes" else na
    if not (5 <= ca <= 94) or ca // 5 != rule["band"]: return None, "outside band"
    f = rule.get("filter")
    if f:
        kind, want = f
        if kind == "spread":
            if cuts is None: return None, "no cuts"
            s = cents(a - b); cls = "low" if s <= cuts[0] else ("mid" if s <= cuts[1] else "high")
            if cls != want: return None, "filter"
        else:
            x = feature(m, e, kind, side)
            if x is None: return None, "missing feature candle"
            if klass(x) != want: return None, "filter"
    raw = side_ask(side, b, a); paid = min(raw + h, 0.99); fin = fee(paid); ex = rule["exit"]
    def settle():
        if m.res not in ("yes", "no"): return round(0 - 0 - fin, 9) if False else round(-fin, 9)
        return round((10 if m.res == side else 0) - paid * 10 - fin, 9)
    if ex == "H": return settle(), None
    if ex in ("M180", "M60"):
        mark = m.close - (180 if ex == "M180" else 60)
        if e > mark: return None, "too late"
        k = m.c.get(mark)
        if k is None or not two(k[0], k[1]): return None, "no mark"
        px = max(side_bid(side, k[0], k[1]) - h, 0.01); return round(px * 10 - paid * 10 - fin - fee(px), 9), None
    if ex in ("T", "S", "B"):
        tgt, stp = min(2 * paid, 0.99), paid / 2
        for t in sorted(t for t in m.c if e < t <= m.close - 60):
            k = m.c[t]
            if not two(k[0], k[1]): continue
            sb = side_bid(side, k[0], k[1]); hit_t = sb >= tgt - 1e-12; hit_s = sb <= stp + 1e-12
            if (ex == "T" and hit_t) or (ex == "S" and hit_s) or (ex == "B" and (hit_t or hit_s)):
                px = max(sb - h, 0.01); return round(px * 10 - paid * 10 - fin - fee(px), 9), None
        return settle(), None
    raise ValueError(ex)
def pf(nets):
    g = sum(x for x in nets if x > 0); l = -sum(x for x in nets if x < 0)
    return g / l if l else float("inf")
def run_rule(markets, rule, phase_of, cuts_for, h):
    out = []
    for m in markets:
        if m.ser != rule["series"] or phase_of(m) != rule["phase"]: continue
        net, why = score(m, rule, h, cuts_for(m.ser, rule["bucket"]))
        if net is not None: out.append((m.close, m.tk, net))
    return sorted(out)
def family(r):
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    f = r["filter"][0] if r.get("filter") else None
    kind = "open-interest trigger" if f in ("oi3", "oi6") else "momentum or volume filter" if f in ("mom1", "mom3", "mom5", "vol3") else "spread filter" if f == "spread" else "plain band"
    return kind + " x " + ("cheap tail" if r["band"] <= 6 else "middle" if r["band"] <= 16 else "high price")
def rank(rows):
    """rows: dicts with series, bucket, band, side, filter, exit, n, pf_2c, dollars_week_1c, spd, sspd. Returns (clusters count, picks)."""
    keep = [r for r in rows if r["series"] != "KXDOGE15M" and r["spd"] >= 3 and r["sspd"] >= 3]
    for r in keep: r["family"] = family(r)
    par = list(range(len(keep)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(keep)):
        for j in range(i + 1, len(keep)):
            a, b = keep[i], keep[j]
            if a["series"] == b["series"] and a["side"] == b["side"] and a["exit"] == b["exit"] and abs(a["bucket"] - b["bucket"]) <= 60 and abs(a["band"] - b["band"]) <= 1: par[find(i)] = find(j)
    cl = collections.defaultdict(list)
    for i in range(len(keep)): cl[find(i)].append(keep[i])
    reps = []
    for g in cl.values():
        g.sort(key=lambda r: (-r["dollars_week_1c"], -r["pf_2c"], r["bucket"], r["band"], str(r["filter"]))); reps.append(g[0])
    reps.sort(key=lambda r: (-r["dollars_week_1c"], r["series"], r["bucket"], r["band"], r["side"], r["exit"], str(r["filter"])))
    picks = []; ps = collections.Counter(); pfam = collections.Counter()
    for r in reps:
        if ps[r["series"]] < 3 and pfam[r["family"]] < 5 and len(picks) < 25: picks.append(r); ps[r["series"]] += 1; pfam[r["family"]] += 1
    return len(reps), picks
def selftest():
    # hand cases from the conventions sheet (invented): market closing at 12:00:00 (close = 43200 for the arithmetic), h = 0.01, 10 contracts
    C = 43200; e = C - 360
    def mk(res, extra=None):
        cs = {e: (0.88, 0.90, 0.9, 5, 100)}; cs.update(extra or {}); return Mkt("T", "KXTST15M", C, res, cs)
    r = {"series": "KXTST15M", "bucket": 360, "band": 18, "side": "favourite", "filter": None, "exit": "H", "phase": "V"}
    assert score(mk("yes"), r, 0.01, None)[0] == 0.84 and score(mk("no"), r, 0.01, None)[0] == -9.16 and score(mk("void"), r, 0.01, None)[0] == -0.06
    r2 = dict(r, exit="M60"); assert score(mk("yes", {C - 60: (0.95, 0.96, 0.95, 1, 1)}), r2, 0.01, None)[0] == 0.20
    r3 = dict(r, exit="S"); assert score(mk("yes", {C - 180: (0.45, 0.47, 0.46, 1, 1)}), r3, 0.01, None)[0] == -4.94
    assert score(mk("yes"), dict(r, exit="M60"), 0.01, None)[1] == "no mark"
    v = [1, 1, 2, 2, 3, 3, 4, 4, 5]; mm = []
    for i, s in enumerate(v): mm.append(Mkt("S%d" % i, "KXTST15M", C + i * 900, "yes", {C + i * 900 - 360: (0.5, 0.5 + s / 100, 0.5, 1, 1)}))
    assert terciles(mm, "KXTST15M", 360) == (2, 3)
    assert abs(feature(Mkt("N", "X", C, "no", {e: (0.88, 0.90, 0, 0, 130), e - 180: (0.78, 0.82, 0, 0, 100)}), e, "oi3", "no") - 30) < 1e-12
    mmn = Mkt("N", "X", C, "no", {e: (0.88, 0.90, 0, 0, 0), e - 180: (0.78, 0.82, 0, 0, 0)}); assert abs(feature(mmn, e, "mom3", "yes") - 0.09) < 1e-12
    # ranking hand case: A (n 140, net 50.40, 5.0 a day, edge 3.6) and B (n 112, net 30.24, 4.0 a day, edge 2.7) cluster; C dropped by the 3 a day gate
    mkr = lambda band, bucket, spd, edge, f=None: {"series": "KXTST15M", "bucket": bucket, "band": band, "side": "yes", "filter": f, "exit": "H", "n": 100, "pf_2c": 1.5, "spd": spd, "sspd": spd, "dollars_week_1c": spd * edge / 100 * 35}
    A, Bq, Cq = mkr(17, 420, 5.0, 3.6), mkr(18, 480, 4.0, 2.7), mkr(17, 420, 2.5, 10.0)
    nc, picks = rank([A, Bq, Cq]); assert nc == 1 and len(picks) == 1 and abs(picks[0]["dollars_week_1c"] - 6.30) < 1e-9, (nc, picks)
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    L = json.load(open(a[0]))["validate_bar_list"]; db = sqlite3.connect("file:%s?mode=ro" % a[1], uri=True)
    series = sorted({r["series"] for r in L}); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market where series in (%s)" % ",".join("?" * len(series)), series): ms[tk] = Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    markets = sorted(ms.values(), key=lambda m: (m.close, m.tk))
    ls = {s: calendar.timegm(tuple(int(x) for x in LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in series}   # epoch of 00:00 UTC the day after the last SEARCH date
    phase_of = lambda m: "S" if m.close < ls[m.ser] else "V"
    cache = {}
    def cuts_for(ser, bucket):
        k = (ser, bucket)
        if k not in cache: cache[k] = terciles([m for m in markets if m.ser == ser and phase_of(m) == "S"], ser, bucket)
        return cache[k]
    vdays, sdays = {}, {}
    for s in series:
        v = [m.close for m in markets if m.ser == s and phase_of(m) == "V"]; sr = [m.close for m in markets if m.ser == s and phase_of(m) == "S"]
        vdays[s] = (max(v) - ls[s]) / 86400; sdays[s] = (max(sr) - min(sr)) / 86400 + 1
    rows = []; worst = 0.0; mism = 0
    for i, r in enumerate(L):
        rule = dict(r); rule["phase"] = "V"; rule["filter"] = tuple(r["filter"]) if r["filter"] else None
        n1 = run_rule(markets, rule, phase_of, cuts_for, 0.01); n2 = run_rule(markets, rule, phase_of, cuts_for, 0.02)
        x1 = [x[2] for x in n1]; x2 = [x[2] for x in n2]
        d = max(abs(pf(x1) - r["pf_1c"]), abs(pf(x2) - r["pf_2c"])) if x1 and x2 else float("inf")
        ok = len(x1) == r["n"] and len(x2) == r["n"] and d < 1e-9
        if not ok: mism += 1; print("MISMATCH rule %d %s b%d band%d %s %s %s: listing n %d pf1 %.12f pf2 %.12f | mine n %d/%d pf1 %.12f pf2 %.12f" % (i, r["series"], r["bucket"], r["band"], r["side"], r["filter"], r["exit"], r["n"], r["pf_1c"], r["pf_2c"], len(x1), len(x2), pf(x1) if x1 else -1, pf(x2) if x2 else -1))
        srule = dict(rule); srule["phase"] = "S"; sn = len(run_rule(markets, srule, phase_of, cuts_for, 0.01)); net1, net2 = sum(x1), sum(x2); n = len(x1)
        spd = n / vdays[r["series"]]; e1 = net1 / (n * 10) * 100 if n else 0.0; e2 = net2 / (n * 10) * 100 if n else 0.0
        rows.append({"series": r["series"], "bucket": r["bucket"], "band": r["band"], "side": r["side"], "filter": r["filter"], "exit": r["exit"], "n": n, "pf_2c": pf(x2) if x2 else 0.0, "spd": spd, "sspd": sn / sdays[r["series"]],
                     "edge_1c": e1, "edge_2c": e2, "dollars_week_1c": spd * e1 / 100 * 35, "dollars_week_2c": spd * e2 / 100 * 35})
    print("rules", len(L), "reproduced exactly", len(L) - mism, "mismatched", mism)
    nc, picks = rank(rows); print("clusters", nc, "picks", len(picks))
    for i, p in enumerate(picks, 1): print(i, p["series"], p["bucket"], p["band"], p["side"], p["filter"], p["exit"], p["n"], "%.9f %.9f %.9f %.9f %.9f" % (p["spd"], p["edge_1c"], p["edge_2c"], p["dollars_week_1c"], p["dollars_week_2c"]), p["family"])
if __name__ == "__main__": main(sys.argv[1:])
