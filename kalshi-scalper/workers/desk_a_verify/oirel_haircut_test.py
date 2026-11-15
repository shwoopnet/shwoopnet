"""python3 -I oirel_haircut_test.py : the hand case of OIREL_HAND_CASE_NOV15.md on invented rows, expected figures from that file."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oirel_haircut as R
base = 1_790_000_000
W = {1: (1000, 1300, (0.20, 0.22), (0.23, 0.25), "yes"), 2: (1000, 1100, (0.20, 0.22), (0.23, 0.25), "yes"), 3: (1000, 1400, (0.80, 0.82), (0.78, 0.80), "no"),
     4: (1000, 1300, (0.28, 0.30), (0.28, 0.30), "no"), 5: (None, 1300, (0.20, 0.22), (0.23, 0.25), "yes"), 6: (1000, 1300, (0.58, 0.60), (0.57, 0.59), "no"),
     7: (1000, 1300, (0.48, 0.52), (0.48, 0.52), "yes"), 8: (1000, 1300, (0.03, 0.04), (0.03, 0.04), "yes"), 9: (1000, 1300, (0.18, 0.20), (0.18, 0.20), "yes")}
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
for k, (o0, o1, sg, fl, res) in W.items():
    C = base + 900 * k; tk = "KXBTC15M-W%d" % k; c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, "KXBTC15M", C - 900, C, res, 77000.0, "t"))
    if o0 is not None: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 360, 0.5, 0.52, 5, o0))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 180, sg[0], sg[1], 5, o1)); c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 120, fl[0], fl[1], 5, o1))
    if k == 9: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C + 60, 0.98, 0.99, 5, o1))
c.commit(); c.close()
r = R.run(db, split=base + 900 * 4)
ok = lambda a, b, t=1e-9: abs(a - b) < t
assert r["counts"] == {"trade": 5, "nofire": 1, "nodata": 1, "noside": 2}, r["counts"]
exp = {"h0.00": (25.28, 28.43 / 3.15, 13.40 / 3.15, 15.03), "h0.01": (24.78, 28.03 / 3.25, 13.20 / 3.25, 14.83), "h0.02": (24.26, 27.62 / 3.36, 12.99 / 3.36, 14.63)}
for h, (net, pf, pf2, net1) in exp.items():
    x = r[h]; assert ok(x["net"], net) and ok(x["pf"], pf, 1e-9) and x["wins"] == 4 and x["losses"] == 1, (h, x)
    assert x["half1"]["n"] == 2 and x["half1"]["pf"] == float("inf") and ok(x["half1"]["net"], net1) and x["half2"]["n"] == 3 and ok(x["half2"]["pf"], pf2), (h, x)
    assert x["discovery"]["n"] == 2 and x["validation"]["n"] == 3 and ok(x["validation"]["pf"], pf2)
assert R.fee_up_order(0.50) == 0.18 and R.fee_up_order(0.15) == 0.09 and R.fee_up_order(0.90) == 0.07
assert R.cash("yes", "yes", 0.985, 0.02)[1] == 0.99          # never past 0.99
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "oirel_haircut.py"), db], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "OIREL_READ" in rr.stdout + rr.stderr, "must refuse without OIREL_READ=1"
print("ALL OK", {h: round(r[h]["pf"], 4) for h in exp})
