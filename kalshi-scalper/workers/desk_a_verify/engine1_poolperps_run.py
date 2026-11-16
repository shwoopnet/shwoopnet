"""ENGPERPS_POOL1 runner (Desk A, Nov 16 2026): audited loader -> engine1_poolperps.evaluate -> one JSON report. Prints only the output path and the rule hashes; the report is read after its sha256 is committed. DEVELOPMENT, funding cadence unverified.
  python3 -I engine1_poolperps_run.py <dir holding the two stock perp extracts> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_poolperps_load as L, engine1_poolperps as W
def main(base, out):
    cand, fund, counts, dropped = L.load(base)
    rep = W.evaluate(cand, fund)
    rep["loader_counts"] = counts; rep["names_dropped"] = dropped; rep["funding_prints_by_name"] = {k: len(v) for k, v in fund.items()}
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_perps.py", "engine1_driver.py", "engine1_poolperps.py", "engine1_poolperps_load.py", "engine1_poolperps_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
