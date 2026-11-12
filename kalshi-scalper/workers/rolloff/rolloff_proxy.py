#!/usr/bin/env python3
"""ROLLOFF proxy check (Idea Desk B, card 13). Registered Nov 12, 2026, BEFORE the
settled history was opened.

Question: does a simple window average rebuilt from the Wikipedia poll table
reproduce the value Kalshi settled the daily approval market on?

Kill rule (as on the card): the proxy is KILLED if it is not within 0.3 points of
the settled value on 80% of settled days.

No price is read. No order, no key. Inputs are two small CSV files:
  polls.csv    pollster,start,end,approve,disapprove   (dates ISO, field dates)
  settled.csv  date,value                              (one row per settled day)

Usage: python3 rolloff_proxy.py polls.csv settled.csv [approve|disapprove|net]
"""
import csv
import sys
from datetime import date, timedelta

# ---- pinned constants (the registration carries the same values) ----
DAYS_START = date(2026, 9, 1)    # settled days before this are ignored
FIT_END = date(2026, 10, 9)      # fit days: DAYS_START..FIT_END inclusive
CHECK_END = date(2026, 11, 11)   # check days: FIT_END+1..CHECK_END inclusive
TOL = 0.3                        # points
SHARE = 0.80                     # of check days
MIN_CHECK_DAYS = 20              # fewer: NOT_ENOUGH_DATA
MIN_POLLS = 3                    # fewer polls in the window: no proxy, counted as a miss
WINDOWS = (7, 10, 14, 21, 30)    # days, by field end date
DEDUPE = (True, False)           # True: only the latest poll of each pollster
LAGS = (0, 1, 2)                 # days between a poll's field end and its use
MISS = 9.9                       # error booked for a day with no proxy


def read_polls(path):
    out = []
    for r in csv.DictReader(open(path, newline="")):
        try:
            end = date.fromisoformat(r["end"])
            a = float(r["approve"])
            d = float(r["disapprove"])
        except (KeyError, ValueError):
            continue
        out.append({"pollster": r.get("pollster", "").strip().lower(), "end": end,
                    "approve": a, "disapprove": d, "net": a - d})
    return out


def read_settled(path):
    out = {}
    for r in csv.DictReader(open(path, newline="")):
        try:
            out[date.fromisoformat(r["date"])] = float(r["value"])
        except (KeyError, ValueError):
            continue
    return out


def proxy(polls, day, field, window, dedupe, lag):
    last = day - timedelta(days=lag)
    first = last - timedelta(days=window)
    rows = [p for p in polls if first < p["end"] <= last]
    if dedupe:
        latest = {}
        for p in sorted(rows, key=lambda p: p["end"]):
            latest[p["pollster"]] = p
        rows = list(latest.values())
    if len(rows) < MIN_POLLS:
        return None
    return sum(p[field] for p in rows) / len(rows)


def errors(polls, settled, days, field, cand):
    out = []
    for d in days:
        v = proxy(polls, d, field, *cand)
        out.append(None if v is None else v - settled[d])
    return out


def main():
    polls = read_polls(sys.argv[1])
    settled = read_settled(sys.argv[2])
    field = sys.argv[3] if len(sys.argv) > 3 else "approve"
    days = sorted(d for d in settled if DAYS_START <= d <= CHECK_END)
    fit = [d for d in days if d <= FIT_END]
    check = [d for d in days if d > FIT_END]
    print(f"polls {len(polls)} | settled days {len(days)} | fit {len(fit)} | check {len(check)} | field {field}")
    if len(check) < MIN_CHECK_DAYS or not fit:
        print(f"VERDICT: NOT_ENOUGH_DATA (check days {len(check)}, need {MIN_CHECK_DAYS}; fit days {len(fit)})")
        return
    cands = [(w, dd, lg) for w in WINDOWS for dd in DEDUPE for lg in LAGS]  # fixed order breaks ties
    best, best_mae = None, None
    for c in cands:
        e = errors(polls, settled, fit, field, c)
        mae = sum(MISS if x is None else abs(x) for x in e) / len(e)
        if best_mae is None or mae < best_mae - 1e-12:
            best, best_mae = c, mae
    print(f"candidates tried on the fit days: {len(cands)}")
    print(f"chosen on fit days only: window {best[0]} days, latest per pollster {best[1]}, lag {best[2]} | fit mean abs error {best_mae:.3f}")
    e = errors(polls, settled, check, field, best)
    hit = sum(1 for x in e if x is not None and abs(x) <= TOL + 1e-9)
    missing = sum(1 for x in e if x is None)
    have = [x for x in e if x is not None]
    share = hit / len(check)
    print(f"check days {len(check)} | within {TOL}: {hit} ({share:.1%}) | days with no proxy {missing}")
    if have:
        print(f"check mean signed error {sum(have)/len(have):+.3f} | mean abs error {sum(abs(x) for x in have)/len(have):.3f} | worst {max(abs(x) for x in have):.2f}")
    # description only: does the proxy call the direction of the day's change?
    agree = n = 0
    for a, b in zip(check, check[1:]):
        pa, pb = proxy(polls, a, field, *best), proxy(polls, b, field, *best)
        ds = settled[b] - settled[a]
        if pa is None or pb is None or abs(ds) < 0.05:
            continue
        n += 1
        agree += 1 if (pb - pa) * ds > 0 else 0
    print(f"description only: on {n} check days where the settled value moved, the proxy moved the same way on {agree}")
    print("VERDICT: " + ("PROXY SURVIVES" if share >= SHARE else "PROXY KILLED") + f" (bar: within {TOL} on {SHARE:.0%} of check days)")


if __name__ == "__main__":
    main()
