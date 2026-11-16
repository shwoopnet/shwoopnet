"""ENGINE1 perps pass 2 runner (Desk A, Nov 16 2026): SPY and QQQ (a second look after read 1), US 500 and US Tech 100 (first looks), funding booked. The loader opens only the three perps extracts named in its constants and the allow line (never the archive).
  python3 -I engine1_perps_run2.py <dir holding the .sqlite.xz extracts> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_perps as P
M_PRIOR = 504                                    # read 1's tries (SPY and QQQ, 252 rules each) stay in the BH denominator
def main(base, out):
    perps, drops, funding, fdrops = L.load_pass2(base)
    rep = P.run_all({k: [tuple(c) for c in v] for k, v in perps.items()}, funding=funding, m_prior=M_PRIOR)
    rep["header"] = "BH m = %d (read 1's 504 prior + %d new rules) before any result" % (rep["m_total"], rep["tried"])
    rep["second_look"] = "SPY and QQQ are a SECOND look at Nov 6 to 14 after read 1 printed 0 of 504 (rerun after a zero, disclosed); US 500 and US Tech 100 are first looks"
    rep["funding_note"] = "funding booked from the funding extract; sign convention 'positive: longs pay shorts' is from Kalshi's single stock help article and is ASSUMED for the index perps; an exit exactly at the 21:00 UTC print pays nothing (a convention: a candle ending at the print instant may be before it); weekend and missing prints leave the trade unbooked and out of the gates, counted in funding_unbooked_trades"
    rep["loader_drops"] = drops; rep["funding_drops"] = fdrops
    rep["run_note"] = "plumbing and counts read: with the 10 trade day floor nothing can pass on Nov 6 to 14; SPY and QQQ days were also read by read 1, PERPSCALP1 and OPENGAP1"
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_extract_load.py", "engine1_split.py", "engine1_perps.py", "engine1_perps_run2.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
