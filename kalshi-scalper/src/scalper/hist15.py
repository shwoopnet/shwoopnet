"""INGEST 3: extend Kalshi 15 minute history backwards via /historical (public, keyless, research only, no strategy statistics).

Cache: data/hist15/<series>.sqlite (git-ignored), same market/candle schema as data/fresh.sqlite plus listing, nocandle and meta tables.
  python3 -I src/scalper/hist15.py list   SERIES [more]   page /historical/markets (newest first) down to the boundary, resumable
  python3 -I src/scalper/hist15.py fetch  SERIES [--max N]  candles for listed markets, newest first, resumable
  python3 -I src/scalper/hist15.py report SERIES [more]   defect screen (counts only, outcomes never read)
Politeness: 3 s between calls, one 6 s retry on 429, STOP after 3 consecutive failed requests (state is committed after every market).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.elections.kalshi.com/trade-api/v2"
ALT = "https://external-api.kalshi.com/trade-api/v2"
SPACING = 3.0
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "data", "hist15")
# Oldest close already held per series (pooled data/*.sqlite, checked 2026-11-07): 2026-08-06 00:00Z for BTC, ETH, GOLD, XRP, DOGE.
BOUNDARY = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
SCHEMA = """
CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL,
  ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY (ticker, end_ts));
