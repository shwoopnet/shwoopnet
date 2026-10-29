#!/usr/bin/env python3
"""Recorder R6 (Oct 29, 2026, the owner approved the research session's spec RECORDER_SPEC_R6_15MIN_BOOK_2026-10-29.md). Research data only: nothing here trades.

For the five 15 minute series the bot trades (KXGOLD15M, KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M, fixed in code) it records, for the WHOLE window of every market:
  - the order book every 2 seconds: one batched public read for all five markets, the best 5 YES bids and 5 NO bids with sizes, the server's Date header, the send and receive
    time (book.csv). If the batched read fails 3 polls in a row, that window falls back to one public read per market (logged in coverage);
  - about 60 seconds after each close, every public trade of that window, following the cursor until it is empty (a 1,000 row page never ends the read), de-duplicated by trade
    id; the id is used for that and NOT stored (trades.csv);
  - one coverage row per window per series, written even for a window with no good poll, so a missed window is counted, not silent (coverage.csv);
  - an SNTP clock offset once an hour (clock.csv).

It reads PUBLIC endpoints only: no key, no signing, no auth header, no account path, no order. At most 2 request streams (the book, and the tape plus housekeeping), each with
at least 0.5 seconds between calls; a 429 waits 2 seconds, doubling up to 30, and is never asked again at once.

It stops by itself: no window opening at or after END_UTC (2026-11-13 23:59 UTC) is recorded, and a run started after it exits at once. Stop it sooner by deleting the workflow.
It replaces R2 (record_book15.py, Bitcoin, Ethereum and gold only), as the spec says.

Rows are written exactly as the exchange returns them (levels re-ordered best first, prices and sizes as numbers, nothing computed). A missing level is empty, never zero."""
import argparse
import calendar
import csv
import json
import os
import socket
import struct
import sys
import threading
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
SERIES = ("KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M")
WINDOW_S = 15 * 60
BOOK_EVERY_S = 2.0
DEPTH = 5
BATCH_FAILS_TO_FALLBACK = 3
BOOK_GAP_S = 0.5             # the book stream: at least this long between calls
HOUSE_GAP_S = 1.5            # the tape and housekeeping stream. The spec said 1 second; a live sweep on Oct 29, 2026 at 1 page a second drew a 429 about every third page
                             # (from a sandbox whose address may be shared), so it is 1.5: a 75 page sweep takes about 2 minutes, well inside SWEEP_BUDGET_S
BACKOFF_S = 2.0              # a 429 waits this long, doubling each time up to BACKOFF_MAX_S
BACKOFF_MAX_S = 30.0
SWEEP_DELAY_S = 60           # read a window's tape this long after its close
SWEEP_MAX_PAGES = 300        # 300,000 trades for one market in one window: far above the 46,744 measured, a guard against an endless cursor
SWEEP_BUDGET_S = 540         # the last sweep of a job must end within this long after the delay, so the next job is never held up past it
DISCOVER_EVERY_S = 2.0
DISCOVER_FOR_S = 30.0
TAPE_PAGES_PER_WINDOW_EST = 75   # the spec's measured 50 to 75 pages a window over the five markets
END_UTC = "2026-11-13T23:59:00Z"  # 14 days: nothing is recorded from here on
UA = {"User-Agent": "shwoopnet-research-recorder"}

BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] \
    + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
