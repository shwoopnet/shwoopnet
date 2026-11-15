"""python3 -I flips0x_haircut_test.py : the hand case of FLIPS0X_HAND_CASE_NOV15.md on invented rows."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import flips0x_haircut as F
base = 1_790_000_000
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
def mkt(k, res, mids, dec):
    C = base + 900 * k; tk = "KXXRP15M-F%d" % k; c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, "KXXRP15M", C - 900, C, res, 1.0, "t"))
    offs = [600, 540, 480, 420][-len(mids):] if len(mids) == 4 else [540, 480, 420]
    for off, m in zip(offs, mids): c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - off, round(m - 0.01, 4), round(m + 0.01, 4), 5, 0))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - 360, dec[0], dec[1], 5, 0)); c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C + 60, 0.5, 0.5, 5, 0))
mkt(1, "yes", [0.84, 0.86, 0.88, 0.90], (0.91, 0.92)); mkt(2, "yes", [0.84, 0.88, 0.86, 0.90], (0.91, 0.92)); mkt(3, "no", [0.20, 0.17, 0.14, 0.11], (0.05, 0.06))
mkt(4, "no", [0.80, 0.82, 0.84, 0.86], (0.89, 0.90)); mkt(5, "yes", [0.84, 0.86, 0.88], (0.91, 0.92)); mkt(6, "yes", [0.84, 0.86, 0.88, 0.90], (0.97, 0.98)); mkt(7, "yes", [0.84, 0.86, 0.8575, 0.88], (0.89, 0.91))
c.commit(); c.close()
r = F.run(db); p = r["pooled"]; ok = lambda a, b, t=1e-9: abs(a - b) < t
assert r["counts"] == {"trade": 4, "flips": 1, "fewer_than_4_earlier": 1, "band_or_quote": 1}, r["counts"]
assert p["n"] == 4
for h, (net, pfv, pf2) in {"h0.00": (-7.03, 2.04 / 9.07, 0.84 / 9.07), "h0.01": (-7.40, 1.76 / 9.16, 0.74 / 9.16), "h0.02": (-7.78, 1.48 / 9.26, 0.65 / 9.26)}.items():
    x = p[h]; assert ok(x["net"], net) and ok(x["pf"], pfv) and x["wins"] == 3 and x["losses"] == 1 and x["half1"]["n"] == 2 and x["half1"]["pf"] == float("inf") and x["half2"]["n"] == 2 and ok(x["half2"]["pf"], pf2), (h, x)
assert F.flips([0.84, 0.86, 0.8575, 0.88, 0.9]) == 0 and F.flips([0.84, 0.88, 0.86, 0.9, 0.915]) == 2
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "flips0x_haircut.py"), db], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "FLIPS0X_READ" in rr.stdout + rr.stderr
print("ALL OK")
