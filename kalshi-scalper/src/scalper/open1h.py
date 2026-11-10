"""OPEN1H ingest (workers/OPEN1H_PROTOCOL.md, registered before any first-hour candle is fetched).
  python3 -I src/scalper/open1h.py choose      pick 300 settled markets per source by md5 of the ticker (never a price or result)
  python3 -I src/scalper/open1h.py fetch [--max N]   hourly candles from open_ts to open_ts + 3 h into data/open1h.sqlite
"""
from __future__ import annotations
import hashlib, os, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h  # noqa: E402

DB = os.path.join(h.ROOT, "data", "open1h.sqlite")
SOURCES = [("newser1.sqlite", "km"), ("nflpc1.sqlite", "km"), ("sports1.sqlite", "market")]
PER = 300


def connect():
    db = sqlite3.connect(DB)
    db.executescript("""
CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, src TEXT, series TEXT, open_ts INT, close_ts INT, result TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);
""")
    return db


def do_choose():
    db = connect()
    for f, t in SOURCES:
        p = os.path.join(h.ROOT, "data", f)
        if not os.path.exists(p):
            print("missing", f); continue
        s = sqlite3.connect(p)
        rows = s.execute("SELECT ticker, series, open_ts, close_ts, result FROM %s WHERE result IN ('yes','no') AND open_ts IS NOT NULL" % t).fetchall()
        rows.sort(key=lambda r: hashlib.md5(r[0].encode()).hexdigest())
        for tk, ser, o, c, res in rows[:PER]:
            db.execute("INSERT OR IGNORE INTO mk VALUES(?,?,?,?,?,?)", (tk, f, ser, o, c, res))
        print(f, "settled with open_ts", len(rows), "chosen", min(len(rows), PER))
    db.commit()
    print("chosen total", db.execute("SELECT count(*) FROM mk").fetchone()[0])


def do_fetch(mx):
    db = connect()
    todo = db.execute("SELECT ticker, open_ts FROM mk WHERE ticker NOT IN (SELECT ticker FROM done) ORDER BY ticker").fetchall()
    print(len(todo), "to fetch", flush=True)
    n = 0; t0 = time.time()
    for tk, o in todo[:mx]:
        try:
            d = h.get(f"/historical/markets/{tk}/candlesticks", {"start_ts": o, "end_ts": o + 3 * 3600, "period_interval": 60})
        except h.Stop:
            raise                      # rate limited: stop the run, do not record the market as done
        except Exception as e:
            print("skipped", tk, str(e)[:60], flush=True)
            db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, 0)); db.commit(); continue
        if d is None:
            continue
        rows = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None:
                rows.append((tk, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rows)
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rows))); db.commit(); n += 1
        if n % 100 == 0:
            print(n, "fetched", int(time.time() - t0), "s", flush=True)
    print("fetched", n, "this run")


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if c == "choose": do_choose()
        elif c == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        else: print(__doc__)
    except h.Stop as e:
        print("STOP:", e)
