"""ENGINE1 held-out read of BATCH C's validate-bar passes (Desk A, Nov 16 2026): ENGC1ETHMOM 36, ENGC2OIACC 19, ENGC3TOD 4, ENGC4GOLDX 9 = 68 rules, registered in each batch C spec's heldout_read_registered and in ENGINE_BATCHC_HELDOUT_PLAN_NOV16.md. Each rule is re-scored UNCHANGED on the held-out markets the held-out loader returns (the same windows, floors and bar as the 190's read). Cross-series features read the held KXETH15M (C1) or KXGOLD15M (C4) market of the SAME close; a held market with no such candle pair (for example a WTI close after Oct 28, because the ETH and gold windows end at 2026-10-28T00:00Z) is skipped and counted, never filled in. oiacc and todct need no other market. BH: the standard step-up over m = the number of rules read (68), every rule ranked (the 190 lesson: the plan's wording ranks all rules, no-evidence rules included); the bar 'holds' = n at the floor, PF 1.3 at 1c, PF 1.0 at 2c. One run; the report is read after its sha256 is committed.
  python3 -I engine1_heldout_run_c.py <dir holding the archive extracts> <dir holding the pull run folders> <out_ENGC1ETHMOM.json> <out_ENGC2OIACC.json> <out_ENGC3TOD.json> <out_ENGC4GOLDX.json> <out.json>
  python3 -I engine1_heldout_run_c.py --dry <archive dir> <the same four lists> <out.json>   (reproduces the VALIDATE rows from the archive's validate half; no held-out data)"""
import sys, os, json, hashlib, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_driver as D, engine1_split as S, engine1_batchb as B, engine1_batchc as C
LABEL = "unread by ENGINE1, seen by earlier development cards"
def bh_all(ps, m, alpha=0.05):
    order = sorted(range(len(ps)), key=lambda i: (ps[i], i)); k = 0
    for r, i in enumerate(order, 1):
        if ps[i] <= alpha * r / m: k = r
    return {order[j] for j in range(k)}
def evaluate(rules, held, floors, windows_days, stats):
    """rules: [(spec, row)]; held: {series: [market]}. -> rows (every rule ranked in BH)."""
    idx = {"ethmom3": B.btc_index(held.get("KXETH15M", [])), "goldmom3": B.btc_index(held.get("KXGOLD15M", []))}; G = {}; rows = []
    for spec, x in rules:
        s = x["series"]; f = x["filter"][0]
        if (s, f) not in G: G[(s, f)] = C.groups_c(held.get(s, []), f, idx.get(f), stats)
        items = G[(s, f)].get((x["bucket"], x["band"], x["side"], tuple(x["filter"])), [])
        agg, p = D.score_group(items, x["exit"]) if items else ({0.01: {"n": 0, "pf": float("nan"), "net": 0.0}, 0.02: {"n": 0, "pf": float("nan"), "net": 0.0}}, 1.0)
        a1, a2 = agg[0.01], agg[0.02]; fl = floors[s]; days = windows_days(s); holds = a1["n"] >= fl and a1["pf"] >= D.PF1 and a2["pf"] >= D.PF2
        rows.append({"spec": spec, "series": s, "bucket": x["bucket"], "band": x["band"], "side": x["side"], "filter": x["filter"], "exit": x["exit"], "n": a1["n"], "n_floor": fl, "pf_1c": a1["pf"], "pf_2c": a2["pf"], "p": p, "income_1c": D.income(a1, days), "income_2c": D.income(a2, days), "validate_pf_1c": x["pf_1c"], "validate_pf_2c": x["pf_2c"], "validate_n": x["n"], "holds_bar": bool(holds),
                     "verdict": ("holds" if holds else ("no evidence at n = %d" % a1["n"] if a1["n"] < fl else "does not hold"))})
    keep = bh_all([r["p"] for r in rows], len(rows))
    for i, r in enumerate(rows): r["bh_survivor_all"] = i in keep; r["verdict_full"] = r["verdict"] + (", BH survivor at 5%% over %d (all ranked)" % len(rows) if i in keep and r["holds_bar"] else "")
    return rows, len(keep)
def load_rules(paths):
    rules = []
    for pth in paths:
        d = json.load(open(pth))
        for x in d["validate_bar_list"]: rules.append((d["spec"], x))
    return rules
def main(argv):
    dry = argv[0] == "--dry"; argv = argv[1:] if dry else argv
    import engine1_extract_load as L
    base_arch = argv[0]; base_pull = None if dry else argv[1]; rest = argv[1:] if dry else argv[2:]; paths, out = rest[:4], rest[4]; rules = load_rules(paths)
    wa = L.load(base_arch)[0]; stats = collections.Counter()
    if dry:
        held = {s: [m for m in wa[s] if S.phase(D.short(s), m["close"]) == "validate"] for s in wa}
        floors = {s: 0 for s in wa}; wd = lambda s: float(D.validate_days([m["close"] for m in held[s]], S.LAST_SEARCH[D.short(s)]) or 1); drops = {}
    else:
        import engine1_heldout_load as H
        held, drops = H.load(base_pull); floors = H.N_FLOOR; wd = lambda s: (H.WINDOWS[s][1] - H.WINDOWS[s][0]) / 86400.0
    rows, nk = evaluate(rules, held, floors, wd, stats)
    rep = {"header": "BH m = %d (every batch C rule read, all ranked) before any result" % len(rows), "label": LABEL, "dry": dry, "markets_by_series": {s: len(v) for s, v in held.items()}, "loader_drops": drops, "stats": dict(stats), "holds": sum(1 for r in rows if r["holds_bar"]), "bh_survivors": nk, "rows": rows,
           "rule_hashes": {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_batchb.py", "engine1_batchc.py", "engine1_heldout_load.py", "engine1_heldout_run_c.py")}}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) < 8: sys.exit(__doc__)
    main(sys.argv[1:])
