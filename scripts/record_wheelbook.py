#!/usr/bin/env python3
"""Recorder WHEELBOOK (Nov 12, 2026, the owner approved: "Yes, build it"; spec: kalshi-scalper/workers/wheelbook/WHEEL_BOOK_RECORDER_SPEC.md on the branch claude/idea-desk-b).
Research data only: nothing here trades. It records the order books of the sports and esports markets the wheel's cards (MAPBREAK, INPLAYJUMP, REMATCH, ESOCTIE) look at, so a
card's decision (taken on minute candles, exactly as registered) can be fill-checked against a real book.

What it keeps, by exact series (fixed in code; phase 1 is 9 series, phase 2 tennis is in the code but OFF):
  - book rows: the best 5 YES and 5 NO bids with sizes, but ONLY when that ticker's top 5 changed since its last stored row (book_fast.csv, book_slow.csv);
  - a poll row for EVERY poll, kept or not (polls.csv: poll id, send and receive time, the server's Date header, tier, tickers asked, tickers answered, HTTP status), so the
    book at any poll is the last stored row at or before it, and the poll log proves a second look happened;
  - results: the raw answer body of a list read of closed and settled markets every 10 minutes per series, gzipped JSON in answers/ with a manifest.json (the kalshi-pull run folder shape:
    manifest.json and NNNN.json.gz), kept AS GIVEN (a void or empty result stays);
  - one-minute candles after each close: the raw answer body of a batched candle read for markets the recorder itself watched close, on the day they close, for that market's recorded window only;
  - the public trade tape of each market once, about 60 seconds after its close (cursor followed to the end, trade ids de-duplicated and NOT stored), as raw answer bodies with the ids removed;
  - a coverage row per ticker (coverage.csv; tape pages, trades, duplicates dropped and summed size beside Kalshi's volume) and an hourly clock check (clock.csv).

Two tiers. SLOW: one read a minute. FAST: one read every 3 seconds. A market's tier is set from the scheduled start S in its ticker (US Eastern), its own open time and whether it is still
open, never from a result (tier_for). Nothing here is tuned on or read back as a result: the files are a FORWARD record, not any card's development or held-out sample.

PUBLIC Kalshi market data only: one host, no key, no signing, no auth header, no account path, no order, no Firestore. GET only. Redirects are refused. Two request streams (the book, and
discovery, results and candles), each with at least 0.5 seconds between calls (1.5 for the second); a 429 waits 2 seconds, doubling up to 30. A hard request budget ends a run.

It stops by itself: nothing is recorded at or after END_UTC (2027-01-31 23:59 UTC) and a run started after it exits at once. Stop it sooner by deleting the workflow."""
import argparse
import calendar
import csv
import gzip
import json
import os
import re
import socket
import struct
import sys
import threading
import time
import urllib.error
import urllib.request

