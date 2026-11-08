"""NflPairAdapter on a synthetic nflpc1-shaped database: shapes, cheap filter, no look-ahead in the decision quote. Synthetic only."""
import os, random, sqlite3, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np
from scalper import scan

tmp = tempfile.mkdtemp(); path = os.path.join(tmp, "nflpc1.sqlite")
db = sqlite3.connect(path)
db.executescript("""CREATE TABLE km(ticker TEXT PRIMARY KEY, series TEXT, game TEXT, subj TEXT, strike REAL, open_ts INT, close_ts INT, result TEXT);
CREATE TABLE chosen(ticker TEXT PRIMARY KEY, kind TEXT); CREATE TABLE candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE done(ticker TEXT PRIMARY KEY, n INT);""")
rng = random.Random(1); base = 1790000000 // 3600 * 3600
for g in range(30):
    close = base + g * 86400 * 3
    for ser, subj, strikes in (("KXNFLPASSYDS", "QB1", (250, 300, 350, 400)), ("KXNFLTOTAL", "", (50, 55, 60)), ("KXNFLSPREAD", "TEAMA", (10, 14, 18))):
        for k in strikes:
            tk = "%s-G%d-%s-%d" % (ser, g, subj, k)
            db.execute("INSERT INTO km VALUES(?,?,?,?,?,?,?,?)", (tk, ser, "G%d" % g, subj, k, close - 86400, close, "yes" if rng.random() < 0.2 else "no"))
            db.execute("INSERT INTO chosen VALUES(?,?)", (tk, "high"))
            for h in range(12):
                e = close - 12 * 3600 + h * 3600
                b = round(rng.uniform(0.04, 0.2), 2)
                db.execute("INSERT INTO candle VALUES(?,?,?,?)", (tk, e, b, round(b + 0.02, 2)))
db.commit(); db.close()
ad = scan.NflPairAdapter(path=path)
tab = ad.build_dev()
assert tab.n > 200 and tab.X.shape == (len(scan.NFLPC_FEATS), tab.n)
rows_ok, net, nets = tab.outcome("yy", 0, "ALL")
assert len(rows_ok) > 100 and np.isfinite(net).all()
a = tab.X[scan.NFLPC_FEATS.index("a_ask")][rows_ok]
assert a.min() >= 0.03 - 1e-6 and a.max() <= 0.30 + 1e-6
assert len(set(tab.win.tolist())) == 3
assert ad.truncation_test(tab, 100)["passed"]
# held-out games are the last third and disjoint from dev
dev, hold = ad._split(ad._games())
assert len(hold) == 10 and not set(dev) & set(hold)
print("test_nflpc1: ok", tab.n, "rows", len(rows_ok), "cheap rows")
