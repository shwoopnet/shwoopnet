#!/usr/bin/env python3
"""Recorder OINIGHTLY (Nov 13, 2026, Idea Desk B; asked by the Head of R&D and Main, form 2). Research data only: nothing here trades, signs or sends an order.

What it records. For the 13 OICORE shadow places (Desk A's twelve at commit 29dd035e plus Ethereum): Kalshi's PUBLIC one minute candles with open interest, from 7 to 2 minutes before each 15 minute
close of ONE UTC day (the previous day by default), one batched candlesticks request per close, so each place's open interest threshold and signal can be computed. A series is asked at a close only if
the committed hours table (kalshi-scalper/workers/oicand/OI_HOURS_TABLE.json, made from the OICAND lists run by workers/oicand/oi_hours_table.py) lists that weekday and time, so no ticker that does not exist is
asked. EVENT830's 8 series skip the 13:30Z close on EVENT830's calendar dates. Forward days only: before 2026-11-14 it refuses. Eastern is taken as EST (UTC-5), valid to 2027-03-13.
  - candles.csv:  one row per candle (day, close_time, ticker, end_period_ts, open interest, volume, price, yes_bid and yes_ask open, high, low, close); a missing value is empty, never zero
  - coverage.csv: one row per request (close, tickers asked, tickers answered, candles, status, tries)
Public data only: no key, no auth header, no order. One host (api.elections.kalshi.com), GET only, redirects refused, a generic User-Agent. One request stream, at least 1.0 s apart. A 429, a 5xx or a dropped
connection waits 2 s, doubling to 30 s, tried 4 times, then the request is marked failed and the run goes on; 3 failures in a row end the run. A hard budget of 120 requests a run. The script always exits 0.
It stops by itself: nothing is recorded from END_UTC (2026-12-31 23:59 UTC). Stop it sooner by deleting the workflow."""
import argparse
import calendar
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://api.elections.kalshi.com/trade-api/v2"
END_UTC = "2026-12-31T23:59:00Z"
SERIES = ["KXXRP15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M", "KXETH15M"]
EV830 = {"KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"}
REL = {"2026-11-05", "2026-11-06", "2026-11-10", "2026-11-12", "2026-11-13", "2026-11-17", "2026-11-19", "2026-11-25", "2026-12-03", "2026-12-04", "2026-12-10", "2026-12-15", "2026-12-16", "2026-12-17", "2026-12-23"}
FIRST_DAY, LAST_EST_DAY = "2026-11-14", "2027-03-13"
MAX_REQUESTS = 120
GAP_S = 1.0
BACKOFF_S, BACKOFF_MAX_S, MAX_TRIES = 2.0, 30.0, 4
MAX_FAIL_RUN = 3
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
UTC = timezone.utc
ROW_COLS = ["day", "close_time", "market_ticker", "end_period_ts", "open_interest_fp", "volume_fp", "price_open", "price_high", "price_low", "price_close", "price_mean", "price_previous",
            "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close"]
COVER_COLS = ["day", "close_time", "request_id", "tickers_asked", "tickers_answered", "candles", "status", "tries"]
UA = {"User-Agent": "shwoopnet-research-recorder"}


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


def ticker(series, close):
    et = close - timedelta(hours=5)
    return "%s-%02d%s%02d%02d%02d-%02d" % (series, et.year % 100, MON[et.month - 1], et.day, et.hour, et.minute, et.minute)


def build_requests(day, hours):
    """The requests for one UTC day, or None when the day is outside the forward window (the Head's rule: nothing before 2026-11-14; EST only to 2027-03-13)."""
    if day < FIRST_DAY or day > LAST_EST_DAY:
        return None
    d0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC)
    wd = str(d0.weekday())
    reqs = []
    for i in range(96):
        close = d0 + timedelta(minutes=15 * i)
        hm = close.strftime("%H:%M")
        ts = [ticker(s, close) for s in SERIES if hm in hours.get(s, {}).get(wd, []) and not (s in EV830 and hm == "13:30" and day in REL)]
        if ts:
            c = int(close.timestamp())
            reqs.append({"id": "c%04d" % (len(reqs) + 1), "close": close.strftime("%Y-%m-%dT%H:%M:%SZ"), "tickers": sorted(ts), "start_ts": c - 420, "end_ts": c - 120})
    return reqs