BASE = "https://api.elections.kalshi.com/trade-api/v2"
PHASE1_SERIES = ("KXCS2GAME", "KXCS2MAP", "KXCS2TOTALMAPS", "KXDOTA2GAME", "KXDOTA2MAP", "KXDOTA2TOTALMAPS", "KXESOCCERGAME", "KXLIGAPROMATCH", "KXEBASKETBALLGAME")
PHASE2_SERIES = ("KXITFMATCH", "KXITFWMATCH", "KXATPCHALLENGERMATCH", "KXWTACHALLENGERMATCH")
PHASE2_ENABLED = False   # tennis (phase 2) is in the code and OFF: its markets carry no start clock, so the tier cannot be set from fields known in advance. Turning it on is a reviewed edit.
SERIES = PHASE1_SERIES + (PHASE2_SERIES if PHASE2_ENABLED else ())
NO_POLL_SERIES = ("KXCS2TOTALMAPS", "KXDOTA2TOTALMAPS")   # only the listing is needed: a best-of-three is an event with a 2.5 market and none higher
DEPTH = 5
FAST_EVERY_S = 3.0
SLOW_EVERY_S = 60.0
BATCH_MAX = 90               # tickers in one batched read. Kalshi's documented cap is not confirmed in this repo (the kalshi-pull runner allows 1 to 100); 90 is under it, so a busy hour is two reads
BATCH_FAILS_TO_FALLBACK = 3
FALLBACK_RETRY_S = 300       # after 3 failed batches in a row a tier reads one market at a time, and tries the batched read again after this long
BOOK_GAP_S = 0.5
HOUSE_GAP_S = 1.5
BACKOFF_S = 2.0
BACKOFF_MAX_S = 30.0
DISCOVER_EVERY_S = 300
RESULTS_EVERY_S = 600
RESULTS_LOOKBACK_S = 7200
LIST_MAX_PAGES = 12
CANDLE_DELAY_S = 120         # read a closed market's candles this long after its close
CANDLE_CELL_CAP = 9000       # window minutes x tickers in one batched candle read: Kalshi answers HTTP 400 above 10,000 (the kalshi-pull runner learned this), so stay under
CANDLE_MAX_TICKERS = 90
REQUEST_BUDGET = 14000       # a hard cap on public reads in one run (about 27 a minute over 4.7 hours is about 7,600)
SLOW_BEFORE_START_S = 45 * 60   # CS2 / Dota match contracts and map contracts: slow from S minus 45 minutes
ESOCCER_FAST_BEFORE_S = 10 * 60
SMALL_FAST_BEFORE_S = 2 * 60    # table tennis, e-basketball
END_UTC = "2027-01-31T23:59:00Z"  # nothing is recorded from here on
UA = {"User-Agent": "shwoopnet-research-recorder"}

BOOK_COLS = ["poll_id", "t_send_ms", "t_recv_ms", "server_date_header", "tier", "ticker"] \
    + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
POLL_COLS = ["poll_id", "t_send_ms", "t_recv_ms", "server_date_header", "tier", "tickers_asked", "tickers_answered", "http_status"]
COVER_COLS = ["series", "event_ticker", "ticker", "open_time", "close_time", "first_seen_ms", "seen_late", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "book_rows", "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]
CLOCK_COLS = ["t_local_ms", "offset_ms"]
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}
START_RE = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})")


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


def _nth_sunday(year, month, n):
    first = calendar.weekday(year, month, 1)            # Monday is 0
    day = 1 + (6 - first) % 7 + 7 * (n - 1)
    return day


def eastern_to_epoch(y, mo, d, h, mi):
    """US Eastern wall clock to a UTC epoch. Daylight time runs from the second Sunday of March 02:00 to the first Sunday of November 02:00 local (no zone database needed)."""
    local = calendar.timegm((y, mo, d, h, mi, 0))
    start = calendar.timegm((y, 3, _nth_sunday(y, 3, 2), 2, 0, 0))
    end = calendar.timegm((y, 11, _nth_sunday(y, 11, 1), 2, 0, 0))
    return local + (4 if start <= local < end else 5) * 3600


def start_epoch(ticker):
    """The scheduled start S read from the date and four digit clock at the front of the ticker key (for example KXESOCCERGAME-26NOV100722GIGIMADD is Nov 10, 2026 07:22 Eastern).
    None when the ticker has no readable clock."""
    m = START_RE.search(ticker or "")
    if not m or m.group(2) not in MONTHS:
        return None
    try:
        hh, mm = int(m.group(4)), int(m.group(5))
        if hh > 23 or mm > 59:
            return None
        return eastern_to_epoch(2000 + int(m.group(1)), MONTHS[m.group(2)], int(m.group(3)), hh, mm)
    except (ValueError, OverflowError):
        return None


def parse_t(s):
    try:
        return epoch_of(s)
    except (TypeError, ValueError):
        return None


