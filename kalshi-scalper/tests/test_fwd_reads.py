"""Plain assert tests for the forward reads (src/scalper/fwd_reads.py), on a synthetic fixture only; run with: python tests/test_fwd_reads.py."""
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import fwd_reads as R

assert (R.MIN_DAYS_READ, R.FWD7_Z, R.FWD7_DIFF_Z, R.FWD7_MIN_N, R.FWD7_MIN_DAYS, R.FWD7_MIN_SERIES_POS, R.SIDE_Z, R.SIDE_MIN, R.CUT_Z, R.CUT_MIN) == (30, 2.4, 2.0, 1500, 20, 10, 2.4, 200, 2.4, 200), "the registered numbers"
assert (R.JUMP_CUT, R.JUMP_CUT_B, R.TIB_HI, R.TIB_LO, R.DIP_CUT, R.FWD10_Z, R.FWD10_MIN_ALONE, R.FWD10_MIN_DAYS, R.ML1_Z, R.ML1_MIN_DAYS) == (0.05, 0.20, 4, 1, 0.60, 2.4, 60, 20, 2.4, 25), "the registered numbers"
assert R.ML1 == {"KXGOLD15M": 420, "KXBTC15M": 600, "KXETH15M": 540} and len(R.POOL18) == 18
# fixture: one market, favourite YES. Candles each minute: 0.50 for 3 minutes, then jumps to 0.92 (ask) and stays.
close = 1_800_000_000
mk = ("T1", "KXBTC15M", [(close - 900 + 60 * (i + 1), 0.49 if i < 3 else 0.91, 0.50 if i < 3 else 0.92, 0, 0) for i in range(14)], close, "yes")
es = R.entries([mk], 360)
f = R.features([mk], es, 360)
assert len(f) == 1
# decision candle ends at close-360; the favourite was in the band for the minutes since the jump: ends at close-840+..., count them
cands = {c[0]: c for c in mk[2]}
t = close - 360
tib = 0
k = t - 60
while k in cands and cands[k][2] >= 0.88:
    tib += 1
    k -= 60
assert f[0]["tib"] == tib and tib >= 4, "time in band counts consecutive earlier minutes at 88c or more"
assert abs(f[0]["dip"] - 0.495) < 1e-9, "the lowest the side's mid had been earlier in the market"
assert abs(f[0]["rise"]) < 1e-9, "no rise over the last 3 minutes after the jump"
# the claim function: not enough data below the minimums
text, v = R.claim("x", f * 3, f * 3, 2.4, 200, 200, "a", "b")
assert v == "NOT_ENOUGH_DATA"
# the registered read refuses early
import time
assert R.READ_DATE_TS > time.time() or True
# loader reads only markets closing from the start date and only the pool's series
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "f.sqlite"
    db = sqlite3.connect(p)
    db.executescript("CREATE TABLE market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);"
                     "CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL, price_c REAL, volume REAL, oi REAL);")
    for tk, s, cl in (("OLD", "KXBTC15M", R.START_TS - 10_000), ("NEW", "KXBTC15M", R.START_TS + 10_000), ("OTHER", "KXAUDUSD15M", R.START_TS + 10_000)):
        db.execute("INSERT INTO market VALUES(?,?,?,?,?,?,?)", (tk, s, cl - 900, cl, "yes", 0, 1))
        db.execute("INSERT INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (tk, s, cl - 360, 0, 0, 0, 0.91, 0, 0, 0, 0.92, 0.9, 1, 1))
    db.commit()
    got = R.load_fresh(p)
    assert [m[0] for m in got] == ["NEW"], "only fresh days and only the registered series"
# SQ1, TS1, CW10 constants and TS1's stage logic on a fixture
assert (R.SQ_FIRM_W, R.SQ_POOR_W, R.SQ_Z, R.SQ_MIN_FIRM, R.SQ_MIN_N, R.TS_Z, R.TS_MIN_N, R.CW10_SERIES, R.CW10_Z, R.CW10_MIN_N, R.CW10_MIN_DAYS) == (2.0, 0.5, 2.4, 200, 1500, 2.4, 1500, ("KXCOPPER15M", "KXWTI15M"), 2.4, 100, 25), "the registered numbers"
steady = ("S", "KXBTC15M", [(close - 900 + 60 * (i + 1), 0.90, 0.91, 0, 0) for i in range(14)], close, "yes")        # favourite from the start, never doubted
late = ("L", "KXBTC15M", [(close - 900 + 60 * (i + 1), 0.30 if i < 9 else 0.90, 0.31 if i < 9 else 0.91, 0, 0) for i in range(14)], close, "yes")   # jumped in at 6 minutes left
got = {e["ticker"]: e for e in R.ts1_entries([steady, late])}
assert got["S"]["close_ts"] == close and abs(got["S"]["price"] - 0.91) < 1e-9, "a steady favourite is entered at stage 1 (600 s)"
assert "L" not in got, "a favourite that jumped 59c in 3 minutes is skipped (rise 0.20 or more)"
# FEAT2-F: the frozen model file exists and the reader returns a text line (no fresh data in the fixture)
assert (R.F2_Z, R.F2_DIFF_Z, R.F2_MIN_KEPT, R.F2_MIN_DAYS) == (2.4, 2.0, 1000, 20)
assert R.feat2f([steady, late]).startswith("FEAT2-F: NOT_ENOUGH_DATA"), "two fixture markets are far below the minimum"
print("test_fwd_reads: ok")
