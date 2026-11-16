"""SHADOW_LIST_V4 (Desk A, Nov 16 2026): batch C's VALIDATE-bar passes (ENGC1ETHMOM 36, ENGC2OIACC 19, ENGC3TOD 4, ENGC4GOLDX 9 = 68), by the WRITTEN ranking spec (SHADOW_RANKING_SPEC_NOV16.md rules 6 to 9; the Head's ruling that the written spec governs): Dogecoin excluded under 7e, the 3 a day gate, clusters (same series, side and exit, look within 60 s, band within 1, transitive; the filter and the found-by spec are NOT in the key), cap 3 per market and 5 per family, ranked by dollars a week at 1c and 5 contracts. Before ranking, the C1 day-correlation check (c1corr.json: Pearson on daily net dollars against every ENGB4XBTC pass, 0.3 or more is a duplicate) drops the duplicate C1 rules. Family = the written spec's rule 6 (the new filters ethmom3, goldmom3, oiacc and todct are not among its named kinds, so their kind is 'plain band'). Held-out column: 'not read'. Start: a pick that TRADES KXBTC15M starts no earlier than 2026-11-21T00:00:00Z (H09); every other pick at the given start (the next whole UTC hour after the freeze commit). A cross-series feature (ETH or gold candles of the same close) is written into each spec. Pure bookkeeping on read figures; m unchanged.
  python3 -I engine1_shadow_pick_v4.py <start_utc> <out dir> <c1corr.json> <out_ENGC1ETHMOM.json> <out_ENGC2OIACC.json> <out_ENGC3TOD.json> <out_ENGC4GOLDX.json>"""
