"""Plain assert tests for OIFEED (src/scalper/oifeed.py, the OICORE feed status line); run with: python tests/test_oifeed.py."""
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import oifeed as O

SCHEMA = """CREATE TABLE market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);
CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL,
  ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY (ticker, end_ts));"""
FZ = 1_800_000_000

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "fresh.sqlite"
    db = sqlite3.connect(p); db.executescript(SCHEMA)

    def win(k, res, bid180, ask180, oi180, oi360):
        c = FZ + 900 * k
        db.execute("insert into market values(?,?,?,?,?,?,?)", (f"T{k}", "KXBTC15M", c - 900, c, res, 1.0, 2))
        for e, b, a, oi in ((c - 360, 0.5, 0.52, oi360), (c - 180, bid180, ask180, oi180), (c - 60, 0.9, 0.91, oi180)):
            db.execute("insert into candle values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f"T{k}", "KXBTC15M", e, b, b, b, b, a, a, a, a, a, 1.0, oi))
    win(0, "yes", 0.10, 0.11, 150_000, 10_000)      # at the freeze: does not count
    win(1, "yes", 0.10, 0.11, 150_000, 10_000)      # cheap YES side, doi 140,000
    win(2, "no", 0.70, 0.71, 50_000, 10_000)        # cheap NO side (ask 0.30), doi 40,000
    win(3, "no", 0.60, 0.61, 500_000, 10_000)       # YES ask 0.61 is not cheap, NO ask 1 - 0.60 = 0.40 is: a candidate, doi 490,000
    win(4, None, 0.10, 0.11, 900_000, 10_000)       # unsettled: not counted, its doi not seen
    db.commit(); db.close()

    now = FZ + 4 * 900 + 3600
    c = O.counts(p, FZ, now)
    assert c["windows"] == 3 and c["candidates"] == 3, c
    assert c["max_doi"] == 490_000 and c["with_doi"] == 3, c
    assert c["last_candle"] == FZ + 4 * 900 - 60 and not c["stale"], c
    line = O.status_line(p, FZ, now)
    assert "3 settled windows" in line and "3 with a 5c to 50c side" in line and "490,000" in line and "STALE" not in line, line
    stale = O.status_line(p, FZ, now + 8 * 3600)
    assert "STALE" in stale and "no new candle" in stale, stale
    # no result value is read: the query touches only the settled flag
    import inspect
    src = inspect.getsource(O.counts)
    assert "result in ('yes','no')" in src and "result" not in src.replace("result in ('yes','no')", ""), "counts must never read a window's result"

# a missing file or a broken one never raises
assert O.status_line(Path("/nonexistent/fresh.sqlite"), FZ, FZ).startswith("OICORE feed: status failed")
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "bad.sqlite"; p.write_text("not a database")
    assert O.status_line(p, FZ, FZ).startswith("OICORE feed: status failed")
print("test_oifeed: ok")