def tier_for(series, ticker, open_epoch, now, still_open=True):
    """'fast', 'slow' or None for one market at `now`, from fields known in advance (S from the ticker, the market's own open time, whether it is still open). Never from a result.
    A market with no readable clock is recorded SLOW from its open. Sets the whole table of spec section 2."""
    if series in NO_POLL_SERIES or series not in SERIES or not still_open:
        return None
    s = start_epoch(ticker)
    if s is None:
        return "slow" if (open_epoch is None or now >= open_epoch) else None
    if series == "KXESOCCERGAME":
        if open_epoch is not None and now < open_epoch:
            return None
        return "fast" if now >= s - ESOCCER_FAST_BEFORE_S else "slow"
    if series in ("KXLIGAPROMATCH", "KXEBASKETBALLGAME"):
        return "fast" if now >= s - SMALL_FAST_BEFORE_S else None
    if series in ("KXCS2GAME", "KXDOTA2GAME"):
        if now >= s:
            return "fast"
        return "slow" if now >= s - SLOW_BEFORE_START_S else None
    if series in ("KXCS2MAP", "KXDOTA2MAP"):
        return "slow" if now >= s - SLOW_BEFORE_START_S else None
    return "slow"


def candle_start(series, ticker, open_epoch):
    """Where a market's recorded window begins, for its candle read: e-soccer from the open (REMATCH needs the earlier match's minutes), table tennis and e-basketball from S minus 10 minutes,
    CS2 and Dota contracts from S minus 45 minutes, anything with no clock from the open."""
    s = start_epoch(ticker)
    if s is None:
        return open_epoch
    if series == "KXESOCCERGAME":
        return open_epoch if open_epoch is not None else s - ESOCCER_FAST_BEFORE_S
    if series in ("KXLIGAPROMATCH", "KXEBASKETBALLGAME"):
        return s - 10 * 60
    return s - SLOW_BEFORE_START_S


def pack_candle_batches(items, cell_cap=CANDLE_CELL_CAP, max_tickers=CANDLE_MAX_TICKERS):
    """items: [(ticker, start_ts, end_ts)]. Groups them into batched reads, each with window minutes x tickers at or under `cell_cap` and at most `max_tickers` tickers (a single
    market over the cap goes alone). Sorted by start so a group's window stays tight. Returns [(tickers, start_ts, end_ts)]."""
    out, cur = [], []
    lo = hi = 0
    for t, a, b in sorted(items, key=lambda x: (x[1], x[2])):
        if cur:
            nlo, nhi = min(lo, a), max(hi, b)
            if len(cur) + 1 <= max_tickers and ((nhi - nlo) / 60.0) * (len(cur) + 1) <= cell_cap:
                cur.append(t)
                lo, hi = nlo, nhi
                continue
            out.append((cur, lo, hi))
        cur, lo, hi = [t], a, b
    if cur:
        out.append((cur, lo, hi))
    return out


def rate_budget():
    """Public calls a minute from the constants: the average (fast, slow, discovery, results, candles) and the peak."""
    fast = 60.0 / FAST_EVERY_S * 2          # two batched reads a poll at the busiest hour (up to BATCH_MAX x 2 tickers)
    slow = 60.0 / SLOW_EVERY_S * 3
    house = 60.0 / (DISCOVER_EVERY_S / 60.0) / 60.0 * len(SERIES) * 2 + len(SERIES) * 2 * 60.0 / RESULTS_EVERY_S + 2
    return {"streams": 2, "avg_per_min": fast / 2 + slow + house, "peak_per_min": fast + slow + 60.0 / HOUSE_GAP_S}


