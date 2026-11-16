"""python3 -I engine1_extract_load_test.py : the extract loader on invented sqlite extracts."""
import os, sys, lzma, sqlite3, tempfile, calendar, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_extract_load as L
base = tempfile.mkdtemp()
def mk(name, build):
    p = os.path.join(base, name + ".sqlite"); con = sqlite3.connect(p); build(con); con.commit(); con.close()
    raw = open(p, "rb").read(); xz = lzma.compress(raw); path = os.path.join(base, name); open(path, "wb").write(xz); return hashlib.sha256(xz).hexdigest()
def arch(con):
    con.execute("CREATE TABLE market(ticker, series, close_ts, result, src)"); con.execute("CREATE TABLE candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    con.executemany("INSERT INTO market VALUES (?,?,?,?,?)", [("K1", "WTI", 1000000, "yes", "x"), ("K2", "WTI", 1791043200, "no", "x"), ("K3", "WTI", 2000000000, "no", "x"), ("K4", "WTI", 1000900, "void", "x")])
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("K1", 999940, .5, .52, .5, 3, 100), ("K1", 1000000, .98, 1.0, .99, 1, 101), ("K1", 1000060, .99, 1.0, .99, 1, 101), ("K2", 5, .1, .2, .1, 1, 1)])
def perps(con):
    con.execute("CREATE TABLE market(ticker, series, close_ts, result, src)"); con.execute("CREATE TABLE candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    con.executemany("INSERT INTO market VALUES (?,?,?,?,?)", [("KXSPYPERP", "SPY", None, None, "p"), ("KXUS500PERP", "US500", None, None, "p")])
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("KXSPYPERP", 1793923199, 600.0, 600.1, 600.0, 1, None), ("KXSPYPERP", 1793923260, 601.0, 601.1, 601.0, None, 5), ("KXUS500PERP", 1793923260, 1, 2, 1, 1, 1)])
a, b = mk("arch.xz", arch), mk("perps.xz", perps)
def arch_nc(con):
    arch(con); con.execute("INSERT INTO candle VALUES ('K3', 1, .1, .2, .1, 1, 1)")                    # different bytes, so a different sha256 from the archive extract
