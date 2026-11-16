"""ENGINE1 shadow picks (Desk A, Nov 16 2026). Reads the rescore of run 2's 190 validate-bar rules (out_rescore.json, which reproduced the listing to 1e-9), clusters them, picks 20 to 30 by dollars a week (1c cash edge x validate signals a day x 5 contracts x 7) under the owner's limits, and writes SHADOW_LIST_V1.json and SHADOW_CLUSTER_MAP_NOV16.md. Pure bookkeeping on figures already read: no data, no new rule, m unchanged.
  python3 -I engine1_shadow_pick.py <out_rescore.json> <out dir>"""
import sys, os, json, hashlib, collections
MAX_PER_MARKET, MAX_PER_FAMILY, MIN_SPD, TARGET = 3, 5, 3.0, 25
def family(r):
    """Mechanism family = the entry condition kind x the price region it buys in (so a spread filter on a 5c tail and a spread filter on an 80c favourite are different families). The favourite-late shape (band 17+, 10 minutes or less left) is its own family whatever the filter."""
    f = r["filter"][0] if r["filter"] else "none"
    if r["band"] >= 17 and r["bucket"] <= 600: return "F1 favourite-late shape"
    kind = "open-interest trigger" if f.startswith("oi") else ("momentum or volume filter" if f in ("mom1", "mom3", "mom5", "vol3") else ("spread filter" if f == "spread" else "plain band"))
    region = "cheap tail (5c to 35c)" if r["band"] <= 6 else ("middle (35c to 85c)" if r["band"] <= 16 else "high price (85c+)")
    return "%s, %s" % (kind, region)
def flags(r, fam):
    out = []
    if fam.startswith("F1"): out.append("favourite-late shape (88c-97c class, late look): a duplicate of gold L1 unless it differs; here it differs only by market and exit, so it is flagged, not claimed unique")
    if fam.startswith("open-interest"): out.append("open-interest trigger: check against OICORE (cheap side, open interest rise); " + ("same market as OICORE" if r["series"] == "KXBTC15M" else "different market"))
    if r["series"] == "KXXRP15M" and r["side"] == "yes" and r["exit"] == "H": out.append("XRP YES held to settlement: the same mechanism as the retired XRPYES10 (7e: favourite-and-hold ban, XRP declined as an L1 market); shadow only, never live without the owner's named exception")
    if r["series"] == "KXETH15M" and r["band"] >= 14: out.append("Ethereum high-price side: Ethereum as L1 is declined (7e); shadow only")
    if r["series"] == "KXBTC15M" and r["side"] in ("favourite",): out.append("Bitcoin favourite: declined (7e Bitcoin as L1)")
    if r["series"] == "KXGOLD15M": out.append("gold: the gold L1 family and the closed gold variants (maker entries, 94.5c floor) are on 7e; compare before any step beyond shadow")
    return out
