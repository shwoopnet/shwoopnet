"""NFLPC1 ingest (workers/NFLPC1_PROTOCOL.md, registered c3f1cf8 before any NFL prop candle or result was fetched).
  python3 -I src/scalper/nflpc1.py list     list KXNFLPASSYDS, KXNFLTOTAL, KXNFLSPREAD from /historical into data/nflpc1.sqlite (result stored, no statistic)
  python3 -I src/scalper/nflpc1.py choose   structure-only market choice and census counts (games with each series, with all three)
  python3 -I src/scalper/nflpc1.py fetch [--max N] [--low]   hourly candles for the chosen markets (--low = floor lines for NFLFAV1)
Selection never uses a price: PASSYDS = the 4 highest strikes per QB, TOTAL = the 6 highest strikes, SPREAD = the 6 highest strikes per team (registered).
"""
from __future__ import annotations
import os, re, sqlite3, sys, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h  # noqa: E402

DB = os.path.join(h.ROOT, "data", "nflpc1.sqlite")
SERIES = ("KXNFLPASSYDS", "KXNFLTOTAL", "KXNFLSPREAD")
TOP = {"KXNFLPASSYDS": 4, "KXNFLTOTAL": 6, "KXNFLSPREAD": 6}


def connect():
    db = sqlite3.connect(DB)
    db.executescript("""
CREATE TABLE IF NOT EXISTS km(ticker TEXT PRIMARY KEY, series TEXT, game TEXT, subj TEXT, strike REAL, open_ts INT, close_ts INT, result TEXT);
CREATE TABLE IF NOT EXISTS chosen(ticker TEXT PRIMARY KEY, kind TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
""")
    return db


def parse_ticker(tk):
    p = tk.split("-")                       # SERIES-26AUG27PITBUF-BUFSBUECHELE6-250  (subject, strike) ; TOTAL: SERIES-GAME-STRIKE ; SPREAD: SERIES-GAME-TEAMNN
    game = p[1] if len(p) > 1 else ""
    subj = p[2] if len(p) > 2 else ""
    return game, subj


def do_list():
    db = connect()
    for ser in SERIES:
        if db.execute("SELECT v FROM meta WHERE k=?", ("list_" + ser,)).fetchone():
            continue
        cur = None
        while True:
            p = {"series_ticker": ser, "limit": 1000}
            if cur:
                p["cursor"] = cur
            d = h.get("/historical/markets", p)
            if d is None:
                time.sleep(20); continue
            for m in d.get("markets", []):
                c, o = h.ts(m.get("close_time")), h.ts(m.get("open_time"))
                if c and m.get("result") in ("yes", "no"):
                    game, subj = parse_ticker(m["ticker"])
                    db.execute("INSERT OR IGNORE INTO km VALUES(?,?,?,?,?,?,?,?)", (m["ticker"], ser, game, subj, m.get("floor_strike"), o, c, m["result"]))
            db.commit()
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("list_" + ser, "1")); db.commit()
        print(ser, db.execute("SELECT count(*) FROM km WHERE series=?", (ser,)).fetchone()[0], "settled markets", flush=True)


def do_choose(low=False):
    db = connect()
    db.execute("DELETE FROM chosen WHERE kind=?", ("low" if low else "high",))
    groups = {}
    for tk, ser, game, subj, strike in db.execute("SELECT ticker, series, game, subj, strike FROM km WHERE strike IS NOT NULL"):
        key = (ser, game, subj if ser != "KXNFLTOTAL" else "")
        groups.setdefault(key, []).append((strike, tk))
    allg = None
    for ser in SERIES:
        g = {r[0] for r in db.execute("SELECT game FROM km WHERE series=?", (ser,))}
        allg = g if allg is None else allg & g              # Amendment 1: only games listed in all three series are fetched (pairs need two series)
    for (ser, game, subj), lst in groups.items():
        if game not in allg:
            continue
        lst.sort(reverse=not low)
        for strike, tk in lst[:TOP[ser]]:
            db.execute("INSERT OR REPLACE INTO chosen VALUES(?,?)", (tk, "low" if low else "high"))
    db.commit()
    games = {s: {r[0] for r in db.execute("SELECT game FROM km WHERE series=?", (s,))} for s in SERIES}
    allg = games["KXNFLPASSYDS"] & games["KXNFLTOTAL"] & games["KXNFLSPREAD"]
    print({s: len(g) for s, g in games.items()}, "games with all three:", len(allg),
          "with PASSYDS and TOTAL:", len(games["KXNFLPASSYDS"] & games["KXNFLTOTAL"]), "with PASSYDS and SPREAD:", len(games["KXNFLPASSYDS"] & games["KXNFLSPREAD"]))
    print("chosen markets (%s):" % ("low" if low else "high"), db.execute("SELECT count(*) FROM chosen WHERE kind=?", ("low" if low else "high",)).fetchone()[0])


def do_fetch(mx, low=False):
    db = connect()
    kind = "low" if low else "high"
    todo = db.execute("""SELECT c.ticker, k.close_ts FROM chosen c JOIN km k ON k.ticker=c.ticker WHERE c.kind=? AND c.ticker NOT IN (SELECT ticker FROM done) ORDER BY k.close_ts DESC""", (kind,)).fetchall()
    print(len(todo), "markets still to fetch", flush=True)
    t0 = time.time(); n = 0
    for tk, c in todo[:mx]:
        d = h.get(f"/historical/markets/{tk}/candlesticks", {"start_ts": c - 12 * 3600, "end_ts": c, "period_interval": 60})
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
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "list": do_list()
        elif cmd == "choose": do_choose("--low" in sys.argv)
        elif cmd == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9, "--low" in sys.argv)
        else: print(__doc__)
    except h.Stop as e:
        print("STOP:", e)