class Stream:
    """One request stream: one call at a time, at least `gap_s` between calls, a 429 waits BACKOFF_S doubling up to BACKOFF_MAX_S and is never asked again at once. `fetch` is the
    transport (url -> (status, body, date)); tests pass a fake one. Counts every call against a budget."""

    def __init__(self, gap_s, fetch=None, clock=time.time, sleep=time.sleep, budget=None):
        assert gap_s >= 0.5
        self.gap_s, self.fetch, self.clock, self.sleep = gap_s, fetch or http_get, clock, sleep
        self.next_ok = 0.0
        self.backoff = BACKOFF_S
        self.n429 = 0
        self.budget = budget          # a shared one-item list [remaining], or None
        self.calls = 0

    def exhausted(self):
        return self.budget is not None and self.budget[0] <= 0

    def get(self, url):
        assert url.startswith(BASE + "/"), "one host only"
        wait = self.next_ok - self.clock()
        if wait > 0:
            self.sleep(wait)
        if self.budget is not None:
            self.budget[0] -= 1
        self.calls += 1
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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the one allowed host is checked on the URL we build, so a redirect could leave it. A 3xx answer is a failed read (its status is returned)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(url):
    """(status, decoded json or None, Date header or ''). Never raises: a failed read is a status. GET only; redirects are refused."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


def sntp_offset_ms(host="time.cloudflare.com", timeout=3.0):
    """How far this machine's clock is from a network time server, in ms. Blank on any failure (UDP is often blocked)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        t0 = time.time()
        s.sendto(b"\x1b" + 47 * b"\0", (host, 123))
        data, _ = s.recvfrom(48)
        t3 = time.time()
        secs, frac = struct.unpack("!II", data[40:48])
        return round((secs - 2208988800 + frac / 2 ** 32 - (t0 + t3) / 2) * 1000)
    except Exception:
        return ""


def parse_levels(levels):
    """The exchange lists levels from the worst price to the best (the best is LAST). Up to 5 (price, size) pairs, best first, as numbers."""
    out = []
    for lv in reversed(levels or []):
        if isinstance(lv, (list, tuple)) and len(lv) >= 2:
            p, s = num(lv[0]), num(lv[1])
            if p is not None and s is not None:
                out.append((p, s))
    return out[:DEPTH]


def book_levels(ob):
    """(yes levels, no levels) from one book object, or None when it has no book object at all. An EMPTY book is ([], []) (a real state: the book was emptied)."""
    if not isinstance(ob, dict):
        return None
    book = ob.get("orderbook_fp") or ob.get("orderbook") or {}
    if not isinstance(book, dict):
        return None
    return parse_levels(book.get("yes_dollars")), parse_levels(book.get("no_dollars"))


def levels_cells(yes, no):
    pad = lambda lv, k: [lv[i][k] if i < len(lv) else "" for i in range(DEPTH)]
    return pad(yes, 0) + pad(yes, 1) + pad(no, 0) + pad(no, 1)


def book_row(poll_id, t_send, t_recv, date_header, tier, ticker, ob):
    """One CSV row, or None when the answer has no book object for the ticker. A missing level is empty, never zero; an empty book is a row of empty levels."""
    lv = book_levels(ob)
    if lv is None:
        return None
    return [poll_id, t_send, t_recv, date_header, tier, ticker] + levels_cells(*lv)


def batch_rows(poll_id, t_send, t_recv, date_header, tier, asked, body):
    """Rows from one batched answer for the tickers in `asked`, keyed by ticker. A ticker missing from the answer gets NO row; one not asked for is ignored.
    Returns (rows, answered) where answered counts the asked tickers the answer had a book object for."""
    rows = {}
    books = body.get("orderbooks") if isinstance(body, dict) else None
    if not isinstance(books, list):
        return rows, 0
    asked = set(asked)
    for ob in books:
        if isinstance(ob, dict) and ob.get("ticker") in asked:
            row = book_row(poll_id, t_send, t_recv, date_header, tier, ob["ticker"], ob)
            if row:
                rows[ob["ticker"]] = row
    return rows, len(rows)


def batch_url(tickers):
    return "%s/markets/orderbooks?%s" % (BASE, "&".join("tickers=" + t for t in tickers))


class ChangeFilter:
    """Row-on-change: a ticker's book row is stored only when its top 5 (all prices and sizes, both sides) differ from the last row STORED for it. The first look always stores."""

    def __init__(self):
        self.last = {}

    def keep(self, ticker, row):
        sig = tuple(row[6:])
        if self.last.get(ticker) == sig:
            return False
        self.last[ticker] = sig
        return True


