"""python3 -I oirel_split8_test.py : the hand case of OIREL_SPLIT8_HAND_CASE_NOV15.md on invented rows."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oirel_split8 as S
base = 1_790_000_000
W = {1: (1000, 1300, (0.20, 0.22), (0.23, 0.25), "yes"), 2: (1000, 1100, (0.20, 0.22), (0.23, 0.25), "yes"), 3: (1000, 1400, (0.80, 0.82), (0.78, 0.80), "no"),
     4: (1000, 1300, (0.28, 0.30), (0.28, 0.30), "no"), 5: (None, 1300, (0.20, 0.22), (0.23, 0.25), "yes"), 6: (1000, 1300, (0.58, 0.60), (0.57, 0.59), "no"),
     7: (1000, 1300, (0.48, 0.52), (0.48, 0.52), "yes"), 8: (1000, 1300, (0.03, 0.04), (0.03, 0.04), "yes"), 9: (1000, 1300, (0.18, 0.20), (0.18, 0.20), "yes"),
     10: (1000, 1300, (0.05, 0.06), (0.06, 0.07), "yes"), 11: (1000, 1300, (0.07, 0.08), (0.07, 0.08), "no")}
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
for k, (o0, o1, sg, fl, res) in W.items():
    C = base + 900 * k; tk = "KXBTC15M-W%d" % k; c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, "KXBTC15M", C - 900, C, res, 77000.0, "t"))
    if o0 is not None: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 360, 0.5, 0.52, 5, o0))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 180, sg[0], sg[1], 5, o1)); c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 120, fl[0], fl[1], 5, o1))
    if k == 9: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C + 60, 0.98, 0.99, 5, o1))
c.commit(); c.close()
r = S.run(db); ok = lambda a, b, t=1e-9: abs(a - b) < t
s8, fb = r["fill_price_0.08_or_more"], r["full_band"]
assert s8["n"] == 6 and fb["n"] == 7 and r["fill_price_under_0.08"]["n"] == 1
for h, (net, pfv, h1, h2) in {"h0.00": (24.42, 28.43 / 4.01, 15.03 / 3.15, 13.40 / 0.86), "h0.01": (23.82, 28.03 / 4.21, 14.83 / 3.25, 13.20 / 0.96), "h0.02": (23.19, 27.62 / 4.43, 14.63 / 3.36, 12.99 / 1.07)}.items():
    x = s8[h]; assert ok(x["net"], net) and ok(x["pf"], pfv) and x["wins"] == 4 and x["losses"] == 2 and x["half1"]["n"] == 3 and ok(x["half1"]["pf"], h1) and x["half2"]["n"] == 3 and ok(x["half2"]["pf"], h2), (h, x)
for h, (net, pfv, h2) in {"h0.00": (33.67, 37.68 / 4.01, 22.65 / 0.86), "h0.01": (32.96, 37.17 / 4.21, None), "h0.02": (32.23, 36.66 / 4.43, None)}.items():
    x = fb[h]; assert ok(x["net"], net) and ok(x["pf"], pfv) and x["wins"] == 5 and x["losses"] == 2 and x["half1"]["n"] == 3 and x["half2"]["n"] == 4, (h, x)
    if h2: assert ok(x["half2"]["pf"], h2)
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "oirel_split8.py"), db], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "OIREL_READ" in rr.stdout + rr.stderr
print("ALL OK")
