"""python3 -I calib3_test.py : the loader hand case (addendum to CALIB3_HAND_CASE_NOV15.md) on invented rows."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import calib3 as K
base = 1790700000          # a close inside third 1 (before 1790755200)
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
M = [("KXBTCD-26SEP2917-T66000", base, 0.51, 0.52, "yes"), ("KXBTCD-26SEP2917-T66500", base, 0.52, 0.53, "no"), ("KXBTCD-26SEP2918-T66000", base + 3600, 0.50, 0.51, "yes"), ("KXBTCD-26SEP2918-T66500", base + 3600, 0.53, 0.54, "yes")]
for tk, cl, b, a, res in M:
    c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, "KXBTCD", cl - 3600, cl, res, 0, "t")); c.execute("insert into candle values(?,?,?,?,?,?)", (tk, cl - 1800, b, a, 5, 9))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, cl + 60, 0.99, 0.995, 5, 9))
c.commit(); c.close()
r = K.run(db); ok = lambda a, b, t=1e-9: abs(a - b) < t
assert r["missing"] == {"600_missing": 4, "120_missing": 4} and r["buckets_inspected"] == 120 and r["eligible_buckets"] == 0 and r["candidates"] == 0
y = r["cells"]["1800_yes_10"]["third1"]; assert y["n"] == 4 and y["wins"] == 3 and ok(y["gap"], 0.225) and y["events"] == 2 and ok(y["event_z"], 0.9)
n9 = r["cells"]["1800_no_9"]["third1"]; assert n9["n"] == 3 and n9["wins"] == 1 and n9["events"] == 2 and ok(n9["event_z"], -0.88, 1e-9), n9
n10 = r["cells"]["1800_no_10"]["third1"]; assert n10["n"] == 1 and n10["events"] == 1 and n10["event_z"] is None
assert sum(v["third1"]["n"] for k, v in r["cells"].items() if k.startswith("1800_")) == 8
assert K.event_of("KXBTCD-26SEP2521-T66000") == "KXBTCD-26SEP2521" and K.third_of(1790755199) == 1 and K.third_of(1790755200) == 2 and K.third_of(1791129600) is None
# a market from third 3 in the file is refused
c = sqlite3.connect(db); c.execute("insert into market values('KXBTCD-26OCT0517-T1','KXBTCD',0,1791200000,'yes',0,'t')"); c.commit(); c.close()
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "calib3.py"), db, os.path.join(d, "o.json")], capture_output=True, text=True, env={"PATH": os.environ["PATH"], "CALIB3_READ": "1"})
assert rr.returncode != 0 and "third 3" in rr.stdout + rr.stderr
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "calib3.py"), db, os.path.join(d, "o.json")], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "CALIB3_READ" in rr.stdout + rr.stderr
print("ALL OK")