nc = mk("nc.xz", arch_nc); assert nc != a
L.ARCHIVE = ("arch.xz", a); L.PERPFILE = ("perps.xz", b); L.NC15FILE = ("nc.xz", nc)
allow = os.path.join(base, "H.md"); L.ALLOW_FILE = allow
try: L.load(base); assert False                                    # 1: no allow line
except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s %s\n" % (L.ALLOW_MARK, "deadbeef", a, b, nc))
try: L.load(base); assert False                                    # 2: wrong loader hash
except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), a, b, nc))
wa, ca, wp, cp, wn, cn = L.load(base, with_nc15=True)
assert list(wn) == ["WTI"] and cn["dropped by the cut"] == 2                                              # the NC15 slot reads like the archive
assert list(wa) == ["WTI"] and len(wa["WTI"]) == 1 and wa["WTI"][0]["ticker"] == "K1" and wa["WTI"][0]["result"] == "yes", wa
assert [c[0] for c in wa["WTI"][0]["candles"]] == [999940, 1000000], wa                                   # the post-close candle is dropped
assert ca["dropped by the cut"] == 2 and ca["candle after close (dropped)"] == 1 and ca["no result (dropped)"] == 1 and ca["no result (dropped): WTI"] == 1, ca
assert list(wp) == ["KXSPYPERP"] and cp["other ticker dropped"] == 1 and cp["perp candle before 2026-11-06 (dropped)"] == 1 and len(wp["KXSPYPERP"]) == 1 and wp["KXSPYPERP"][0][4] is None, (wp, cp)
assert L.PERP_FROM == calendar.timegm((2026, 11, 6, 0, 0, 0)) == 1793923200 and L.CUT == calendar.timegm((2026, 10, 3, 16, 0, 0))
def perps2(con):
    con.execute("CREATE TABLE market(ticker, series, close_ts, result, src)"); con.execute("CREATE TABLE candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    con.execute("INSERT INTO market VALUES ('KXSPYPERP','SPY',NULL,NULL,'p')")
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("KXSPYPERP", 1793923199, 1, 2, 1, 1, 1), ("KXSPYPERP", 1793923200, 1, 2, 1, 1, 1)])
b2 = mk("perps2.xz", perps2); L.PERPFILE = ("perps2.xz", b2)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), a, b2, nc))
wp2 = L.load_perps(base)[0]; assert [c[0] for c in wp2["KXSPYPERP"]] == [1793923200], wp2                 # literal boundary: 1793923199 dropped, 1793923200 kept
L.NC15FILE = ("nc.xz", "")
try: L.load(base, with_nc15=True); assert False                                                           # an open NC15 sha refuses the NC15 pass
except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), a, b2))
fa = L.load(base); assert fa[4] == {} and fa[5] == {} and list(fa[0]) == ["WTI"]                           # first pass: two hashes are enough, NC15 is not opened
try: L.load(base, with_nc15=True); assert False
except SystemExit as e: assert "REFUSED" in str(e)
L.NC15FILE = ("nc.xz", nc); L.PERPFILE = ("perps.xz", b)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), a, b, nc))
# any-line rule: a first-pass line B1 sitting BEFORE the NC15 line must not hide it
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\ny %s engine1_extract_load.py %s %s %s %s\n" % (L.ALLOW_MARK, "0" * 64, a, b, L.ALLOW_MARK, L.self_sha(), a, b, nc))
assert list(L.load(base, with_nc15=True)[4]) == ["WTI"]                                              # the second line grants the NC15 pass although the first line is for another hash
try: open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), a, b)); L.load(base, with_nc15=True); assert False
except SystemExit as e: assert "REFUSED" in str(e)                                                    # a line without the NC15 sha does not grant the NC15 pass
assert L.load(base)[0]                                                                                # but it grants the first pass
open(os.path.join(base, "arch.xz"), "ab").write(b"x")                                                      # 3: a changed file is refused
try: L.load(base); assert False
except SystemExit as e: assert "sha256" in str(e)
# perps pass 2: SPY and QQQ from the first extract, US 500 and US Tech 100 from the extension, funding for the four; the archive extract is never opened
def perps_a(con):
    con.execute("CREATE TABLE market(ticker, series, close_ts, result, src)"); con.execute("CREATE TABLE candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    con.executemany("INSERT INTO market VALUES (?,?,?,?,?)", [("KXSPYPERP", "SPY", None, None, "p"), ("KXQQQPERP", "QQQ", None, None, "p"), ("KXNVDAPERP", "NVDA", None, None, "p")])
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("KXSPYPERP", 1793923200, 1, 2, 1, 1, 1), ("KXQQQPERP", 1793923260, 1, 2, 1, 1, 1), ("KXNVDAPERP", 1793923260, 1, 2, 1, 1, 1)])
def perps_x(con):
    con.execute("CREATE TABLE market(ticker, series, close_ts, result, src)"); con.execute("CREATE TABLE candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    con.executemany("INSERT INTO market VALUES (?,?,?,?,?)", [("KXUS500PERP", "US500", None, None, "p"), ("KXGOLDPERP", "GOLD", None, None, "p")])
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("KXUS500PERP", 1793923199, 1, 2, 1, 1, 1), ("KXUS500PERP", 1793923200, 5, 6, 1, 1, 1), ("KXGOLDPERP", 1793923200, 5, 6, 1, 1, 1)])
def fund(con):
    con.execute("CREATE TABLE funding(ticker, ts, rate)")
    con.executemany("INSERT INTO funding VALUES (?,?,?)", [("KXSPYPERP", 1793923200 + 75600, 0.0001), ("KXSPYPERP", 1793923200 - 3600, 0.5), ("KXNVDAPERP", 1793923200 + 75600, 0.2), ("KXUS500PERP", 1793923200 + 75600, -0.0002), ("KXQQQPERP", 1793923200 + 75600, None)])
