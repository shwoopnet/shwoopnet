"""ENGINE1 run script, first pass (Desk A, Nov 16 2026): audited loader -> driver -> one JSON report. Archive binaries only; the perps block (time exits) is a separate driver not yet written.
  python3 -I engine1_run.py <dir holding the two .sqlite.xz extracts> <out.json>
Prints nothing but the output path and the rule hashes; the report is read only after its sha256 is committed."""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D
def main(base, out):
    wa, ca, wp, cp, wn, cn = L.load(base)                       # first pass: archive and perps extracts only
    rep = D.run({"archive": wa})
    rep["loader_drops_archive"] = ca; rep["loader_drops_perps"] = cp; rep["perps_block"] = "not run (separate driver)"
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_run.py")}
    rep["tried_by_series"] = {"%s|%s" % k: v for k, v in rep["tried_by_series"].items()}      # JSON keys must be strings (the first attempt of run 1 died here, after the compute, before any print)
    json.dump(rep, open(out, "w"), indent=1, default=str)
    print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
