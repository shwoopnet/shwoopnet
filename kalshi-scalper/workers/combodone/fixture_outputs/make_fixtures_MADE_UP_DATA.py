#!/usr/bin/env python3
"""MADE-UP DATA for combodone.py. Writes invented combo-recorder folders (the layout of scripts/record_combo.py:
<day>/<HHMM>/{coverage,quotes,books}.csv.gz) and an invented leg pull (manifest.json with its job, one answer file).
Nothing here came from Kalshi. Usage: make_fixtures_MADE_UP_DATA.py <out dir>

Days: D0 = 2026-11-13 (a few runs), D1..D7 = 2026-11-14..20 (the week), D8 = 2026-11-21 (one run, so D7 is over).
t0 is the receive time of run 6 on D2. The legs, as the invented leg pull reports them:
  LA yes, settled an hour before t0      LB open                      LC no, settled an hour before t0
  LD scalar, settled an hour before t0   LE yes, no settlement time   LF yes, settled exactly 60 s before t0
  LG yes, settled 59 s before t0         LH asked for, not returned   LI, LJ open     M01.. open

  base           the rows listed in ROWS below; 269 completed runs (six days of 40 and one of 29).
  week_29        base plus 25 more one-leg-open combos with an ask on D4: 29 independent combos with an ask.
  week_30        base plus 26: exactly 30, which is not "fewer than 30".
  runs_268       as week_30 with one run fewer: no full week.
  day_23         as week_30 but D5 has 23 completed runs and D1 has 46: 269 in all, one day under 24: no full week.
  day_not_over   as week_30 without the D8 run: the seventh day is not over: no full week.
  stopped_early  as week_30 but one D3 run has stopped_early = 1 (268 completed): no full week.
  second_week    as week_30 with D8..D14 full as well: the earliest week is used, the figures equal week_30's.
  legs_refused   as week_30, the leg pull has a second request that was refused: not decided.
  legs_cursor    as week_30, the leg answer still carries a cursor: not decided.
  legs_other     as week_30, the leg pull's job did not ask for LI: the counter must refuse.
"""
import csv
import gzip
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone

QUOTE_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "event_ticker", "exchange_index", "open_time", "close_time", "yes_bid", "yes_ask", "no_bid", "no_ask",
              "yes_bid_size", "yes_ask_size", "last_price", "volume", "open_interest", "legs", "leg_tickers"]