pa, px, pf_ = mk("pa.xz", perps_a), mk("px.xz", perps_x), mk("fund.xz", fund)
L.PERPFILE = ("pa.xz", pa); L.PERPEXT = ("px.xz", px); L.FUNDING = ("fund.xz", pf_)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), pa, px, pf_))
pp, dr, ff, fdr = L.load_pass2(base)
assert sorted(pp) == ["KXQQQPERP", "KXSPYPERP", "KXUS500PERP"] and [c[0] for c in pp["KXUS500PERP"]] == [1793923200] and dr["ext"]["other ticker dropped"] == 1 and dr["perps"]["other ticker dropped"] == 1, (pp, dr)
assert ff == {"KXSPYPERP": {1793923200 + 75600: 0.0001}, "KXUS500PERP": {1793923200 + 75600: -0.0002}, "KXQQQPERP": {}}, ff
assert fdr["other ticker dropped"] == 1 and fdr["print before 2026-11-06 (dropped)"] == 1 and fdr["print without a rate (dropped)"] == 1, fdr
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), pa, px))      # a line without the funding hash refuses pass 2
try: L.load_pass2(base); assert False
except SystemExit as e: assert "REFUSED" in str(e)
# perps pass 3: the back-pull extracts, ticker wall and the window on both ends; the other extracts are not opened
def bp(con):
    con.execute("CREATE TABLE market(ticker, series, close_ts, result, src)"); con.execute("CREATE TABLE candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    con.executemany("INSERT INTO market VALUES (?,?,?,?,?)", [("KXGOLDPERP", "GOLD", None, None, "p"), ("KXUS500PERP", "US500", None, None, "p"), ("KXWTIFUTURE", "WTI", None, None, "p")])
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("KXGOLDPERP", L.P3_FROM - 1, 1, 2, 1, 1, 1), ("KXGOLDPERP", L.P3_FROM, 1, 2, 1, 1, 1), ("KXGOLDPERP", L.P3_TO - 1, 1, 2, 1, 1, 1), ("KXGOLDPERP", L.P3_TO, 1, 2, 1, 1, 1), ("KXUS500PERP", L.P3_FROM + 60, 5, 6, 1, 1, 1), ("KXWTIFUTURE", L.P3_FROM + 60, 5, 6, 1, 1, 1)])
def bpf(con):
    con.execute("CREATE TABLE funding(ticker, ts, rate)")
    con.executemany("INSERT INTO funding VALUES (?,?,?)", [("KXGOLDPERP", L.P3_FROM + 3600, 0.0001), ("KXGOLDPERP", L.P3_TO, 0.5), ("KXWTIFUTURE", L.P3_FROM + 3600, 0.3), ("KXUS500PERP", L.P3_FROM - 5, 0.2)])
b1, b2 = mk("bp.xz", bp), mk("bpf.xz", bpf)
L.BACKPULL = ("bp.xz", b1); L.BACKPULL_FUNDING = ("bpf.xz", b2)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), b1, b2))
p3, d3, f3, fd3 = L.load_pass3(base)
assert sorted(p3) == ["KXGOLDPERP", "KXUS500PERP"] and [c[0] for c in p3["KXGOLDPERP"]] == [L.P3_FROM, L.P3_TO - 1], p3
assert d3["other ticker dropped"] == 1 and d3["candle before the window start (dropped)"] == 1 and d3["candle at or after the window end (dropped)"] == 1, d3
assert f3 == {"KXGOLDPERP": {L.P3_FROM + 3600: 0.0001}, "KXUS500PERP": {}} and fd3["other ticker dropped"] == 1 and fd3["print at or after the window end (dropped)"] == 1 and fd3["print before the window start (dropped)"] == 1, (f3, fd3)
open(allow, "w").write("x %s engine1_extract_load.py %s %s\n" % (L.ALLOW_MARK, L.self_sha(), b1))              # without the funding hash it refuses
try: L.load_pass3(base); assert False
except SystemExit as e: assert "REFUSED" in str(e)
assert L.P3_FROM == calendar.timegm((2026, 9, 4, 0, 0, 0)) and L.P3_TO == calendar.timegm((2026, 11, 1, 0, 0, 0))
print("ALL OK")
