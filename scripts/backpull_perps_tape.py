#!/usr/bin/env python3
"""One-time back-pull of Kalshi's PUBLIC perps trade tape, one UTC day per file (Nov 17, 2026, the owner's yes via the EA, the Head of R&D's order; research only).
GET https://external-api.kalshi.com/trade-api/v2/margin/trades with NO ticker (every perp), newest first, limit 1000, min_ts and max_ts bracketing one UTC day, following the cursor until it ends.
Public GET only: no key, no signing, no auth header, no account path, no order, no Firestore. One host, redirects refused, a generic User-Agent, at least 1.2 seconds between two requests, a 429 waits 2 s
doubling to 30 and three in a row end the run (finished days are kept). A day is written ONLY when its cursor ended, to OUT/tape/<date>.csv.gz with the same columns as the live recorder's tape.csv
(t_recv_ms, server_date_header, ticker, created_time, price, count, taker_side, is_block_trade; the trade id is used only to drop repeats inside a day and is not written). A day that already exists
in the skip list is not asked again, so the job can be started again and carries on. Exit code 10 means more days remain (the workflow commits and calls it again), 0 means finished or stopped for a reason.
usage: python3 backpull_perps_tape.py OUT_DIR --from YYYY-MM-DD --to YYYY-MM-DD [--skip-list FILE] [--max-days N] [--deadline-s S]"""
import argparse
import csv
import datetime as dt
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2/margin"
UA = {"User-Agent": "shwoopnet-research-recorder"}
END_UTC = "2027-02-26T23:59:00Z"
GAP_S = 1.2
BACKOFF_S, BACKOFF_MAX_S, MAX_429_IN_ROW = 2.0, 30.0, 3
LIMIT = 1000
MAX_PAGES_PER_DAY = 20000                  # a safety ceiling: 20 million trades a day would be 20,000 pages
TAPE_COLS = ["t_recv_ms", "server_date_header", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"]
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def now_ms():
    return int(time.time() * 1000)


def get(path):
    """One public GET. Returns (status, parsed object or None, server date header, t_recv_ms)."""
    url = BASE + path
    assert url.startswith("https://external-api.kalshi.com/"), url
    try:
        with OPENER.open(urllib.request.Request(url, headers=UA), timeout=30) as r:
            body = r.read(); st = r.status; date = r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, "", now_ms()
    except Exception:
        return 0, None, "", now_ms()
    try:
        obj = json.loads(body)
    except ValueError:
        return st, None, date, now_ms()
    return st, (obj if isinstance(obj, dict) else None), date, now_ms()


def num(x):
    try:
        return float(x) if x not in ("", None) else ""
    except (TypeError, ValueError):
        return ""


def day_start(d):
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def pull_day(day, getter, sleep=time.sleep, clock=time.time, deadline=None):
    """Read one finished UTC day. Returns (status, rows, pages): status is "ok" (cursor ended), "stopped" (three 429s, a bad answer, the deadline or the page ceiling), never raises."""
    lo = day_start(day); hi = lo + 86400 - 1
    rows, seen, cursor, pages, streak, wait = [], set(), None, 0, 0, BACKOFF_S
    while pages < MAX_PAGES_PER_DAY:
        if deadline is not None and clock() >= deadline:
            return "stopped", rows, pages
        path = "/trades?limit=%d&min_ts=%d&max_ts=%d" % (LIMIT, lo, hi) + (("&cursor=" + cursor) if cursor else "")
        st, obj, date, t1 = getter(path); pages += 1
        sleep(GAP_S)
        if st == 429:
            streak += 1
            if streak >= MAX_429_IN_ROW:
                return "stopped", rows, pages
            sleep(wait); wait = min(wait * 2, BACKOFF_MAX_S); continue
        streak = 0; wait = BACKOFF_S
        if st != 200 or not obj or not isinstance(obj.get("trades"), list):
            return "stopped", rows, pages
        for x in obj["trades"]:
            if not isinstance(x, dict):
                continue
            tid = x.get("trade_id")
            if tid is not None:
                if tid in seen:
                    continue
                seen.add(tid)
            rows.append([t1, date, x.get("ticker", ""), x.get("created_time", ""), num(x.get("price")), num(x.get("count")), x.get("taker_side", ""), x.get("is_block_trade", "")])
        cursor = obj.get("cursor")
        if not cursor or not isinstance(cursor, str) or not cursor.replace("-", "").replace("_", "").replace("=", "").isalnum():
            return "ok", rows, pages
    return "stopped", rows, pages


def write_day(out_dir, day, rows):
    path = os.path.join(out_dir, "tape", day.isoformat() + ".csv.gz")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with gzip.open(tmp, "wt", newline="") as f:
        w = csv.writer(f); w.writerow(TAPE_COLS); w.writerows(rows)
    os.replace(tmp, path)


def days_between(a, b):
    out = []; d = b
    while d >= a:
        out.append(d); d -= dt.timedelta(days=1)
    return out


def run(out_dir, first, last, skip=(), max_days=5, deadline_s=None, getter=None, sleep=time.sleep, clock=time.time, today=None):
    getter = getter or get
    today = today or dt.datetime.now(dt.timezone.utc).date()
    if today >= dt.date.fromisoformat(END_UTC[:10]) + dt.timedelta(days=1):
        print("past the end date; nothing pulled"); return 0
    if last >= today:
        print("the last date must be a finished UTC day; nothing pulled"); return 1
    todo = [d for d in days_between(first, last) if d.isoformat() not in skip]
    if not todo:
        print("every day in the range is already pulled"); return 0
    deadline = clock() + deadline_s if deadline_s else None
    done = 0
    for d in todo:                                   # newest first, so the days nearest the live recorder are safe first
        if done >= max_days:
            print("chunk of %d days done; more remain" % done); return 10
        st, rows, pages = pull_day(d, getter, sleep, clock, deadline)
        print("%s: %s, %d pages, %d trades" % (d, st, pages, len(rows)))
        if st != "ok":
            print("stopped before the day finished; nothing written for it"); return 0
        write_day(out_dir, d, rows); done += 1
    print("range finished"); return 0


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--from", dest="first", required=True); ap.add_argument("--to", dest="last", required=True)
    ap.add_argument("--skip-list", default=""); ap.add_argument("--max-days", type=int, default=5); ap.add_argument("--deadline-s", type=float, default=0.0)
    a = ap.parse_args(argv)
    if not (DAY_RE.match(a.first) and DAY_RE.match(a.last)):
        print("bad date"); return 1
    first, last = dt.date.fromisoformat(a.first), dt.date.fromisoformat(a.last)
    if first > last or (last - first).days > 120:
        print("bad range"); return 1
    skip = set()
    if a.skip_list and os.path.exists(a.skip_list):
        skip = {m.group(1) for m in (re.search(r"(\d{4}-\d{2}-\d{2})\.csv\.gz", l) for l in open(a.skip_list)) if m}
    return run(a.out, first, last, skip, max(1, a.max_days), a.deadline_s or None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
