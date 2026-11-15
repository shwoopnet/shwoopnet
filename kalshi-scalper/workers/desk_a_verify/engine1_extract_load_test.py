"""python3 -I engine1_extract_load_test.py : the extract loader on invented sqlite extracts."""
import os, sys, lzma, sqlite3, tempfile, hashlib
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
    con.executemany("INSERT INTO candle VALUES (?,?,?,?,?,?,?)", [("KXSPYPERP", 1793750399, 600.0, 600.1, 600.0, 1, None), ("KXSPYPERP", 1793750460, 601.0, 601.1, 601.0, None, 5), ("KXUS500PERP", 1793750460, 1, 2, 1, 1, 1)])
a, b = mk("arch.xz", arch), mk("perps.xz", perps)
L.ARCHIVE = ("arch.xz", a); L.PERPFILE = ("perps.xz", b)
allow = os.path.join(base, "H.md"); L.ALLOW_FILE = allow
try: L.load(base); assert False                                    # 1: no allow line
except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\\n" % (L.ALLOW_MARK, "deadbeef", a, b))
try: L.load(base); assert False                                    # 2: wrong loader hash
except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write("x %s engine1_extract_load.py %s %s %s\n" % (L.ALLOW_MARK, L.self_sha(), a, b))
wa, ca, wp, cp = L.load(base)
assert list(wa) == ["WTI"] and len(wa["WTI"]) == 1 and wa["WTI"][0]["ticker"] == "K1" and wa["WTI"][0]["result"] == "yes", wa
assert [c[0] for c in wa["WTI"][0]["candles"]] == [999940, 1000000], wa                                   # the post-close candle is dropped
assert ca["dropped by the cut"] == 2 and ca["candle after close (dropped)"] == 1 and ca["no result (dropped)"] == 1 and ca["no result (dropped): WTI"] == 1, ca
assert list(wp) == ["KXSPYPERP"] and cp["other ticker dropped"] == 1 and cp["perp candle before 2026-11-06 (dropped)"] == 1 and len(wp["KXSPYPERP"]) == 1 and wp["KXSPYPERP"][0][4] is None, (wp, cp)
open(os.path.join(base, "arch.xz"), "ab").write(b"x")                                                      # 3: a changed file is refused
try: L.load(base); assert False
except SystemExit as e: assert "sha256" in str(e)
print("ALL OK")
