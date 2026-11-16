import os, sys, sqlite3, lzma, hashlib, tempfile, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_poolperps_load as L
U = lambda *a: calendar.timegm(a)
d = tempfile.mkdtemp()
def mkxz(name, ddl, rows, ins):
    p = os.path.join(d, name + ".sqlite"); c = sqlite3.connect(p); c.execute(ddl); c.executemany(ins, rows); c.commit(); c.close()
    raw = lzma.compress(open(p, "rb").read()); fn = name + ".sqlite.xz"; open(os.path.join(d, fn), "wb").write(raw); return fn, hashlib.sha256(raw).hexdigest()
cr = []
for tk, days in (("KXAAAPERP", (9, 10, 11, 12, 13, 16)), ("KXBBBPERP", (9, 10)), ("KXCCCPERP", (9, 10, 11, 12, 13))):
    for dd in days:
        for k in range(0, 391): t = U(2026, 11, dd, 14, 30, 0) + 60 * k; cr.append((tk, t, 99.99, 100.01, 100.0, 1.0, 1.0))
cr.append(("KXAAAPERP", 1793904000, None, 100.0, 100.0, 1, 1)); cr.append(("KXAAAPERP", 1794873600, 99.99, 100.01, 100.0, 1.0, 1.0)); cr.append(("KXAAAPERP", 1793903939, 99.99, 100.01, 100.0, 1.0, 1.0))
L.CANDLES = mkxz("c", "create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)", cr, "insert into candle values(?,?,?,?,?,?,?)")
fr = [("KXAAAPERP", U(2026, 11, 9, 21, 0, 0), 0.0001), ("KXAAAPERP", U(2026, 11, 10, 21, 0, 0), 0.0002), ("KXBBBPERP", U(2026, 11, 9, 21, 0, 0), 0.0001), ("KXBBBPERP", U(2026, 11, 10, 21, 0, 0), 0.0), ("KXCCCPERP", U(2026, 11, 9, 21, 0, 0), 0.0001), ("KXAAAPERP", 1794873600, 0.5)]
L.FUNDING = mkxz("f", "create table funding(ticker, ts, rate)", fr, "insert into funding values(?,?,?)")
try: L.load(d); raise AssertionError("loaded without an allow line")
except SystemExit as e: assert "REFUSED" in str(e)
cand, fund, c, drop = L.load(d, check_allow=False)
assert c["candle outside the window (dropped)"] == 2 and c["print outside the window (dropped)"] == 1 and 1794873600 not in cand["KXAAAPERP"] and 1793903939 not in cand["KXAAAPERP"] and 1794873600 not in fund["KXAAAPERP"]
assert sorted(cand) == ["KXAAAPERP"] and "KXBBBPERP" in drop and "fewer than 5" in drop["KXBBBPERP"] and drop["KXCCCPERP"] == "fewer than 2 funding prints" and c["candle without bid or ask"] == 1, (list(cand), drop, c)
assert cand["KXAAAPERP"][U(2026, 11, 9, 14, 30, 0)] == (99.99, 100.01) and fund["KXAAAPERP"][U(2026, 11, 10, 21, 0, 0)] == 0.0002
L.CANDLES = (L.CANDLES[0], "0" * 64)
try: L.load(d, check_allow=False); raise AssertionError("opened a file with the wrong hash")
except SystemExit as e: assert "sha256" in str(e)
print("POOLPERPS LOADER OK")