class Batching:
    """Whether a tier still uses the batched read. 3 failed batches IN A ROW (anything but 200, or no book object back) switch to one read per market; after FALLBACK_RETRY_S the batched read is
    tried again. A good batch resets the count. A 429 is not a failure of the batched read."""

    def __init__(self):
        self.fails = 0
        self.since = None

    def fallback(self, now):
        if self.since is not None and now - self.since >= FALLBACK_RETRY_S:
            self.since, self.fails = None, 0
        return self.since is not None

    def note(self, ok, now):
        if self.since is not None:
            return True
        self.fails = 0 if ok else self.fails + 1
        if self.fails >= BATCH_FAILS_TO_FALLBACK:
            self.since = now
        return self.since is not None


class Tally:
    """One ticker's counters, the source of its coverage row."""

    def __init__(self, series, ticker, event, open_time, close_time, first_seen_ms, seen_late):
        self.series, self.ticker, self.event, self.open_time, self.close_time = series, ticker, event, open_time, close_time
        self.first_seen_ms, self.seen_late = first_seen_ms, seen_late
        self.polls = self.ok = self.n429 = self.rows = self.fallback = 0
        self.max_gap, self.last = 0, 0
        self.pages = self.trades = self.dupes = 0
        self.sum_count = 0.0
        self.volume, self.result = "", ""
        self.written = False
        self.notes = []

    def poll(self, status, t_recv, got, kept, fallback=False):
        self.polls += 1
        if status == 429:
            self.n429 += 1
        if fallback:
            self.fallback = 1
        if got:
            self.ok += 1
            if self.last:
                self.max_gap = max(self.max_gap, t_recv - self.last)
            self.last = t_recv
        if kept:
            self.rows += 1


def coverage_row(t):
    return [t.series, t.event, t.ticker, t.open_time, t.close_time, t.first_seen_ms, 1 if t.seen_late else 0, t.polls, t.ok, t.n429, t.fallback, t.max_gap, t.rows, t.pages, t.trades, t.dupes, round(t.sum_count, 2), t.volume, t.result, ";".join(t.notes)]


TAPE_COLS = ["ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side"]
TAPE_DELAY_S = 60
TAPE_MAX_PAGES = 300


def tape_page(trades, seen, tally):
    """One page of the tape reduced to the kept fields. A trade id already seen this market (page edges shift, a page is retried) is dropped and counted. The id is NOT kept."""
    kept = []
    for t in (trades or []):
        if not isinstance(t, dict):
            continue
        tid = t.get("trade_id")
        if tid is not None:
            if tid in seen:
                tally.dupes += 1
                continue
            seen.add(tid)
        kept.append({k: t.get(k) for k in TAPE_COLS})
        tally.sum_count += num(t.get("count_fp")) or 0.0
    tally.trades += len(kept)
    return kept


def sweep_tape(stream, ticker, open_epoch, close_epoch, tally, save, max_pages=TAPE_MAX_PAGES):
    """Every public trade of one market, the cursor followed until it is EMPTY (a full 1,000 row page never ends the read). Each page is saved as a raw answer body with the trade ids
    removed. A 429 is waited out by the stream and the same page asked again; three other failures mark the tape incomplete."""
    seen, cursor, fails = set(), "", 0
    lo = int(open_epoch) if open_epoch else int(close_epoch) - 86400
    while True:
        if tally.pages >= max_pages or stream.exhausted():
            tally.notes.append("tape page cap" if tally.pages >= max_pages else "tape out of budget")
            return False
        url = "%s/markets/trades?ticker=%s&min_ts=%d&max_ts=%d&limit=1000%s" % (BASE, ticker, lo, int(close_epoch) + 5, ("&cursor=" + cursor) if cursor else "")
        st, body, _d, _s, t_recv = stream.get(url)
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
        cursor = body.get("cursor") or ""
        save(url, st, {"trades": tape_page(body.get("trades"), seen, tally), "cursor": cursor}, t_recv)
        if not cursor:
            return True


def cycle_boundary(now, cycle_s):
    """The 4 hour boundary this job runs to: the first one ahead, or the one after it if the first is less than 30 minutes away (same rule as R6)."""
    into = now % cycle_s
    first = now - into + cycle_s
    return first + cycle_s if cycle_s - into < 1800 else first


