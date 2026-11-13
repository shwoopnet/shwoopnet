#!/usr/bin/env python3
"""Combo trade-tape recorder (Nov 13, 2026, the owner: "Yes, nonstop recorder"; Idea Desk C's CROWDLEG and NOTAKER cards, both paper only). Research data only: nothing here trades.

Why it exists: a trial read of Kalshi's public trade tape for one half hour on a Sunday (CROWDLEG_TAPE_TRIAL, Nov 13) filled its 50 page cap, so the whole exchange prints at least 50,000
trades a half hour, about a fifth of them combos. The tape comes newest first and has no combo filter, so a 30 minute poll cannot read it whole. This job reads it every minute instead.

Every CYCLE_S seconds, until the 4 hour boundary: one cycle reads GET /markets/trades?min_ts=&max_ts=&limit=1000 (no ticker, cursor followed, percent-encoded) from the last good cycle's
start (minus OVERLAP_S) to now, at most MAX_PAGES_CYCLE pages, and keeps only combo rows (a ticker of the safe shape COMBO_TICKER_RE), each trade_id once a job. A cycle that ran out of
cursor is complete; one that read MAX_PAGES_CYCLE pages with a cursor left is capped (the oldest trades of its window are lost, and the coverage row says so); one cut by a failed read or
three refusals in a row moves nothing, so the next cycle reads that window again. Then, if the cycle was not cut, the legs of combos seen for the first time this job are looked up with
/markets?tickers= (LEG_BATCH a request, at most LEG_LOOKUPS_CYCLE requests, never past MAX_REQ_CYCLE requests in the cycle); a combo the answer does not return is missing, never guessed.

PUBLIC Kalshi market data only: no key, no signing, no auth header, no account path, no order, no Firestore. One request stream, at least GAP_S seconds between calls, so never more than
10 a minute; a 429 waits 5 seconds doubling up to 60. Redirects are refused. It stops by itself: a run started at or after END_UTC exits at once, and no cycle starts after it.

Rows are written as the exchange returns them (dollar fields as strings), nothing computed."""
import argparse
import calendar
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
END_UTC = "2027-01-31T23:59:00Z"   # nothing is recorded from here on
GAP_S = 6.0                        # at least this long between calls: at most 10 a minute
BACKOFF_S = 5.0
BACKOFF_MAX_S = 60.0
MAX_CONSEC_429 = 3                 # this many refusals in a row end the cycle (not the job)
CYCLE_S = 60                       # one cycle a minute
OVERLAP_S = 15                     # each window reaches back this far past the last good cycle (clock skew); trade_id de-duplicates
MAX_PAGES_CYCLE = 10               # 10,000 trades a minute of headroom, about 6 times the trial's lower bound
MAX_REQ_CYCLE = 10                 # tape pages plus legs look-ups in one cycle
LEG_BATCH = 40                     # combo tickers per /markets?tickers= request (combo tickers are long; 40 keeps the URL under about 3 KB)
LEG_LOOKUPS_CYCLE = 2              # at most 80 new combos' legs a minute; the rest wait in the queue
LEG_QUEUE_MAX = 20000              # a queue longer than this drops the newest and counts them missing
SINCE_DEFAULT_S = 300              # the first cycle reaches back 5 minutes when the previous job's mark is unknown
SINCE_MIN_S = 60
SINCE_MAX_S = 7200                 # never further back than 2 hours (a long gap is a gap, not a bigger read)
PAGE_LIMIT = 1000
COMBO_TICKER_RE = re.compile(r"^KXMVE[A-Z0-9._-]{1,120}$")
LEGS_MAX_CHARS = 600
LEGS_MARKER = "|..."
UA = {"User-Agent": "shwoopnet-research-recorder"}

