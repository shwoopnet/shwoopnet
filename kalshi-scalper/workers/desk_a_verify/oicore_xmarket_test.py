"""Test of oicore_xmarket on the hand case of OICORE_XMARKET_REGISTRATION_NOV17.md. python3 -I oicore_xmarket_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oicore_xmarket as X
def mk(tk, close, r, result, ent=(0.20, 0.24)):
    c = [(close - 360, 0.5, 0.52, 0.5, 1, 100), (close - 180, ent[0], ent[1], 0.5, 1, 100 + r) if r is not None else (close - 180, ent[0], ent[1], 0.5, 1, None)]
    return {"series": "KXT15M", "ticker": tk, "close": close, "result": result, "candles": c}
C0 = 1790000000
ms = [mk("A", C0, 20, "yes"), mk("B", C0 + 900, 0, "yes"), mk("C", C0 + 1800, 5, "yes"), mk("D", C0 + 2700, 30, "no")]        # D: r 30 fires too but is VALIDATE; A, B, C are SEARCH
ph = lambda key, ts: "search" if ts < C0 + 2000 else "validate"
assert X.rise(ms[0]) == 20 and X.p90([20, 0, 5]) == 20
out = X.run({"KXT15M": ms}, ph, min_rises=3)["KXT15M"]
assert out["cut"] == 20, out["cut"]
s = out["phases"]["search"]["1c"]; assert s["n"] == 1 and s["wins"] == 1 and abs(s["cents_per_contract"] - 73.6) < 1e-9, s          # one fire (A): +7.36 on 10 contracts = 73.6 cents a contract
assert abs(out["phases"]["validate"]["1c"]["cents_per_contract"] - (-26.4)) < 1e-9, out["phases"]["validate"]       # D: -2.64 / 10
assert out["skipped"].get("below cut") == 2, out["skipped"]
# the hand case's PF: with {7.36, -2.64}
import engine1_core as K
assert abs(K.pf([7.36, -2.64]) - 7.36 / 2.64) < 1e-9
# no entry when the cheap ask is outside 0.08..0.50, or the quote is not sellable
assert X.entry(mk("E", C0, 20, "yes", ent=(0.45, 0.55)))[0] is None and X.entry(mk("F", C0, 20, "yes", ent=(0.02, 0.05)))[0] is None
assert X.entry(mk("G", C0, 20, "yes", ent=(0.0, 0.2)))[0] is None
# a market whose own cut is not above 0 is reported
flat = [mk("H%d" % i, C0 + 900 * i, 0, "yes") for i in range(5)]; assert X.run({"KXT15M": flat}, ph, min_rises=3)["KXT15M"]["note"] == "no usable threshold"
# correlation needs 10 common days
assert X.corr({str(i): float(i) for i in range(12)}, {str(i): float(2 * i) for i in range(12)}) > 0.999999 and X.corr({"a": 1.0}, {"a": 1.0}) is None
# the Head's rules: fewer than 20 rises gives no threshold; the entry is the candle ending exactly close - 180 and no other candle
assert X.run({"KXT15M": ms}, ph)["KXT15M"]["note"] == "no usable threshold"
m2 = mk("Z", C0, 20, "yes", ent=(0.60, 0.62)); m2["candles"].append((C0 - 150, 0.20, 0.24, 0.2, 1, 120)); assert X.entry(m2)[0]["ask"] == 0.40, X.entry(m2)
m3 = mk("Y", C0, 20, "yes", ent=(0.45, 0.55)); m3["candles"].append((C0 - 150, 0.20, 0.24, 0.2, 1, 120)); assert X.entry(m3)[0] is None
print("ok")
