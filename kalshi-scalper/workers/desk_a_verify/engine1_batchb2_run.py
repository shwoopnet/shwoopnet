"""ENGINE1 batch B runner for ENGB1TIMESTOP, ENGB2VSPIKE and ENGB3SPRW (Desk A, Nov 16 2026): audited loader (Line B1 archive extract: the same SEARCH and VALIDATE data as run 2) -> engine1_batchb2.run_family -> one JSON report. Prints only the output path and the rule hashes; read the report after its sha256 is committed.
BH at m = 2,347,488 + this spec's tries, and again at the whole batch B m = 4,073,472.
  python3 -I engine1_batchb2_run.py <ENGB1TIMESTOP|ENGB2VSPIKE|ENGB3SPRW> <dir holding the archive extracts> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_batchb2 as B
M_FULL = 4073472
def main(spec, base, out):
    if spec not in ("ENGB1TIMESTOP", "ENGB2VSPIKE", "ENGB3SPRW"): sys.exit(__doc__)
    wa, ca, wp, cp, wn, cn = L.load(base)
    rep = B.run_family(wa, spec, m_full=M_FULL)
    rep["header"] = "BH m = %d now (%d prior + %d tries of %s), %d for the whole batch B, before any result" % (rep["m_now"], B.PRIOR_M, rep["tries_this_spec"], spec, M_FULL)
    rep["loader_drops_archive"] = ca
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_batchb2.py", "engine1_batchb2_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
