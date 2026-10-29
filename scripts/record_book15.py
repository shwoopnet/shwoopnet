#!/usr/bin/env python3
"""Whole-window order book recorder for the research session's R2 (Oct 29, 2026), built because MM1 (market making on gold) needs a real queue model.

For each 15 minute series (KXBTC15M, KXETH15M, KXGOLD15M) it records the market closing next: the best 5 YES bids and 5 NO bids with sizes every 3 seconds from 15 minutes before
the close (the whole window) to the close, plus the public trade tape every 30 seconds with trade ids de-duplicated. It reads PUBLIC endpoints only: no key, no signing, no account,
no order. The server's Date header is stored on every row so clock skew can be measured. A refused read (429) backs off. Back to back jobs cover every window.
It is modelled on record_book.py (the hourly Bitcoin ladder) and shares no code with it, so changing one can never change the other.

Rows are written exactly as the exchange returns them (levels re-ordered best first, prices and sizes as numbers, nothing computed)."""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")
WINDOW_S = 15 * 60         # the whole window: record from this long before each close
BOOK_EVERY_S = 3.0
TRADES_EVERY_S = 30.0
BACKOFF_S = 2.0
DEPTH = 5
UA = {"User-Agent": "shwoopnet-research-recorder"}

BOOK_COLS = ["poll_ts_local_ms", "server_date_header", "series", "ticker", "close_time"] \
    + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
TRADE_COLS = ["poll_ts_local_ms", "server_date_header", "series", "ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side", "trade_id"]
COVER_COLS = ["series", "close_time", "polls", "ok_polls", "n429", "first_ms", "last_ms"]


