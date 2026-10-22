import sqlite3
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, "src")
from scalper import flat_r as T

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "x.sqlite"
    db = sqlite3.connect(p)
    db.executescript("CREATE TABLE market(ticker TEXT, series TEXT, open_ts INT, close_ts INT, result TEXT, strike REAL, n_candles INT);"
                     "CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INT, bid_c REAL, ask_c REAL);")
    db.execute("INSERT INTO market VALUES('A-1','KXSOL15M',0,1000,'yes',0,2)")
    db.execute("INSERT INTO market VALUES('B-1','KXBTC15M',0,1000,'yes',0,1)")        # not a replication series
    db.executemany("INSERT INTO candle VALUES(?,?,?,?,?)", [("A-1", "KXSOL15M", 940, 0.9, 0.91), ("A-1", "KXSOL15M", 1000, 0.95, 0.96), ("B-1", "KXBTC15M", 940, 0.9, 0.91)])
    db.commit()
    m = T.load_rep(p)
    assert len(m) == 1 and m[0][1] == "KXSOL15M" and len(m[0][2]) == 2, m
print("ok")
