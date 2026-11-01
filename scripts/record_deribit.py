#!/usr/bin/env python3
"""Deribit implied-probability recorder for the research session's DERIBIT-IMPLIED (Oct 31, 2026, the owner approved; registration in kalshi-scalper/workers/DERIBIT_IMPLIED_REGISTRATION.md).

For each hourly close of the Bitcoin ladder (KXBTCD), once a minute from 60 to 30 minutes before the close, it records (1) Kalshi's open ladder quotes within 5% of the Deribit index, with the
server's Date header, and (2) Deribit's option summary (mark_iv, forward, bid, ask) for the two nearest expiries at or after the close, plus the Deribit index price, with Deribit's own server
timestamp, so clock skew can be measured. Five minutes after each close it also records the settled results of that close from Kalshi's public settled markets.
PUBLIC endpoints only: no key, no signing, no account, no order, no auth header, GET only. After STOP_DATE it records nothing. Rows are written as the exchanges return them (nothing computed)."""
import argparse
import csv
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

KALSHI = "https://external-api.kalshi.com/trade-api/v2"
DERIBIT = "https://www.deribit.com/api/v2"
SERIES = "KXBTCD"
STOP_DATE = datetime.date(2026, 12, 31)   # UTC. After this date the script records nothing (the registration's stop date).
LEAD_START_S = 60 * 60     # first poll this long before each hourly close
LEAD_END_S = 30 * 60       # last poll this long before it
POLL_EVERY_S = 60.0
KALSHI_BAND = 0.05         # Kalshi strikes within 5% of the Deribit index
DERIBIT_BAND = 0.12        # Deribit strikes within 12% of the index (the model interpolates between strikes, so a wider band than the ladder's)
RESULT_DELAY_S = 300
SPACING_S = 1.5            # pause between two requests
UA = {"User-Agent": "shwoopnet-research-recorder"}
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}

