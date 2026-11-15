"""FAV10-X hand case (FAV10X_HAND_CASE_NOV15.md), invented rows only. Run: python3 -I test_fav10x.py"""
import os, sys, sqlite3, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fav10x as F
X, U = F.X, F.U
CL = 100_000
A = lambda x, y: abs(x - y) < 1e-12
assert A(X.net(0.90, 0.0, None, "yes", "yes", 1), 0.09) and A(X.net(0.90, 0.01, None, "yes", "yes", 1), 0.08) and A(X.net(0.90, 0.02, None, "yes", "yes", 1), 0.07)
assert A(X.net(0.90, 0.0, None, "yes", "yes", 10), 0.093)
en = F.entry({CL - 600: (0.11, 0.13)}, CL)
assert en == {"side": "no", "e": 0.89, "entry_end": CL - 600} and A(X.net(0.89, 0.0, None, "no", "no", 1), 0.10)
assert A(X.net(0.88, 0.0, None, "no", "yes", 1), -0.89) and A(X.net(0.90, 0.0, None, "void", "yes", 1), -0.01)
assert F.entry({CL - 640: (0.50, 0.52), CL - 570: (0.88, 0.90)}, CL)["e"] == 0.90
assert F.entry({CL - 560: (0.88, 0.90)}, CL) is None and F.entry({CL - 600: (0.92, 0.93)}, CL) is None
assert F.entry({CL - 600: (0.0, 0.90)}, CL) == "not two-sided"
print("engine: ok")
mk = lambda pf, h1, h2: {"pf": pf, "pf_half1": h1, "pf_half2": h2}
s = {0.0: mk(2, 2, 2), 0.01: mk(1.3, 1.0, 1.2), 0.02: mk(1.0, 0.5, 0.5)}
assert F.verdict("KXBTC15M", 100, s) == "PASS" and F.verdict("KXSILVER15M", 100, s) == "fail"
s[0.01] = mk(1.29, 1.0, 1.2); assert F.verdict("KXBTC15M", 100, s) == "fail"
assert F.verdict("KXBTC15M", 99, s) == "no evidence at n = 99"
assert "KXXRP15M" not in F.SERIES and len(F.SERIES) == 18
print("verdict: ok")
tmp = tempfile.mkdtemp()
for src in U.SOURCES:
    con = sqlite3.connect(os.path.join(tmp, src + ".sqlite"))
    con.execute("create table market (ticker, series, close_ts, result)"); con.execute("create table candle (ticker, end_ts, bid_c, ask_c)"); con.commit(); con.close()
con = sqlite3.connect(os.path.join(tmp, "l1b.sqlite"))
for t, ser, cl, res in (("A", "KXBTC15M", U.D(9, 20), "yes"), ("B", "KXBTC15M", U.D(10, 5), "yes"), ("C", "KXXRP15M", U.D(8, 10), "yes"),
                        ("S", "KXSOL15M", 1790760600, "yes")):
    con.execute("insert into market values (?,?,?,?)", (t, ser, cl, res)); con.execute("insert into candle values (?,?,?,?)", (t, cl - 600, 0.88, 0.90))
con.commit(); con.close()
r = F.run(tmp)
assert r["markets_read"] == 1 and r["series"]["KXBTC15M"]["n"] == 1 and r["series"]["KXBTC15M"]["wins"] == 1   # third 3 kept, cut and XRP and SOL cut dropped
assert r["series"]["KXBTC15M"]["verdict"] == "no evidence at n = 1" and "gold_flag" in r["series"]["KXGOLD15M"] and r["tries"] == 18
print("loader: ok")