TRADE_COLS = ["ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side"]
COVER_COLS = ["close_time", "series", "ticker", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "first_recv_ms", "last_recv_ms", "book_rows",
              "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]
CLOCK_COLS = ["t_local_ms", "offset_ms"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def past_end(now):
    return now >= END_EPOCH


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def rate_budget():
    """Public calls a minute from the constants: the average (book plus discovery, result and tape spread over a window) and the peak (the sweep minute after a close)."""
    book = 60.0 / BOOK_EVERY_S
    per_window = len(SERIES) + 1 + TAPE_PAGES_PER_WINDOW_EST
    return {"streams": 2, "avg_per_min": book + per_window / (WINDOW_S / 60.0), "peak_per_min": book + 60.0 / HOUSE_GAP_S}


class Stream:
    """One request stream: one call at a time, at least `gap_s` between calls, and after a 429 a wait of BACKOFF_S that doubles up to BACKOFF_MAX_S.
    `fetch` is the transport (url -> (status, body, date)); tests pass a fake one. A 429 is returned to the caller, who never asks again before the wait is over."""

    def __init__(self, gap_s, fetch=None, clock=time.time, sleep=time.sleep):
        assert gap_s >= 0.5
        self.gap_s, self.fetch, self.clock, self.sleep = gap_s, fetch or http_get, clock, sleep
        self.next_ok = 0.0
        self.backoff = BACKOFF_S
        self.n429 = 0

    def get(self, url):
        wait = self.next_ok - self.clock()
        if wait > 0:
            self.sleep(wait)
        t_send = int(self.clock() * 1000)
        st, body, date = self.fetch(url)
        t_recv = int(self.clock() * 1000)
        if st == 429:
            self.n429 += 1
            self.next_ok = self.clock() + self.backoff
            self.backoff = min(BACKOFF_MAX_S, self.backoff * 2)
        else:
            self.next_ok = self.clock() + self.gap_s
            if st == 200:
                self.backoff = BACKOFF_S
        return st, body, date, t_send, t_recv


def http_get(url):
    """(status, decoded json or None, Date header or ''). Never raises: a failed read is a status, so one bad second cannot end the run."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


def sntp_offset_ms(host="time.cloudflare.com", timeout=3.0):
    """How far this machine's clock is from a network time server, in ms (positive: the server is ahead). Blank on any failure (UDP is often blocked). Same as record_quotes.py."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        t0 = time.time()
        s.sendto(b"\x1b" + 47 * b"\0", (host, 123))
        data, _ = s.recvfrom(48)
        t3 = time.time()
        secs, frac = struct.unpack("!II", data[40:48])
        server = secs - 2208988800 + frac / 2 ** 32
        return round((server - (t0 + t3) / 2) * 1000)
    except Exception:
        return ""


def parse_levels(levels):
    """The exchange lists levels from the worst price to the best (the best is LAST). Return up to 5 (price, size) pairs, best first, as numbers."""
    out = []
    for lv in reversed(levels or []):
        if isinstance(lv, (list, tuple)) and len(lv) >= 2:
            p, s = num(lv[0]), num(lv[1])
            if p is not None and s is not None:
                out.append((p, s))
    return out[:DEPTH]


def book_row(t_send, t_recv, date_header, ticker, series, close_time, ob):
    """One CSV row from one market's book object, or None when there is no book. Missing levels are left empty, never zero."""
    if not isinstance(ob, dict):
        return None
    book = ob.get("orderbook_fp") or ob.get("orderbook") or {}
    if not isinstance(book, dict):
        return None
    yes, no = parse_levels(book.get("yes_dollars")), parse_levels(book.get("no_dollars"))
    if not yes and not no:
        return None
    pad = lambda lv, k: [lv[i][k] if i < len(lv) else "" for i in range(DEPTH)]
    return [t_send, t_recv, date_header, ticker, series, close_time] + pad(yes, 0) + pad(yes, 1) + pad(no, 0) + pad(no, 1)


def batch_rows(t_send, t_recv, date_header, markets, body):
    """Rows from one batched answer, keyed by ticker. `markets` maps ticker -> (series, close_time). A ticker missing from the answer gets NO row (never zeros);
    a ticker the answer has but we did not ask for is ignored. Returns (rows, all_present)."""
    rows = {}
    books = body.get("orderbooks") if isinstance(body, dict) else None
    if not isinstance(books, list):
        return rows, False
    for ob in books:
        if not isinstance(ob, dict) or ob.get("ticker") not in markets:
            continue
        t = ob["ticker"]
        series, close_time = markets[t]
        row = book_row(t_send, t_recv, date_header, t, series, close_time, ob)
        if row:
            rows[t] = row
    return rows, all(t in rows for t in markets)


def batch_url(tickers):
    return "%s/markets/orderbooks?%s" % (BASE, "&".join("tickers=" + t for t in tickers))


class Batching:
    """Whether a window still uses the batched read. 3 failed batches IN A ROW (anything but 200, or a ticker missing) switch that window to one read per market
    for the rest of the window; a good batch resets the count. A 429 is not a failure of the batched read (the per-market read would be refused too)."""

    def __init__(self):
        self.fails = 0
        self.fallback = False

    def note(self, ok):
        if self.fallback:
            return True
        self.fails = 0 if ok else self.fails + 1
        if self.fails >= BATCH_FAILS_TO_FALLBACK:
            self.fallback = True
        return self.fallback


class Tally:
    """One market's counters for one window, the source of its coverage row."""

    def __init__(self, series, ticker=""):
        self.series, self.ticker = series, ticker
        self.polls = self.ok = self.n429 = self.book_rows = 0
        self.max_gap = 0
        self.first = self.last = 0
        self.pages = self.trades = self.dupes = 0
        self.sum_count = 0.0
        self.volume, self.result, self.notes = "", "", []

    def poll(self, status, t_recv, wrote):
        self.polls += 1
        if status == 429:
            self.n429 += 1
        if wrote:
            self.ok += 1
            self.book_rows += 1
            if self.last:
                self.max_gap = max(self.max_gap, t_recv - self.last)
            self.first = self.first or t_recv
            self.last = t_recv


def coverage_row(close_time, tally, fallback):
    return [close_time, tally.series, tally.ticker, tally.polls, tally.ok, tally.n429, 1 if fallback else 0, tally.max_gap, tally.first, tally.last, tally.book_rows,
            tally.pages, tally.trades, tally.dupes, round(tally.sum_count, 2), tally.volume, tally.result, ";".join(tally.notes)]


def trade_page_rows(trades, seen, tally):
    """Rows for one page of the tape. A trade id already written this window (page edges shift, a page is retried) is dropped and counted. The id is NOT stored."""
    rows = []
    for t in (trades or []):
        if not isinstance(t, dict):
            continue
        tid = t.get("trade_id")
        if tid is not None:
            if tid in seen:
                tally.dupes += 1
                continue
            seen.add(tid)
        rows.append([t.get("ticker"), t.get("created_time"), t.get("yes_price_dollars"), t.get("count_fp"), t.get("taker_outcome_side")])
        c = num(t.get("count_fp"))
        tally.sum_count += c or 0.0
    tally.trades += len(rows)
    return rows


def sweep_tape(stream, ticker, open_epoch, close_epoch, tally, write, deadline=None, max_pages=SWEEP_MAX_PAGES):
    """Every public trade of one market's window: follow the cursor until it is EMPTY, so a full 1,000 row page never ends the read (the truncation trap this project has hit
    four times). A 429 is waited out by the stream and the same page asked again; any other failure is tried 3 times, then the tape is marked incomplete."""
    seen, cursor, fails = set(), "", 0
    while True:
        if tally.pages >= max_pages:
            tally.notes.append("tape page cap")
            return False
        if deadline is not None and time.time() > deadline:
            tally.notes.append("tape out of time")
            return False
        url = "%s/markets/trades?ticker=%s&min_ts=%d&max_ts=%d&limit=1000%s" % (BASE, ticker, open_epoch, close_epoch + 5, ("&cursor=" + cursor) if cursor else "")
        st, body, _d, _s, _r = stream.get(url)
        if st == 429:
            continue
        if st != 200 or not isinstance(body, dict):
            fails += 1
            if fails >= 3:
                tally.notes.append("tape incomplete (HTTP %s)" % st)
                return False
            continue
        fails = 0
        tally.pages += 1
        write(trade_page_rows(body.get("trades"), seen, tally))
        cursor = body.get("cursor") or ""
        if not cursor:
            return True


def cycle_boundary(now, cycle_s):
    """The 4 hour boundary this job runs to: the first one ahead, or the one after it if the first is less than 30 minutes away. Same rule as record_quotes.py and record_book.py,
    so a job started up to 30 minutes late or early still runs about a full cycle."""
    into = now % cycle_s
    first = now - into + cycle_s
    return first + cycle_s if cycle_s - into < 1800 else first


def owned_closes(now, boundary):
    """The windows this job records: every window closing after `now` up to and including the one closing AT the boundary, and none opening at or after END_UTC.
    The window open at `now` is joined late (its book starts now; its tape is complete because the sweep reads the whole window after the close). The next job starts at the
    window closing at boundary + 15 minutes, so each window belongs to exactly one job."""
    first = int(now - now % WINDOW_S + WINDOW_S)
    return [c for c in range(first, int(boundary) + 1, WINDOW_S) if c - WINDOW_S < END_EPOCH]


def job_stop(boundary):
    """The latest moment the job may still be working: the last window's sweep (boundary + delay) plus its budget."""
    return boundary + SWEEP_DELAY_S + SWEEP_BUDGET_S


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        self.lock = threading.Lock()
        for name, cols in (("book", BOOK_COLS), ("trades", TRADE_COLS), ("coverage", COVER_COLS), ("clock", CLOCK_COLS)):
            f = open(os.path.join(d, name + ".csv"), "a", newline="")
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(cols)
            self.files.append(f)
            self.w[name] = w

    def write(self, name, rows):
        with self.lock:
            self.w[name].writerows(rows)

    def flush(self):
        with self.lock:
            for f in self.files:
                f.flush()

    def close(self):
        self.flush()
        for f in self.files:
            f.close()


class Window:
    def __init__(self, close_epoch):
        self.close = close_epoch
        self.open = close_epoch - WINDOW_S
        self.close_time = iso(close_epoch)
        self.markets = {}                      # ticker -> (series, close_time), filled as discovery finds them
        self.tally = {s: Tally(s) for s in SERIES}
        self.batching = Batching()
        self.lock = threading.Lock()


def discover(stream, win):
    """Find each series' market closing at this window's close. Every series not yet found is asked once a round; rounds repeat every 2 seconds for up to 30 seconds
    (a new market can take a moment to be listed). Gold is closed at weekends and in its daily break: it is then simply not found, and its coverage row says so."""
    end = time.time() + DISCOVER_FOR_S
    missing = list(SERIES)
    while missing and time.time() < end:
        round_start = time.time()
        for s in list(missing):
            st, body, _d, _s, _r = stream.get("%s/markets?series_ticker=%s&status=open" % (BASE, s))
            if st != 200 or not isinstance(body, dict):
                continue
            for m in body.get("markets") or []:
                if isinstance(m, dict) and m.get("close_time") == win.close_time and m.get("ticker"):
                    with win.lock:
                        win.markets[m["ticker"]] = (s, win.close_time)
                        win.tally[s].ticker = m["ticker"]
                    missing.remove(s)
                    break
        if missing:
            time.sleep(max(0.0, DISCOVER_EVERY_S - (time.time() - round_start)))
    for s in missing:
        win.tally[s].notes.append("no open market")


def poll_once(stream, win, out):
    """One poll of every market of the window: one batched read, or one read per market after the fallback."""
    with win.lock:
        markets = dict(win.markets)
    if not markets:
        return
    by_ticker = {t: win.tally[s] for t, (s, _c) in markets.items()}
    if not win.batching.fallback:
        st, body, date, t_send, t_recv = stream.get(batch_url(sorted(markets)))
        rows, all_present = batch_rows(t_send, t_recv, date, markets, body) if st == 200 else ({}, False)
        for t, tally in by_ticker.items():
            tally.poll(st, t_recv, t in rows)
        out.write("book", [rows[t] for t in sorted(rows)])
        if st != 429:
            win.batching.note(st == 200 and all_present)
        return
    for t, (s, close_time) in sorted(markets.items()):
        if time.time() >= win.close:
            return
        st, body, date, t_send, t_recv = stream.get("%s/markets/%s/orderbook?depth=%d" % (BASE, t, DEPTH))
        row = book_row(t_send, t_recv, date, t, s, close_time, body) if st == 200 else None
        by_ticker[t].poll(st, t_recv, row is not None)
        if row:
            out.write("book", [row])


def book_loop(stream, windows, out, done):
    """The book stream. Polls the window that is open now, every BOOK_EVERY_S, until told to stop."""
    while not done.is_set():
        start = time.time()
        for win in list(windows):
            if win.open <= start < win.close:
                poll_once(stream, win, out)
        done.wait(max(0.0, BOOK_EVERY_S - (time.time() - start)))


def finish_window(stream, win, out, deadline):
    """After the close: the tape sweep for every market found, then one read of each market's result and volume, then the coverage rows."""
    with win.lock:
        markets = dict(win.markets)
    for t, (s, _c) in sorted(markets.items()):
        sweep_tape(stream, t, win.open, win.close, win.tally[s], lambda rows: out.write("trades", rows), deadline)
    if markets:
        st, body, _d, _s, _r = stream.get("%s/markets?tickers=%s" % (BASE, ",".join(sorted(markets))))
        if st == 200 and isinstance(body, dict):
            for m in body.get("markets") or []:
                if isinstance(m, dict) and m.get("ticker") in markets:
                    tally = win.tally[markets[m["ticker"]][0]]
                    tally.volume, tally.result = m.get("volume_fp", ""), m.get("result", "")
    out.write("coverage", [coverage_row(win.close_time, win.tally[s], win.batching.fallback) for s in SERIES])
    out.flush()


def sleep_until(t):
    while time.time() < t:
        time.sleep(min(5.0, max(0.05, t - time.time())))


def run(out_dir, closes, stop_at):
    out = Out(out_dir)
    book_stream, house = Stream(BOOK_GAP_S), Stream(HOUSE_GAP_S)
    windows, done = [], threading.Event()
    th = threading.Thread(target=book_loop, args=(book_stream, windows, out, done), daemon=True)
    th.start()
    next_clock = 0.0
    pending = None     # the window whose close has passed and whose tape is still to be read
    try:
        for c in closes:
            win = Window(c)
            sleep_until(win.open)
            if time.time() >= c:
                continue
            if time.time() > win.open + 10:
                for t in win.tally.values():
                    t.notes.append("joined late")
            windows.append(win)            # before discovery, so the book stream starts on each market the moment it is found
            discover(house, win)
            if pending is not None:
                sleep_until(pending.close + SWEEP_DELAY_S)
                finish_window(house, pending, out, pending.close + SWEEP_DELAY_S + SWEEP_BUDGET_S)
                windows.remove(pending)
            pending = win
            if time.time() >= next_clock:
                next_clock = time.time() + 3600
                out.write("clock", [[int(time.time() * 1000), sntp_offset_ms()]])
            out.flush()
        if pending is not None:
            sleep_until(pending.close + SWEEP_DELAY_S)
            finish_window(house, pending, out, min(stop_at, pending.close + SWEEP_DELAY_S + SWEEP_BUDGET_S))
    finally:
        done.set()
        th.join(timeout=15)
        out.close()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--cycle-hours", type=float, default=4, help="back to back jobs: record every window closing up to the 4 hour boundary (see cycle_boundary)")
    ap.add_argument("--max-minutes", type=float, default=0, help="for a test: only the windows closing within this many minutes")
    a = ap.parse_args(argv)
    now = time.time()
    if past_end(now):
        print("past the end date %s: nothing to record" % END_UTC)
        return 0
    boundary = now + a.max_minutes * 60 if a.max_minutes else cycle_boundary(now, a.cycle_hours * 3600)
    closes = owned_closes(now, boundary)
    print("recording %d windows, closes %s to %s" % (len(closes), iso(closes[0]) if closes else "-", iso(closes[-1]) if closes else "-"), flush=True)
    if closes:
        run(a.out_dir, closes, job_stop(closes[-1]))
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