KALSHI_COLS = ["poll_ts_local_ms", "server_date_header", "close_time", "ticker", "strike", "yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "open_interest", "volume"]
DERIBIT_COLS = ["poll_ts_local_ms", "deribit_us_out", "close_time", "expiry_rank", "instrument_name", "strike", "kind", "mark_iv", "underlying_price", "underlying_index",
                "bid_price", "ask_price", "mark_price", "open_interest", "creation_timestamp"]
INDEX_COLS = ["poll_ts_local_ms", "deribit_us_out", "close_time", "index_price"]
RESULT_COLS = ["poll_ts_local_ms", "close_time", "ticker", "strike", "result", "expiration_value"]
COVER_COLS = ["close_time", "polls", "kalshi_ok", "deribit_ok", "index_ok", "retries", "first_ms", "last_ms"]

STATS = {"retries": 0}


def today_utc():
    return datetime.datetime.now(datetime.timezone.utc).date()


def past_stop(day=None):
    """True from the day AFTER STOP_DATE: the stop date itself is the last day that records."""
    return (day or today_utc()) > STOP_DATE


def http_get_backoff(url, tries=4, base_wait=2.0):
    """(status, decoded json or None, Date header, retry count). Never raises. A 429, a 503 and Deribit's too-many-requests error 10028 are retried with a growing wait; anything else is returned as it is."""
    status, body, date = 0, None, ""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
                status, body, date = r.status, json.load(r), r.headers.get("Date", "")
        except urllib.error.HTTPError as e:
            status, body, date = e.code, None, ""
        except Exception:
            status, body, date = 0, None, ""
        throttled = status in (429, 503) or (isinstance(body, dict) and isinstance(body.get("error"), dict) and body["error"].get("code") == 10028)
        if not throttled:
            break
        STATS["retries"] += 1
        time.sleep(base_wait * (2 ** attempt))
    return status, body, date, attempt


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def parse_instrument(name):
    """('BTC-13NOV26-83000-P') -> (expiry epoch at 08:00 UTC, strike, 'P'), or None."""
    try:
        cur, d, k, kind = name.split("-")
        day, mon, yr = int(d[:-5]), MONTHS[d[-5:-2]], 2000 + int(d[-2:])
        ts = datetime.datetime(yr, mon, day, 8, 0, tzinfo=datetime.timezone.utc).timestamp()
        return int(ts), float(k), kind
    except Exception:
        return None


def pick_expiries(instrument_rows, close_epoch):
    """The first expiry at or after the close (rank 1) and the next one (rank 2), from (name, expiry_epoch) pairs. Both [] when none."""
    exps = sorted({e for _n, e in instrument_rows if e is not None})
    after = [e for e in exps if e >= close_epoch]
    return after[:2]


def deribit_rows(ts_ms, us_out, close_time, summary, expiries, index_price, band=DERIBIT_BAND):
    """Rows for the options of the two expiries within `band` of the index. Rows are as returned; rank 1 or 2 says which expiry."""
    rows = []
    for o in (summary or []):
        if not isinstance(o, dict):
            continue
        p = parse_instrument(o.get("instrument_name") or "")
        if not p or p[0] not in expiries:
            continue
        if index_price and abs(p[1] / index_price - 1.0) > band:
            continue
        rows.append([ts_ms, us_out, close_time, expiries.index(p[0]) + 1, o.get("instrument_name"), p[1], p[2], o.get("mark_iv"), o.get("underlying_price"),
                     o.get("underlying_index"), o.get("bid_price"), o.get("ask_price"), o.get("mark_price"), o.get("open_interest"), o.get("creation_timestamp")])
    return rows


def kalshi_rows(ts_ms, date_header, close_time, markets, index_price, band=KALSHI_BAND):
    """Rows for the open markets of the closing event whose strike is within `band` of the index. Quotes are kept as returned (strings in dollars)."""
    rows = []
    for m in (markets or []):
        if not isinstance(m, dict) or m.get("close_time") != close_time:
            continue
        k = num(m.get("floor_strike"))
        if k is None or (index_price and abs(k / index_price - 1.0) > band):
            continue
        rows.append([ts_ms, date_header, close_time, m.get("ticker"), k, m.get("yes_bid_dollars"), m.get("yes_ask_dollars"), m.get("no_bid_dollars"), m.get("no_ask_dollars"),
                     m.get("last_price_dollars"), m.get("open_interest_fp"), m.get("volume_fp")])
    return rows


def result_rows(ts_ms, close_time, markets):
    rows = []
    for m in (markets or []):
        if isinstance(m, dict) and m.get("close_time") == close_time and m.get("result"):
            rows.append([ts_ms, close_time, m.get("ticker"), m.get("floor_strike"), m.get("result"), m.get("expiration_value")])
    return rows


def cycle_stop_time(now, cycle_s):
    """Same rule as record_book.py: stop a minute after the first cycle boundary that leaves this job a full cycle, so the next job (which starts early) queues behind it."""
    into = now % cycle_s
    first_boundary = now - into + cycle_s
    if cycle_s - into < 1800:
        return first_boundary + cycle_s + 60
    return first_boundary + 60


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        for name, cols in (("kalshi", KALSHI_COLS), ("deribit", DERIBIT_COLS), ("index", INDEX_COLS), ("results", RESULT_COLS), ("coverage", COVER_COLS)):
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


def kalshi_event_markets(close_epoch, status):
    """One request: the markets of the event closing at close_epoch (open ones, or settled ones). (status, markets, date header)."""
    q = urllib.parse.urlencode({"series_ticker": SERIES, "status": status, "min_close_ts": close_epoch, "max_close_ts": close_epoch, "limit": 1000})
    st, body, date, _a = http_get_backoff("%s/markets?%s" % (KALSHI, q))
    return st, (body.get("markets") if st == 200 and isinstance(body, dict) else []), date


def deribit_call(method, params):
    st, body, _d, _a = http_get_backoff("%s/public/%s?%s" % (DERIBIT, method, urllib.parse.urlencode(params)))
    ok = st == 200 and isinstance(body, dict) and "result" in body
    return ok, (body.get("result") if ok else None), (body.get("usOut") if ok else None)


def record_hour(out, close_epoch, stop_at, pending):
    """Poll once a minute from 60 to 30 minutes before the close. Per minute at peak: 1 Kalshi request, 2 Deribit requests."""
    close_time = iso(close_epoch)
    start, end = close_epoch - LEAD_START_S, close_epoch - LEAD_END_S
    while time.time() < start:
        if time.time() >= stop_at or past_stop():
            return False
        time.sleep(min(5.0, max(0.1, start - time.time())))
    ok_i, res_i, _u = deribit_call("get_instruments", {"currency": "BTC", "kind": "option"})
    pairs = []
    if ok_i and isinstance(res_i, list):
        pairs = [(i.get("instrument_name"), int(i["expiration_timestamp"] / 1000)) for i in res_i if isinstance(i, dict) and i.get("expiration_timestamp")]
    expiries = pick_expiries(pairs, close_epoch)
    polls = k_ok = d_ok = i_ok = 0
    first_ms = last_ms = 0
    r0 = STATS["retries"]
    while time.time() < min(end, stop_at):
        if past_stop():
            break
        minute_start = time.time()
        ts = int(minute_start * 1000)
        polls += 1
        ok_x, idx, us_x = deribit_call("get_index_price", {"index_name": "btc_usd"})
        index_price = num(idx.get("index_price")) if ok_x and isinstance(idx, dict) else None
        if index_price:
            out.write("index", [[ts, us_x, close_time, index_price]])
            i_ok += 1
        time.sleep(SPACING_S)
        st, markets, date = kalshi_event_markets(close_epoch, "open")
        rows = kalshi_rows(ts, date, close_time, markets, index_price) if st == 200 else []
        if rows:
            out.write("kalshi", rows)
            k_ok += 1
        time.sleep(SPACING_S)
        ok_s, summary, us_s = deribit_call("get_book_summary_by_currency", {"currency": "BTC", "kind": "option"})
        if ok_s and not expiries and isinstance(summary, list):
            # get_instruments failed: the expiry is in each name (08:00 UTC on its date), so the window is not lost
            expiries = pick_expiries([(o.get("instrument_name"), (parse_instrument(o.get("instrument_name") or "") or [None])[0]) for o in summary if isinstance(o, dict)], close_epoch)
        if ok_s and expiries and index_price:
            drows = deribit_rows(ts, us_s, close_time, summary, expiries, index_price)
            if drows:
                out.write("deribit", drows)
                d_ok += 1
        first_ms = first_ms or ts
        last_ms = ts
        for c in list(pending):   # the previous close is settled by now: one more Kalshi request, once per close
            if time.time() >= c + RESULT_DELAY_S:
                time.sleep(SPACING_S)
                record_results(out, c)
                pending.remove(c)
        out.flush()
        time.sleep(max(0.0, POLL_EVERY_S - (time.time() - minute_start)))
    out.write("coverage", [[close_time, polls, k_ok, d_ok, i_ok, STATS["retries"] - r0, first_ms, last_ms]])
    out.flush()
    return True


def record_results(out, close_epoch):
    st, markets, _d = kalshi_event_markets(close_epoch, "settled")
    rows = result_rows(int(time.time() * 1000), iso(close_epoch), markets) if st == 200 else []
    out.write("results", rows)
    out.flush()
    return bool(rows)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--cycle-hours", type=float, default=4, help="back to back jobs: stop a minute after the cycle boundary that leaves one full cycle")
    ap.add_argument("--max-minutes", type=float, default=0, help="for a test: stop after this many minutes")
    a = ap.parse_args(argv)
    if past_stop():
        print("past the stop date %s: recording nothing" % STOP_DATE.isoformat())
        return 0
    now = time.time()
    stop_at = now + a.max_minutes * 60 if a.max_minutes else cycle_stop_time(now, a.cycle_hours * 3600)
    out = Out(a.out_dir)
    pending = []
    try:
        close_epoch = int(now - now % 3600 + 3600)
        while close_epoch - LEAD_START_S < stop_at and time.time() < stop_at and not past_stop():
            if not record_hour(out, close_epoch, stop_at, pending):
                break
            pending.append(close_epoch)
            close_epoch += 3600
    finally:
        out.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
