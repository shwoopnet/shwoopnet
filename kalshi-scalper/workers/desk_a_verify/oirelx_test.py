"""python3 -I oirelx_test.py : the hand case of OIRELX_HAND_CASE_NOV15.md on invented rows."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oirelx as X
base = 1_790_000_000
A = {1: (1000, 1300, (0.20, 0.22), (0.23, 0.25), "yes"), 2: (1000, 1100, (0.20, 0.22), (0.23, 0.25), "yes"), 3: (1000, 1400, (0.80, 0.82), (0.78, 0.80), "no"),
     4: (1000, 1300, (0.28, 0.30), (0.28, 0.30), "no"), 5: (None, 1300, (0.20, 0.22), (0.23, 0.25), "yes"), 6: (1000, 1300, (0.58, 0.60), (0.57, 0.59), "no"),
     7: (1000, 1300, (0.48, 0.52), (0.48, 0.52), "yes"), 8: (1000, 1300, (0.03, 0.04), (0.03, 0.04), "yes"), 9: (1000, 1300, (0.18, 0.20), (0.18, 0.20), "yes")}
B = {1: (1000, 1300, (0.30, 0.32), (0.33, 0.35), "yes"), 2: (1000, 1300, (0.30, 0.32), (0.33, 0.35), "no")}
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
for ser, W in (("KXZZ15M", A), ("KXSILVER15M", B), ("KXBTC15M", B)):
    for k, (o0, o1, sg, fl, res) in W.items():
        C = base + 900 * k; tk = "%s-W%d" % (ser, k); c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, ser, C - 900, C, res, 1.0, "t"))
        if o0 is not None: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 360, 0.5, 0.52, 5, o0))
        c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 180, sg[0], sg[1], 5, o1)); c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 120, fl[0], fl[1], 5, o1))
        if ser == "KXZZ15M" and k == 9: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C + 60, 0.98, 0.99, 5, o1))
c.commit(); c.close()
r = X.run(db); ok = lambda a, b, t=1e-9: abs(a - b) < t
assert r["tries"] == 2 and r["series"]["KXBTC15M"]["in_sample_home_market_not_a_try"] is True and not r["series"]["KXZZ15M"]["in_sample_home_market_not_a_try"]
za, zb = r["series"]["KXZZ15M"], r["series"]["KXSILVER15M"]
assert za["sources_of_kept_markets"] == {"t": 9} and za["all"]["n"] == 5 and ok(za["all"]["h0.00"]["pf"], 9.0254, 1e-4) and ok(za["all"]["h0.01"]["net"], 24.78) and ok(za["all"]["h0.02"]["pf"], 8.2202, 1e-4)
assert za["fill_0.08_or_more"]["n"] == 5 and za["fill_under_0.08"]["n"] == 0 and za["flags"]["evidence"] == "no evidence at n = 5" and za["flags"]["pass_standard"] is None and not za["c11_series"]
assert zb["all"]["n"] == 2 and zb["c11_series"] and ok(zb["all"]["h0.00"]["pf"], 6.34 / 3.66) and ok(zb["all"]["h0.00"]["net"], 2.68) and ok(zb["all"]["h0.01"]["pf"], 6.23 / 3.77) and ok(zb["all"]["h0.02"]["pf"], 6.13 / 3.87) and ok(zb["all"]["h0.02"]["net"], 2.26)
assert zb["all"]["h0.00"]["half1_pf"] == float("inf") and zb["all"]["h0.00"]["half2_pf"] == 0 and zb["flags"]["evidence"] == "no evidence at n = 2"
def st(n, pf1, a1, b1, pf2, a2, b2): return {"n": n, "h0.01": {"pf": pf1, "half1_pf": a1, "half2_pf": b1}, "h0.02": {"pf": pf2, "half1_pf": a2, "half2_pf": b2}}
assert X.flags(st(150, 1.5, 1.2, 1.1, 1.1, 1.0, 1.0), False)["pass_standard"] is True
assert X.flags(st(150, 1.5, 1.2, 0.9, 1.1, 1.0, 1.0), False)["pass_standard"] is False
assert X.flags(st(150, 1.25, 1.2, 1.1, 1.1, 1.0, 1.0), False)["pass_standard"] is False
assert X.flags(st(150, 1.5, 1.2, 1.1, 0.99, 1.0, 1.0), False)["pass_standard"] is False
f = X.flags(st(150, 1.0, 1.0, 1.0, 1.35, 1.1, 1.0), True); assert f["pass_c11"] is True and f["applicable"] == "pass_c11"
assert X.flags(st(150, 1.0, 1.0, 1.0, 1.29, 1.1, 1.0), True)["pass_c11"] is False and X.flags(st(150, 1.0, 1.0, 1.0, 1.4, 1.4, 0.99), True)["pass_c11"] is False
assert X.flags(st(99, 9, 9, 9, 9, 9, 9), False)["pass_standard"] is None
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "oirelx.py"), db], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "OIRELX_READ" in rr.stdout + rr.stderr
print("ALL OK")
