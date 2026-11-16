import csv, contextlib, gzip, hashlib, io, os, tempfile, opengap2 as o, opengap1f as f
def near(a, b, t=1e-7): return abs(a - b) < t
assert hashlib.sha256(open("opengap1f.py", "rb").read()).hexdigest() == o.F_SHA
d = tempfile.mkdtemp(); hdr = "ticker,end_period_ts,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,price_open,price_high,price_low,price_close,price_mean,price_previous,open_interest,volume"
def row(t, ts, b, a): return f"{t},{ts},0,0,0,{b},0,0,0,{a},0,0,0,0,0,0,0,0"
t16, t25, t31, t32 = f._ts("2026-11-06", 16, 0), f._ts("2026-11-09", 9, 25), f._ts("2026-11-09", 9, 31), f._ts("2026-11-09", 9, 32)
# US 500 follows the hand-case E1 numbers; US Tech 100 candles are the E3 numbers (long, closes at once); a SPY perp row must be ignored (the wall is the two index perps)
with gzip.open(os.path.join(d, "2026-11-06.csv.gz"), "wt") as fh:
    fh.write(hdr + "\n" + row("KXUS500PERP", t16, 9.99, 10.01) + "\n" + row("KXUSTECH100PERP", t16, 19.99, 20.01) + "\n" + row("KXSPYPERP", t16, 1.0, 2.0) + "\n")
with gzip.open(os.path.join(d, "2026-11-09.csv.gz"), "wt") as fh:
    t36 = f._ts("2026-11-09", 9, 36)
    fh.write(hdr + "\n" + row("KXUS500PERP", t25, 10.04, 10.06) + "\n" + row("KXUS500PERP", t31, 10.06, 10.08) + "\n" + row("KXUS500PERP", t32, 10.07, 10.09) + "\n"
             + row("KXUSTECH100PERP", t25, 19.99, 20.01) + "\n" + row("KXUSTECH100PERP", t31, 20.01, 20.03) + "\n" + row("KXUSTECH100PERP", t36, 20.14, 20.16) + "\n" + row("KXSPYPERP", t31, 5.0, 6.0) + "\n")
uf = os.path.join(d, "u.csv")
with open(uf, "w") as fh: fh.write("perp,date,prev_date,u_open,u_prev_close,x_open,x_prev_close\nKXSPYPERP,2026-11-09,2026-11-06,101,100,101,100\nKXQQQPERP,2026-11-09,2026-11-06,202,200,202,200\nKXNVDAPERP,2026-11-09,2026-11-06,5,4,5,4\nKXSPYPERP,2026-11-16,2026-11-13,101,100,101,100\nKXSPYPERP,2026-11-06,2026-11-05,101,100,101,100\n")
# the remap is one-to-one, drops NVDA, and keeps every other column
rm = os.path.join(d, "r.csv"); assert o.remap(uf, rm) == 4
rows = list(csv.DictReader(open(rm))); assert [r["perp"] for r in rows] == ["KXUS500PERP", "KXUSTECH100PERP", "KXUS500PERP", "KXUS500PERP"] and rows[0]["u_open"] == "101" and rows[1]["u_prev_close"] == "200"
saved = (f.PERPS, f.FWD_FROM, f.FWD_TO)
evs = o.events(d, uf); assert (f.PERPS, f.FWD_FROM, f.FWD_TO) == saved          # the borrowed module globals are restored
assert sorted((e["name"], e["day"]) for e in evs) == [("KXUS500PERP", "2026-11-06"), ("KXUS500PERP", "2026-11-09"), ("KXUSTECH100PERP", "2026-11-09")], [(e["name"], e["day"]) for e in evs]          # Nov 16 is outside the window
f.PERPS = o.NAMES
by = {e["name"]: e for e in evs if e["day"] == "2026-11-09"}
assert near(f.run([by["KXUS500PERP"]], "rel", 0.0002, 0.0)[0]["ret"], -0.0013916) and near(f.run([by["KXUS500PERP"]], "rel", 0.0005, 0.0)[0]["ret"], -0.0019906)          # hand case E1 figures
assert near(f.run([by["KXUSTECH100PERP"]], "rel", 0.0002, 0.0)[0]["ret"], 0.0050897)          # the E3 figure: QQQ's 202/200 against the perp's flat 09:25
assert f.score_event([e for e in evs if e["day"] == "2026-11-06"][0], "abs", 0.0, 0.0)[0] == "no_perp"          # Nov 6: no previous 16:00 candle of the previous day
f.PERPS = saved[0]
buf = io.StringIO()
with contextlib.redirect_stdout(buf): o.main(d, uf, [0.0012])
out = buf.getvalue(); assert "events 3 triggered events pooled 2" in out and "UST100" in out and "US500" in out and "no evidence at n = 1" in out and "not independent" in out and "KXSPY" not in out and f.PERPS == saved[0]
o.F_SHA = "0" * 64
try: o.main(d, uf, [0.0012]); raise AssertionError("must refuse")
except SystemExit as e: assert "not the checked build" in str(e)
print("opengap2 tests passed")
