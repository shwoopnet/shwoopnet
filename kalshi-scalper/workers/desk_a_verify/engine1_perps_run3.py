"""ENGINE1 perps pass 3 runner (Desk A, Nov 16 2026): gold, US 500, US Tech 100 from the back-pull extracts (Sep 10 to Oct 31), funding booked, ET clocks. The loader opens ONLY the two back-pull extracts.
  python3 -I engine1_perps_run3.py <dir holding the two .sqlite.xz extracts> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_perps as P, engine1_split as S
M_PRIOR = 2184                                   # passes 1 and 2 (504 + 1680)
def main(base, out):
    perps, drops, funding, fdrops = L.load_pass3(base)
    rep = P.run_all({k: [tuple(c) for c in v] for k, v in perps.items()}, funding=funding, m_prior=M_PRIOR, last_search=S.LAST_SEARCH_P3)
    rep["header"] = "BH m = %d (passes 1 and 2: %d prior + %d new rules) before any result" % (rep["m_total"], M_PRIOR, rep["tried"])
    rep["pass3_note"] = "gold SEARCH 2026-09-10 to 09-30 and VALIDATE 10-01 to 10-31; US 500 SEARCH 10-06 to 10-18, VALIDATE 10-19 to 10-30; US Tech 100 SEARCH 10-14 to 10-21, VALIDATE 10-22 to 10-30 (under the 10 trade day floor: plumbing and counts only); ET clocks (EDT until 2026-11-01 06:00 UTC); funding booked from the back-pull funding extract, a missing print leaves the trade unbooked and out of the gates; fee 12 bp taker (gate) and 5 bp maker (flag) ASSUMED; gold's weekend candles used as they are"
    rep["loader_drops"] = drops; rep["funding_drops"] = fdrops
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_extract_load.py", "engine1_split.py", "engine1_perps.py", "engine1_perps_run3.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
