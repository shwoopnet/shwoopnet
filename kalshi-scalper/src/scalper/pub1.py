"""PUB1 (README, Pre-registration: GAS1, APP1 and CMD1): daily ladders on a published number or a spot price, one walk-forward model each.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

This file starts as the DOWNLOAD only. History goes into its OWN database (`data/pub1.sqlite`): settled markets with their published value, hourly
bid and ask candles, and Yahoo's 5 minute spot bars for the commodity series. The rules are written in the README before any of them is computed.
Usage: python -m scalper.pub1 fetch
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from . import api, backfill
from .paths import DATA_DIR

PUB_DB = DATA_DIR / "pub1.sqlite"
DAYS = 69
GAS = "KXAAAGASD"
APPROVE = "KXTRUMPAPPROVE"
# series -> Yahoo symbol for the spot price the market settles near (a proxy, not the settlement source itself)
COMMODITIES = {"KXBRENTD": "BZ=F", "KXWTI": "CL=F", "KXGOLDD": "GC=F", "KXSILVERD": "SI=F", "KXNATGASD": "NG=F", "KXCOPPERD": "HG=F"}
SERIES = [GAS, APPROVE] + list(COMMODITIES)


def fetch_spot(symbol: str) -> list[tuple[int, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=60d"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                res = json.load(r)["chart"]["result"][0]
            break
        except Exception:
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))
    closes = res["indicators"]["quote"][0]["close"]
    return [(int(t), float(c)) for t, c in zip(res["timestamp"], closes) if c is not None]


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(PUB_DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike_type TEXT, floor REAL, cap REAL, value TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid_c REAL, ask_c REAL, volume REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS spot(symbol TEXT, ts INTEGER, close REAL, PRIMARY KEY(symbol, ts));""")
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    for series, sym in COMMODITIES.items():
        rows = fetch_spot(sym)
        db.executemany("INSERT OR REPLACE INTO spot VALUES(?,?,?)", [(sym, t, c) for t, c in rows])
        db.commit()
        print(f"spot {sym}: {len(rows)} bars", flush=True)
    for series in SERIES:
        listed = [m for m in api.settled_markets(series, now - DAYS * 86400, now) if m.get("result") in ("yes", "no")]
        by_day: dict = defaultdict(list)
        for m in listed:
            by_day[m["close_time"]].append(m)
        stored = 0
        for close_iso in sorted(by_day):
            ms = [m for m in by_day[close_iso] if m["ticker"] not in have]
            if not ms:
                continue
            close_ts = backfill.iso_ts(close_iso)
            open_ts = max(min(backfill.iso_ts(m.get("open_time")) or close_ts for m in ms), close_ts - 3 * 86400)
            for i in range(0, len(ms), 100):
                chunk = ms[i:i + 100]
                got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": open_ts, "end_ts": close_ts, "period_interval": 60})
                by_t = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
                for m in chunk:
                    rows = [r for r in (backfill.parse_candle(c, m["ticker"], series) for c in by_t.get(m["ticker"], [])) if r]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?)", [(r[0], r[2], r[6], r[10], r[12]) for r in rows])
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?,?,?,?)", (m["ticker"], series, backfill.iso_ts(m.get("open_time")), close_ts, m["result"],
                                                                                         m.get("strike_type"), m.get("floor_strike"), m.get("cap_strike"),
                                                                                         m.get("expiration_value"), api.f(m.get("volume_fp"))))
                    have.add(m["ticker"])
                    stored += 1
            db.commit()
            time.sleep(0.3)
        print(f"{series}: {len(listed)} settled markets, {stored} new", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["fetch"]:
        fetch()
    else:
        sys.exit("run() is added after the rules are registered in the README")
