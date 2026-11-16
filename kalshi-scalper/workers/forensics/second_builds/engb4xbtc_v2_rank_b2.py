#!/usr/bin/env python3
"""SHADOW_LIST_V2 RANKING, INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from SHADOW_RANKING_SPEC_NOV16.md (sha256 45dd2ca7...) and the Head's note (V2 = the ENGB4XBTC passes, Dogecoin excluded) ONLY. Desk A's V2 picker, SHADOW_LIST_V2.json and the rebuilt prints were not opened before this file was committed.
Input rows: my own 33 VALIDATE passes of ENGB4XBTC (engb4xbtc_b2.py, 6 Dogecoin rules dropped by the spec), SEARCH signals a day added; ranked by shadow_rank_b2.rank exactly as written (cluster key: series, side rule, exit, |bucket| <= 60, |band| <= 1; the filter is NOT in the key).
Declared reading (R1): the written family function knows no btcmom3, so the filter falls to 'plain band'. Both readings are printed: A = written function (plain band), B = 'cross-series filter' as its own family label; the pick list is printed for each.
usage: python3 -I engb4xbtc_v2_rank_b2.py <archive_extract.sqlite>"""
import sys, os, collections, calendar, sqlite3, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
import engb4xbtc_b2 as E
def build_rows(db_path):
    db = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"): ms[tk] = P.Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    mk = collections.defaultdict(list)
    for m in sorted(ms.values(), key=lambda m: (m.close, m.tk)): mk[m.ser].append(m)
    btc = {m.close: m for m in mk[E.BTC]}; alts = [s for s in sorted(P.LAST_SEARCH) if s != E.BTC and s in mk]
    ls_of = {s: calendar.timegm(tuple(int(x) for x in P.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in alts}
    with multiprocessing.Pool(min(8, os.cpu_count() or 2)) as pool: out = dict(pool.map(E.work, [(s, mk, btc, ls_of[s]) for s in alts], chunksize=1))
    rows = []
    for s in alts:
        sc = [m.close for m in mk[s] if m.close < ls_of[s]]; vc = [m.close for m in mk[s] if m.close >= ls_of[s]]
        sdays = (max(sc) - min(sc)) / 86400 + 1; vdays = (max(vc) - ls_of[s]) / 86400; res = out[s]
        for (B, sr, band, cls, ph), g in res.items():
            if ph != "S" or g["n"] < 100: continue
            v = res.get((B, sr, band, cls, "V"))
            for ex in E.EXITS:
                x1, x2, _ = g[ex]
                if len(x1) < 100 or E.pfv(x1) < 1.3 or E.pfv(x2) < 1.0 or len(x1) / sdays < 3: continue
                if v is None or v["n"] < 100: continue
                y1, y2, cn = v[ex]
                if len(y1) < 100 or E.pfv(y1) < 1.3 or E.pfv(y2) < 1.0: continue
                n = len(y1); spd = n / vdays; e1 = sum(y1) / (n * 10) * 100; e2 = sum(y2) / (n * 10) * 100
                rows.append({"series": s, "bucket": B, "band": band, "side": sr, "filter": ("btcmom3", cls), "exit": ex, "n": n, "pf_2c": E.pfv(y2), "spd": spd, "sspd": len(x1) / sdays,
                             "edge_1c": e1, "edge_2c": e2, "dollars_week_1c": spd * e1 / 100 * 35, "dollars_week_2c": spd * e2 / 100 * 35})
    return rows
def show(tag, rows):
    nc, picks = P.rank([dict(r) for r in rows]); print(tag, "clusters", nc, "picks", len(picks))
    for i, p in enumerate(picks, 1): print(i, p["series"], p["bucket"], p["band"], p["side"], p["filter"], p["exit"], p["n"], "%.9f %.9f %.9f %.9f %.9f" % (p["spd"], p["edge_1c"], p["edge_2c"], p["dollars_week_1c"], p["dollars_week_2c"]), p["family"])
def main(a):
    rows = build_rows(a[0]); print("passes", len(rows), "Dogecoin", sum(1 for r in rows if r["series"] == "KXDOGE15M"))
    show("A (written family function)", rows)
    orig = P.family
    P.family = lambda r: ("cross-series filter x " + ("cheap tail" if r["band"] <= 6 else "middle" if r["band"] <= 16 else "high price")) if r["band"] < 17 or r["bucket"] > 600 else "F1 favourite-late shape"
    show("B (cross-series family label)", rows); P.family = orig
if __name__ == "__main__": main(sys.argv[1:])
