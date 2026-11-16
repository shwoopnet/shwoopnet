#!/usr/bin/env python3
"""SHADOW LIST V3 RANKING, INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from SHADOW_RANKING_SPEC_NOV16.md (sha256 45dd2ca7...) and the Head's note (clusters, caps, 3 a day, Dogecoin exclusion, H09 start for the Bitcoin-market picks) ONLY.
Desk A's V3 picker code and SHADOW_LIST_V3.json were not opened before this file was committed.
Input rows: my own VALIDATE passes of batch B2 (ENGB1TIMESTOP, ENGB2VSPIKE, ENGB3SPRW) from engb_b2_blind.py, with SEARCH signals a day added; ranked by shadow_rank_b2.rank (reproduced V1's 190 rules and 17 picks exactly).
Declared readings: (R1) family labels for the new filters: vspike counts as 'momentum or volume filter', swid as 'spread filter', filter none as 'plain band'; (R2) the Bitcoin-market picks (series KXBTC15M) get start_utc 1795219200 (2026-11-21T00:00Z, H09), every other pick starts at the freeze.
usage: python3 -I engb_v3_rank_b2.py <archive_extract.sqlite>"""
import sys, os, collections, calendar, sqlite3, multiprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
import engb4xbtc_b2 as E
import engb_b2_blind as G
START_BTC = calendar.timegm((2026, 11, 21, 0, 0, 0))
def family(r):
    f = r["filter"][0] if r.get("filter") else None
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    kind = "open-interest trigger" if f in ("oi3", "oi6") else "momentum or volume filter" if f in ("mom1", "mom3", "mom5", "vol3", "vspike") else "spread filter" if f in ("spread", "swid") else "plain band"
    return kind + " x " + ("cheap tail" if r["band"] <= 6 else "middle" if r["band"] <= 16 else "high price")
P.family = family
def rows_for(mode, mk, ls_of, sers, db_path):
    G.CFG[mode]
    exits = G.CFG[mode]["exits"]
    with multiprocessing.Pool(min(8, os.cpu_count() or 2)) as pool:
        out = dict(pool.map(G.work, [(mode, s, mk[s], ls_of[s]) for s in sers], chunksize=1))
    rows = []
    for s in sers:
        sc = [m.close for m in mk[s] if m.close < ls_of[s]]; vc = [m.close for m in mk[s] if m.close >= ls_of[s]]
        sdays = (max(sc) - min(sc)) / 86400 + 1; vdays = (max(vc) - ls_of[s]) / 86400; res = out[s]
        for (B, sr, band, f, ph), g in res.items():
            if ph != "S" or g["n"] < 100: continue
            v = res.get((B, sr, band, f, "V"))
            for ex in exits:
                x1, x2, _ = g[ex]
                if len(x1) < 100 or E.pfv(x1) < 1.3 or E.pfv(x2) < 1.0 or len(x1) / sdays < 3: continue
                if v is None or v["n"] < 100: continue
                y1, y2, cn = v[ex]
                if len(y1) < 100 or E.pfv(y1) < 1.3 or E.pfv(y2) < 1.0: continue
                n = len(y1); spd = n / vdays; e1 = sum(y1) / (n * 10) * 100; e2 = sum(y2) / (n * 10) * 100
                rows.append({"series": s, "bucket": B, "band": band, "side": sr, "filter": f, "exit": ex, "n": n, "pf_2c": E.pfv(y2), "spd": spd, "sspd": len(x1) / sdays,
                             "edge_1c": e1, "edge_2c": e2, "dollars_week_1c": spd * e1 / 100 * 35, "dollars_week_2c": spd * e2 / 100 * 35})
    return rows
def main(a):
    db = sqlite3.connect("file:%s?mode=ro" % a[0], uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"): ms[tk] = P.Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    mk = collections.defaultdict(list)
    for m in sorted(ms.values(), key=lambda m: (m.close, m.tk)): mk[m.ser].append(m)
    sers = [s for s in sorted(P.LAST_SEARCH) if s in mk]; ls_of = {s: calendar.timegm(tuple(int(x) for x in P.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in sers}
    rows = []
    for mode in ("TS", "VS", "SW"):
        r = rows_for(mode, mk, ls_of, sers, a[0]); print("mode", mode, "VALIDATE passes", len(r), flush=True); rows += r
    print("pooled passes", len(rows), "Dogecoin dropped", sum(1 for r in rows if r["series"] == "KXDOGE15M"))
    nc, picks = P.rank(rows); print("clusters", nc, "picks", len(picks))
    for i, p in enumerate(picks, 1):
        st = START_BTC if p["series"] == "KXBTC15M" else 0
        print(i, p["series"], p["bucket"], p["band"], p["side"], p["filter"], p["exit"], p["n"], "%.9f %.9f %.9f %.9f %.9f" % (p["spd"], p["edge_1c"], p["edge_2c"], p["dollars_week_1c"], p["dollars_week_2c"]), p["family"], "start_epoch", st or "freeze")
if __name__ == "__main__": main(sys.argv[1:])
