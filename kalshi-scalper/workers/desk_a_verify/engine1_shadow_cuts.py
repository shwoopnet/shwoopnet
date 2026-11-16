"""ENGINE1 shadow spread cuts (Desk A, Nov 16 2026): the SEARCH tercile cuts of the spread filter, per series and bucket, exactly as engine1_driver.run builds them (SEARCH markets only, spread = cents(ask - bid) of the YES candle ending at close - bucket with 0 < bid < ask < 1; c1 = value at position ceil(n/3), c2 = ceil(2n/3), 1 based, sorted). Constants for the shadow runner: spread:low means spread_cents <= c1.
  python3 -I engine1_shadow_cuts.py <dir holding the two archive extracts> <out.json>      (Line B1 loader, SEARCH half only)"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D, engine1_enum as N, engine1_split as S
def main(base, out):
    wa, ca, wp, cp, wn, cn = L.load(base); table = {}
    for series in sorted(wa):
        if D.short(series) not in S.LAST_SEARCH: continue
        sm = [m for m in wa[series] if S.phase(D.short(series), m["close"]) == "search"]; row = {}
        for b in N.BUCKETS:
            sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
            cuts = N.spread_cuts(sp) if sp else None
            row[str(b)] = {"c1": cuts[0], "c2": cuts[1], "n_spreads": len(sp)} if cuts else {"c1": None, "c2": None, "n_spreads": 0}
        table[series] = row
    picks = {"SH1_01_HYPE": ("KXHYPE15M", 600), "SH1_03_ETH": ("KXETH15M", 660), "SH1_04_BTC": ("KXBTC15M", 180), "SH1_16_BNB": ("KXBNB15M", 420)}
    doc = {"note": "SEARCH tercile cuts of the spread filter from the archive SEARCH half only (ENGINE1 run 2 split constants), whole cents; spread:low = cents(ask - bid) <= c1. Constants: never recomputed on new data.", "picks": {k: dict(table[s][str(b)], series=s, bucket=b, spread_low_rule="spread_cents <= c1") for k, (s, b) in picks.items()}, "all_series_buckets": table,
           "rule_hashes": {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest() for f in ("engine1_core.py", "engine1_enum.py", "engine1_split.py", "engine1_driver.py", "engine1_shadow_cuts.py")}}
    json.dump(doc, open(out, "w"), indent=1, sort_keys=True); print("wrote", out)
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