BOOK_COLS = ["t_recv_ms", "server_date_header", "ticker", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
COVER_COLS = ["t_recv_ms", "listed", "pages", "list_complete", "selected", "quote_rows", "books", "trades_read", "requests", "n429", "stopped_early"]
D0 = datetime(2026, 11, 13, tzinfo=timezone.utc)


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_time(day, k):
    """Receive time of run k (0-based) on day index `day`: 00:11:20, 00:41:20, ..."""
    return (D0 + timedelta(days=day, minutes=11 + 30 * k, seconds=20)).timestamp()


T0 = run_time(2, 5)
FAR = iso(run_time(30, 0))
LEGS = {"LA": ("yes", T0 - 3600), "LB": ("", None), "LC": ("no", T0 - 3600), "LD": ("scalar", T0 - 3600), "LE": ("yes", None),
        "LF": ("yes", T0 - 60), "LG": ("yes", T0 - 59), "LI": ("", None), "LJ": ("", None)}
# (day, run, combo, leg string, leg count, yes ask, ask size, close time, best NO bid in the books file or None, its size)
ROWS = [
    (2, 5, "C01", "LA:yes|LB:yes", 2, "0.5000", "5.00", FAR, "0.5200", "3.00"),
    (2, 5, "C02", "LA:yes|LC:yes|LB:yes", 3, "0.5000", "5.00", FAR, "0.5200", "3.00"),
    (2, 5, "C03", "LA:yes|LD:yes|LB:yes", 3, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C04", "LA:yes|LE:yes", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C05", "LA:yes|LH:yes", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C06", "LA:yes|LB", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C07", "LB:yes|LI:yes", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C08", "LG:yes|LB:yes", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C09", "LF:yes|LI:yes", 2, "0.8700", "1.00", FAR, "0.1200", "4.00"),
    (2, 5, "C10", "LA:yes|LC:no", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C11", "LA:yes|LJ:yes", 2, "0.5000", "5.00", iso(T0), None, None),
    (2, 5, "C12", "", 2, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C13", "LA:yes|LB:yes|...", 9, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C14", "LA:yes|LB:yes|LI:yes", 3, "0.8701", "5.00", FAR, "0.1300", "1.00"),
    (2, 5, "C15", "LC:no|LJ:yes", 2, "0.4000", "0.50", FAR, None, None),
    (2, 5, "C16", "LA:yes|LB:yes", 3, "0.5000", "5.00", FAR, None, None),
    (2, 5, "C17", "LA:yes|LG:yes|LI:yes", 3, "0.3000", "2.00", FAR, None, None),
    (2, 9, "C01", "LA:yes|LB:yes", 2, "0.4500", "5.00", FAR, None, None),
    (3, 2, "C01", "LA:yes|LB:yes", 2, "0.6000", "5.00", FAR, None, None),
    (2, 9, "C14", "LA:yes|LB:yes|LI:yes", 3, "0.8000", "3.00", FAR, None, None),
]


def gz_csv(path, cols, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    w.writerows(rows)
    with gzip.open(path, "wt", newline="") as f:
        f.write(buf.getvalue())


def build(out, name, per_day, extra=0, stopped=(), legs="whole"):
    """per_day: {day index: number of run folders}. stopped: (day, run) folders with stopped_early = 1."""
    rows = list(ROWS) + [(4, 3, "X%02d" % i, "LA:yes|M%02d:yes" % i, 2, "0.5000", "1.00", FAR, None, None) for i in range(1, extra + 1)]
    facts = dict(LEGS)
    facts.update({"M%02d" % i: ("", None) for i in range(1, extra + 1)})
    for day, n in sorted(per_day.items()):
        for k in range(n):
            t = run_time(day, k)
            folder = os.path.join(out, name, "combo", datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), datetime.fromtimestamp(t - 20, timezone.utc).strftime("%H%M"))
            os.makedirs(folder)
            mine = [r for r in rows if (r[0], r[1]) == (day, k)]
            ms = int(t * 1000)
            gz_csv(os.path.join(folder, "quotes.csv.gz"), QUOTE_COLS, [[ms, ms, "MADE-UP", r[2], "EV-" + r[2], 2, "", r[7], "", r[5], "", "", "", r[6], "", "0.00", "0.00", r[4], r[3]] for r in mine])
            gz_csv(os.path.join(folder, "books.csv.gz"), BOOK_COLS, [[ms, "MADE-UP", r[2], r[7]] + [""] * 10 + [r[8]] + [""] * 4 + [r[9]] + [""] * 4 for r in mine if r[8] is not None])
            gz_csv(os.path.join(folder, "coverage.csv.gz"), COVER_COLS, [[ms, 900, 1, 1, 400, len(mine), 40, 15, 57, 0, 1 if (day, k) in stopped else 0]])
    named = sorted({p.split(":")[0] for r in rows if r[3] and not r[3].endswith("|...") for p in r[3].split("|")})
    asked = [t for t in named if not (legs == "other" and t == "LI")]
    run = os.path.join(out, name, "legs")
    os.makedirs(run)
    body = {"markets": [{"ticker": t, "status": "finalized" if facts[t][0] else "active", "result": facts[t][0],
                         "settlement_ts": iso(facts[t][1]) if facts[t][1] is not None else None} for t in asked if t in facts], "cursor": "MADE-UP-MORE" if legs == "cursor" else ""}
    with gzip.open(os.path.join(run, "0001.json.gz"), "wt") as f:
        json.dump(body, f)
    reqs = [{"id": "legs001", "path": "/markets", "params": {"tickers": ",".join(asked), "limit": 1000}}]
    rws = [{"index": 1, "id": "legs001", "page": 1, "status": 200, "file": "0001.json.gz"}]
    if legs == "refused":
        reqs.append({"id": "legs002", "path": "/markets", "params": {"tickers": "LA", "limit": 1000}})
        rws.append({"index": 2, "id": "legs002", "page": 1, "status": 429, "file": None})
    json.dump({"status": "complete", "job": {"job_id": "MADE_UP", "requests": reqs}, "rows": rws}, open(os.path.join(run, "manifest.json"), "w"))


def main():
    out = sys.argv[1]
    week = {0: 3, 1: 40, 2: 40, 3: 40, 4: 40, 5: 40, 6: 40, 7: 29, 8: 1}
    build(out, "base", week)
    build(out, "week_29", week, extra=25)
    build(out, "week_30", week, extra=26)
    build(out, "runs_268", {**week, 7: 28}, extra=26)
    build(out, "day_23", {**week, 1: 46, 5: 23, 7: 40}, extra=26)
    build(out, "day_not_over", {d: n for d, n in week.items() if d != 8}, extra=26)
    build(out, "stopped_early", week, extra=26, stopped=((3, 20),))
    build(out, "second_week", {**week, 8: 48, 9: 48, 10: 48, 11: 48, 12: 48, 13: 48, 14: 48, 15: 1}, extra=26)
    build(out, "legs_refused", week, extra=26, legs="refused")
    build(out, "legs_cursor", week, extra=26, legs="cursor")
    build(out, "legs_other", week, extra=26, legs="other")


if __name__ == "__main__":
    main()
