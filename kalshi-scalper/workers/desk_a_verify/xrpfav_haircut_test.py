"""python3 -I xrpfav_haircut_test.py : the hand case of XRPFAV_HAND_CASE_NOV15.md on invented rows."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import xrpfav_haircut as X
base = 1_790_000_000
Q = {"A1": ((0.89, 0.90), "yes"), "A2": ((0.10, 0.11), "no"), "A3": ((0.88, 0.89), "no"), "A4": ((0.88, 0.91), "yes"), "A5": ((0.92, 0.93), "yes"), "A6": ((0.89, 0.90), "yes"), "A7": ((0.00, 0.92), "yes")}
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
for k, (w, ((b, a), res)) in enumerate(Q.items(), 1):
    C = base + 900 * k; tk = "KXXRP15M-" + w; c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, "KXXRP15M", C - 900, C, res, 0.5, "t"))
    if w != "A6": c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 360, b, a, 5, 0))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 600, b, a, 5, 0))
    if w == "A6": c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 300, 0.95, 0.96, 5, 0))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C + 60, 0.99, 0.995, 5, 0))       # after the close: must be dropped
c.commit(); c.close()
r = X.run(db); ok = lambda a, b, t=1e-9: abs(a - b) < t
f6, f10 = r["XRPFAV6"], r["XRPFAV10"]
assert f6["n"] == 3 and f10["n"] == 5, (f6["n"], f10["n"])
assert f6["counts"] == {"trade": 3, "spread": 1, "band": 1, "no_candle": 1, "bad_quote": 1}, f6["counts"]
assert f10["counts"] == {"trade": 5, "band": 1, "bad_quote": 1}, f10["counts"]
e6 = {"h0.00": (-7.11, 1.86 / 8.97, 0.93 / 8.97), "h0.01": (-7.39, 1.68 / 9.07, 0.84 / 9.07), "h0.02": (-7.68, 1.48 / 9.16, 0.74 / 9.16)}
e10 = {"h0.00": (-5.34, 3.63 / 8.97, 1.77 / 8.97), "h0.01": (-5.81, 3.26 / 9.07, 1.58 / 9.07), "h0.02": (-6.29, 2.87 / 9.16, 1.39 / 9.16)}
for res, e, nh in ((f6, e6, (1, 2)), (f10, e10, (2, 3))):
    for h, (net, pfv, pf2) in e.items():
        x = res[h]; assert ok(x["net"], net) and ok(x["pf"], pfv) and x["half1"]["n"] == nh[0] and x["half2"]["n"] == nh[1] and x["half1"]["pf"] == float("inf") and ok(x["half2"]["pf"], pf2), (h, x)
assert X.fee_up_order(0.50) == 0.18 and X.cash("yes", "yes", 0.985, 0.02) == 10 * (1 - 0.99) - X.fee_up_order(0.99)
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "xrpfav_haircut.py"), db], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "XRPFAV_READ" in rr.stdout + rr.stderr
print("ALL OK")