def url_for(r):
    return "%s/markets/candlesticks?market_tickers=%s&start_ts=%d&end_ts=%d&period_interval=1" % (BASE, ",".join(r["tickers"]), r["start_ts"], r["end_ts"])


def _g(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return "" if d is None else str(d)


def rows_from(day, close, resp):
    """CSV rows from one candlesticks answer; a missing value is empty, never zero."""
    out = []
    for m in (resp.get("markets") or []) if isinstance(resp, dict) else []:
        for c in m.get("candlesticks") or []:
            out.append([day, close, m.get("market_ticker", ""), _g(c, "end_period_ts"), _g(c, "open_interest_fp"), _g(c, "volume_fp"),
                        _g(c, "price", "open_dollars"), _g(c, "price", "high_dollars"), _g(c, "price", "low_dollars"), _g(c, "price", "close_dollars"), _g(c, "price", "mean_dollars"), _g(c, "price", "previous_dollars"),
                        _g(c, "yes_bid", "open_dollars"), _g(c, "yes_bid", "high_dollars"), _g(c, "yes_bid", "low_dollars"), _g(c, "yes_bid", "close_dollars"),
                        _g(c, "yes_ask", "open_dollars"), _g(c, "yes_ask", "high_dollars"), _g(c, "yes_ask", "low_dollars"), _g(c, "yes_ask", "close_dollars")])
    return out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the one allowed host is checked on the URL we build, so a redirect could leave it. A 3xx answer is a failed read."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(url):
    """(status, decoded json or None). Never raises: a failed read is a status, so one bad second cannot end the run."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=UA), timeout=15) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


class Stream:
    """One request stream, at least GAP_S between calls; a 429, a 5xx or a dropped connection waits BACKOFF_S, doubling to BACKOFF_MAX_S, tried MAX_TRIES times."""

    def __init__(self):
        self.last = 0.0

    def get(self, url):
        wait, status, body = BACKOFF_S, 0, None
        for k in range(1, MAX_TRIES + 1):
            gap = GAP_S - (time.time() - self.last)
            if gap > 0:
                time.sleep(gap)
            self.last = time.time()
            status, body = http_get(url)
            if status == 200 and isinstance(body, dict):
                return status, body, k
            if status in (429, 0) or status >= 500:
                if k < MAX_TRIES:
                    time.sleep(wait)
                    wait = min(wait * 2, BACKOFF_MAX_S)
                continue
            break
        return status, None, k


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--hours", required=True)
    ap.add_argument("--day", default=None)
    a = ap.parse_args(argv)
    if past_end(time.time()):
        print("past the end date: nothing to record"); return 0
    day = a.day or (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        hours = json.load(open(a.hours))
    except Exception:
        print("no hours table: nothing recorded"); return 0
    reqs = build_requests(day, hours)
    if reqs is None:
        print("day %s is outside the forward window %s to %s: nothing recorded" % (day, FIRST_DAY, LAST_EST_DAY)); return 0
    os.makedirs(a.out_dir, exist_ok=True)
    s, fails, n = Stream(), 0, 0
    with open(os.path.join(a.out_dir, "candles.csv"), "w", newline="") as fc, open(os.path.join(a.out_dir, "coverage.csv"), "w", newline="") as fv:
        wc, wv = csv.writer(fc), csv.writer(fv)
        wc.writerow(ROW_COLS); wv.writerow(COVER_COLS)
        for r in reqs:
            if n >= MAX_REQUESTS or fails >= MAX_FAIL_RUN:
                wv.writerow([day, r["close"], r["id"], len(r["tickers"]), "", "", "not asked", ""]); continue
            n += 1
            status, body, tries = s.get(url_for(r))
            rows = rows_from(day, r["close"], body) if body else []
            fails = 0 if status == 200 else fails + 1
            for row in rows:
                wc.writerow(row)
            answered = len({x[2] for x in rows})
            wv.writerow([day, r["close"], r["id"], len(r["tickers"]), answered, len(rows), status, tries])
    print("day %s | requests built %d | asked %d" % (day, len(reqs), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
