"""ENGPERPS lanes 1 and 6 runner (Desk A, Nov 16 2026): audited POOL1 loader (engine1_poolperps_load, allow line merged) -> engine1_perps_lanes.evaluate_lanes -> one JSON report. Page maxima come from Forensics' census TSV (column "page max"; the file must have a ticker column and that one); a name without a value is REFUSED, no default. Prints only the output path and the rule hashes; the report is read after its sha256 is committed. DEVELOPMENT, first week, one regime.
  python3 -I engine1_perps_lanes_run.py <dir holding the two stock perp extracts> <census.tsv> <m_carried> <out.json>"""
import sys, os, json, hashlib, csv
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_poolperps_load as PL, engine1_perps_lanes as L
def read_census(path):
    rows = list(csv.reader(open(path, encoding="utf-8"), delimiter="\\t")); head = [h.strip().lower() for h in rows[0]]
    ti = next((i for i, h in enumerate(head) if "ticker" in h or h == "name"), None); pi = next((i for i, h in enumerate(head) if h == "page max"), None)
    if ti is None or pi is None: raise SystemExit("REFUSED: the census has no ticker column or no 'page max' column: %r" % head)
    out = {}
    for r in rows[1:]:
        if len(r) > max(ti, pi) and r[pi].strip():
            try: out[r[ti].strip()] = float(r[pi].strip().rstrip("xX"))
            except ValueError: pass
    return out
def main(base, census, m_carried, out):
    cand, fund, counts, dropped = PL.load(base); lev = read_census(census)
    def levmax(n):
        if n not in lev: raise SystemExit("REFUSED: no page max in the census for " + n)
        return lev[n]
    rep = L.evaluate_lanes(cand, fund, levmax, int(m_carried))
    rep["loader_counts"] = counts; rep["names_dropped"] = dropped; rep["page_max_used"] = {n: lev[n] for n in sorted({x for v in rep["kept_baskets"].values() for x in v})}
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("engine1_perps.py", "engine1_driver.py", "engine1_poolperps.py", "engine1_poolperps_load.py", "engine1_perps_lanes.py", "engine1_perps_lanes_run.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
