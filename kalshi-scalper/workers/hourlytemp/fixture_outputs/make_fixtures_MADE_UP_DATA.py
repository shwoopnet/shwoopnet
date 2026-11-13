#!/usr/bin/env python3
"""MADE-UP DATA. Writes invented list and candle answers for hourlytemp.py, in the shape a pull run has
(manifest.json with rows of id, status, file; numbered .json.gz files). Nothing here came from Kalshi.
Every price is a whole number of cents. Usage: make_fixtures_MADE_UP_DATA.py <out dir>

  closed         every city and look has a spread of 8c: one-way cost near the money 6c, above the line.
  not_closed     as closed, but Miami at 10 minutes has a spread of 2c: one-way cost 3c.
  boundary_4c    as closed, but New York at 30 minutes has a spread of 4c: the median one-way cost is EXACTLY 4c,
                 which is "4c or less", so not closed. Plain float arithmetic gives 0.04000000000000002 here.
  just_above_4c  as closed, but New York at 30 minutes has a spread of 5c: median 4.5c, closed.
  carry_matters  as closed, but Los Angeles goes to a spread of 2c from 15 minutes before the hour and has NO candle
                 in the last 12 minutes: the carried quote says not closed, the exact quote cannot say.
  odd_cases      Chicago is listed but has no candle at all (never quoted); in every New York event the two middle strikes sit at 55c and 45c (a tie
                 for nearest 50c: the lower strike is rank 0) and the top strike shows an empty book (0.00 and 1.00)
                 at the 10 minute look with a good quote one minute earlier (no quote: the search stops there).
  pull_not_whole as closed, but the candle run has a second request that was refused (429): not decided.
  other_job      as closed, but the candle run's job asked for one ticker fewer than the sample: the reader must refuse.
  no_job         as closed, but the candle run's manifest carries no job: the reader must refuse.
  missing_field  one listed New York market has no strike: no job written.
  odd_life       one listed Miami market opened 90 minutes before its close: no job written.
  mixed_types    one listed Chicago market is a "between" range, the rest thresholds: no job written.
  list_cut       as closed, but the New York settled list ends on a page that still carries a cursor: no job written.
  outside        one market closing on Nov 12: the builder must refuse.
  over_cap       15 strikes a city-hour for 168 hours: two hours do not fit one request, so 168 requests, over the cap
                 of 110, no job written. Lists only.
"""
import gzip
import json
import os
import sys
from datetime import datetime, timezone

SERIES = ("KXTEMPCHIHS", "KXTEMPLAXHS", "KXTEMPMIAH", "KXTEMPNYCHS")
MIDS = (90, 75, 50, 25, 10, 3)                       # cents, by rising strike
HOURS = (datetime(2026, 11, 6, 15, tzinfo=timezone.utc), datetime(2026, 11, 9, 3, tzinfo=timezone.utc))


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def market(series, close, k, strike):
    ev = "%s-%s" % (series, close.strftime("%y%b%d%H").upper())
    return {"ticker": "%s-T%s" % (ev, strike), "event_ticker": ev, "floor_strike": strike, "strike_type": "greater",
            "open_time": iso(datetime.fromtimestamp(close.timestamp() - 3600, timezone.utc)), "close_time": iso(close),
            "rules_primary": "MADE-UP rules text for %s: the invented station reading at the top of the hour." % series,
            "rules_secondary": "", "result": "MADE-UP, never read", "yes_bid_size_fp": "0.00", "yes_ask_size_fp": "0.00"}


def write_run(folder, answers, refused=(), job=None):
    os.makedirs(folder, exist_ok=True)
    rows = []
    for n, (rid, body) in enumerate(answers, 1):
        name = "%04d.json.gz" % n
        with gzip.open(os.path.join(folder, name), "wt") as f:
            json.dump(body, f)
        rows.append({"index": n, "id": rid, "page": 1, "status": 200, "file": name})
    rows += [{"index": len(rows) + 1 + i, "id": rid, "page": 1, "status": 429, "file": None} for i, rid in enumerate(refused)]
    man = {"status": "complete", "rows": rows}
    if job is not None:
        man["job"] = {"job_id": "MADE_UP", "requests": job}
    json.dump(man, open(os.path.join(folder, "manifest.json"), "w"))


def candle(t, bid, ask, vol=0):
    return {"end_period_ts": t, "yes_bid": {"close_dollars": "%.4f" % (bid / 100.0)}, "yes_ask": {"close_dollars": "%.4f" % (ask / 100.0)}, "volume_fp": "%.2f" % vol}


