#!/usr/bin/env python3
"""Politics shadow recorder (Nov 11, 2026, the owner approved). Research data only: nothing here trades. The politics census found a thin universe (two series with 30 or more settled
events, most weekly series only 8 to 12 events old), so this records FORWARD: the quote of every open market of the listed series every 30 minutes, and the result of each market after it
settles, so history accrues for the research chats.

The series come from kalshi-scalper/workers/POLREC_SERIES.json (at most max_series, names checked), so a list edit is a reviewed change. The hold cap (cap_days in the series file: 14 days until Nov 11, 2026, then 30 days by the owner's decision) holds: a market is
recorded only if it closes within cap_days of now AND its open-to-close span is at most cap_days (within_cap). Markets past the cap are counted, not recorded, and the count is written once a
day (daily.csv) so we know what was left out.

It reads PUBLIC Kalshi market data only: no key, no signing, no auth header, no account path, no order, no Firestore. One request stream with at least 5 seconds between calls (at most 12 a
minute); a 429 waits 5 seconds doubling up to 60 and is not asked again at once. A body that is not an object is no answer, never an error. Redirects are refused.

It stops by itself: a run started at or after END_UTC (2027-02-28 23:59 UTC) exits at once, and a poll never starts after it. Stop it sooner by deleting the workflow.

Rows are written as the exchange returns them (dollar fields as strings), nothing computed. A missing field is empty."""
import argparse
import calendar
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
SERIES_FILE = os.path.join(HERE, "..", "kalshi-scalper", "workers", "POLREC_SERIES.json")
END_UTC = "2027-02-28T23:59:00Z"   # nothing is recorded from here on
POLL_EVERY_S = 1800              # politics markets are slow: a quote every 30 minutes (the owner, via the coordinator, Nov 11)
GAP_S = 5.0                        # at least this long between calls: at most 12 a minute
BACKOFF_S = 5.0
BACKOFF_MAX_S = 60.0
PAGE_LIMIT = 1000
MAX_PAGES = 10                     # a guard against an endless cursor for one series
SETTLED_LOOKBACK_S = 48 * 3600     # the hourly result read asks for markets closed in the last 48 hours; a repeat across jobs is expected, read by ticker
HARD_MAX_SERIES = 60
UA = {"User-Agent": "shwoopnet-research-recorder"}

QUOTE_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "series", "ticker", "event_ticker", "open_time", "close_time", "yes_bid", "yes_ask", "no_bid", "no_ask",
              "yes_bid_size", "yes_ask_size", "last_price", "volume", "open_interest"]
