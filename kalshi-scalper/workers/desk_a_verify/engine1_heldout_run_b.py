"""ENGINE1 held-out read of BATCH B's validate-bar passes (Desk A, Nov 16 2026): ENGB4XBTC (33) and ENGB1TIMESTOP, ENGB2VSPIKE, ENGB3SPRW (3 + 16 + 28 = 47), registered in each spec's heldout_read_registered and in ENGINE1_HELDOUT_READ_PLAN_NOV16.md v3. Each rule is re-scored UNCHANGED on the held-out markets the held-out loader returns (the same windows, floors and bar as the 190's read); its feature classes use SEARCH-only cuts from the archive (vspike and spread terciles), swid and btcmom3 need none. btcmom3 reads the held KXBTC15M candles of the same close (a held market whose Bitcoin candle pair is missing, e.g. a series window past the Bitcoin window, is skipped and counted). One run, the report read after its sha256 is committed. BH over m = the number of batch B rules read (80), printed; the bar 'holds' = n at the floor, PF 1.3 at 1c, PF 1.0 at 2c.
  python3 -I engine1_heldout_run_b.py <dir holding the archive extracts> <dir holding the pull run folders> <out_engb4.json> <out_ENGB1TIMESTOP.json> <out_ENGB2VSPIKE.json> <out_ENGB3SPRW.json> <out.json>
  python3 -I engine1_heldout_run_b.py --dry <archive dir> <the same four lists> <out.json>   (reproduces the VALIDATE rows from the archive's validate half; no held-out data)"""
import sys, os, json, hashlib, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_driver as D, engine1_enum as N, engine1_split as S, engine1_batchb as B, engine1_batchb2 as B2, engine1_core as K
LABEL = "unread by ENGINE1, seen by earlier development cards"
def score(items, x):
    if x in ("TA3", "TA5"):
        k = 3 if x == "TA3" else 5; es = [D.to_core(m, ent) for m, ent in items]
        out = {h: B2.aggregate_x(es, lambda e, hh, n, k=k: B2.score_ta(e, k, hh, n), h, D.CONTRACTS) for h in (0.01, 0.02)}
        return out, D.pval(out[0.01]["day_z"])
    return D.score_group(items, x)
def evaluate(rules, held, search, floors, windows_days, stats):
    """rules: [(spec, row)]; held, search: {series: [market]} (held-out markets; archive SEARCH markets for the cuts). -> rows."""
    btc_idx = B.btc_index(held.get(B.BTC, [])); G = {}; rows = []
    for spec, x in rules:
        s = x["series"]; f = x["filter"][0]
        if (s, f) not in G:
            sm = search.get(s, [])
            if f == "btcmom3": G[(s, f)] = B.groups_x(held.get(s, []), btc_idx, stats)
            elif f == "vspike": G[(s, f)] = B2.groups_f(held.get(s, []), "vspike", B2.feature_cuts(sm, "vspike"), stats)
            elif f == "swid": G[(s, f)] = B2.groups_f(held.get(s, []), "swid", {}, stats)
            else:
                cuts = {}
                for b in N.BUCKETS:
                    sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
                    cuts[b] = N.spread_cuts(sp) if sp else None
                G[(s, f)] = D.groups(held.get(s, []), cuts)
        items = G[(s, f)].get((x["bucket"], x["band"], x["side"], tuple(x["filter"])), [])
        agg, p = score(items, x["exit"]) if items else ({0.01: {"n": 0, "pf": float("nan"), "net": 0.0}, 0.02: {"n": 0, "pf": float("nan"), "net": 0.0}}, 1.0)
        a1, a2 = agg[0.01], agg[0.02]; fl = floors[s]; days = windows_days(s)
        holds = a1["n"] >= fl and a1["pf"] >= D.PF1 and a2["pf"] >= D.PF2
        rows.append({"spec": spec, "series": s, "bucket": x["bucket"], "band": x["band"], "side": x["side"], "filter": x["filter"], "exit": x["exit"], "n": a1["n"], "n_floor": fl, "pf_1c": a1["pf"], "pf_2c": a2["pf"], "p": p, "income_1c": D.income(a1, days), "income_2c": D.income(a2, days), "validate_pf_1c": x["pf_1c"], "validate_pf_2c": x["pf_2c"], "validate_n": x["n"], "holds_bar": bool(holds),
                     "verdict": ("holds" if holds else ("no evidence at n = %d" % a1["n"] if a1["n"] < fl else "does not hold"))})
    pv = {i: r["p"] for i, r in enumerate(rows) if r["holds_bar"]}; keep = D.bh(pv, len(rows))
    for i, r in enumerate(rows): r["bh_survivor_80"] = i in keep
    return rows, len(keep)
def load_rules(paths):
    rules = []
    for pth in paths:
        d = json.load(open(pth)); spec = d["spec"]
        for x in d["validate_bar_list"]: rules.append((spec, x))
    return rules
def main(argv):
    dry = argv[0] == "--dry"; argv = argv[1:] if dry else argv
    import engine1_extract_load as L
    base_arch = argv[0]; rest = argv[1:] if dry else argv[2:]; base_pull = None if dry else argv[1]
    paths, out = rest[:4], rest[4]; rules = load_rules(paths)
    wa, ca, wp, cp, wn, cn = L.load(base_arch)
    search = {s: [m for m in wa[s] if S.phase(D.short(s), m["close"]) == "search"] for s in wa}
    stats = collections.Counter()
    if dry:
        held = {s: [m for m in wa[s] if S.phase(D.short(s), m["close"]) == "validate"] for s in wa}
        floors = {s: 0 for s in wa}; wd = lambda s: float(D.validate_days([m["close"] for m in held[s]], S.LAST_SEARCH[D.short(s)]) or 1); drops = {}
    else:
        import engine1_heldout_load as H
        held, drops = H.load(base_pull); floors = H.N_FLOOR; wd = lambda s: (H.WINDOWS[s][1] - H.WINDOWS[s][0]) / 86400.0
    rows, nk = evaluate(rules, held, search, floors, wd, stats)
    rep = {"header": "BH m = %d (every batch B rule read counts) before any result" % len(rows), "label": LABEL, "dry": dry, "markets_by_series": {s: len(v) for s, v in held.items()}, "loader_drops": drops, "stats": dict(stats), "holds": sum(1 for r in rows if r["holds_bar"]), "bh_survivors": nk, "rows": rows,
           "rule_hashes": {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_batchb.py", "engine1_batchb2.py", "engine1_heldout_load.py", "engine1_heldout_run_b.py")}}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__": 
    if len(sys.argv) < 8: sys.exit(__doc__)
    main(sys.argv[1:])
