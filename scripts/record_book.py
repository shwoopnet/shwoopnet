#!/usr/bin/env python3
"""Order book recorder for the research session's QUOTE2B (Oct 29, 2026, the owner approved; the research session wrote the spec).

Records the Bitcoin hourly "above K" ladder (KXBTCD): for the 7 strikes nearest the money of the event closing at the next top of the hour, the best 5 YES bids and 5 NO bids
with sizes every 3 seconds, from 55 minutes before the close to the close, plus the public trade tape every 30 seconds. It is what a queue model needs: the size ahead of a
posted price, and what traded at that price afterwards. It reads PUBLIC endpoints only: no key, no signing, no account, no order. The server's Date header is stored on every
row so clock skew can be measured. Back to back jobs cover every hour (see cycle_stop_time).

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
SERIES = "KXBTCD"
STRIKES = 7
LEAD_S = 55 * 60           # start recording this long before each hourly close
BOOK_EVERY_S = 3.0
TRADES_EVERY_S = 30.0
DEPTH = 5
UA = {"User-Agent": "shwoopnet-research-recorder"}

BOOK_COLS = ["poll_ts_local_ms", "server_date_header", "ticker", "strike", "close_time"] \
    + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
TRADE_COLS = ["poll_ts_local_ms", "ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side", "trade_id"]
COVER_COLS = ["close_time", "tickers", "polls", "ok_polls", "n429", "first_ms", "last_ms"]


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


def book_row(ts_ms, date_header, market, resp):
    """One CSV row, or None when the response has no book. Missing levels are left empty, never zero."""
    if not isinstance(resp, dict):
        return None
    ob = resp.get("orderbook_fp") or resp.get("orderbook") or {}
    yes, no = parse_levels(ob.get("yes_dollars")), parse_levels(ob.get("no_dollars"))
    if not yes and not no:
        return None
    pad = lambda lv, k: [lv[i][k] if i < len(lv) else "" for i in range(DEPTH)]
    return [ts_ms, date_header, market.get("ticker"), market.get("floor_strike"), market.get("close_time")] \
        + pad(yes, 0) + pad(yes, 1) + pad(no, 0) + pad(no, 1)


def trade_rows(ts_ms, trades):
    return [[ts_ms, t.get("ticker"), t.get("created_time"), t.get("yes_price_dollars"), t.get("count_fp"), t.get("taker_outcome_side"), t.get("trade_id")]
            for t in (trades or []) if isinstance(t, dict)]


def pick_near_money(markets, close_time, limit=STRIKES):
    """The `limit` strikes of the event closing at close_time whose YES bid is closest to 50c. A market with no quoted bid is skipped. Cost is observable before any outcome."""
    cands = []
    for m in markets:
        if m.get("close_time") != close_time:
            continue
        b = num(m.get("yes_bid_dollars"))
        if b is None or b <= 0:
            continue
        cands.append((abs(b - 0.5), num(m.get("floor_strike")) or 0, m))
    cands.sort(key=lambda c: (c[0], c[1]))
    return [c[2] for c in cands[:limit]]


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


def discover(close_epoch):
    """The 7 near-the-money markets of the event that closes at close_epoch (UTC), or []."""
    close_time = iso(close_epoch)
    markets, cursor = [], ""
    for _ in range(6):
        url = "%s/markets?series_ticker=%s&status=open&limit=1000%s" % (BASE, SERIES, ("&cursor=" + cursor) if cursor else "")
        st, body, _d = http_get(url)
        if st != 200 or not isinstance(body, dict):
            break
        markets += body.get("markets") or []
        cursor = body.get("cursor") or ""
        if not cursor:
            break
    return pick_near_money(markets, close_time)


def record_hour(out, close_epoch, stop_at):
    """Record one hour: from LEAD_S before the close to the close (or the job's stop time)."""
    start = close_epoch - LEAD_S
    while time.time() < start:
        if time.time() >= stop_at:
            return False
        time.sleep(min(5.0, max(0.1, start - time.time())))
    picks = discover(close_epoch)
    if not picks:
        print("no markets found for the close at %s" % iso(close_epoch), flush=True)
        return True
    polls = ok = n429 = 0
    first_ms = last_ms = 0
    last_trade_ts = {m["ticker"]: iso(time.time() - 60) for m in picks}
    next_trades = 0.0
    while time.time() < min(close_epoch, stop_at + 1e9):
        loop_start = time.time()
        for m in picks:
            ts = int(time.time() * 1000)
            st, body, date = http_get("%s/markets/%s/orderbook?depth=%d" % (BASE, m["ticker"], DEPTH))
            polls += 1
            if st == 429:
                n429 += 1
                time.sleep(2.0)
                continue
            row = book_row(ts, date, m, body) if st == 200 else None
            if row:
                out.write("book", [row])
                ok += 1
                first_ms = first_ms or ts
                last_ms = ts
        if time.time() >= next_trades:
            next_trades = time.time() + TRADES_EVERY_S
            for m in picks:
                st, body, _d = http_get("%s/markets/trades?ticker=%s&min_ts=%d&limit=1000" % (BASE, m["ticker"], int(time.mktime(time.strptime(last_trade_ts[m["ticker"]], "%Y-%m-%dT%H:%M:%SZ"))) - time.timezone))
                if st == 200 and isinstance(body, dict):
                    rows = trade_rows(int(time.time() * 1000), body.get("trades"))
                    out.write("trades", rows)
                    last_trade_ts[m["ticker"]] = iso(time.time() - 5)
        out.flush()
        time.sleep(max(0.0, BOOK_EVERY_S - (time.time() - loop_start)))
    out.write("coverage", [[iso(close_epoch), len(picks), polls, ok, n429, first_ms, last_ms]])
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
        close_epoch = int(now - now % 3600 + 3600)
        while close_epoch - LEAD_S < stop_at and time.time() < stop_at:
            if not record_hour(out, close_epoch, stop_at):
                break
            close_epoch += 3600
    finally:
        out.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
