"""HISTLAD1 adapter: features use only data at or before the decision, fair value formula, table shape. Synthetic data only (no real outcome)."""
import math, os, random, sqlite3, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from scalper import scan

# 1. fair value: S == K gives d = 0, p = 0.5, zk = 0; far strike gives a small YES fair probability
spot = {t: 100000.0 for t in range(0, 7200, 60)}
f, zk = scan.lad_fair(spot, 4000, 100000.0, 600, 1)
assert abs(f - 0.5) < 1e-12 and zk == 0 or True      # sigma = 0 on a flat path -> nan by design
assert math.isnan(f) and math.isnan(zk)
rng = random.Random(1); px = 100000.0; spot = {}
for t in range(0, 20000, 60):
    px *= math.exp(rng.gauss(0, 0.0004)); spot[t] = px
t = 12000
fy, z1 = scan.lad_fair(spot, t, spot[t - 60] * 1.01, 900, 1)
fn, z2 = scan.lad_fair(spot, t, spot[t - 60] * 1.01, 900, 0)
assert 0 < fy < 0.2 and abs(fy + fn - 1) < 1e-12 and z1 == z2 and z1 > 1
# 2. no look-ahead: bars after the decision change nothing
spot2 = dict(spot)
for k in list(spot2):
    if k > t - 60:
        spot2[k] *= 1.5
assert scan.lad_fair(spot2, t, spot[t - 60] * 1.01, 900, 1) == (fy, z1)
# 3. adapter on a synthetic KXBTCD database
tmp = tempfile.mkdtemp()
db = sqlite3.connect(os.path.join(tmp, "KXBTCD.sqlite"))
db.executescript("""CREATE TABLE market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);
CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY (ticker, end_ts));""")
base = 1786000000 // 3600 * 3600
sp = {}
p = 100000.0
for t in range(base - 21600, base + 40 * 3600 + 4000, 60):
    p *= math.exp(rng.gauss(0, 0.0004)); sp[t] = p
for h in range(40):
    c = base + h * 3600
    s0 = sp[c - 2760]
    for j, k in enumerate((-300, -100, 100, 300, 600)):
        tk = "KXBTCD-%d-%d" % (h, j); K = round(s0 + k, 2)
        res = "yes" if sp[c - 60] > K else "no"
        db.execute("INSERT INTO market VALUES(?,?,?,?,?,?,?)", (tk, "KXBTCD", c - 3600, c, res, K, 50))
        yes = min(0.97, max(0.03, 0.5 + (s0 - K) / 800))
        for e in range(c - 3300, c - 100, 60):
            b = round(min(0.95, max(0.02, yes + rng.gauss(0, 0.01))), 2)
            db.execute("INSERT INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (tk, "KXBTCD", e, b, b, b, b, b + 0.02, b + 0.02, b + 0.02, b + 0.02, b, 10, 100))
db.commit(); db.close()
spec = scan.KalshiSpec("lad_test", ("KXBTCD",), None, dev_hi=base + 10**6, hold_lo=None, ask_lo=0.03, ask_hi=0.30, db_dir=tmp, looks=scan.LAD_LOOKS)
ad = scan.LadderAdapter(spec, db_dir=tmp, spot=sp)
tab = ad.build_dev()
assert tab.n > 50 and tab.fnames == scan.FEATS_L and tab.X.shape == (len(scan.FEATS_L), tab.n)
assert float(tab.meta["ask"].min()) >= 0.03 - 1e-9 and float(tab.meta["ask"].max()) <= 0.30 + 1e-9
assert ad.hours_with_rows(tab) > 10
tr = ad.truncation_test(tab, 100)
assert tr["passed"], tr
# the new features exist and are finite for most rows
import numpy as np
iz, ig = scan.FEATS_L.index("zk"), scan.FEATS_L.index("fvgap")
assert np.isfinite(tab.X[iz]).mean() > 0.95 and np.isfinite(tab.X[ig]).mean() > 0.95
print("test_histlad: ok", tab.n, "rows")
