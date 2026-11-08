"""HISTLAD1 ingest: Kalshi /historical hourly Bitcoin ladder KXBTCD (public, keyless, research only, no strategy statistics).

Protocol: workers/HISTLAD1_PROTOCOL.md (registered before any outcome is read). Cache: data/hist15/KXBTCD.sqlite (git-ignored).
  python3 -I src/scalper/histlad.py list             page /historical/markets (newest first) into the listing, window 2026-07-09 to 2026-09-08 closes
  python3 -I src/scalper/histlad.py choose           10 strikes per event from BINANCE only (5 at or below, 5 above the spot 45 min before the close)
  python3 -I src/scalper/histlad.py fetch [--max N]  candles T-55 min to T-3 min for the chosen strikes, newest first, resumable
  python3 -I src/scalper/histlad.py report           counts only
Only the settlement result is stored; no outcome statistic is computed here.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h  # noqa: E402  (shared get/parse/connect; BASE and SPACING reused)
from histbinance import load  # noqa: E402

SERIES = "KXBTCD"
LO, HI = 1783555200, 1788825600          # closes in [2026-07-09, 2026-09-08)
PER_SIDE = 5
REF_LEAD = 2700                           # spot 45 minutes before the close
H = h


def do_list():
    db = h.connect(SERIES)
    if h.meta(db, "list_done") == "1":
        print("listing already complete"); return
    cursor = h.meta(db, "cursor") or None
    pages = 0
    while True:
        p = {"series_ticker": SERIES, "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        d = h.get("/historical/markets", p)
        if d is None:
            continue
        pages += 1
        ms = d.get("markets", [])
        rows = []
        for m in ms:
            c, o = h.ts(m.get("close_time")), h.ts(m.get("open_time"))
            if c is not None and o is not None and LO <= c < HI and m.get("result") in ("yes", "no"):
                rows.append((m["ticker"], SERIES, o, c, m["result"], m.get("floor_strike")))
        db.executemany("INSERT OR IGNORE INTO listing VALUES(?,?,?,?,?,?)", rows)
        cursor = d.get("cursor")
        db.commit()
        oldest = min((h.ts(m.get("close_time")) or 0 for m in ms), default=0)
        print(f"page {pages}: {len(ms)} markets, kept {len(rows)}, oldest close {oldest}", flush=True)
        if cursor:
            h.meta(db, "cursor", cursor)
        if not cursor or not ms or oldest < LO:
            h.meta(db, "list_done", "1"); break
    print("listing done")


def spot_index():
    rows = load("BTCUSDT", "spot_1m")
    return {r[0]: r[4] for r in rows}      # bar open ts (s) -> close


def do_choose():
    db = h.connect(SERIES)
    db.execute("CREATE TABLE IF NOT EXISTS chosen(ticker TEXT PRIMARY KEY, close_ts INTEGER, strike REAL, spot REAL)")
    spot = spot_index()
    ev = {}
    for t, c, k in db.execute("SELECT ticker, close_ts, strike FROM listing WHERE strike IS NOT NULL"):
        ev.setdefault(c, []).append((k, t))
    nev = nmiss = 0
    for c, lst in sorted(ev.items()):
        s = spot.get(c - REF_LEAD - 60)    # bar opening T-46 min closes at T-45 min
        if s is None:
            nmiss += 1; continue
        lst.sort()
        below = [x for x in lst if x[0] <= s][-PER_SIDE:]
        above = [x for x in lst if x[0] > s][:PER_SIDE]
        for k, t in below + above:
            db.execute("INSERT OR REPLACE INTO chosen VALUES(?,?,?,?)", (t, c, k, s))
        nev += 1
    db.commit()
    print(f"events chosen {nev}, events without a Binance spot {nmiss}, chosen strikes {db.execute('select count(*) from chosen').fetchone()[0]}")


def do_fetch(mx):
    db = h.connect(SERIES)
    todo = db.execute("""SELECT c.ticker, c.close_ts, l.result, l.strike FROM chosen c JOIN listing l ON l.ticker=c.ticker
                         WHERE c.ticker NOT IN (SELECT ticker FROM market) AND c.ticker NOT IN (SELECT ticker FROM nocandle)
                         ORDER BY c.close_ts DESC""").fetchall()
    print(f"{len(todo)} chosen strikes still to fetch", flush=True)
    t0 = time.time(); n = 0
    for t, c, res, strike in todo[:mx]:
        d = h.get(f"/historical/markets/{t}/candlesticks", {"start_ts": c - 3300, "end_ts": c - 120, "period_interval": 1})
        if d is None:
            continue
        rows = [r for r in (h.parse(x, t, SERIES) for x in d.get("candlesticks", [])) if r]
        if rows:
            db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (t, SERIES, c - 3600, c, res, strike, len(rows)))
        else:
            db.execute("INSERT OR REPLACE INTO nocandle VALUES(?,?)", (t, c))
        db.commit(); n += 1
        if n % 100 == 0:
            el = time.time() - t0
            print(f"{n} fetched, {el:.0f}s, {el/n*1200/60:.1f} min per 1,200", flush=True)
    print(f"fetched {n} this run in {time.time()-t0:.0f}s")


def report():
    db = h.connect(SERIES)
    q = lambda s: db.execute(s).fetchone()[0]
    ev = q("select count(distinct close_ts) from listing")
    print({"listed": q("select count(*) from listing"), "events": ev,
           "chosen": q("select count(*) from chosen") if db.execute("select name from sqlite_master where name='chosen'").fetchone() else 0,
           "with_candles": q("select count(*) from market"), "no_candles": q("select count(*) from nocandle")})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "list":
            do_list()
        elif cmd == "choose":
            do_choose()
        elif cmd == "fetch":
            mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9
            do_fetch(mx)
        elif cmd == "report":
            report()
        else:
            print(__doc__)
    except h.Stop as e:
        print("STOP:", e)