TRADE_COLS = ["t_recv_ms", "ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side", "trade_id"]
LEG_COLS = ["t_recv_ms", "ticker", "event_ticker", "legs", "leg_tickers"]
COVER_COLS = ["cycle", "min_ts", "max_ts", "pages", "complete", "capped", "n429", "tape_rows", "combo_rows", "dup_dropped", "new_combos", "lookups", "legs_found", "legs_missing",
              "queue_len", "requests", "t_start_ms", "t_end_ms"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the one allowed host is checked on the URL we build. A 3xx answer is a failed read (its status is returned)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(url):
    """(status, decoded json or None). Never raises: a failed read is a status. Redirects are refused."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=UA), timeout=15) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


class Stream:
    """One request stream: one call at a time, GAP_S between calls, after a 429 a wait that doubles up to BACKOFF_MAX_S. `fetch` is the transport (url -> (status, body)); tests pass a
    fake one. Returns (status, body, t_recv_ms). It never stops for good: a cycle decides what to do with refusals."""

    def __init__(self, fetch=None, clock=time.time, sleep=time.sleep):
        self.fetch, self.clock, self.sleep = fetch or http_get, clock, sleep
        self.next_ok, self.backoff, self.calls, self.n429 = 0.0, BACKOFF_S, 0, 0

    def get(self, url):
        wait = self.next_ok - self.clock()
        if wait > 0:
            self.sleep(wait)
        self.calls += 1
        st, body = self.fetch(url)
        t_recv = int(self.clock() * 1000)
        if st == 429:
            self.n429 += 1
            self.next_ok = self.clock() + self.backoff
            self.backoff = min(BACKOFF_MAX_S, self.backoff * 2)
        else:
            self.next_ok = self.clock() + GAP_S
            if st == 200:
                self.backoff = BACKOFF_S
        return st, body, t_recv


def is_combo(t):
    """A combo ticker of a safe shape, end to end (fullmatch: a trailing newline is not safe). It is the only text from an answer that ever goes into a URL we build (the legs look-up)."""
    return isinstance(t, str) and COMBO_TICKER_RE.fullmatch(t) is not None


def tape_url(min_ts, max_ts, cursor=""):
    # the cursor comes from the answer, so it is percent-encoded before it goes into the next URL
    return "%s/markets/trades?min_ts=%d&max_ts=%d&limit=%d%s" % (BASE, min_ts, max_ts, PAGE_LIMIT, ("&cursor=" + urllib.parse.quote(cursor, safe="")) if cursor else "")


def legs_url(tickers):
    return "%s/markets?tickers=%s" % (BASE, ",".join(tickers))


def first_mark(start, since):
    """Where the first cycle's window begins: the previous job's mark (from the workflow), clamped to SINCE_MIN_S..SINCE_MAX_S back; SINCE_DEFAULT_S back when unknown or junk."""
    start = int(start)
    if isinstance(since, int) and not isinstance(since, bool) and 0 < since <= start:
        return start - min(SINCE_MAX_S, max(SINCE_MIN_S, start - since))
    return start - SINCE_DEFAULT_S


def leg_tickers(legs):
    """The legs of a combo as `ticker:side` joined by `|` (the same form as record_combo.py), capped at LEGS_MAX_CHARS and cut at a whole leg with LEGS_MARKER. Not a list: empty."""
    if not isinstance(legs, list):
        return ""
    parts = []
    for lg in legs:
        t, side = (lg, "") if isinstance(lg, str) else ((lg.get("market_ticker") or lg.get("ticker") or "", lg.get("side") or "") if isinstance(lg, dict) else ("", ""))
        if isinstance(t, str) and t:
            parts.append(t + (":" + side if isinstance(side, str) and side else ""))
    full = "|".join(parts)
    if len(full) <= LEGS_MAX_CHARS:
        return full
    out = ""
    for x in parts:
        nxt = (out + "|" if out else "") + x
        if len(nxt) + len(LEGS_MARKER) > LEGS_MAX_CHARS:
            break
        out = nxt
    return out + LEGS_MARKER


def trade_row(t_recv, t):
    return [t_recv, t.get("ticker"), t.get("created_time"), t.get("yes_price_dollars"), t.get("count_fp"), t.get("taker_outcome_side"), t.get("trade_id")]


class Recorder:
    """The state of one job: the mark (start of the next window), the trade ids written, the combos seen and the legs queue. One `cycle` call is one minute's work."""

    def __init__(self, stream, start, since=None):
        self.stream, self.mark, self.n = stream, first_mark(start, since), 0
        self.ids, self.seen, self.queue, self.missing_end = set(), set(), [], 0

    def cycle(self, now):
        """One cycle at `now`. Returns (trade rows, legs rows, coverage row)."""
        self.n += 1
        t0, calls0, n429_0 = int(now * 1000), self.stream.calls, self.stream.n429
        lo, hi = self.mark - OVERLAP_S, int(now)
        rows, cursor, pages, tape_rows, dups, new, complete, capped, consec, cut = [], "", 0, 0, 0, 0, False, False, 0, False
        while True:
            if self.stream.calls - calls0 >= MAX_REQ_CYCLE:
                cut = True
                break
            st, body, r = self.stream.get(tape_url(lo, hi, cursor))
            if st == 429:
                consec += 1
                if consec >= MAX_CONSEC_429:
                    cut = True
                    break
                continue
            consec = 0
            if st != 200 or not isinstance(body, dict) or not isinstance(body.get("trades"), list):
                cut = True
                break
            pages += 1
            tape_rows += len(body["trades"])
            for t in body["trades"]:
                if not isinstance(t, dict) or not is_combo(t.get("ticker")) or not isinstance(t.get("trade_id"), (str, int)) or t.get("trade_id") == "":
                    continue
                if t["trade_id"] in self.ids:
                    dups += 1
                    continue
                self.ids.add(t["trade_id"])
                rows.append(trade_row(r, t))
                if t["ticker"] not in self.seen:
                    self.seen.add(t["ticker"])
                    new += 1
                    if len(self.queue) < LEG_QUEUE_MAX:
                        self.queue.append(t["ticker"])
                    else:
                        self.missing_end += 1
            cursor = body.get("cursor")
            if not isinstance(cursor, str) or not cursor:
                complete = True
                break
            if pages >= MAX_PAGES_CYCLE:
                capped = True
                break
        if (complete or capped) and pages > 0:
            self.mark = hi
        legs, lookups, found, missing = [], 0, 0, 0
        if not cut:
            while self.queue and lookups < LEG_LOOKUPS_CYCLE and self.stream.calls - calls0 < MAX_REQ_CYCLE:
                batch, self.queue = self.queue[:LEG_BATCH], self.queue[LEG_BATCH:]
                st, body, r = self.stream.get(legs_url(batch))
                lookups += 1
                got = set()
                if st == 200 and isinstance(body, dict) and isinstance(body.get("markets"), list):
                    for m in body["markets"]:
                        if isinstance(m, dict) and m.get("ticker") in batch and m["ticker"] not in got:
                            got.add(m["ticker"])
                            lg = m.get("mve_selected_legs")
                            legs.append([r, m["ticker"], m.get("event_ticker") or "", len(lg) if isinstance(lg, list) else "", leg_tickers(lg)])
                found += len(got)
                missing += len(batch) - len(got)
        cov = [self.n, lo, hi, pages, int(complete), int(capped), self.stream.n429 - n429_0, tape_rows, len(rows), dups, new, lookups, found, missing, len(self.queue),
               self.stream.calls - calls0, t0, int(self.stream.clock() * 1000)]
        return rows, legs, cov

    def end(self):
        """At the job end: what is still queued counts as missing (and anything dropped from a full queue)."""
        return self.missing_end + len(self.queue)


def write_csv(path, cols, rows):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(cols)
        w.writerows(rows)


def cycle_boundary(now, cycle_s):
    """The 4 hour boundary this job runs to: the first one ahead, or the one after it if the first is less than 30 minutes away (the same rule as record_nc_book.py)."""
    into = now % cycle_s
    first = now - into + cycle_s
    return first + cycle_s if cycle_s - into < 1800 else first


def run(out_dir, stream, start, stop, since=None, clock=time.time, sleep=time.sleep):
    """Cycles every CYCLE_S seconds from `start` while the next cycle starts before `stop` and before END_UTC. Each cycle's rows are appended as soon as it ends.
    Writes mark.txt (the last good cycle's start) after every cycle, for the next job's --since. Returns the recorder."""
    rec = Recorder(stream, start, since)
    tick = float(start)
    while tick < stop and not past_end(tick):
        wait = tick - clock()
        if wait > 0:
            sleep(wait)
        rows, legs, cov = rec.cycle(max(tick, clock()))
        write_csv(os.path.join(out_dir, "trades.csv"), TRADE_COLS, rows)
        write_csv(os.path.join(out_dir, "legs.csv"), LEG_COLS, legs)
        write_csv(os.path.join(out_dir, "coverage.csv"), COVER_COLS, [cov])
        with open(os.path.join(out_dir, "mark.txt"), "w") as f:   # every cycle, so a job cut off early still tells the next job where its tape ended
            f.write("%d\n" % rec.mark)
        tick += CYCLE_S
        while tick < clock() - CYCLE_S:   # an overrun skips missed ticks instead of bursting; the next window still starts at the mark, so nothing is skipped
            tick += CYCLE_S
    with open(os.path.join(out_dir, "mark.txt"), "w") as f:
        f.write("%d\n" % rec.mark)
    with open(os.path.join(out_dir, "end.txt"), "w") as f:
        f.write("legs_missing_at_end=%d\n" % rec.end())
    return rec


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", nargs="?")
    ap.add_argument("--since", type=int, default=0, help="unix seconds: the previous chunk's or job's mark (from the workflow); 0 means 5 minutes back")
    ap.add_argument("--cycle-hours", type=float, default=4, help="back to back jobs: run to the 4 hour boundary (see cycle_boundary)")
    ap.add_argument("--boundary", action="store_true", help="print this job's 4 hour boundary (unix seconds) and exit: the workflow runs hourly chunks up to it")
    ap.add_argument("--until", type=int, default=0, help="unix seconds: never start a cycle at or after this (the job's boundary)")
    ap.add_argument("--max-minutes", type=float, default=0, help="stop after this many minutes (the workflow's hourly chunk, so each hour is pushed)")
    a = ap.parse_args(argv)
    now = time.time()
    if a.boundary:
        print(int(cycle_boundary(now, a.cycle_hours * 3600)))
        return 0
    if past_end(now):
        print("past the end date %s: nothing to record" % END_UTC)
        return 0
    if not a.out_dir:
        ap.error("out_dir is required")
    os.makedirs(a.out_dir, exist_ok=True)
    stop = now + a.max_minutes * 60 if a.max_minutes else cycle_boundary(now, a.cycle_hours * 3600)
    if a.until > 0:
        stop = min(stop, a.until)
    stream = Stream()
    rec = run(a.out_dir, stream, now, stop, a.since or None)
    print("done: %d cycles, %d requests, %d refused (429), %d legs missing at the end" % (rec.n, stream.calls, stream.n429, rec.end()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
