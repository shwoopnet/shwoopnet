"""ENGPERPS lanes 1 and 6 runner (Desk A, Nov 16 2026): audited POOL1 loader (engine1_poolperps_load, allow line merged) -> engine1_perps_lanes.evaluate_lanes -> one JSON report. Page maxima come from Forensics' census TSV (PERPS_PAGE_MAX_20261116.tsv: columns ticker, class, page_max_leverage, page_max_source; values the owner pasted; "unknown" means none); a name without a value stays in the run with its margin and liquidation columns marked "no page max, not shown" (no default anywhere); a pass on a rule that trades such a name is printed but cannot be named for shadow or as a CANDIDATE until a page max is pinned for every name it trades. Prints only the output path and the rule hashes; the report is read after its sha256 is committed. DEVELOPMENT, first week, one regime.
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
    no_pm = sorted(n for n in cand if n not in lev)                                     # a name with no pinned page max STAYS in the run (the Head, Nov 16): its margin and liquidation columns read "no page max, not shown"; no default anywhere; a pass that trades it cannot be named for shadow or as a CANDIDATE
    def levmax(n): return lev.get(n)
    rep = L.evaluate_lanes(cand, fund, levmax, int(m_carried))
    rep["loader_counts"] = counts; rep["page_max_file_sha256"] = hashlib.sha256(open(census, "rb").read()).hexdigest(); rep["names_dropped"] = dropped; rep["names_without_page_max"] = no_pm; rep["page_max_used"] = {n: lev.get(n) for n in sorted({x for v in rep["kept_baskets"].values() for x in v})}
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_perps.py", "engine1_driver.py", "engine1_poolperps.py", "engine1_poolperps_load.py", "engine1_perps_lanes.py", "engine1_perps_lanes_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
