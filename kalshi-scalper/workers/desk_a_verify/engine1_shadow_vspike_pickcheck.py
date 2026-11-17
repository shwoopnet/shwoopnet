"""Head's extra check (Nov 17 2026): for the three V3 vspike picks, SEARCH and VALIDATE n and PF at 1c and 2c computed from the COMMITTED cuts file (not recomputed), to compare with the batch B run's validate rows.
  python3 -I engine1_shadow_vspike_pickcheck.py <dir holding the archive extract> <cuts.json> <batch B run json>"""
import sys, os, json, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D, engine1_enum as N, engine1_split as S, engine1_core as K, engine1_batchb2 as B2
PICKS = {"SH3_08_ETH": ("KXETH15M", 540, 14, "favourite", "mid", "H"), "SH3_11_ETH": ("KXETH15M", 540, 14, "favourite", "mid", "T"), "SH3_17_HYPE": ("KXHYPE15M", 420, 1, "cheap", "low", "M60")}
def main(base, cuts_path, run_path):
    wa = L.load(base)[0]; tab = json.load(open(cuts_path))["all_series_buckets"]; run = json.load(open(run_path))["validate_bar_list"]; bad = 0
    for pid, (series, b, band, rs, kl, x) in PICKS.items():
        row = tab[series]; cuts = {int(k): ((v["c1"], v["c2"]) if v["c1"] is not None else None) for k, v in row.items()}
        sm = [m for m in wa[series] if S.phase(D.short(series), m["close"]) == "search"]; vm = [m for m in wa[series] if S.phase(D.short(series), m["close"]) == "validate"]
        out = {}
        for nm, mk in (("SEARCH", sm), ("VALIDATE", vm)):
            g = B2.groups_f(mk, "vspike", cuts, None); items = g.get((b, band, rs, ("vspike", kl)), [])
            es = [D.to_core(m, ent) for m, ent in items]
            agg = {h: K.aggregate(es, x, h, D.CONTRACTS) for h in (0.01, 0.02)}
            out[nm] = (agg[0.01]["n"], agg[0.01]["pf"], agg[0.02]["pf"])
        r = [r for r in run if (r["series"], r["bucket"], r["band"], r["side"], r["exit"], tuple(r["filter"])) == (series, b, band, rs, x, ("vspike", kl))]
        ok = bool(r) and r[0]["n"] == out["VALIDATE"][0] and abs(r[0]["pf_1c"] - out["VALIDATE"][1]) < 1e-9 and abs(r[0]["pf_2c"] - out["VALIDATE"][2]) < 1e-9
        bad += 0 if ok else 1
        print(pid, "SEARCH n=%d pf1c=%.6f pf2c=%.6f | VALIDATE n=%d pf1c=%.6f pf2c=%.6f | run row: %s | equal at 1e-9: %s" % (out["SEARCH"] + out["VALIDATE"] + ((("n=%d pf1c=%.6f pf2c=%.6f" % (r[0]["n"], r[0]["pf_1c"], r[0]["pf_2c"])) if r else "none"), ok)))
    print("mismatches", bad)
if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
