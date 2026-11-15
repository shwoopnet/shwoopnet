"""UNDERDOG2X hand case (UNDERDOG2X_HAND_CASE_NOV15.md), invented candles only. Run: python3 -I test_underdog2x.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import underdog2x as U

CL = 100_000
A = lambda x, y: abs(x - y) < 1e-12
q = lambda b, a: (b, a)

# entry
u1 = {CL - 700: q(0.70, 0.72), CL - 650: q(0.76, 0.78), CL - 600: q(0.78, 0.80)}
assert U.entry(u1, CL) == {"side": "no", "e": 0.24, "end": CL - 650}, U.entry(u1, CL)
assert U.entry({CL - 550: q(0.20, 0.22)}, CL) is None
assert U.entry({CL - 700: q(0.0, 0.22), CL - 650: q(0.21, 0.23)}, CL) == {"side": "yes", "e": 0.23, "end": CL - 650}
assert U.entry({CL - 700: q(0.18, 0.20)}, CL)["e"] == 0.20 and U.entry({CL - 700: q(0.23, 0.25)}, CL)["e"] == 0.25
assert U.entry({CL - 700: q(0.24, 0.26)}, CL) is None
print("entry: ok")

en = {"side": "yes", "e": 0.22, "end": CL - 700}
def run(c, v, h, res):
    n, legs = U.plan(c, CL, en, v)
    return U.net_per_contract(0.22, h, n, legs, res, "yes")

v1 = {CL - 700: q(0.20, 0.22), CL - 400: q(0.30, 0.32), CL - 240: q(0.45, 0.47), CL - 180: q(0.40, 0.42), CL - 60: q(0.90, 0.92)}
assert A(run(v1, "a", 0, "yes"), 0.190) and A(run(v1, "b", 0, "yes"), 0.190) and A(run(v1, "c", 0, "yes"), 0.425), (run(v1, "c", 0, "yes"))
v2 = {CL - 700: q(0.20, 0.22), CL - 400: q(0.30, 0.32), CL - 180: q(0.25, 0.27), CL - 60: q(0.50, 0.52)}
assert A(run(v2, "a", 0, "no"), -0.010) and A(run(v2, "b", 0, "no"), 0.240) and A(run(v2, "c", 0, "no"), 0.005), (run(v2, "a", 0, "no"), run(v2, "c", 0, "no"))
v3 = {CL - 700: q(0.20, 0.22), CL - 400: q(0.30, 0.32), CL - 180: q(0.30, 0.32), CL - 60: q(0.35, 0.37)}
assert A(run(v3, "a", 0, "yes"), 0.040) and A(run(v3, "b", 0, "yes"), 0.760) and A(run(v3, "c", 0, "yes"), 0.765)
assert A(run(v1, "a", 0.01, "yes"), 0.170)
assert A(run(v3, "b", 0, "void"), -0.02)
print("exits: ok")

assert U.third("KXBTC15M", U.D(8, 24)) == 1 and U.third("KXBTC15M", U.D(8, 25)) == 2 and U.third("KXBTC15M", U.D(9, 13)) == 3
assert U.third("KXEURUSD15M", U.D(9, 28)) == 2 and U.third("KXSOL15M", U.D(9, 17)) == 3
s = U.summarise([{"ticker": str(i), "close": i, "third": 1 if i < 2 else 2, "day": "d%d" % i, "net": v} for i, v in enumerate((0.2, -0.1, 0.3, -0.3))])
assert A(s["pf"], 1.25) and A(s["pf_third1"], 2.0) and A(s["pf_third2"], 1.0) and s["n_third1"] == 2
print("thirds and summary: ok")

# loader: cut, third 3 and duplicate sources dropped before candles or results are read
import sqlite3, tempfile
tmp = tempfile.mkdtemp()
for s in U.SOURCES:
    con = sqlite3.connect(os.path.join(tmp, s + ".sqlite"))
    con.execute("create table market (ticker, series, close_ts, result)"); con.execute("create table candle (ticker, end_ts, bid_c, ask_c)")
    con.commit(); con.close()
def put(src, t, ser, cl, res):
    con = sqlite3.connect(os.path.join(tmp, src + ".sqlite"))
    con.execute("insert into market values (?,?,?,?)", (t, ser, cl, res)); con.execute("insert into candle values (?,?,?,?)", (t, cl - 700, 0.20, 0.22))
    con.execute("insert into candle values (?,?,?,?)", (t, cl + 60, 0.5, 0.6)); con.commit(); con.close()
put("l1b", "A", "KXBTC15M", U.D(8, 10), "yes")          # third 1, kept
put("book", "A", "KXBTC15M", U.D(8, 10), "no")          # duplicate, later source
put("book", "B", "KXBTC15M", U.D(9, 20), "yes")         # third 3: dropped
put("alts2", "C", "KXXRP15M", U.D(10, 5), "yes")        # after the cut: dropped
put("rep", "E", "KX10YRRATE15M", U.D(9, 1), "yes")      # not in the 19: dropped
mk, cd, dr = U.load(tmp)
assert set(mk) == {"A"} and mk["A"][2] == "yes" and dr == {"dup_later_source": 1, "third3_heldout": 1, "on_or_after_cut": 2}, (mk, dr)
assert list(cd["A"]) == [U.D(8, 10) - 700]                # the after-close candle dropped
print("loader: ok")
put("rep", "S1", "KXSOL15M", 1790760600, "yes")           # SOL at its own cut: dropped
put("rep", "S2", "KXSOL15M", U.D(8, 20), "yes")           # SOL third 1: kept
mk, cd, dr = U.load(tmp)
assert set(mk) == {"A", "S2"} and dr["on_or_after_cut"] == 3, (mk, dr)
print("sol cut: ok")