RESULT_COLS = ["t_recv_ms", "series", "ticker", "event_ticker", "close_time", "result", "expiration_value", "last_price", "volume"]
DAILY_COLS = ["date", "series", "open_markets", "recorded", "skipped_by_cap", "skipped_no_close_time"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


def parse_time(s):
    """Kalshi times look like 2026-11-15T14:59:00Z, sometimes with fractional seconds. None for anything unreadable."""
    if not isinstance(s, str):
        return None
    try:
        return epoch_of(re.sub(r"\.\d+Z$", "Z", s))
    except ValueError:
        return None


def within_cap(market, now, cap_days=14):
    """The owner's 14 day cap. A market is recorded only if it closes within cap_days of now AND its open-to-close span is at most cap_days. No readable close time fails closed
    (not recorded). A market with no readable open time is judged on the close alone."""
    if not isinstance(market, dict):
        return False
    close = parse_time(market.get("close_time"))
    if close is None:
        return False
    cap = cap_days * 86400
    if close - now > cap:
        return False
    opened = parse_time(market.get("open_time"))
    return opened is None or close - opened <= cap


def load_series(path=SERIES_FILE):
    """(series list, max_requests_per_run, cap_days) from the committed JSON. More than max_series (or the hard cap of 60), a bad name or a duplicate is an error, so the list cannot grow
    unreviewed or carry a stray character into a URL."""
    with open(path) as f:
        cfg = json.load(f)
    series = cfg.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("series list missing")
    cap = min(int(cfg.get("max_series", HARD_MAX_SERIES)), HARD_MAX_SERIES)
    if len(series) > cap:
        raise ValueError("%d series, the cap is %d" % (len(series), cap))
    if len(set(series)) != len(series) or not all(isinstance(s, str) and re.fullmatch(r"[A-Z0-9]{2,40}", s) for s in series):
        raise ValueError("bad or repeated series name")
    return series, int(cfg.get("max_requests_per_run", 600)), int(cfg.get("cap_days", 14))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the one allowed host is checked on the URL we build, so a redirect could leave it. A 3xx answer is a failed read (its status is returned)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(url):
    """(status, decoded json or None, Date header or ''). Never raises: a failed read is a status, so one bad second cannot end the run. Redirects are refused."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


class Stream:
    """One request stream: one call at a time, at least GAP_S between calls, after a 429 a wait that doubles up to BACKOFF_MAX_S, and a hard budget of calls per run.
    `fetch` is the transport (url -> (status, body, date)); tests pass a fake one. Returns (status, body, date, t_send_ms, t_recv_ms); status -1 means the budget is spent."""

    def __init__(self, budget, fetch=None, clock=time.time, sleep=time.sleep):
        self.budget, self.fetch, self.clock, self.sleep = budget, fetch or http_get, clock, sleep
        self.next_ok, self.backoff, self.n429, self.calls = 0.0, BACKOFF_S, 0, 0

    def get(self, url):
        if self.calls >= self.budget:
            return -1, None, "", 0, 0
        wait = self.next_ok - self.clock()
        if wait > 0:
            self.sleep(wait)
        self.calls += 1
        t_send = int(self.clock() * 1000)
        st, body, date = self.fetch(url)
        t_recv = int(self.clock() * 1000)
        if st == 429:
            self.n429 += 1
            self.next_ok = self.clock() + self.backoff
            self.backoff = min(BACKOFF_MAX_S, self.backoff * 2)
        else:
            self.next_ok = self.clock() + GAP_S
            if st == 200:
                self.backoff = BACKOFF_S
        return st, body, date, t_send, t_recv


def quote_row(t_send, t_recv, date, series, m):
    """One CSV row from a market object, or None when it has no ticker. A missing field is empty, never zero."""
    if not isinstance(m, dict) or not m.get("ticker"):
        return None
    g = lambda k: m.get(k, "") if m.get(k) is not None else ""
    return [t_send, t_recv, date, series, m["ticker"], g("event_ticker"), g("open_time"), g("close_time"), g("yes_bid_dollars"), g("yes_ask_dollars"), g("no_bid_dollars"),
            g("no_ask_dollars"), g("yes_bid_size_fp"), g("yes_ask_size_fp"), g("last_price_dollars"), g("volume_fp"), g("open_interest_fp")]


def result_row(t_recv, series, m):
    if not isinstance(m, dict) or not m.get("ticker") or m.get("result") in (None, ""):
        return None
    g = lambda k: m.get(k, "") if m.get(k) is not None else ""
    return [t_recv, series, m["ticker"], g("event_ticker"), g("close_time"), m["result"], g("expiration_value"), g("last_price_dollars"), g("volume_fp")]


def markets_url(series, status, cursor="", min_close_ts=None):
    u = "%s/markets?series_ticker=%s&status=%s&limit=%d" % (BASE, series, status, PAGE_LIMIT)
    if min_close_ts is not None:
        u += "&min_close_ts=%d" % min_close_ts
    return u + ("&cursor=" + cursor if cursor else "")


def read_series(stream, series, status, min_close_ts=None):
    """Every market of one series in one status, following the cursor until it is empty. Returns (markets, date, t_send, t_recv, ok). A non-object body, a non-list `markets` or a
    failed read is no answer: ok is False and what was read so far is kept. A 429 is waited out by the stream and the same page asked again (at most 4 times)."""
    out, cursor, date, ts, tr, tries = [], "", "", 0, 0, 0
    for _ in range(MAX_PAGES):
        st, body, d, s, r = stream.get(markets_url(series, status, cursor, min_close_ts))
        if st == 429 and tries < 4:
            tries += 1
            continue
        if st != 200 or not isinstance(body, dict) or not isinstance(body.get("markets"), list):
            return out, date, ts, tr, False
        out += [m for m in body["markets"] if isinstance(m, dict)]
        date, ts, tr = d, ts or s, r
        cursor = body.get("cursor")
        if not isinstance(cursor, str) or not cursor:
            return out, date, ts, tr, True
    return out, date, ts, tr, False


def poll_quotes(stream, series_list, now, cap_days, out_rows, daily):
    """One poll: every open market of every series. Returns the series that could not be read. `daily` (a dict series -> [open, recorded, capped, no_close]) is filled for the daily file."""
    failed = []
    for s in series_list:
        markets, date, ts, tr, ok = read_series(stream, s, "open")
        if not ok:
            failed.append(s)
        d = daily.setdefault(s, [0, 0, 0, 0])
        d[:] = [len(markets), 0, 0, 0]
        for m in markets:
            if within_cap(m, now, cap_days):
                row = quote_row(ts, tr, date, s, m)
                if row:
                    out_rows.append(row)
                    d[1] += 1
            elif parse_time(m.get("close_time")) is None:
                d[3] += 1
            else:
                d[2] += 1
    return failed


def poll_results(stream, series_list, now, out_rows, seen):
    """The hourly result read: markets of each series closed in the last 48 hours that carry a result, once per ticker per run."""
    for s in series_list:
        markets, _d, _s, tr, _ok = read_series(stream, s, "settled", int(now) - SETTLED_LOOKBACK_S)
        for m in markets:
            if m.get("ticker") in seen:
                continue
            row = result_row(tr, s, m)
            if row:
                seen.add(m["ticker"])
                out_rows.append(row)


def daily_rows(date, daily, series_list):
    return [[date, s] + daily.get(s, [0, 0, 0, 0]) for s in series_list]


def write_csv(path, cols, rows):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(cols)
        w.writerows(rows)


def sleep_until(t):
    while time.time() < t:
        time.sleep(min(5.0, max(0.05, t - time.time())))


def run(out_dir, minutes, fetch=None):
    series_list, budget, cap_days = load_series()
    os.makedirs(out_dir, exist_ok=True)
    stream = Stream(budget, fetch)
    start = time.time()
    seen = set()
    daily = {}
    polls = int(minutes * 60 // POLL_EVERY_S) + 1   # a poll at 0, 30, ... minutes: --minutes 35 gives two
    for i in range(polls):
        sleep_until(start + i * POLL_EVERY_S)
        now = time.time()
        if past_end(now):
            break
        rows = []
        failed = poll_quotes(stream, series_list, now, cap_days, rows, daily)
        write_csv(os.path.join(out_dir, "quotes.csv"), QUOTE_COLS, rows)
        if failed:
            print("poll %d: no answer for %s" % (i, ",".join(failed)), flush=True)
        if i == 0:
            res = []
            poll_results(stream, series_list, now, res, seen)
            write_csv(os.path.join(out_dir, "results.csv"), RESULT_COLS, res)
            if time.gmtime(now).tm_hour == 0:
                write_csv(os.path.join(out_dir, "daily.csv"), DAILY_COLS, daily_rows(time.strftime("%Y-%m-%d", time.gmtime(now)), daily, series_list))
        if stream.calls >= budget:
            print("request budget spent", flush=True)
            break
    print("done: %d requests, %d refused (429)" % (stream.calls, stream.n429))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--minutes", type=float, default=35, help="poll every 30 minutes for this long (35 gives polls at 0 and 30)")
    a = ap.parse_args(argv)
    if past_end(time.time()):
        print("past the end date %s: nothing to record" % END_UTC)
        return 0
    run(a.out_dir, a.minutes)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
