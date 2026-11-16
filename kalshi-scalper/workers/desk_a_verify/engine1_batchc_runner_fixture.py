"""Fixture for the shadow runner's V4 features (Desk A, Nov 16 2026): invented cases, expected value and class for oiacc, ethmom3 and goldmom3, each checked here by hand arithmetic AND by the audited engine1_batchc functions. The runner's pure functions are gated against these lines.
  python3 -I engine1_batchc_runner_fixture.py <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_batchc as C, engine1_batchb as B, engine1_enum as N
def main(out):
    e = 100000; cases = []
    # oiacc: (oi_e - oi_e-180) - (oi_e-180 - oi_e-360); a candle is (end, bid, ask, last, volume, oi)
    for a, b, c, x in ((100, 110, 130, 10), (100, 110, 120, 0), (100, 120, 130, -10), (500, 400, 300, 0), (100, 100, 90, -10), (100, 90, 90, 10)):
        by = {e - 360: (e - 360, .5, .6, None, 1, a), e - 180: (e - 180, .5, .6, None, 1, b), e: (e, .5, .6, None, 1, c)}
        got = C.oiacc(by, e); assert got == x == (c - b) - (b - a), (a, b, c, got); cases.append({"feature": "oiacc", "oi_e_minus_360": a, "oi_e_minus_180": b, "oi_e": c, "expected_x": x, "expected_class": N.cls(x)})
    for name, hole in (("oi at e - 360 null", "a"), ("oi at e - 180 null", "b"), ("oi at e null", "c"), ("candle e - 180 absent", "x")):
        by = {e - 360: (e - 360, .5, .6, None, 1, 100), e - 180: (e - 180, .5, .6, None, 1, 110), e: (e, .5, .6, None, 1, 130)}
        if hole == "a": by[e - 360] = (e - 360, .5, .6, None, 1, None)
        if hole == "b": by[e - 180] = (e - 180, .5, .6, None, 1, None)
        if hole == "c": by[e] = (e, .5, .6, None, 1, None)
        if hole == "x": del by[e - 180]
        assert C.oiacc(by, e) is None; cases.append({"feature": "oiacc", "case": name, "expected_x": None, "expected_class": "missing"})
    # ethmom3 and goldmom3 (same function): the other market's mid at e minus the mid at e - 180, mid = (yes bid + yes ask) / 2, class by cls() with 1e-12
    for fname in ("ethmom3", "goldmom3"):
        for b0, a0, b1, a1, cl in ((.49, .51, .59, .61, "up"), (.59, .61, .49, .51, "down"), (.49, .51, .49, .51, "flat"), (.50, .52, .495, .525, "flat"), (.40, .42, .40, .4200001, "up")):
            idx = {e - 180: (e - 180, b0, a0, 0, 0, 0), e: (e, b1, a1, 0, 0, 0)}; x = C.xmom(idx, e); want = (b1 + a1) / 2 - (b0 + a0) / 2
            assert x == want and N.cls(x) == cl, (fname, x, cl); cases.append({"feature": fname, "other_e_minus_180": [b0, a0], "other_e": [b1, a1], "expected_x": want, "expected_class": cl})
        for name, idx in (("candle e - 180 absent", {e: (e, .5, .6, 0, 0, 0)}), ("candle e absent", {e - 180: (e - 180, .5, .6, 0, 0, 0)}), ("other market absent", None)):
            assert idx is None or C.xmom(idx, e) is None; cases.append({"feature": fname, "case": name, "expected_x": None, "expected_class": "missing"})
    json.dump({"fixture": "V4 runner features", "rules": {"cls": "up if x > 1e-12, down if x < -1e-12, else flat", "pairing": "the other series' market with the SAME close time; candles ending EXACTLY at e - 180 and at e, where e = close - the pick's seconds_left", "mid": "(yes_bid + yes_ask) / 2 of the candle's close fields; no two sided test", "oiacc": "(oi_e - oi_e-180) - (oi_e-180 - oi_e-360), the candles' open interest (open_interest_fp else open_interest), all three present and non-null"}, "pins": {"engine1_batchc.py": "ba77f70c7d86152539ad01cbd958d1056e3e78b40b3a568693f6ea444f77a279", "engine1_batchb.py": "68a5ab435d8246be30681a703179d88608b0384ce2ca50f4f6bad458cea07f1e", "engine1_enum.py": "e42ee1a45f67b76e8560cd9cbefac352fce9a765c8300bc04d5ce05a27e4d5a7"}, "n": len(cases), "cases": cases}, open(out, "w"), indent=1); print(len(cases), "cases")
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
