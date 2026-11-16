"""ENGINE1 run script, first pass (Desk A, Nov 16 2026): audited loader -> driver -> one JSON report. Archive binaries only; the perps block (time exits) is a separate driver not yet written.
  python3 -I engine1_run.py <dir holding the two .sqlite.xz extracts> <out.json>
Prints nothing but the output path and the rule hashes; the report is read only after its sha256 is committed."""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D
def summarize(lst):
    """Clusters of the bar-passers: counts by series, side rule, exit, filter feature, bucket, and by (series, side, exit); the largest single (series, side, exit) group and how many share one series and one side rule."""
    import collections
    c = lambda f: dict(collections.Counter(f(x) for x in lst).most_common())
    ssx = collections.Counter((x["series"], x["side"], x["exit"]) for x in lst); ss = collections.Counter((x["series"], x["side"]) for x in lst)
    return {"n": len(lst), "by_series": c(lambda x: x["series"]), "by_side": c(lambda x: x["side"]), "by_exit": c(lambda x: x["exit"]), "by_filter_feature": c(lambda x: x["filter"][0] if x["filter"] else "none"),
            "by_bucket": c(lambda x: x["bucket"]), "by_family": c(lambda x: x["family"]),
            "top_series_side_exit": ["%s|%s|%s %d" % (k[0], k[1], k[2], v) for k, v in ssx.most_common(8)], "top_series_side": ["%s|%s %d" % (k[0], k[1], v) for k, v in ss.most_common(8)], "max_in_one_series_side": max(ss.values()) if ss else 0}
def main(base, out):
    wa, ca, wp, cp, wn, cn = L.load(base)                       # first pass: archive and perps extracts only
    rep = D.run({"archive": wa})
    rep["loader_drops_archive"] = ca; rep["loader_drops_perps"] = cp; rep["perps_block"] = "not run (separate driver)"
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_run.py")}
    rep["bar_summary"] = summarize(rep.get("validate_bar_list", []))
    rep["tried_by_series"] = {"%s|%s" % k: v for k, v in rep["tried_by_series"].items()}      # JSON keys must be strings (the first attempt of run 1 died here, after the compute, before any print)
    json.dump(rep, open(out, "w"), indent=1, default=str)
    print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