CREATE TABLE IF NOT EXISTS listing(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL);
CREATE TABLE IF NOT EXISTS nocandle(ticker TEXT PRIMARY KEY, close_ts INTEGER);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS calllog(t REAL, kind TEXT, n INTEGER);
"""


class Stop(Exception):
    pass


_last = [0.0]
_fails = [0]


def get(path, params=None):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    for attempt in range(2):
        wait = SPACING - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(BASE + path + q, timeout=30) as r:
                _fails[0] = 0
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
        except Exception:
            pass
        if attempt == 0:
            time.sleep(6)
    _fails[0] += 1
    print(f"request failed ({path}); consecutive failures {_fails[0]}", flush=True)
    if _fails[0] >= 3:
        raise Stop("3 consecutive failed requests (429s?), stopping; rerun later to resume")
    return None


def ts(iso):
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
    except Exception:
        return None


def fl(x):
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


def connect(series):
    os.makedirs(OUT, exist_ok=True)
    db = sqlite3.connect(os.path.join(OUT, series + ".sqlite"))
    db.executescript(SCHEMA)
    return db


def meta(db, k, v=None):
    if v is None:
        r = db.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        return r[0] if r else None
    db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, v))
    db.commit()


def do_list(series):
    db = connect(series)
    if meta(db, "list_done") == "1":
        print(series, "listing already complete"); return
    cursor = meta(db, "cursor") or None
    t0 = time.time(); pages = 0
    while True:
        p = {"series_ticker": series, "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        d = get("/historical/markets", p)
        if d is None:
            continue
        pages += 1
        ms = d.get("markets", [])
        rows = []
        for m in ms:
            c, o = ts(m.get("close_time")), ts(m.get("open_time"))
            if c is not None and o is not None and c < BOUNDARY and m.get("result") in ("yes", "no"):
                rows.append((m["ticker"], series, o, c, m["result"], m.get("floor_strike")))
        db.executemany("INSERT OR IGNORE INTO listing VALUES(?,?,?,?,?,?)", rows)
        cursor = d.get("cursor")
        db.execute("INSERT INTO calllog VALUES(?,?,?)", (time.time(), "list", len(ms)))
        db.commit()
        oldest = min((ts(m.get("close_time")) or 0 for m in ms), default=0)
        print(f"{series} page {pages}: {len(ms)} markets, kept {len(rows)}, oldest close {datetime.fromtimestamp(oldest, timezone.utc):%Y-%m-%d %H:%M}", flush=True)
        if cursor:
            meta(db, "cursor", cursor)
        if not cursor or not ms:
            meta(db, "list_done", "1"); break
    print(f"{series} listing done in {time.time()-t0:.0f}s")


def parse(c, t, series):
    b, a, p = c.get("yes_bid") or {}, c.get("yes_ask") or {}, c.get("price") or {}
    end = c.get("end_period_ts")
    if end is None:
        return None
    return (t, series, int(end), fl(b.get("open")), fl(b.get("high")), fl(b.get("low")), fl(b.get("close")),
            fl(a.get("open")), fl(a.get("high")), fl(a.get("low")), fl(a.get("close")),
            fl(p.get("close")), fl(c.get("volume")), fl(c.get("open_interest")))


def do_fetch(series, mx):
    db = connect(series)
    todo = db.execute("""SELECT ticker, open_ts, close_ts, result, strike FROM listing WHERE ticker NOT IN (SELECT ticker FROM market)
                         AND ticker NOT IN (SELECT ticker FROM nocandle) ORDER BY close_ts DESC""").fetchall()
    print(f"{series}: {len(todo)} listed markets still to fetch", flush=True)
    t0 = time.time(); n = 0
    for t, o, c, res, strike in todo[:mx]:
        d = get(f"/historical/markets/{t}/candlesticks", {"start_ts": o, "end_ts": c, "period_interval": 1})
        if d is None:
            continue
        rows = [r for r in (parse(x, t, series) for x in d.get("candlesticks", [])) if r]
        if rows:
            db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (t, series, o, c, res, strike, len(rows)))
        else:
            db.execute("INSERT OR REPLACE INTO nocandle VALUES(?,?)", (t, c))
        db.commit(); n += 1
        if n % 100 == 0:
            el = time.time() - t0
            db.execute("INSERT INTO calllog VALUES(?,?,?)", (time.time(), "fetch100", 100)); db.commit()
            print(f"{series}: {n} fetched, {el:.0f}s, {el/n*1200/60:.1f} min per 1,200", flush=True)
    print(f"{series}: fetched {n} this run in {time.time()-t0:.0f}s")


def report(series):
    db = connect(series)
    q = lambda s, *a: db.execute(s, a).fetchone()[0]
    iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%d %H:%M") if x else "-"
    out = {"series": series, "listed": q("SELECT count(*) FROM listing"), "with_candles": q("SELECT count(*) FROM market"),
           "no_candles": q("SELECT count(*) FROM nocandle"), "candle_rows": q("SELECT count(*) FROM candle")}
    lo, hi = db.execute("SELECT min(close_ts), max(close_ts) FROM market").fetchone()
    out["first_close"], out["last_close"] = iso(lo), iso(hi)
    llo, lhi = db.execute("SELECT min(close_ts), max(close_ts) FROM listing").fetchone()
    out["listing_first"], out["listing_last"] = iso(llo), iso(lhi)
    out["distinct_utc_dates"] = q("SELECT count(DISTINCT date(close_ts,'unixepoch')) FROM market")
    closes = [r[0] for r in db.execute("SELECT close_ts FROM market ORDER BY close_ts")]
    gaps = [(a, b) for a, b in zip(closes, closes[1:]) if b - a > 900]
    out["gaps_over_15min"] = len(gaps)
    out["missing_windows_in_gaps"] = sum((b - a) // 900 - 1 for a, b in gaps)
    out["gaps_over_6h"] = [(iso(a), iso(b)) for a, b in gaps if b - a > 6 * 3600][:12]
    out["gaps_over_6h_count"] = sum(1 for a, b in gaps if b - a > 6 * 3600)
    out["markets_under_10_candles"] = q("SELECT count(*) FROM market WHERE n_candles<10")
    out["markets_16plus_candles"] = q("SELECT count(*) FROM market WHERE n_candles>=15")
    out["null_bid_or_ask_close"] = q("SELECT count(*) FROM candle WHERE bid_c IS NULL OR ask_c IS NULL")
    out["crossed_bid_gt_ask"] = q("SELECT count(*) FROM candle WHERE bid_c>ask_c")
    out["sentinel_bid0_ask_ge_099"] = q("SELECT count(*) FROM candle WHERE bid_c=0 AND ask_c>=0.99")
    out["sentinel_bid0_ask1"] = q("SELECT count(*) FROM candle WHERE bid_c=0 AND ask_c>=1")
    out["bid_zero"] = q("SELECT count(*) FROM candle WHERE bid_c=0")
    out["out_of_range"] = q("SELECT count(*) FROM candle WHERE bid_c<0 OR ask_c>1 OR bid_c>1 OR ask_c<0")
    out["markets_no_quote_in_last_8min"] = q("""SELECT count(*) FROM market m WHERE NOT EXISTS (SELECT 1 FROM candle c WHERE c.ticker=m.ticker
        AND c.end_ts BETWEEN m.close_ts-480 AND m.close_ts AND c.bid_c IS NOT NULL AND c.ask_c IS NOT NULL)""")
    out["markets_without_6min_candle"] = q("""SELECT count(*) FROM market m WHERE NOT EXISTS (SELECT 1 FROM candle c WHERE c.ticker=m.ticker AND c.end_ts=m.close_ts-360)""")
    out["markets_without_10min_candle"] = q("""SELECT count(*) FROM market m WHERE NOT EXISTS (SELECT 1 FROM candle c WHERE c.ticker=m.ticker AND c.end_ts=m.close_ts-600)""")
    out["by_month"] = db.execute("SELECT strftime('%Y-%m',close_ts,'unixepoch'), count(*), count(DISTINCT date(close_ts,'unixepoch')) FROM market GROUP BY 1").fetchall()
    out["listing_by_month"] = db.execute("SELECT strftime('%Y-%m',close_ts,'unixepoch'), count(*) FROM listing GROUP BY 1").fetchall()
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    mx = 10**9
    if "--max" in args:
        i = args.index("--max"); mx = int(args[i + 1]); args = args[:i] + args[i + 2:]
    try:
        for s in args:
            {"list": do_list, "fetch": lambda x: do_fetch(x, mx), "report": report}[cmd](s)
    except Stop as e:
        print("STOPPED:", e); sys.exit(2)