class RawStore:
    """Raw answer bodies, gzipped JSON with Kalshi's own keys, as NNNN.json.gz plus a manifest.json (file, request path, parameters, status, receive time): the shape of a kalshi-pull run folder."""

    def __init__(self, d):
        self.dir = d
        os.makedirs(d, exist_ok=True)
        self.n = 0
        self.entries = []
        self.lock = threading.Lock()

    def save(self, url, status, body, t_recv):
        with self.lock:
            self.n += 1
            name = "%04d.json.gz" % self.n
            path, _, query = url[len(BASE):].partition("?")
            params = {}
            for kv in query.split("&") if query else []:
                k, _, v = kv.partition("=")
                params[k] = v
            if body is not None:
                with gzip.open(os.path.join(self.dir, name), "wt") as f:
                    json.dump(body, f)
            self.entries.append({"file": name if body is not None else None, "path": path, "params": params, "status": status, "t_recv_ms": t_recv})
            self.write_manifest()

    def write_manifest(self):
        tmp = os.path.join(self.dir, "manifest.json.tmp")
        with open(tmp, "w") as f:
            json.dump({"recorder": "wheelbook", "host": "api.elections.kalshi.com", "files": self.entries}, f)
        os.replace(tmp, os.path.join(self.dir, "manifest.json"))


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        self.lock = threading.Lock()
        for name, cols in (("book_fast", BOOK_COLS), ("book_slow", BOOK_COLS), ("polls", POLL_COLS), ("coverage", COVER_COLS), ("clock", CLOCK_COLS)):
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


class State:
    """What the recorder knows about the markets, shared by the two threads."""

    def __init__(self):
        self.lock = threading.Lock()
        self.known = {}      # ticker -> dict(series, event, open, close, tally)
        self.closed = {}     # ticker -> same dict, once it left the open list (kept for the candle read)
        self.last_open = {}  # set of tickers per series seen in the last full discovery

    def watch(self, now):
        """{ticker: tier} for every open market that should be polled at `now`."""
        with self.lock:
            return {t: tier_for(m["series"], t, m["open"], now) for t, m in self.known.items()
                    if (m["close"] is None or now < m["close"] + 60) and tier_for(m["series"], t, m["open"], now)}

    def tally(self, t):
        with self.lock:
            m = self.known.get(t)
            return m["tally"] if m else None


def parse_markets(body):
    """[(ticker, event_ticker, open_epoch, close_epoch)] from one list answer."""
    out = []
    for m in (body.get("markets") if isinstance(body, dict) else None) or []:
        if isinstance(m, dict) and m.get("ticker"):
            out.append((m["ticker"], m.get("event_ticker") or "", parse_t(m.get("open_time")), parse_t(m.get("close_time"))))
    return out


def list_all(stream, series, status, extra=""):
    """Every page of one list read (cursor followed, at most LIST_MAX_PAGES). Returns (markets, ok, raw pages [(url, status, body, t_recv)])."""
    cursor, pages, mk = "", [], []
    for _ in range(LIST_MAX_PAGES):
        url = "%s/markets?series_ticker=%s&status=%s&limit=1000%s%s" % (BASE, series, status, extra, ("&cursor=" + cursor) if cursor else "")
        st, body, _d, _s, t_recv = stream.get(url)
        pages.append((url, st, body, t_recv))
        if st == 429:
            continue
        if st != 200 or not isinstance(body, dict):
            return mk, False, pages
        mk.extend(parse_markets(body))
        cursor = body.get("cursor") or ""
        if not cursor:
            return mk, True, pages
    return mk, False, pages


