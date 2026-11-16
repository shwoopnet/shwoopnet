"""ENGPERPS lanes 1 and 6 runner (Desk A, Nov 16 2026): audited POOL1 loader (engine1_poolperps_load, allow line merged) -> engine1_perps_lanes.evaluate_lanes -> one JSON report. Page maxima come from Forensics' census TSV (PERPS_PAGE_MAX_20261116.tsv: columns ticker, class, page_max_leverage, page_max_source; values the owner pasted; "unknown" means none); a name without a value is REFUSED (removed from the run and printed), no default; a basket left under 3 names is dropped by the engine. Prints only the output path and the rule hashes; the report is read after its sha256 is committed. DEVELOPMENT, first week, one regime.
  python3 -I engine1_perps_lanes_run.py <dir holding the two stock perp extracts> <census.tsv> <m_carried> <out.json>"""
import sys, os, json, hashlib, csv
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_poolperps_load as PL, engine1_perps_lanes as L
def read_census(path):
    rows = list(csv.reader(open(path, encoding="utf-8"), delimiter="\t")); head = [h.strip().lower() for h in rows[0]]
    ti = next((i for i, h in enumerate(head) if "ticker" in h or h == "name"), None); pi = next((i for i, h in enumerate(head) if h in ("page_max_leverage", "page_max_owner_pasted")), None)
    if ti is None or pi is None: raise SystemExit("REFUSED: the census has no ticker column or no 'page max' column: %r" % head)
    out = {}
    for r in rows[1:]:
        if len(r) > max(ti, pi) and r[pi].strip():
            try: out[r[ti].strip()] = float(r[pi].strip().rstrip("xX"))
            except ValueError: pass
    return out
def main(base, census, m_carried, out):
    cand, fund, counts, dropped = PL.load(base); lev = read_census(census)
    refused = sorted(n for n in cand if n not in lev)                                   # a name with no page max (the census says 'unknown') is REFUSED: removed from the run and printed, never given a default
    cand = {n: v for n, v in cand.items() if n in lev}
    def levmax(n):
        if n not in lev: raise SystemExit("REFUSED: no page max in the census for " + n)
        return lev[n]
    rep = L.evaluate_lanes(cand, fund, levmax, int(m_carried))
    rep["loader_counts"] = counts; rep["page_max_file_sha256"] = hashlib.sha256(open(census, "rb").read()).hexdigest(); rep["names_dropped"] = dropped; rep["names_refused_no_page_max"] = refused; rep["page_max_used"] = {n: lev[n] for n in sorted({x for v in rep["kept_baskets"].values() for x in v})}
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_perps.py", "engine1_driver.py", "engine1_poolperps.py", "engine1_poolperps_load.py", "engine1_perps_lanes.py", "engine1_perps_lanes_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
