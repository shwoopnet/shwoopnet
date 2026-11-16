"""ENGINE1 held-out read runner (Desk A, Nov 16 2026), plan ENGINE1_HELDOUT_READ_PLAN_NOV16.md (v3). One run: the 190 rules of run 2's validate_bar_list, re-scored UNCHANGED on the held-out markets the held-out loader returns; spread cuts from the archive SEARCH half only (Line B1 loader); BH over m = 190.
  python3 -I engine1_heldout_run.py <dir holding the archive extracts> <dir holding the pull run folders> <barlist.json> <SHADOW_LIST_V1.json> <out.json>
Prints only the output path; the report is read after its sha256 is committed."""
import sys, os, json, hashlib, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_driver as D, engine1_enum as N, engine1_split as S, engine1_heldout_load as H
LABEL = "unread by ENGINE1, seen by earlier development cards"
INCOME_LABEL = "held-out income at 5 contracts, 7 days a week, upward biased by selection on the old window, not a forecast; signals a day counts calendar days"
M_BH = 190
def window_days(series): lo, hi = H.WINDOWS[series]; return (hi - lo) / 86400.0
def rule_key(x): return (x["series"], x["bucket"], x["band"], x["side"], tuple(x["filter"]) if x["filter"] else None, x["exit"])
def verdicts(rules, groups_by_series, shadow, floors=None, m=M_BH):
    """rules: the barlist rows; groups_by_series: {series: D.groups output of the held-out markets}. -> rows with verdicts; BH over m (every rule counts, read or not)."""
    floors = floors or H.N_FLOOR; rows, pv = [], {}
    for i, x in enumerate(rules):
        items = groups_by_series.get(x["series"], {}).get((x["bucket"], x["band"], x["side"], tuple(x["filter"]) if x["filter"] else None), [])
        agg, p = D.score_group(items, x["exit"]) if items else ({0.01: {"n": 0, "net": 0.0, "pf": float("nan")}, 0.02: {"n": 0, "net": 0.0, "pf": float("nan")}}, 1.0)
        a1, a2 = agg[0.01], agg[0.02]; fl = floors[x["series"]]; days = window_days(x["series"])
        holds = a1["n"] >= fl and a1["pf"] >= D.PF1 and a2["pf"] >= D.PF2
        row = {"i": i, "series": x["series"], "bucket": x["bucket"], "band": x["band"], "side": x["side"], "filter": x["filter"], "exit": x["exit"], "n": a1["n"], "n_floor": fl, "pf_1c": a1["pf"], "pf_2c": a2["pf"], "p": p,
               "income_1c": D.income(a1, days), "income_2c": D.income(a2, days), "validate_pf_1c": x["pf_1c"], "validate_pf_2c": x["pf_2c"], "validate_n": x["n"], "holds_bar": bool(holds),
               "verdict": ("holds" if holds else ("no evidence at n = %d" % a1["n"] if a1["n"] < fl else "does not hold")), "shadow": shadow.get(rule_key(x))}
        if a1["n"] < 100: row["label_note"] = "no evidence at n under 100 (standing label)"
        rows.append(row)
        if holds: pv[i] = p
    keep = D.bh(pv, m)
    for r in rows: r["bh_survivor_190"] = r["i"] in keep; r["verdict_full"] = (r["verdict"] + (", BH survivor at 5% over 190" if r["i"] in keep else (", not proven by BH" if r["holds_bar"] else "")))
    rows.sort(key=lambda r: (-r["income_1c"]["dollars_week"], r["i"]))
    return rows, len(keep)
def main(base_arch, base_pull, barlist, shadowlist, out):
    import engine1_extract_load as L
    rules = json.load(open(barlist))["validate_bar_list"]; spec = json.load(open(shadowlist))["specs"]; shadow = {}
    for s in spec:
        e = s["spec"]["entry"]; f = None if e["filter"] == "none" else tuple(e["filter"].split(":"))
        shadow[(s["spec"]["market"], e["seconds_left"], e["price_band_5c"], e["side_rule"], f, s["spec"]["exit"])] = {"id": s["spec"]["id"], "rank": s["rank"], "admission": s["admission"]}
    wa, ca, wp, cp, wn, cn = L.load(base_arch)                                  # Line B1: the archive extract, for the SEARCH half only
    cuts_all = {}
    for series in sorted({x["series"] for x in rules}):
        sm = [m for m in wa[series] if S.phase(D.short(series), m["close"]) == "search"]; cuts = {}
        for b in N.BUCKETS:
            sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
            cuts[b] = N.spread_cuts(sp) if sp else None
        cuts_all[series] = cuts
    cuts_sha = hashlib.sha256(json.dumps({s: {str(b): c for b, c in v.items()} for s, v in sorted(cuts_all.items())}, sort_keys=True).encode()).hexdigest()
    held, drops = H.load(base_pull)
    groups = {s: D.groups(held.get(s, []), cuts_all[s]) for s in cuts_all}
    rows, nk = verdicts(rules, groups, shadow)
    rep = {"header": "BH m = %d (every one of the 190 counts, read or not) before any result" % M_BH, "label": LABEL, "income_label": INCOME_LABEL, "tercile_cuts_sha256": cuts_sha, "windows": {s: list(w) for s, w in H.WINDOWS.items()}, "n_floor": H.N_FLOOR,
           "markets_by_series": {s: len(v) for s, v in held.items()}, "loader_drops": drops, "holds": sum(1 for r in rows if r["holds_bar"]), "bh_survivors_190": nk, "rows": rows,
           "rule_hashes": {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_heldout_load.py", "engine1_heldout_run.py")}}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 6: sys.exit(__doc__)
    main(*sys.argv[1:])