def main(src, out):
    rows = json.load(open(src))["rows"]; excl = [r for r in rows if r["series"] == "KXDOGE15M"]; rows = [r for r in rows if r["series"] != "KXDOGE15M"]
    rows = [r for r in rows if r["signals_per_day"] >= MIN_SPD and r["search_signals_per_day"] >= MIN_SPD]
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
    clusters = []
    for k, ms in cl.items():
        ms.sort(key=lambda r: (-r["dollars_week_5c_1c"], -r["pf_2c"], r["bucket"], r["band"], str(r["filter"])))
        clusters.append(ms)
    clusters.sort(key=lambda ms: -ms[0]["dollars_week_5c_1c"])
    per_m, per_f, picks = collections.Counter(), collections.Counter(), []
    for ci, ms in enumerate(clusters):
        rep = ms[0]
        if per_m[rep["series"]] >= MAX_PER_MARKET or per_f[rep["family"]] >= MAX_PER_FAMILY or len(picks) >= TARGET: continue
        per_m[rep["series"]] += 1; per_f[rep["family"]] += 1; picks.append((ci, rep))
    specs = []
    for n, (ci, r) in enumerate(picks, 1):
        sid = "SH1_%02d_%s" % (n, r["series"][2:-3])
        filt = "none" if not r["filter"] else "%s:%s" % tuple(r["filter"])
        rule = {"id": sid, "kind": "grid15m", "source": r["source"], "market": r["series"], "entry": {"seconds_left": r["bucket"], "price_band_5c": r["band"], "side_rule": r["side"], "filter": filt}, "exit": r["exit"],
                "costs": {"contracts": 10, "haircuts_primary": [0.01, 0.02], "fee_form": "ceil(round(100 x 0.07 x c x p x (1 - p), 9)) / 100 per order"}, "size_in_log": 1, "mode": "log_only_forward"}
        h = hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        specs.append({"spec": rule, "spec_sha256": h, "rank": n, "family": r["family"], "flags": flags(r, r["family"]), "cluster": ci + 1, "cluster_size": len(clusters[ci]),
                      "paper_research": {"validate_n": r["n"], "signals_per_day": round(r["signals_per_day"], 3), "pf_1c": round(r["pf_1c"], 3), "pf_2c": round(r["pf_2c"], 3), "edge_1c_cents_per_contract": round(r["edge_1c_cents_per_contract"], 3), "edge_2c_cents_per_contract": round(r["edge_2c_cents_per_contract"], 3), "dollars_week_5c_1c": round(r["dollars_week_5c_1c"], 2), "dollars_week_5c_2c": round(r["dollars_week_5c_2c"], 2), "bh_p": r["p"], "note": "archive validate window to 2026-10-02; upper bound, not fill-checked; dollars scale linearly from the 10 contract cash (fees are per order, so 5 contracts differ slightly)"}})
    json.dump({"list": "SHADOW_LIST_V1", "date": "2026-11-16", "n": len(specs), "no_money_no_orders": True, "specs": specs}, open(os.path.join(out, "SHADOW_LIST_V1.json"), "w"), indent=1)
    md = ["# SHADOW_CLUSTER_MAP_NOV16 (Desk A, 2026-11-16)", "", "Source: the 190 rules that passed VALIDATE in ENGINE1 run 2 (1c PF 1.3+, 2c PF 1.0+, both halves, n 100+), re-scored with the same audited driver code (reproduces the listing to 1e-9; no new rule tried, m 2,347,488 unchanged). **None is a pass:** BH survivors 0 at m 2.35 million; these are candidates for a log-only forward test, upper bound, not fill-checked. Paper research figures only. Dollars a week = signals a day (validate) x cash edge at 1c per contract x 5 contracts x 7, scaled linearly from the 10 contract cash.", "",
          "Excluded before clustering: **%d Dogecoin rules** (7e: Dogecoin removed from the bot, any Dogecoin strategy declined). Admission: validate and search signals a day both at least %.0f (all 190 met it)." % (len(excl), MIN_SPD), "",
          "Clustering: near-duplicates merged when same market, same side rule, same exit, entry time within one bucket step (60 s) and price band within one band (5c); the cluster's best by dollars a week represents it. %d clusters of %d rules." % (len(clusters), len(rows)), "",
          "Families (cap 5 each): the entry condition kind (plain band, spread filter, momentum or volume filter, open-interest trigger) x the price region bought (cheap tail 5c to 35c, middle 35c to 85c, high 85c+), with the favourite-late shape (price band 17+ and 10 minutes or less left) as its own family, flagged as the closed gold L1 mechanism. Cap 3 per market.", "",
          "## Picks (ranked by dollars a week at 1c, 5 contracts)", "", "| # | spec | market | side | look (s left) | band | filter | exit | n | signals/day | PF 1c | PF 2c | edge 1c c/ct | edge 2c c/ct | $/wk 1c | $/wk 2c | family | cluster (size) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in specs:
        r = s["spec"]; p = s["paper_research"]
        md.append("| %d | %s | %s | %s | %d | %d | %s | %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %.1f | %.1f | %s | %d (%d) |" % (s["rank"], r["id"], r["market"], r["entry"]["side_rule"], r["entry"]["seconds_left"], r["entry"]["price_band_5c"], r["entry"]["filter"], r["exit"], p["validate_n"], p["signals_per_day"], p["pf_1c"], p["pf_2c"], p["edge_1c_cents_per_contract"], p["edge_2c_cents_per_contract"], p["dollars_week_5c_1c"], p["dollars_week_5c_2c"], s["family"], s["cluster"], s["cluster_size"]))
    md += ["", "Totals: %d picks; per market %s; per family %s." % (len(specs), dict(per_m), dict(per_f)), "", "## Flags (7e and uniqueness; nothing silently dropped)", ""]
    for s in specs:
        if s["flags"]: md.append("- **%s** (%s %s): %s" % (s["spec"]["id"], s["spec"]["market"], s["family"], "; ".join(s["flags"])))
    md += ["", "## All clusters (representative, size, why not picked if not)", "", "| cluster | market | family | best $/wk 1c | size | picked |", "|---|---|---|---|---|---|"]
    pc = {ci for ci, _ in picks}
    for ci, ms in enumerate(clusters):
        r = ms[0]; why = "picked" if ci in pc else ("market cap 3" if per_m[r["series"]] >= MAX_PER_MARKET else ("family cap 5" if per_f[r["family"]] >= MAX_PER_FAMILY else "beyond 25"))
        md.append("| %d | %s | %s | %.1f | %d | %s |" % (ci + 1, r["series"], r["family"], r["dollars_week_5c_1c"], len(ms), why))
    open(os.path.join(out, "SHADOW_CLUSTER_MAP_NOV16.md"), "w").write("\n".join(md) + "\n")
    print(len(specs), "picks;", len(clusters), "clusters;", dict(per_m), dict(per_f))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
