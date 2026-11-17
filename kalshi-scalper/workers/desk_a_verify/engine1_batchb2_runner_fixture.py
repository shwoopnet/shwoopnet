"""Fixture for the shadow runner's V3 features (Desk A, Nov 17 2026): invented cases, expected value and class for swid and vspike, each checked by hand arithmetic AND by the audited engine1_batchb2 functions. The runner's pure functions are gated against these lines.
  python3 -I engine1_batchb2_runner_fixture.py <out.json>"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_batchb2 as B, engine1_enum as N
def main(out):
    e = 100000; cases = []; CUT = (0.7, 1.1)
    # swid: cents(ask - bid) at e minus the same at e - 180; both candles present and two sided (0 < bid < ask < 1); class up > 0, flat 0, down < 0 (cls, 1e-12)
    for b0, a0, b1, a1, x in ((.50, .51, .50, .52, 1), (.50, .52, .50, .52, 0), (.50, .53, .50, .52, -1), (.40, .41, .40, .46, 5), (.60, .64, .60, .61, -3)):
        by = {e - 180: (e - 180, b0, a0, None, 1, 1), e: (e, b1, a1, None, 1, 1)}
        got = B.swid(by, e); assert got == x == round((a1 - b1) * 100) - round((a0 - b0) * 100), (got, x)
        cases.append({"feature": "swid", "e_minus_180": [b0, a0], "e": [b1, a1], "expected_x": x, "expected_class": N.cls(x)})
    for name, by in (("candle e - 180 absent", {e: (e, .5, .52, None, 1, 1)}), ("candle e absent", {e - 180: (e - 180, .5, .52, None, 1, 1)}), ("e - 180 not two sided (bid 0)", {e - 180: (e - 180, 0, .52, None, 1, 1), e: (e, .5, .52, None, 1, 1)}), ("e crossed or locked (bid = ask)", {e - 180: (e - 180, .5, .52, None, 1, 1), e: (e, .52, .52, None, 1, 1)}), ("e ask = 1", {e - 180: (e - 180, .5, .52, None, 1, 1), e: (e, .5, 1.0, None, 1, 1)})):
        assert B.swid(by, e) is None; cases.append({"feature": "swid", "case": name, "expected_x": None, "expected_class": "missing"})
    # vspike: volume(e) / mean(volume of the candles ending e - 60 ... e - 300), volume = candle tuple index 4; all six present and non-null, mean positive
    def cand(vs): return {t: (t, .5, .52, None, v, 1) for t, v in zip((e, e - 60, e - 120, e - 180, e - 240, e - 300), vs)}
    for vs, x in (((10, 10, 10, 10, 10, 10), 1.0), ((20, 10, 10, 10, 10, 10), 2.0), ((5, 10, 10, 10, 10, 10), 0.5), ((7, 10, 20, 0, 5, 15), 0.7), ((0, 10, 10, 10, 10, 10), 0.0)):
        got = B.vspike(cand(vs), e); want = vs[0] / (sum(vs[1:]) / 5.0); assert got == want and abs(got - x) < 1e-12, (vs, got, x)
        k = B.klass("vspike", got, CUT); cases.append({"feature": "vspike", "volumes_e_to_e_minus_300_step_60": list(vs), "cuts_used_in_this_case": list(CUT), "expected_x": want, "expected_class": k})
    for name, by in (("volume at e null", None), ("volume at e - 120 null", None), ("candle e - 240 absent", None), ("mean of the five is 0", None)):
        vs = [10] * 6
        by = cand(vs)
        if name == "volume at e null": by[e] = (e, .5, .52, None, None, 1)
        if name == "volume at e - 120 null": by[e - 120] = (e - 120, .5, .52, None, None, 1)
        if name == "candle e - 240 absent": del by[e - 240]
        if name == "mean of the five is 0": by = cand((5, 0, 0, 0, 0, 0))
        assert B.vspike(by, e) is None; cases.append({"feature": "vspike", "case": name, "expected_x": None, "expected_class": "missing"})
    edge = [("at c1 (low)", .7, "low"), ("just over c1 (mid)", .7000001, "mid"), ("at c2 (mid)", 1.1, "mid"), ("just over c2 (high)", 1.1000001, "high")]
    for name, x, k in edge: assert B.klass("vspike", x, CUT) == k; cases.append({"feature": "vspike", "case": "class edge: " + name, "cuts_used_in_this_case": list(CUT), "expected_x": x, "expected_class": k})
    json.dump({"fixture": "V3 runner features", "rules": {"swid": "cents(ask - bid) of the entry candle (ends at e = close - the pick's seconds_left) minus the same at the candle ending EXACTLY e - 180; each candle must exist and have 0 < yes_bid < yes_ask < 1, else missing (no entry); class up if x > 1e-12, down if x < -1e-12, else flat (cls); x is a whole number of cents", "vspike": "volume(e) / mean(volume of the 5 candles ending e - 60, e - 120, e - 180, e - 240, e - 300); volume is index 4 of the candle tuple (volume_fp, null means missing); all six candles must exist with a non-null volume and the mean must be > 0, else missing; class low if x <= c1, mid if x <= c2, else high, with c1 and c2 read from SHADOW_VSPIKE_CUTS_V1.json for the pick's series and bucket", "entry_candle": "also needs 0 < bid < ask < 1 at e, as for every ENGINE1 entry"}, "pins": {f: hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f), "rb").read()).hexdigest() for f in ("engine1_batchb2.py", "engine1_batchb.py", "engine1_enum.py")}, "n": len(cases), "cases": cases}, open(out, "w"), indent=1); print(len(cases), "cases")
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
