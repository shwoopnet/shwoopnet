"""C1 day-correlation check (Desk A, Nov 16 2026), required by the ENGC1ETHMOM spec: each C1 VALIDATE pass against every ENGB4XBTC VALIDATE pass. The daily series of a rule = its net dollars (10 contracts, haircut 1c, the audited scorer) summed by UTC close date over the VALIDATE window Sep 4 to Oct 2 2026 (a day with no trade is 0). Pearson correlation of the two 29 day vectors; 0.3 or more is a duplicate (the Head's 7d rule). Reads the archive extract through the audited loader (same data as the batch runs); prints correlations and flags only.
  python3 -I engine1_batchc_c1corr.py <dir with the archive extracts> <out_engb4.json> <out_ENGC1ETHMOM.json> <out.json>"""
import sys, os, json, math, datetime, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D, engine1_enum as N, engine1_split as S, engine1_batchb as B, engine1_batchc as C, engine1_core as K
DAYS = [(datetime.date(2026, 9, 4) + datetime.timedelta(days=i)).isoformat() for i in range(29)]
def daily(items, ex):
    es = [D.to_core(m, ent) for m, ent in items]; by = collections.defaultdict(float)
    for e in sorted(es, key=lambda e: (e["close_ts"], e["id"])):
        x, r = K.score(e, ex, 0.01, D.CONTRACTS)
        if x is not None: by[e["day"]] += x
    return [by.get(d, 0.0) for d in DAYS]
def corr(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n; va = sum((x - ma) ** 2 for x in a); vb = sum((x - mb) ** 2 for x in b)
    return None if va == 0 or vb == 0 else sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)
def main(base, b4, c1, out):
    wa = L.load(base)[0]; btc_idx = B.btc_index(wa[B.BTC]); eth_idx = B.btc_index(wa["KXETH15M"]); cache = {}
    def series_series(series, kind):
        if (series, kind) not in cache:
            vm = [m for m in wa[series] if S.phase(D.short(series), m["close"]) == "validate"]
            cache[(series, kind)] = B.groups_x(vm, btc_idx) if kind == "btcmom3" else C.groups_c(vm, "ethmom3", eth_idx)
        return cache[(series, kind)]
    def vec(r, kind):
        items = series_series(r["series"], kind).get((r["bucket"], r["band"], r["side"], (kind, r["filter"][1])), []); return daily(items, r["exit"])
    A = json.load(open(b4))["validate_bar_list"]; Cc = json.load(open(c1))["validate_bar_list"]
    av = [(r, vec(r, "btcmom3")) for r in A]; res = []
    for r in Cc:
        v = vec(r, "ethmom3"); best = (None, None)
        for ra, va in av:
            c = corr(v, va)
            if c is not None and (best[0] is None or c > best[0]): best = (c, "%s %d %d %s %s %s" % (ra["series"], ra["bucket"], ra["band"], ra["side"], ra["filter"][1], ra["exit"]))
        res.append({"c1": [r["series"], r["bucket"], r["band"], r["side"], r["filter"][1], r["exit"]], "n": r["n"], "max_corr_vs_engb4xbtc": best[0], "most_correlated_engb4xbtc_rule": best[1], "duplicate_0.3": bool(best[0] is not None and best[0] >= 0.3)})
    json.dump({"days": DAYS, "rule": "Pearson on daily net dollars at 1c, 0.3 or more is a duplicate", "n_c1": len(res), "n_duplicates": sum(1 for x in res if x["duplicate_0.3"]), "rows": res}, open(out, "w"), indent=1)
    print("wrote", out, len(res), "c1 rules;", sum(1 for x in res if x["duplicate_0.3"]), "duplicates at 0.3")
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
