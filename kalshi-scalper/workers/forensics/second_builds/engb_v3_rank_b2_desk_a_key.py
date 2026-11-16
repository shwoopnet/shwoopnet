#!/usr/bin/env python3
"""V3 ranking, variant of engb_v3_rank_b2.py (commit 0c18f227) with TWO departures that Desk A stated in words on 2026-11-16 (a reading to test, not the written spec): (D1) the cluster key also contains the found-by spec (TS, VS, SW); (D2) family labels: F1 favourite-late shape (band >= 17 and bucket <= 600) first, else '<filter name> by price region' with regions cheap tail (band <= 6), middle (7 to 16), high price (17 and 18). Everything else as in the committed build. Diff target: Desk A's 18 picks.
usage: python3 -I engb_v3_rank_b2_desk_a_key.py <archive_extract.sqlite>"""
import sys, os, collections, calendar, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
import engb_v3_rank_b2 as V
def fam(r):
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    f = r["filter"][0]; reg = "cheap tail" if r["band"] <= 6 else "middle" if r["band"] <= 16 else "high price"
    return {"swid": "spread-width", "vspike": "volume spike", "spread": "spread level", "none": "plain band"}.get(f, "momentum or volume") + ", " + reg
def rank(rows):
    keep = [r for r in rows if r["series"] != "KXDOGE15M" and r["spd"] >= 3 and r["sspd"] >= 3]
    for r in keep: r["family"] = fam(r)
    par = list(range(len(keep)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(keep)):
        for j in range(i + 1, len(keep)):
            a, b = keep[i], keep[j]
            if a["spec"] == b["spec"] and a["series"] == b["series"] and a["side"] == b["side"] and a["exit"] == b["exit"] and abs(a["bucket"] - b["bucket"]) <= 60 and abs(a["band"] - b["band"]) <= 1: par[find(i)] = find(j)
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
        r = V.rows_for(mode, mk, ls_of, sers, a[0])
        for x in r: x["spec"] = mode
        rows += r
    nc, picks = rank(rows); print("pooled", len(rows), "clusters", nc, "picks", len(picks))
    for i, p in enumerate(picks, 1): print(i, p["series"], p["bucket"], p["band"], p["side"], p["filter"], p["exit"], p["n"], "%.9f %.9f %.9f %.9f %.9f" % (p["spd"], p["edge_1c"], p["edge_2c"], p["dollars_week_1c"], p["dollars_week_2c"]), p["family"], p["spec"])
if __name__ == "__main__": main(sys.argv[1:])
