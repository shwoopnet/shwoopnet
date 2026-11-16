"""ENGINE1 perps pass 3 runner (Desk A, Nov 16 2026): gold, US 500, US Tech 100 from the back-pull extracts (Sep 10 to Oct 31), funding booked, ET clocks. The loader opens ONLY the two back-pull extracts.
  python3 -I engine1_perps_run3.py <dir holding the two .sqlite.xz extracts> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_perps as P, engine1_split as S
PRIOR_PERPS = 2184                               # passes 1 and 2 (504 + 1680)
PERPGEN_RULES = 100000                           # PERPGEN NONCRYPTO 100,000 (rule, group) pairs, upper bound per name (Auditor B, Nov 16): m_prior 102,184
def main(base, out):
    if PERPGEN_RULES is None: sys.exit("REFUSED: PERPGEN_RULES is unset (the BH prior must include PERPGEN's exact rule count)")
    M_PRIOR = PRIOR_PERPS + PERPGEN_RULES
    perps, drops, funding, fdrops = L.load_pass3(base)
    rep = P.run_all({k: [tuple(c) for c in v] for k, v in perps.items()}, funding=funding, m_prior=M_PRIOR, last_search=S.LAST_SEARCH_P3)
    rep["header"] = "BH m = %d (perps passes 1 and 2: %d + PERPGEN NONCRYPTO %d (rule, group) pairs, upper bound per name + %d new rules) before any result" % (rep["m_total"], PRIOR_PERPS, PERPGEN_RULES, rep["tried"])
    rep["label"] = "all of Sep 4 to Oct 31 is DEVELOPMENT, not a clean held-out; the forward Nov 15 on read (ENGINE1-PERPS-F) is the real test"
    rep["pass3_note"] = "gold SEARCH 2026-09-10 to 09-30 and VALIDATE 10-01 to 10-31; US 500 SEARCH 10-06 to 10-18, VALIDATE 10-19 to 10-30; US Tech 100 SEARCH 10-14 to 10-21, VALIDATE 10-22 to 10-30 (under the 10 trade day floor: plumbing and counts only); ET clocks (EDT until 2026-11-01 06:00 UTC); funding booked from the extract's OWN print timestamps (entry candle end < print < exit candle end, whatever the hour; gold prints at 14:00 UTC), no schedule constant; a position overlapping a stretch with no print (two prints more than 26 h apart, before the first, or after the last plus 26 h) is unbooked, counted per ticker and out of the gates; gold's 14:00 UTC is NOT extrapolated beyond Oct 31; TC for gold stays the 16:00 ET candle; fee 12 bp taker (gate) and 5 bp maker (flag) ASSUMED; gold's weekend candles used as they are"
    rep["funding_prints"] = {tk: len(v) for tk, v in funding.items()}
    rep["funding_cross_check"] = {tk: {"prints": len(v), "not_at_20_00Z": sum(1 for t in v if t % 86400 != 72000)} for tk, v in funding.items() if tk != "KXGOLDPERP"}    # a CROSS-CHECK of the 16:00 ET schedule for the two index perps only; gold's prints (14:00 UTC) are booked as they are
    rep["gold_print_hours_utc"] = sorted({(t % 86400) // 3600 for t in funding.get("KXGOLDPERP", {})})
    rep["loader_drops"] = drops; rep["funding_drops"] = fdrops
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_extract_load.py", "engine1_split.py", "engine1_perps.py", "engine1_perps_run3.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
