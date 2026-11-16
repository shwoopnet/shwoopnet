"""SHADOW_LIST_V2 (Desk A, Nov 16 2026): the 33 ENGB4XBTC validate-bar passes, same procedure as V1 (engine1_shadow_pick.py): Dogecoin excluded under 7e, 3-a-day gate on validate signals, clusters (same series, side and exit, look within 60 s, band within 1, transitive: the WRITTEN spec rule 7, the filter class is NOT in the key), cap 3 per market and 5 per family, rank by dollars a week at 1c, 5 contracts. Favourite-late shapes carry admission "owner_override_shadow (standing, Nov 16)". Each spec carries the cross-series feature (Bitcoin candles at the same close) and a fixed start_utc. Held-out verdict field is null until the registered read runs. Pure bookkeeping on figures already read; m unchanged.
  python3 -I engine1_shadow_pick_v2.py <out_engb4.json> <out dir>"""
import sys, os, json, hashlib, collections
MAX_PER_MARKET, MAX_PER_FAMILY, MIN_SPD = 3, 5, 3.0
START_UTC = "2026-11-21T00:00:00Z"  # 1795219200; Head and Auditor B: btcmom3 reads the held BTC15M path (H09), so not before Nov 21
def family(r):
    """WRITTEN ranking spec rule 6 (SHADOW_RANKING_SPEC_NOV16.md; the Head's ruling of Nov 16: the written spec governs): F1 first, else kind x region; btcmom3 is not one of the named filter kinds, so its kind is 'plain band'."""
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    return "plain band, %s" % ("cheap tail" if r["band"] <= 6 else ("middle" if r["band"] <= 16 else "high price"))
def main(src, out):
    d = json.load(open(src)); rows = d["validate_bar_list"]
    excl = [r for r in rows if r["series"] == "KXDOGE15M"]; rows = [r for r in rows if r["series"] != "KXDOGE15M"]
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
        sid = "SH2_%02d_%s" % (n, r["series"][2:-3])
        rule = {"id": sid, "kind": "grid15m", "source": "archive", "market": r["series"], "entry": {"seconds_left": r["bucket"], "price_band_5c": r["band"], "side_rule": r["side"], "filter": "btcmom3:" + r["filter"][1]},
                "cross_series_feature": {"name": "btcmom3", "series": "KXBTC15M", "definition": "mid (bid+ask)/2 of the Bitcoin market at the same close at end_period 0 s minus the one 180 s earlier; class up, down or flat", "needs_bitcoin_candles_at_same_close": True},
                "exit": r["exit"], "costs": {"contracts": 10, "haircuts_primary": [0.01, 0.02], "fee_form": "ceil(round(100 x 0.07 x c x p x (1 - p), 9)) / 100 per order"}, "size_in_log": 1, "mode": "log_only_forward", "start_utc": START_UTC}
        h = hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        fav = r["family"].startswith("F1")
        specs.append({"spec": rule, "spec_sha256": h, "rank": n, "admission": "owner_override_shadow (standing, Nov 16)" if fav else "clean", "admission_note": "favourite-late shape (band 17+, 10 minutes or less left): same mechanism as gold L1; owner standing override of Nov 16: logging only, going live needs its own popup" if fav else "search plus validate bar; no 7e row touched", "family": r["family"], "cluster": ci + 1, "cluster_size": len(clusters[ci]),
                      "heldout_verdict": None,
                      "paper_research": {"validate_n": r["n"], "signals_per_day": round(r["income_1c"]["signals_per_day"], 3), "pf_1c": round(r["pf_1c"], 3), "pf_2c": round(r["pf_2c"], 3), "edge_1c_cents_per_contract": round(r["income_1c"]["edge_cents_per_contract"], 3), "dollars_week_5c_1c": round(r["income_1c"]["dollars_week"], 2), "dollars_week_5c_2c": round(r["income_2c"]["dollars_week"], 2), "p_day_clustered": r["p"], "bh_survivor": bool(r.get("bh_m_now")), "label": "validate-window income, upward biased, not a forecast"}})
    json.dump({"list": "SHADOW_LIST_V2", "date": "2026-11-16", "start_utc": START_UTC, "n": len(specs), "source": "ENGB4XBTC validate-bar list (33 passes; BH survivors 0)", "excluded_dogecoin_7e": len(excl), "dropped_by_3_a_day_gate": dropped, "clusters": len(clusters), "spec_sha256_covers": "the spec object only", "no_money_no_orders": True, "specs": specs}, open(os.path.join(out, "SHADOW_LIST_V2.json"), "w"), indent=1)
    print(len(specs), "picks;", len(clusters), "clusters; dogecoin excluded", len(excl), "gate dropped", dropped, dict(per_m), dict(per_f))
    for s in specs: print(s["spec"]["id"], s["admission"], s["paper_research"]["dollars_week_5c_1c"])
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
