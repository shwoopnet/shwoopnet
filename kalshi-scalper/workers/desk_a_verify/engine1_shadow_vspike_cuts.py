"""ENGINE1 shadow vspike cuts (Desk A, Nov 17 2026): the SEARCH tercile cuts of the vspike ratio (volume(e) / mean volume of the 5 candles ending e - 60 ... e - 300), per series and bucket, exactly as engine1_batchb2.feature_cuts builds them (SEARCH markets only, archive extract, N.spread_cuts on the ratios: c1 = ceil(n/3)-th, c2 = ceil(2n/3)-th sorted value; low <= c1, mid <= c2, else high). Constants for the shadow runner: never recomputed on forward or held-out markets.
  python3 -I engine1_shadow_vspike_cuts.py <dir holding the archive extract> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D, engine1_enum as N, engine1_split as S, engine1_batchb2 as B2
PICKS = {"SH3_08_ETH": ("KXETH15M", 540, "mid"), "SH3_11_ETH": ("KXETH15M", 540, "mid"), "SH3_17_HYPE": ("KXHYPE15M", 420, "low")}
def main(base, out):
    wa, ca, wp, cp, wn, cn = L.load(base); table = {}
    for series in sorted(wa):
        if D.short(series) not in S.LAST_SEARCH: continue
        sm = [m for m in wa[series] if S.phase(D.short(series), m["close"]) == "search"]
        cuts = B2.feature_cuts(sm, "vspike"); row = {}
        for b in N.BUCKETS:
            c = cuts[b]; row[str(b)] = {"c1": c[0], "c2": c[1]} if c else {"c1": None, "c2": None}
        table[series] = row
    doc = {"note": "SEARCH tercile cuts of vspike from the archive SEARCH half only (ENGINE1 split constants); floats as computed; class: low if x <= c1, mid if x <= c2, else high. Constants: never recomputed on new data. A candle volume is index 4 of the tuple; the six candles ending e, e-60, ..., e-300 must all exist with a non-null volume and the mean of the five earlier must be positive, else the feature is missing and there is no entry.",
           "all_series_buckets": table,
           "picks": {k: dict(table[s][str(b)], series=s, bucket=b, class_read=cl) for k, (s, b, cl) in PICKS.items()},
           "rule_hashes": {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest() for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_batchb2.py", "engine1_shadow_vspike_cuts.py")}}
    json.dump(doc, open(out, "w"), indent=1, sort_keys=True); print("wrote", out); print(json.dumps(doc["picks"], indent=0))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