def discover(stream, state, now_ms, started_ms):
    """One discovery round: the open markets of every series. A market new to us is registered (flagged seen_late if its window already began); one that left the open list, or is past its
    close, moves to `closed` for its candle read."""
    ready = []
    for s in SERIES:
        mk, ok, _p = list_all(stream, s, "open")
        if not ok or stream.exhausted():
            continue
        seen = set()
        with state.lock:
            for t, ev, o, c in mk:
                seen.add(t)
                if t not in state.known and t not in state.closed:
                    st = start_epoch(t)
                    late = o is not None and tier_for(s, t, o, now_ms / 1000.0) == "fast" and tier_for(s, t, o, o + 1) != "fast"   # first seen when it was already in its fast tier
                    state.known[t] = {"series": s, "event": ev, "open": o, "close": c, "tally": Tally(s, t, ev, iso(o) if o else "", iso(c) if c else "", now_ms, late)}
            for t in [t for t, m in state.known.items() if m["series"] == s and t not in seen and (m["close"] is None or now_ms / 1000.0 >= m["close"] - 5)]:
                state.closed[t] = state.known.pop(t)
                ready.append(t)
    return ready


def run_house(stream, state, out, raw, done, stop_at):
    """Discovery every 5 minutes, results every 10, candles after each close, the clock check hourly."""
    next_disc = next_res = next_clock = 0.0
    tape = {}      # ticker -> read after
    queue = {}     # ticker -> (series, start_ts, end_ts, read_after)
    while not done.is_set() and not stream.exhausted():
        now = time.time()
        if now >= next_disc:
            next_disc = now + DISCOVER_EVERY_S
            for t in discover(stream, state, int(now * 1000), int(now * 1000)):
                m = state.closed[t]
                c = m["close"] if m["close"] is not None else now
                a = candle_start(m["series"], t, m["open"])
                queue[t] = (m["series"], int(a if a is not None else c - 3600), int(c) + 60, c + CANDLE_DELAY_S)
                tape[t] = c + TAPE_DELAY_S
        if now >= next_res:
            next_res = now + RESULTS_EVERY_S
            for s in SERIES:
                for status in ("settled", "closed"):
                    if done.is_set() or stream.exhausted():
                        break
                    _mk, _ok, pages = list_all(stream, s, status, "&min_close_ts=%d" % int(now - RESULTS_LOOKBACK_S))
                    for url, st, body, t_recv in pages:
                        raw.save(url, st, body, t_recv)
        for t in [t for t, at in tape.items() if at <= now]:
            if done.is_set() or stream.exhausted():
                break
            m = state.closed[t]
            tl = m["tally"]
            sweep_tape(stream, t, m["open"], m["close"] or now, tl, raw.save)
            st, body, _d, _s, t_recv = stream.get("%s/markets/%s" % (BASE, t))     # volume and result, to set beside the summed tape size
            if st == 200 and isinstance(body, dict) and isinstance(body.get("market"), dict):
                tl.volume, tl.result = body["market"].get("volume_fp", ""), body["market"].get("result", "")
            out.write("coverage", [coverage_row(tl)])
            tl.written = True
            del tape[t]
        due = [(t, v) for t, v in queue.items() if v[3] <= now]
        if due:
            for tickers, a, b in pack_candle_batches([(t, v[1], v[2]) for t, v in due]):
                if done.is_set() or stream.exhausted():
                    break
                url = "%s/markets/candlesticks?market_tickers=%s&start_ts=%d&end_ts=%d&period_interval=1" % (BASE, ",".join(tickers), a, b)
                st, body, _d, _s, t_recv = stream.get(url)
                if st == 429:
                    continue              # asked again on the next round; the stream has waited
                raw.save(url, st, body, t_recv)
                if st == 200:
                    for t in tickers:
                        queue.pop(t, None)
                else:
                    for t in tickers:     # a failed read is tried again 3 minutes later
                        v = queue.get(t)
                        if v:
                            queue[t] = (v[0], v[1], v[2], now + 180)
        if now >= next_clock:
            next_clock = now + 3600
            out.write("clock", [[int(now * 1000), sntp_offset_ms()]])
        out.flush()
        done.wait(1.0)


