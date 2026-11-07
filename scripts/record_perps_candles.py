#!/usr/bin/env python3
"""Saves Kalshi's PUBLIC 1 minute candles and funding history for the stock and index perps, one UTC date at a time (research only, 2026-11-06, V2's request, the owner approved).

Why: V2's stock perp tests need the perp's own minute bars (bid, ask, price, open interest, volume) and the funding paid, and the candle endpoint only helps while the history is
kept. The universe is every perp the public list marks Equities or Indices (the 19 name design list was not in the repo, so the whole class is taken; a market that is
not listed on a date simply has no bars). Plain GETs of public endpoints: no key, no login, no order. It writes files and nothing else.

Run after the US session ends: it archives the PREVIOUS UTC date (a finished day) and does nothing if both of that day's files exist. At least 1.2 seconds between calls,
and three refused (429) answers in a row end the run without writing, so the next start retries. It stops by itself after STOP_DATE.

Usage: python3 scripts/record_perps_candles.py OUT_DIR   (writes OUT_DIR/kalshi1m/<date>.csv.gz and OUT_DIR/funding/<date>.csv.gz)
"""
import csv
import datetime as dt
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2/margin"
CLASSES = ("Equities", "Indices")
STOP_DATE = dt.date(2027, 2, 26)
GAP_S = 1.2
MAX_429_IN_A_ROW = 3
CANDLE_COLS = ["ticker", "end_period_ts", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close", "price_open", "price_high",
               "price_low", "price_close", "price_mean", "price_previous", "open_interest", "volume"]
FUNDING_COLS = ["ticker", "funding_time", "funding_rate", "mark_price"]
UA = {"User-Agent": "shwoopnet-research-recorder"}


class Refused(Exception):
    pass


def http_get(url):
    """(status, json or None). Never raises."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def num(x):
    return x if x not in (None, "") else ""


def candle_row(ticker, c):
    def o(k, f):
        v = c.get(k)
        return num(v.get(f)) if isinstance(v, dict) else ""
    return [ticker, c.get("end_period_ts", ""), o("bid", "open"), o("bid", "high"), o("bid", "low"), o("bid", "close"), o("ask", "open"), o("ask", "high"), o("ask", "low"),
            o("ask", "close"), o("price", "open"), o("price", "high"), o("price", "low"), o("price", "close"), o("price", "mean"), o("price", "previous"),
            num(c.get("open_interest")), num(c.get("volume"))]


def funding_row(ticker, f):
    return [ticker, f.get("funding_time", ""), num(f.get("funding_rate")), num(f.get("mark_price"))]


def run(out_dir, now=None, get=None, sleep=time.sleep):
    now = now or dt.datetime.now(dt.timezone.utc)
    get = get or http_get
    if now.date() > STOP_DATE:
        print("past the stop date; nothing recorded")
        return 0
    day = now.date() - dt.timedelta(days=1)
    name = day.isoformat() + ".csv.gz"
    cpath, fpath = os.path.join(out_dir, "kalshi1m", name), os.path.join(out_dir, "funding", name)
    if os.path.exists(cpath) and os.path.exists(fpath):
        print("this date is already archived; nothing to do")
        return 0
    start = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())
    streak = [0]

    def call(url):
        st, body = get(url)
        sleep(GAP_S)
        if st == 429:
            streak[0] += 1
            if streak[0] >= MAX_429_IN_A_ROW:
                raise Refused()
            sleep(3.0)
            return None
        streak[0] = 0
        return body if st == 200 and isinstance(body, dict) else None

    try:
        listing = call(BASE + "/markets?limit=200")
        markets = (listing or {}).get("markets") or []
        tickers = sorted(m["ticker"] for m in markets if m.get("asset_class") in CLASSES and m.get("ticker"))
        if not tickers:
            print("no stock or index perps listed; nothing written")
            return 1
        crows, frows, ok_c, ok_f = [], [], 0, 0
        for t in tickers:
            b = call("%s/markets/%s/candlesticks?period_interval=1&start_ts=%d&end_ts=%d" % (BASE, t, start, start + 86400))
            if b is not None:
                ok_c += 1
                crows += [candle_row(t, c) for c in b.get("candlesticks") or []]
            b = call("%s/funding_rates/historical?ticker=%s&limit=30" % (BASE, t))
            if b is not None:
                ok_f += 1
                frows += [funding_row(t, f) for f in b.get("funding_rates") or [] if str(f.get("funding_time", ""))[:10] == day.isoformat()]
    except Refused:
        print("refused three times in a row; nothing written, the next start retries")
        return 1
    if ok_c * 2 < len(tickers) or ok_f * 2 < len(tickers):
        print("fewer than half the reads worked; nothing written")
        return 1
    for path, cols, rows in ((cpath, CANDLE_COLS, crows), (fpath, FUNDING_COLS, frows)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with gzip.open(path, "wt", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
    print("wrote %d candles and %d funding rows for %d markets (%s)" % (len(crows), len(frows), len(tickers), day))
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "perp-data"))
