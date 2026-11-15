"""python3 -I search1_haircut_test.py : the hand case of SEARCH1_HAND_CASE_NOV15.md on invented rows."""
import os, sys, sqlite3, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import search1_haircut as S
base = 1_790_000_000
d = tempfile.mkdtemp(); db = os.path.join(d, "x.sqlite"); c = sqlite3.connect(db)
c.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); c.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
def mkt(k, res, cands):
    C = base + 900 * k; tk = "KXBTC15M-S%d" % k; c.execute("insert into market values(?,?,?,?,?,?,?)", (tk, "KXBTC15M", C - 900, C, res, 1.0, "t"))
    for off, b, a in cands: c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C - off, b, a, 5, 0))
    c.execute("insert into candle values(?,?,?,?,?,?)", (tk, C + 60, 0.5, 0.5, 5, 0))                  # after the close: dropped
mkt(1, "yes", [(420, 0.97, 0.98), (360, 0.96, 0.97), (240, 0.95, 0.96)])
mkt(2, "no", [(420, 0.01, 0.02), (360, 0.02, 0.03), (240, 0.52, 0.55), (120, 0.01, 0.02)])
mkt(3, "no", [(420, 0.96, 0.97), (360, 0.95, 0.96), (240, 0.94, 0.95)])
mkt(4, "yes", [(420, 0.50, 0.52), (360, 0.5, 0.52)])
mkt(5, "yes", [(360, 0.97, 0.98)])
mkt(7, "yes", [(420, 0.97, 0.98), (360, None, 0.97)])
c.commit(); c.close()
r = S.run(db, cut=base + 900 * 3); a = r["all_days"]; ok = lambda x, y, t=1e-9: abs(x - y) < t
assert r["counts"] == {"trade": 3, "band_or_quote": 1, "no_candle": 1, "incomplete_market": 1}, r["counts"]
assert a["n"] == 3 and a["exits"] == 1
for h, (net, pfv, n2) in {"h0.00": (-15.14, 0.18 / 15.32, -15.32), "h0.01": (-15.42, 0.09 / 15.51, -15.51), "h0.02": (-15.61, 0.09 / 15.70, -15.70)}.items():
    x = a[h]; assert ok(x["net"], net) and ok(x["pf"], pfv) and x["wins"] == 1 and x["losses"] == 2 and x["half1"]["n"] == 1 and x["half1"]["pf"] == float("inf") and x["half2"]["n"] == 2 and x["half2"]["pf"] == 0 and ok(x["half2"]["net"], n2), (h, x)
assert r["before_cut_days_(discovery, where the combination was chosen: information only)"]["n"] == 2 and r["from_cut_days_(surviving confirmation days)"]["n"] == 1
assert S.fee_up_order(0.45) == 0.18 and S.favorite(0.96, 0.97) == ("yes", 0.97) and S.favorite(0.01, 0.02) == ("no", 0.99)
rr = subprocess.run([sys.executable, "-I", os.path.join(here, "search1_haircut.py"), db], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "SEARCH1_READ" in rr.stdout + rr.stderr
print("ALL OK")
