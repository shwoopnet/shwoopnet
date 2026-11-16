"""ENGINE1 perps block runner (Desk A, Nov 16 2026): audited loader -> perps driver -> one JSON report. The loader reads the archive extract too and ignores it (no archive data reaches the perps driver).
  python3 -I engine1_perps_run.py <dir holding the two .sqlite.xz extracts> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_perps as P
def main(base, out):
    wa, ca, wp, cp, wn, cn = L.load(base)
    rep = P.run_all({k: [tuple(c) for c in v] for k, v in wp.items() if k in ("KXSPYPERP", "KXQQQPERP", "KXNVDAPERP", "KXAAPLPERP")})
    rep["loader_drops_perps"] = cp
    rep["boundary_note"] = "SEARCH exits may read up to 30 minutes of prices after the SEARCH/VALIDATE date boundary (candles are not cut at the boundary for an exit)"
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_extract_load.py", "engine1_split.py", "engine1_perps.py", "engine1_perps_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
