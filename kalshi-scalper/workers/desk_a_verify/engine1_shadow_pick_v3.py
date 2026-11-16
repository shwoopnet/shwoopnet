"""SHADOW_LIST_V3 (Desk A, Nov 16 2026): the batch B2 validate-bar passes (ENGB1TIMESTOP, ENGB2VSPIKE, ENGB3SPRW; 47 rules), same procedure as V1 and V2: Dogecoin excluded under 7e, 3-a-day gate on validate signals, clusters (same market, side, exit, filter, look within 60 s, band within 1), cap 3 per market and 5 per family, rank by dollars a week at 1c and 5 contracts. Favourite-late shapes carry admission "owner_override_shadow (standing, Nov 16)". None of these filters reads Bitcoin (own-market volume, own-market spread, own-market momentum, TA time exits), so start_utc is a command line argument: the next whole UTC hour after the freeze commit. Held-out verdict null until the registered read runs. Pure bookkeeping on read figures; m unchanged.
  python3 -I engine1_shadow_pick_v3.py <start_utc> <out dir> <out_ENGB1TIMESTOP.json> <out_ENGB2VSPIKE.json> <out_ENGB3SPRW.json>"""
import sys, os, json, hashlib, collections
MAX_PER_MARKET, MAX_PER_FAMILY, MIN_SPD = 3, 5, 3.0
OVERRIDE = "owner_override_shadow (standing, Nov 16)"
EXIT_DEF = {"TA3": "time exit: sell at the bid of the candle ending exactly 180 s after entry (exit fee paid)", "TA5": "time exit: sell at the bid of the candle ending exactly 300 s after entry (exit fee paid)"}
def family(r, spec):
    f = r["filter"][0] if r["filter"] else "none"
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    region = "cheap tail (5c to 35c)" if r["band"] <= 6 else ("middle (35c to 85c)" if r["band"] <= 16 else "high price (85c+)")
    kind = {"vspike": "entry volume spike filter", "swid": "spread-width change filter"}.get(f, "momentum, volume or spread filter")
    return "%s, %s%s" % (kind, region, ", time-stop exit" if r["exit"] in EXIT_DEF else "")
def main(start, out, *srcs):
    rows = []
    for src in srcs:
        d = json.load(open(src))
        for r in d["validate_bar_list"]: r["_spec"] = d["spec"]; rows.append(r)
    total = len(rows); excl = [r for r in rows if r["series"] == "KXDOGE15M"]; rows = [r for r in rows if r["series"] != "KXDOGE15M"]
    gate = [r for r in rows if r["income_1c"]["signals_per_day"] >= MIN_SPD]; dropped = len(rows) - len(gate); rows = gate
    for r in rows: r["family"] = family(r, r["_spec"])
    par = list(range(len(rows)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i, a in enumerate(rows):
        for j in range(i + 1, len(rows)):
            b = rows[j]
            if a["series"] == b["series"] and a["side"] == b["side"] and a["exit"] == b["exit"] and a["filter"] == b["filter"] and a["_spec"] == b["_spec"] and abs(a["bucket"] - b["bucket"]) <= 60 and abs(a["band"] - b["band"]) <= 1: par[find(i)] = find(j)
    cl = collections.defaultdict(list)
    for i, r in enumerate(rows): cl[find(i)].append(r)
    key = lambda r: (-r["income_1c"]["dollars_week"], -r["pf_2c"], r["bucket"], r["band"])
    clusters = [sorted(ms, key=key) for ms in cl.values()]
    clusters.sort(key=lambda ms: (key(ms[0]), ms[0]["series"], ms[0]["side"], ms[0]["exit"], str(ms[0]["filter"]), ms[0]["_spec"]))
    per_m, per_f, picks = collections.Counter(), collections.Counter(), []
    for ci, ms in enumerate(clusters):
        r = ms[0]
        if per_m[r["series"]] >= MAX_PER_MARKET or per_f[r["family"]] >= MAX_PER_FAMILY: continue
        per_m[r["series"]] += 1; per_f[r["family"]] += 1; picks.append((ci, r))
    specs = []
    for n, (ci, r) in enumerate(picks, 1):
        sid = "SH3_%02d_%s" % (n, r["series"][2:-3])
        rule = {"id": sid, "kind": "grid15m", "source": "archive", "market": r["series"], "entry": {"seconds_left": r["bucket"], "price_band_5c": r["band"], "side_rule": r["side"], "filter": "%s:%s" % tuple(r["filter"]) if r["filter"] else "none"},
                "exit": r["exit"], "costs": {"contracts": 10, "haircuts_primary": [0.01, 0.02], "fee_form": "ceil(round(100 x 0.07 x c x p x (1 - p), 9)) / 100 per order"}, "size_in_log": 1, "mode": "log_only_forward", "start_utc": start, "found_by_spec": r["_spec"]}
        if r["exit"] in EXIT_DEF: rule["exit_definition"] = EXIT_DEF[r["exit"]]
        h = hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        fav = r["family"].startswith("F1")
        specs.append({"spec": rule, "spec_sha256": h, "rank": n, "admission": OVERRIDE if fav else "clean", "admission_note": "favourite-late shape: same mechanism as gold L1; owner standing override of Nov 16: logging only, going live needs its own popup" if fav else "search plus validate bar; no 7e row touched", "family": r["family"], "cluster": ci + 1, "cluster_size": len(clusters[ci]), "heldout_verdict": None,
                      "paper_research": {"validate_n": r["n"], "signals_per_day": round(r["income_1c"]["signals_per_day"], 3), "pf_1c": round(r["pf_1c"], 3), "pf_2c": round(r["pf_2c"], 3), "edge_1c_cents_per_contract": round(r["income_1c"]["edge_cents_per_contract"], 3), "dollars_week_5c_1c": round(r["income_1c"]["dollars_week"], 2), "dollars_week_5c_2c": round(r["income_2c"]["dollars_week"], 2), "p_day_clustered": r["p"], "bh_survivor": bool(r.get("bh_m_now")), "label": "validate-window income, upward biased, not a forecast"}})
    json.dump({"list": "SHADOW_LIST_V3", "date": "2026-11-16", "start_utc": start, "n": len(specs), "source": "batch B2 validate-bar lists (%d passes; BH survivors 0)" % total, "excluded_dogecoin_7e": len(excl), "dropped_by_3_a_day_gate": dropped, "clusters": len(clusters), "spec_sha256_covers": "the spec object only", "no_money_no_orders": True, "specs": specs}, open(os.path.join(out, "SHADOW_LIST_V3.json"), "w"), indent=1)
    print(len(specs), "picks;", len(clusters), "clusters; total", total, "dogecoin", len(excl), "gate dropped", dropped, dict(per_m), dict(per_f))
    for s in specs: print(s["spec"]["id"], s["spec"]["market"], s["spec"]["entry"]["filter"], s["spec"]["exit"], s["admission"][:20], s["paper_research"]["dollars_week_5c_1c"])
if __name__ == "__main__":
    if len(sys.argv) != 6: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], *sys.argv[3:])