def http_get(url):
    """(status, decoded json or None, Date header or ''). Never raises: a failed read is a status, so one bad second cannot end the run."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_levels(levels):
    """The exchange lists levels from the worst price to the best (the best is LAST). Return up to 5 [price, size] pairs, best first, as numbers."""
    out = []
    for lv in reversed(levels or []):
        if isinstance(lv, (list, tuple)) and len(lv) >= 2:
            p, s = num(lv[0]), num(lv[1])
            if p is not None and s is not None:
                out.append((p, s))
    return out[:DEPTH]


def book_row(ts_ms, date_header, series, market, resp):
    """One CSV row, or None when the response has no book. Missing levels are left empty, never zero."""
    if not isinstance(resp, dict):
        return None
    ob = resp.get("orderbook_fp") or resp.get("orderbook") or {}
    yes, no = parse_levels(ob.get("yes_dollars")), parse_levels(ob.get("no_dollars"))
    if not yes and not no:
        return None
    pad = lambda lv, k: [lv[i][k] if i < len(lv) else "" for i in range(DEPTH)]
    return [ts_ms, date_header, series, market.get("ticker"), market.get("close_time")] \
        + pad(yes, 0) + pad(yes, 1) + pad(no, 0) + pad(no, 1)


def trade_rows(ts_ms, date_header, series, trades, seen=None):
    """One row per trade. The tape is read with a few seconds of overlap so nothing is missed, so a trade id already written (in `seen`) is skipped."""
    rows = []
    for t in (trades or []):
        if not isinstance(t, dict):
            continue
        tid = t.get("trade_id")
        if seen is not None and tid is not None:
            if tid in seen:
                continue
            seen.add(tid)
        rows.append([ts_ms, date_header, series, t.get("ticker"), t.get("created_time"), t.get("yes_price_dollars"), t.get("count_fp"), t.get("taker_outcome_side"), tid])
    return rows


def pick_closing(markets, close_time):
    """The market of the series that closes at close_time, or None. Only the close time is looked at, so the choice cannot be selected on returns."""
    for m in markets:
        if m.get("close_time") == close_time:
            return m
    return None


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def cycle_stop_time(now, cycle_s):
    """Same rule as record_quotes.py: stop a minute after the first cycle boundary that leaves this job a full cycle, so the next job (which starts early) queues behind it."""
    into = now % cycle_s
    first_boundary = now - into + cycle_s
    if cycle_s - into < 1800:
        return first_boundary + cycle_s + 60
    return first_boundary + 60


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        for name, cols in (("book", BOOK_COLS), ("trades", TRADE_COLS), ("coverage", COVER_COLS)):
            f = open(os.path.join(d, name + ".csv"), "a", newline="")
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(cols)
            self.files.append(f)
            self.w[name] = w

    def write(self, name, rows):
        self.w[name].writerows(rows)

    def flush(self):
        for f in self.files:
            f.flush()

    def close(self):
        self.flush()
        for f in self.files:
            f.close()


def discover(series, close_epoch):
    """The open market of `series` that closes at close_epoch (UTC), or None (gold has no market when its venue is shut)."""
    st, body, _d = http_get("%s/markets?series_ticker=%s&status=open&limit=100" % (BASE, series))
    if st != 200 or not isinstance(body, dict):
        return None
    return pick_closing(body.get("markets") or [], iso(close_epoch))


def record_window(out, close_epoch, stop_at):
    """Record one 15 minute window for every series: from WINDOW_S before the close to the close (or the job's stop time)."""
    start = close_epoch - WINDOW_S
    while time.time() < start:
        if time.time() >= stop_at:
            return False
        time.sleep(min(5.0, max(0.1, start - time.time())))
    picks = {}
    for s in SERIES:
        m = discover(s, close_epoch)
        if m:
            picks[s] = m
        else:
            print("no %s market for the close at %s" % (s, iso(close_epoch)), flush=True)
    if not picks:
        return True
    stats = {s: [0, 0, 0, 0, 0] for s in picks}   # polls, ok, n429, first_ms, last_ms
    last_trade_epoch = {s: int(time.time()) - 60 for s in picks}
    seen_trades = set()
    next_trades = 0.0
    while time.time() < min(close_epoch, stop_at):
        loop_start = time.time()
        for s, m in picks.items():
            ts = int(time.time() * 1000)
            st, body, date = http_get("%s/markets/%s/orderbook?depth=%d" % (BASE, m["ticker"], DEPTH))
            stats[s][0] += 1
            if st == 429:
                stats[s][2] += 1
                time.sleep(BACKOFF_S)
                continue
            row = book_row(ts, date, s, m, body) if st == 200 else None
            if row:
                out.write("book", [row])
                stats[s][1] += 1
                stats[s][3] = stats[s][3] or ts
                stats[s][4] = ts
        if time.time() >= next_trades:
            next_trades = time.time() + TRADES_EVERY_S
            for s, m in picks.items():
                st, body, date = http_get("%s/markets/trades?ticker=%s&min_ts=%d&limit=1000" % (BASE, m["ticker"], last_trade_epoch[s]))
                if st == 429:
                    stats[s][2] += 1
                    time.sleep(BACKOFF_S)
                elif st == 200 and isinstance(body, dict):
                    out.write("trades", trade_rows(int(time.time() * 1000), date, s, body.get("trades"), seen_trades))
                    last_trade_epoch[s] = int(time.time()) - 5
        out.flush()
        time.sleep(max(0.0, BOOK_EVERY_S - (time.time() - loop_start)))
    for s, v in stats.items():
        out.write("coverage", [[s, iso(close_epoch), v[0], v[1], v[2], v[3], v[4]]])
    out.flush()
    return True


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--cycle-hours", type=float, default=4, help="back to back jobs: stop a minute after the cycle boundary that leaves one full cycle")
    ap.add_argument("--max-minutes", type=float, default=0, help="for a test: stop after this many minutes")
    a = ap.parse_args(argv)
    now = time.time()
    stop_at = now + a.max_minutes * 60 if a.max_minutes else cycle_stop_time(now, a.cycle_hours * 3600)
    out = Out(a.out_dir)
    try:
        close_epoch = int(now - now % WINDOW_S + WINDOW_S)
        while close_epoch - WINDOW_S < stop_at and time.time() < stop_at:
            if not record_window(out, close_epoch, stop_at):
                break
            close_epoch += WINDOW_S
    finally:
        out.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