def poll_chunk(stream, state, out, flt, batching, tier, tickers, poll_ids, now):
    """One batched read of up to BATCH_MAX tickers (or one read per ticker in fallback). Every poll writes its poll row; a book row is written only if the top 5 changed."""
    name = "book_" + tier
    if not batching.fallback(now):
        poll_ids[0] += 1
        pid = "%d-%d" % (poll_ids[1], poll_ids[0])
        st, body, date, t_send, t_recv = stream.get(batch_url(tickers))
        rows, answered = batch_rows(pid, t_send, t_recv, date, tier, tickers, body) if st == 200 else ({}, 0)
        kept = [rows[t] for t in tickers if t in rows and flt.keep(t, rows[t])]
        for t in tickers:
            tl = state.tally(t)
            if tl:
                tl.poll(st, t_recv, t in rows, any(r[5] == t for r in kept))
        out.write("polls", [[pid, t_send, t_recv, date, tier, len(tickers), answered, st]])
        out.write(name, kept)
        if st != 429:
            batching.note(st == 200 and answered == len(tickers), now)
        return
    for t in tickers:
        if stream.exhausted():
            return
        poll_ids[0] += 1
        pid = "%d-%d" % (poll_ids[1], poll_ids[0])
        st, body, date, t_send, t_recv = stream.get("%s/markets/%s/orderbook?depth=%d" % (BASE, t, DEPTH))
        row = book_row(pid, t_send, t_recv, date, tier, t, body) if st == 200 else None
        keep = bool(row) and flt.keep(t, row)
        tl = state.tally(t)
        if tl:
            tl.poll(st, t_recv, row is not None, keep, fallback=True)
        out.write("polls", [[pid, t_send, t_recv, date, tier, 1, 1 if row else 0, st]])
        if keep:
            out.write(name, [row])


def run_book(stream, state, out, done, started):
    flt = ChangeFilter()
    batching = {"fast": Batching(), "slow": Batching()}
    poll_ids = [0, int(started)]
    nxt = {"fast": 0.0, "slow": 0.0}
    every = {"fast": FAST_EVERY_S, "slow": SLOW_EVERY_S}
    while not done.is_set() and not stream.exhausted():
        now = time.time()
        if past_end(now):
            return
        watch = None
        for tier in ("fast", "slow"):
            if now >= nxt[tier]:
                nxt[tier] = now + every[tier]
                watch = watch if watch is not None else state.watch(now)
                tickers = sorted(t for t, v in watch.items() if v == tier)
                for i in range(0, len(tickers), BATCH_MAX):
                    if done.is_set():
                        return
                    poll_chunk(stream, state, out, flt, batching[tier], tier, tickers[i:i + BATCH_MAX], poll_ids, time.time())
        done.wait(0.25)


def run(out_dir, stop_at):
    out = Out(out_dir)
    raw = RawStore(os.path.join(out_dir, "answers"))
    budget = [REQUEST_BUDGET]
    book_stream, house = Stream(BOOK_GAP_S, budget=budget), Stream(HOUSE_GAP_S, budget=budget)
    state, done = State(), threading.Event()
    started = time.time()
    th = [threading.Thread(target=run_book, args=(book_stream, state, out, done, started), daemon=True),
          threading.Thread(target=run_house, args=(house, state, out, raw, done, stop_at), daemon=True)]
    for t in th:
        t.start()
    try:
        while time.time() < stop_at and not past_end(time.time()) and any(t.is_alive() for t in th):
            time.sleep(1.0)
    finally:
        done.set()
        for t in th:
            t.join(timeout=20)
        with state.lock:
            tallies = [m["tally"] for m in list(state.known.values()) + list(state.closed.values())]
        out.write("coverage", [coverage_row(t) for t in tallies if t.polls and not t.written])
        raw.write_manifest()
        out.close()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--cycle-hours", type=float, default=4, help="back to back jobs: record up to the next 4 hour boundary (see cycle_boundary)")
    ap.add_argument("--max-minutes", type=float, default=0, help="for a test: stop after this many minutes")
    a = ap.parse_args(argv)
    now = time.time()
    if past_end(now):
        print("past the end date %s: nothing to record" % END_UTC)
        return 0
    stop_at = now + a.max_minutes * 60 if a.max_minutes else cycle_boundary(now, a.cycle_hours * 3600) + 240
    print("recording to %s" % iso(stop_at), flush=True)
    run(a.out_dir, stop_at)
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
