"""ENGINE1 batch C runner (Desk A, Nov 16 2026): audited loader (Line B1 archive extract: the same SEARCH and VALIDATE data as run 2) -> engine1_batchc.run_c -> one JSON report. Prints only the output path and the rule hashes; read the report after its sha256 is committed. BH at m = the Head's carried number (6,290,660 on Nov 16; pass 7,492,484 as the argument from Nov 17) plus this spec's tries, and again at the whole batch C m.
  python3 -I engine1_batchc_run.py <ENGC1ETHMOM|ENGC2OIACC|ENGC3TOD|ENGC4GOLDX> <dir holding the archive extracts> <m_carried> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_batchc as C
BATCH_C_TRIES = 1201824
def main(spec, base, m_carried, out):
    if spec not in C.SPECS: sys.exit(__doc__)
    wa, ca, wp, cp, wn, cn = L.load(base)
    rep = C.run_c(wa, spec, prior_m=int(m_carried), m_full=int(m_carried) + BATCH_C_TRIES)
    rep["header"] = "BH m = %d now (%d carried + %d tries of %s), %d for the whole batch C, before any result" % (rep["m_now"], int(m_carried), rep["tries_this_spec"], spec, int(m_carried) + BATCH_C_TRIES)
    rep["loader_drops_archive"] = ca
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_extract_load.py", "engine1_batchb.py", "engine1_batchc.py", "engine1_batchc_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
