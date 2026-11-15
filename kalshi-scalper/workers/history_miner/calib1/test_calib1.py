"""CALIB1 hand case (CALIB1_HAND_CASE_NOV15.md), invented rows only. Run: python3 -I test_calib1.py"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib1 as C

CL = 100_000
A = lambda x, y: abs(x - y) < 1e-12
k1 = {CL - 600: (0.20, 0.23), CL - 300: (0.10, 0.12), CL - 120: (0.0, 0.05)}
rows, miss = C.rows_for(k1, CL, "no")
assert [(L, s, round(a, 6), w) for L, s, a, w, _ in rows] == [(600, "yes", 0.23, False), (600, "no", 0.80, True), (300, "yes", 0.12, False), (300, "no", 0.90, True)], rows
assert miss == [(120, "not two-sided")]
assert [C.bucket(x) for x in (0.23, 0.80, 0.12, 0.90)] == [4, 16, 2, 18]
_, miss2 = C.rows_for({CL - 600: (0.2, 0.23), CL - 120: (0.2, 0.23)}, CL, "yes")
assert miss2 == [(300, "missing")]
assert C.bucket(0.25) == 5 and C.bucket(0.25 - 1e-12) == 5 and C.bucket(0.2499) == 4 and C.bucket(0.999) == 19
print("rows and buckets: ok")
s = C.stats([(0.20, True, 0.01), (0.22, False, 0.01), (0.24, True, 0.02), (0.22, True, 0.01)])
assert s["n"] == 4 and s["wins"] == 3 and A(s["win_rate"], 0.75) and A(s["mean_ask"], 0.22) and A(s["gap"], 0.53) and A(s["mean_fee1"], 0.02)
assert abs(s["z"] - 2.12 / math.sqrt(0.6856)) < 1e-12, s
print("stats: ok")
mk = lambda n, g: {"n": n, "gap": g, "mean_fee1": 0.02}
assert C.candidate(mk(300, 0.05), mk(320, 0.045)) and not C.candidate(mk(300, 0.05), mk(299, 0.05))
assert not C.candidate(mk(300, 0.05), mk(320, 0.039)) and not C.candidate(mk(300, -0.05), mk(320, -0.05))
print("candidate: ok")

# end to end on invented databases: void counted, a candidate printed with its neighbours (MIN_N lowered for the fixture only)
import sqlite3, tempfile
U = C.U
tmp = tempfile.mkdtemp()
for s in U.SOURCES:
    con = sqlite3.connect(os.path.join(tmp, s + ".sqlite"))
    con.execute("create table market (ticker, series, close_ts, result)"); con.execute("create table candle (ticker, end_ts, bid_c, ask_c)"); con.commit(); con.close()
con = sqlite3.connect(os.path.join(tmp, "l1b.sqlite"))
for i, (cl, res) in enumerate(((U.D(8, 10), "yes"), (U.D(8, 30), "yes"), (U.D(8, 11), "void"))):
    con.execute("insert into market values (?,?,?,?)", ("M%d" % i, "KXBTC15M", cl, res))
    con.execute("insert into candle values (?,?,?,?)", ("M%d" % i, cl - 600, 0.20, 0.22))
con.commit(); con.close()
C.MIN_N = 1
r = C.run(tmp)
assert r["counts"]["void"] == 1 and r["counts"]["missing_300"] == 2 and r["counts"]["missing_120"] == 2, r["counts"]
k = "KXBTC15M|600|yes|04"
assert k in r["candidates"] and set(r["table"][k]["neighbours"]) == {"KXBTC15M|600|yes|03", "KXBTC15M|600|yes|05"}, r["candidates"]
assert r["table"][k]["third1"]["n"] == 1 and r["table"][k]["third2"]["n"] == 1 and r["buckets_inspected"] == 2400
print("end to end: ok")
s300 = C.stats([(0.50, True, 0.01)] * 300)
assert abs(s300["p_pass_null"] - 0.082928) < 1e-6 and abs(s300["p_pass_null"] ** 2 - 0.006877) < 1e-6, s300["p_pass_null"]
assert "expected_chance_candidates_null" in r and r["buckets_eligible_300_both"] >= 1
print("null expectation: ok")
