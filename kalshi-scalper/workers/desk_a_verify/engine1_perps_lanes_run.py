"""ENGPERPS lanes 1 and 6 runner (Desk A, Nov 16 2026): audited POOL1 loader (engine1_poolperps_load, allow line merged) -> engine1_perps_lanes.evaluate_lanes -> one JSON report. Page maxima come from Forensics' census TSV (PERPS_PAGE_MAX_20261116.tsv: columns ticker, class, page_max_leverage, page_max_source; values the owner pasted; "unknown" means none); a name without a value stays in the run with its margin and liquidation columns marked "no page max, not shown" (no default anywhere); a pass on a rule that trades such a name is printed but cannot be named for shadow or as a CANDIDATE until a page max is pinned for every name it trades. Prints only the output path and the rule hashes; the report is read after its sha256 is committed. DEVELOPMENT, first week, one regime.
  python3 -I engine1_perps_lanes_run.py <dir holding the two stock perp extracts> <census.tsv> <m_carried> <out.json>"""
import sys, os, json, hashlib, csv
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_poolperps_load as PL, engine1_perps_lanes as L
def read_census(path):
    """-> {ticker: (L, basis)}. Columns: ticker plus page_max (or page_max_leverage, page_max_owner_pasted); an optional size_max_known like "17.4x at $800 (owner ticket)": where it is present its number is the leverage used (the size-specific max) and the page max is only the small-size ceiling; the basis of every name is printed. "unknown" or empty = no value."""
    import re
    rows = list(csv.reader(open(path, encoding="utf-8"), delimiter="\t")); head = [h.strip().lower() for h in rows[0]]
    ti = next((i for i, h in enumerate(head) if "ticker" in h or h == "name"), None); pi = next((i for i, h in enumerate(head) if h in ("page_max", "page_max_leverage", "page_max_owner_pasted")), None); si = next((i for i, h in enumerate(head) if h == "size_max_known"), None)
    if ti is None or pi is None: raise SystemExit("REFUSED: the census has no ticker column or no page max column: %r" % head)
    out = {}
    for r in rows[1:]:
        if len(r) <= max(ti, pi): continue
        nm = r[ti].strip(); sz = r[si].strip() if si is not None and len(r) > si else ""; m = re.match(r"^\s*([0-9.]+)\s*x", sz) if sz else None
        try: pm = float(r[pi].strip().rstrip("xX")) if r[pi].strip() else None
        except ValueError: pm = None
        if m: out[nm] = (float(m.group(1)), "size-specific max %s (page max %s is the small-size ceiling)" % (sz, r[pi].strip()))
        elif pm is not None: out[nm] = (pm, "page max (small-size ceiling), no size-specific figure")
    return out
def main(base, census, m_carried, out):
    cand, fund, counts, dropped = PL.load(base); lev = read_census(census)
    no_pm = sorted(n for n in cand if n not in lev)                                     # a name with no pinned page max STAYS in the run (the Head, Nov 16): its margin and liquidation columns read "no page max, not shown"; no default anywhere; a pass that trades it cannot be named for shadow or as a CANDIDATE
    def levmax(n): return lev[n][0] if n in lev else None
    rep = L.evaluate_lanes(cand, fund, levmax, int(m_carried))
    rep["loader_counts"] = counts; rep["page_max_file_sha256"] = hashlib.sha256(open(census, "rb").read()).hexdigest(); rep["names_dropped"] = dropped; rep["names_without_page_max"] = no_pm; rep["page_max_used"] = {n: (list(lev[n]) if n in lev else None) for n in sorted({x for v in rep["kept_baskets"].values() for x in v})}      # [leverage used, basis] per name
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_perps.py", "engine1_driver.py", "engine1_poolperps.py", "engine1_poolperps_load.py", "engine1_perps_lanes.py", "engine1_perps_lanes_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