def build(out, name, spread, cities=SERIES, mids=None, gap=None, empty=None, hours=HOURS, per_hour=None, candles=True, cursor_on=None, refused=(), spoil=None, job="whole"):
    """spread(series, minutes_left) -> cents. gap(series) -> minutes before the hour from which no candle exists.
    empty(series, k, minutes_left) -> True for an empty book. mids(series) -> cents by strike."""
    settled, per = [], {}
    for s in cities:
        ms = []
        for close in hours:
            row = (mids(s) if mids else MIDS) if per_hour is None else tuple(range(per_hour))
            for k, mid in enumerate(row):
                m = market(s, close, k, 40 + k)
                if spoil:
                    spoil(m, s, close, k)
                ms.append(m)
                per[m["ticker"]] = (s, k, mid, int(close.timestamp()))
        settled.append(("settled_" + s, {"markets": ms, "cursor": "MADE-UP-MORE" if s == cursor_on else ""}))
    opens = []
    for s in cities:
        far = datetime(2026, 11, 13, 6, tzinfo=timezone.utc)
        a, b = market(s, far, 0, 40), market(s, far, 1, 41)
        a.update(yes_bid_size_fp="10.00", yes_ask_size_fp="30.00")
        b.update(yes_bid_size_fp="50.00", yes_ask_size_fp="70.00")
        opens.append(("open_" + s, {"markets": [a, b], "cursor": ""}))
    write_run(os.path.join(out, name, "lists"), settled + opens + [("series_KXTEMPNYCHS", {"series": {"ticker": "KXTEMPNYCHS"}})])
    if not candles:
        return
    body = []
    for tk, (s, k, mid, close) in sorted(per.items()):
        cs = []
        for left in range(59, -1, -1):                       # candle ending `left` minutes before the hour
            if gap and gap(s) is not None and left < gap(s):
                continue
            t = close - 60 * left
            if empty and empty(s, k, left):
                cs.append(candle(t, 0, 100))
                continue
            w = spread(s, left)
            lo = mid - w // 2
            hi = lo + w
            lo, hi = max(1, lo), min(99, max(hi, 2))
            cs.append(candle(t, lo, hi, 5 if left == 40 else 0))
        body.append({"market_ticker": tk, "candlesticks": cs})
    asked = sorted(per)[1:] if job == "other" else sorted(per)
    reqs = [{"id": rid, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(asked)}} for rid in ("h001",) + tuple(refused)]
    write_run(os.path.join(out, name, "candles"), [("h001", {"markets": body})], refused, None if job == "none" else reqs)


def main():
    out = sys.argv[1]
    wide = lambda s, left: 8
    build(out, "closed", wide)
    build(out, "not_closed", lambda s, left: 2 if s == "KXTEMPMIAH" and left <= 12 else 8)
    build(out, "boundary_4c", lambda s, left: 4 if s == "KXTEMPNYCHS" and 28 <= left <= 32 else 8)
    build(out, "just_above_4c", lambda s, left: 5 if s == "KXTEMPNYCHS" and 28 <= left <= 32 else 8)
    build(out, "carry_matters", lambda s, left: 2 if s == "KXTEMPLAXHS" and left <= 15 else 8, gap=lambda s: 12 if s == "KXTEMPLAXHS" else None)
    build(out, "odd_cases", wide, gap=lambda s: 60 if s == "KXTEMPCHIHS" else None, mids=lambda s: (90, 55, 45, 25, 10, 3) if s == "KXTEMPNYCHS" else MIDS,
          empty=lambda s, k, left: s == "KXTEMPNYCHS" and k == 0 and left == 10)
    build(out, "pull_not_whole", wide, refused=("h002",))
    build(out, "other_job", wide, job="other")
    build(out, "no_job", wide, job="none")
    first = HOURS[0]
    build(out, "missing_field", wide, candles=False, spoil=lambda m, s, c, k: m.pop("floor_strike") if (s, c, k) == ("KXTEMPNYCHS", first, 2) else None)
    build(out, "odd_life", wide, candles=False, spoil=lambda m, s, c, k: m.update(open_time=iso(datetime.fromtimestamp(c.timestamp() - 5400, timezone.utc))) if (s, c, k) == ("KXTEMPMIAH", first, 1) else None)
    build(out, "mixed_types", wide, candles=False, spoil=lambda m, s, c, k: m.update(strike_type="between", cap_strike=99) if (s, c, k) == ("KXTEMPCHIHS", first, 0) else None)
    build(out, "list_cut", wide, candles=False, cursor_on="KXTEMPNYCHS")
    build(out, "outside", wide, hours=(datetime(2026, 11, 12, 3, tzinfo=timezone.utc),), candles=False)
    week = tuple(datetime.fromtimestamp(datetime(2026, 11, 5, 0, tzinfo=timezone.utc).timestamp() + 3600 * h, timezone.utc) for h in range(168))
    build(out, "over_cap", wide, hours=week, per_hour=15, candles=False)


if __name__ == "__main__":
    main()
