"""btcmom3 fixture for the shadow runner (Desk A, Nov 16 2026). From the archive extract, takes up to 4 cases per class (up, down, flat) and 4 missing-candle cases, each with the non-Bitcoin market, its close, the look time (e = close - seconds_left), the two Bitcoin candles' yes_bid and yes_ask closes (or null), the expected x and class. Pure read of audited loader output; no rule, no m.
  python3 -I engine1_btcmom3_fixture.py <dir holding the archive extracts> <out.json>"""
import sys, os, json
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_batchb as B, engine1_enum as N
def main(base, out):
    wa = L.load(base)[0]; idx = B.btc_index(wa[B.BTC]) if hasattr(B, "btc_index") else None
    if idx is None:
        idx = {m["close"]: {c[0]: c for c in m["candles"] if c[0] <= m["close"]} for m in wa[B.BTC]}
    cases = {"up": [], "down": [], "flat": [], "missing": []}
    for s in ("KXETH15M", "KXHYPE15M", "KXXRP15M", "KXSOL15M", "KXBNB15M", "KXNEAR15M"):
        for m in wa.get(s, []):
            for b in (600, 480, 360):
                e = m["close"] - b; bt = idx.get(m["close"])
                a = bt.get(e - 180) if bt else None; z = bt.get(e) if bt else None
                x = B.btcmom3(bt, e) if bt else None
                k = "missing" if x is None else N.cls(x)
                if len(cases[k]) < 5 and (len(cases[k]) == 0 or cases[k][-1]["market"] != s or True) and sum(1 for c in cases[k] if c["market"] == s) < 1:
                    cases[k].append({"market": s, "close": m["close"], "seconds_left": b, "e": e, "btc_candle_e_minus_180": None if a is None else {"end": a[0], "yes_bid": a[1], "yes_ask": a[2]}, "btc_candle_e": None if z is None else {"end": z[0], "yes_bid": z[1], "yes_ask": z[2]}, "expected_x": x, "expected_class": k})
    flat = [c for v in cases.values() for c in v]
    json.dump({"fixture": "btcmom3", "rule": "x = (yes_bid+yes_ask)/2 at e minus the same at e-180, Bitcoin KXBTC15M with the same close; up if x > 1e-12, down if x < -1e-12, else flat; missing if either candle absent", "pins": {"engine1_batchb.py": "68a5ab435d8246be30681a703179d88608b0384ce2ca50f4f6bad458cea07f1e", "engine1_core.py": "53317e4b56a8328fb616d460d5cb4597af13a2b9020d73aefaa37717439694bf"}, "n": len(flat), "cases": flat}, open(out, "w"), indent=1)
    print({k: len(v) for k, v in cases.items()})
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