import sys, os, json, hashlib, collections
MAX_PER_MARKET, MAX_PER_FAMILY, MIN_SPD = 3, 5, 3.0
BTC_HOLD_START = "2026-11-21T00:00:00Z"
OVERRIDE = "owner_override_shadow (standing, Nov 16)"
CROSS = {"ethmom3": {"series": "KXETH15M", "definition": "mid (bid+ask)/2 of the KXETH15M market with the same close at the candle ending e minus the one at e - 180; class up, flat or down by cls() (1e-12); both candles present, no two sided test (B4's rule)"}, "goldmom3": {"series": "KXGOLD15M", "definition": "mid (bid+ask)/2 of the KXGOLD15M market with the same close at the candle ending e minus the one at e - 180; class up, flat or down by cls() (1e-12); both candles present, no two sided test; missing on a gold break or weekend (no entry)"}}
OWN = {"oiacc": "(open interest at e minus at e - 180) minus (at e - 180 minus at e - 360) of the market's own candles, all three present; class up, flat or down by cls()", "todct": "US Central clock hour of the entry candle end e, America/Chicago with DST: ct00 (00:00 to 05:59), ct06, ct12, ct18"}
def family(r):
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    return "plain band, %s" % ("cheap tail" if r["band"] <= 6 else ("middle" if r["band"] <= 16 else "high price"))
def main(start, out, c1corr, *srcs):
    dup = {tuple(r["c1"]) for r in json.load(open(c1corr))["rows"] if r["duplicate_0.3"]}; rows = []; counts = {}
    for src in srcs:
        d = json.load(open(src)); sp = d["spec"]; counts[sp] = [len(d["validate_bar_list"]), 0]
        for r in d["validate_bar_list"]:
            r["_spec"] = sp
            if sp == "ENGC1ETHMOM" and (r["series"], r["bucket"], r["band"], r["side"], r["filter"][1], r["exit"]) in dup: counts[sp][1] += 1; continue
            rows.append(r)
    total = sum(v[0] for v in counts.values()); excl = [r for r in rows if r["series"] == "KXDOGE15M"]; rows = [r for r in rows if r["series"] != "KXDOGE15M"]
    gate = [r for r in rows if r["income_1c"]["signals_per_day"] >= MIN_SPD]; dropped = len(rows) - len(gate); rows = gate
    for r in rows: r["family"] = family(r)
    par = list(range(len(rows)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i, a in enumerate(rows):
        for j in range(i + 1, len(rows)):
            b = rows[j]
            if a["series"] == b["series"] and a["side"] == b["side"] and a["exit"] == b["exit"] and abs(a["bucket"] - b["bucket"]) <= 60 and abs(a["band"] - b["band"]) <= 1: par[find(i)] = find(j)
    cl = collections.defaultdict(list)
    for i, r in enumerate(rows): cl[find(i)].append(r)
    key = lambda r: (-r["income_1c"]["dollars_week"], -r["pf_2c"], r["bucket"], r["band"], str(r["filter"]))
    clusters = [sorted(ms, key=key) for ms in cl.values()]
    clusters.sort(key=lambda ms: (-ms[0]["income_1c"]["dollars_week"], ms[0]["series"], ms[0]["bucket"], ms[0]["band"], ms[0]["side"], ms[0]["exit"], str(ms[0]["filter"])))
    per_m, per_f, picks = collections.Counter(), collections.Counter(), []
    for ci, ms in enumerate(clusters):
        r = ms[0]
        if per_m[r["series"]] >= MAX_PER_MARKET or per_f[r["family"]] >= MAX_PER_FAMILY: continue
        per_m[r["series"]] += 1; per_f[r["family"]] += 1; picks.append((ci, r))
    specs = []
    for n, (ci, r) in enumerate(picks, 1):
        fname = r["filter"][0]; sid = "SH4_%02d_%s" % (n, r["series"][2:-3])
        rule = {"id": sid, "kind": "grid15m", "source": "archive", "market": r["series"], "entry": {"seconds_left": r["bucket"], "price_band_5c": r["band"], "side_rule": r["side"], "filter": "%s:%s" % (fname, r["filter"][1])}, "exit": r["exit"],
                "costs": {"contracts": 10, "haircuts_primary": [0.01, 0.02], "fee_form": "ceil(round(100 x 0.07 x c x p x (1 - p), 9)) / 100 per order"}, "size_in_log": 1, "mode": "log_only_forward", "start_utc": BTC_HOLD_START if r["series"] == "KXBTC15M" and start < BTC_HOLD_START else start, "found_by_spec": r["_spec"]}
        if fname in CROSS: rule["cross_series_feature"] = dict(CROSS[fname], name=fname)
        else: rule["feature_definition"] = {"name": fname, "definition": OWN[fname]}
        h = hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(",", ":")).encode()).hexdigest(); fav = r["family"].startswith("F1")
        specs.append({"spec": rule, "spec_sha256": h, "rank": n, "admission": OVERRIDE if fav else "clean", "admission_note": "favourite-late shape: same mechanism as gold L1; owner standing override of Nov 16: logging only, going live needs its own popup" if fav else "search plus validate bar; no 7e row touched", "family": r["family"], "cluster": ci + 1, "cluster_size": len(clusters[ci]), "heldout_verdict": "not read",
                      "paper_research": {"validate_n": r["n"], "signals_per_day": round(r["income_1c"]["signals_per_day"], 3), "pf_1c": round(r["pf_1c"], 3), "pf_2c": round(r["pf_2c"], 3), "edge_1c_cents_per_contract": round(r["income_1c"]["edge_cents_per_contract"], 3), "dollars_week_5c_1c": round(r["income_1c"]["dollars_week"], 2), "dollars_week_5c_2c": round(r["income_2c"]["dollars_week"], 2), "p_day_clustered": r["p"], "bh_survivor": bool(r.get("bh_m_now")), "label": "validate-window income, upward biased, not a forecast"}})
    json.dump({"list": "SHADOW_LIST_V4", "date": "2026-11-16", "start_utc": start, "start_rule": "picks on KXBTC15M start no earlier than %s (H09); others at start_utc (the next whole UTC hour after the freeze commit)" % BTC_HOLD_START, "n": len(specs), "source": "batch C VALIDATE-bar passes (%d; BH survivors 0 at carried 6,290,660 + own tries and at 7,492,484)" % total, "c1_duplicates_dropped_by_day_correlation_0.3": counts["ENGC1ETHMOM"][1], "passes_by_spec": {k: v[0] for k, v in counts.items()}, "excluded_dogecoin_7e": len(excl), "dropped_by_3_a_day_gate": dropped, "clusters": len(clusters), "spec_sha256_covers": "the spec object only", "no_money_no_orders": True, "specs": specs}, open(os.path.join(out, "SHADOW_LIST_V4.json"), "w"), indent=1)
    print(len(specs), "picks;", len(clusters), "clusters; passes", counts, "dogecoin", len(excl), "gate dropped", dropped, dict(per_m), dict(per_f))
    for s in specs: print(s["spec"]["id"], s["spec"]["market"], s["spec"]["entry"]["filter"], s["spec"]["exit"], s["admission"][:20], s["paper_research"]["dollars_week_5c_1c"], s["spec"]["start_utc"][:10])
if __name__ == "__main__":
    if len(sys.argv) != 8: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3], *sys.argv[4:])
