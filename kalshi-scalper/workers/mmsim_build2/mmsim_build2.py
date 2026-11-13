#!/usr/bin/env python3
"""MMSIM1 build 2: an independent Rule Q and Rule P simulator written from MMSIM1_PROTOCOL.md (sha256 e800152f) and MMSIM1_AMENDMENT_3.md
(sha256 cb681eae) ONLY, by Idea Desk B. It was written without reading mmsim1.py, Desk A's port, mm_probe_prio2.py or mmsim_rederive.py.
DEVELOPMENT events only: there is NO held-out mode. It refuses any folder dated after 2026-11-08 and drops every row of an event closing at or after
PINNED_CUTOFF at load (counted, never simulated). Text gaps G1 to G14 are in BUILD2_SPEC_AND_GAPS.md; each default is a named option below.
Usage: python3 -I mmsim_build2.py <data_dir>   (data_dir holds book/<date>/<hhmm>/book.csv.gz and trades.csv.gz). Standard library only."""
import csv, glob, gzip, math, os, sys
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

PINNED_CUTOFF = "2026-11-07T15:00:00Z"
LAST_FOLDER = "2026-11-08"
POST_MIN, FLAT_MIN = 50, 15
OPT = {"POST": os.environ.get("B2_POST", "first_only"),        # G3: first_only | first_with_bid
       "FLAT": os.environ.get("B2_FLAT", "first_at_or_after"), # G6: first_at_or_after | last_before
       "NOBID_SALE": 0.0}                                      # G7
EPS = 1e-9

def num(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None

def iso_epoch(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

def trade_epoch(s):
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).timestamp()

def load(data):
    book, trades, dropped = defaultdict(list), defaultdict(list), set()
    folders = sorted(glob.glob(os.path.join(data, "book", "*", "*")))
    for f in folders:
        date = f.split(os.sep)[-2]
        if date > LAST_FOLDER:
            continue                                           # refused: never opened
        bp = os.path.join(f, "book.csv.gz")
        if os.path.exists(bp):
            for r in csv.DictReader(gzip.open(bp, "rt")):
                if r["close_time"] >= PINNED_CUTOFF:
                    dropped.add(r["close_time"]); continue     # held-out event: counted, not kept
                book[(r["close_time"], r["ticker"])].append(
                    (parsedate_to_datetime(r["server_date_header"]).timestamp(), num(r["yes_bid_px_1"]), num(r["yes_bid_sz_1"]), num(r["no_bid_px_1"]), num(r["no_bid_sz_1"])))
        tp = os.path.join(f, "trades.csv.gz")
        if os.path.exists(tp):
            for r in csv.DictReader(gzip.open(tp, "rt")):
                trades[r["ticker"]].append((trade_epoch(r["created_time"]), r["trade_id"], num(r["yes_price_dollars"]), num(r["count_fp"]) or 0.0, r["taker_outcome_side"]))
    seen_tid = set(); clean = defaultdict(list)
    for tk, v in trades.items():
        for t in sorted(v, key=lambda x: (x[0], x[1])):
            if t[1] and t[1] in seen_tid:
                continue
            seen_tid.add(t[1]); clean[tk].append(t)
    for v in book.values():
        v.sort(key=lambda x: x[0])
    return book, clean, dropped

def ceil_cent(x):
    return math.ceil(round(x * 100, 9)) / 100.0

def maker_fee(p, bound, rounded):
    f = 0.0175 * p * (1 - p) if bound else 0.0
    return ceil_cent(f) if (rounded and f > 0) else f

def taker_fee(s, rounded):
    f = 0.07 * s * (1 - s)
    return ceil_cent(f) if (rounded and f > 0) else f

def side_px(row, side):
    return (row[1], row[2]) if side == "yes" else (row[3], row[4])

def simulate_strike(polls, tr, T, rule):
    post_t, flat_t = T - POST_MIN * 60, T - FLAT_MIN * 60
    cand = [r for r in polls if post_t <= r[0] < flat_t]
    orders = {}
    for side in ("yes", "no"):
        for r in cand:
            px, sz = side_px(r, side)
            if px is not None:
                orders[side] = (r[0], px, sz or 0.0); break
            if OPT["POST"] == "first_only":
                break
    legs = {}
    for side, (pt, price, queue) in orders.items():
        want = price if side == "yes" else 1 - price
        fills = []
        cum = 0.0
        for t in tr:
            if t[0] <= pt or t[0] > flat_t:
                continue
            qual = (t[4] == "no" and abs(t[2] - want) < EPS) if side == "yes" else (t[4] == "yes" and abs(t[2] - want) < EPS)
            if qual:
                cum += t[3]
                if cum >= queue + 1 - EPS:
                    fills.append((t[0], "queue", t[3])); break
        if rule == "P":
            for t in tr:
                if t[0] <= pt or t[0] > flat_t:
                    continue
                thru = (t[4] == "no" and t[2] < price - EPS) if side == "yes" else (t[4] == "yes" and t[2] > (1 - price) + EPS)
                if thru:
                    fills.append((t[0], "through", t[3])); break
            for r in polls:
                if r[0] <= pt or r[0] >= flat_t:
                    continue
                px, _ = side_px(r, side)
                if px is None or px < price - EPS:
                    fills.append((r[0], "book", None)); break
        if fills:
            legs[side] = (price, min(fills, key=lambda x: x[0]))
    sale = {}
    if len(legs) == 1:
        side = next(iter(legs))
        after = [r for r in polls if r[0] >= flat_t]
        before = [r for r in polls if r[0] <= flat_t]
        r = (after[0] if after else None) if OPT["FLAT"] == "first_at_or_after" else (before[-1] if before else None)
        s = side_px(r, side)[0] if r else None
        sale[side] = OPT["NOBID_SALE"] if s is None else s
    return orders, legs, sale

def pnl(legs, sale, bound, rounded):
    if len(legs) == 2:
        return 1.0 - legs["yes"][0] - legs["no"][0] - maker_fee(legs["yes"][0], bound, rounded) - maker_fee(legs["no"][0], bound, rounded)
    if len(legs) == 1:
        side = next(iter(legs)); price = legs[side][0]; s = sale[side]
        return s - price - maker_fee(price, bound, rounded) - (taker_fee(s, rounded) if s > 0 else 0.0)
    return 0.0

def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    return "no losses" if neg == 0 and pos > 0 else ("n/a" if neg == 0 else "%.2f" % (pos / neg))

def main():
    book, trades, dropped = load(sys.argv[1])
    events = defaultdict(list)
    for (ct, tk) in book:
        events[ct].append(tk)
    print("development events %d | held-out events dropped at load (counted, never simulated) %d | strikes %d [development only, no held-out mode]" % (len(events), len(dropped), len(book)))
    for rule in ("Q", "P"):
        sims = {}
        for ct, tks in events.items():
            T = iso_epoch(ct)
            sims[ct] = [simulate_strike(book[(ct, tk)], trades.get(tk, []), T, rule) for tk in sorted(tks)]
        quotable = [ct for ct, s in sims.items() if any(o for o, _, _ in s)]
        orders = sum(len(o) for s in sims.values() for o, _, _ in s)
        fills = sum(len(l) for s in sims.values() for _, l, _ in s)
        pairs = sum(1 for s in sims.values() for _, l, _ in s if len(l) == 2)
        singles = sum(1 for s in sims.values() for _, l, _ in s if len(l) == 1)
        posted = sum(1 for s in sims.values() for o, _, _ in s if o)
        tf = [f for s in sims.values() for _, l, _ in s for _, f in l.values() if f[1] != "book"]
        frac = sum(1 for f in tf if abs(f[2] - round(f[2])) > EPS)
        book_fills = fills - len(tf)
        print("== Rule %s: quotable events %d | strikes posted %d | orders %d | fills %d (trade fills %d, fractional filling trades %d, book fills %d) | pairs %d | singles %d" % (rule, len(quotable), posted, orders, fills, len(tf), frac, book_fills, pairs, singles))
        for rounded in (False, True):
            for bound in (False, True):
                ev = {ct: sum(pnl(l, sa, bound, rounded) for _, l, sa in s) for ct, s in sims.items() if ct in quotable}
                v = [ev[c] for c in sorted(ev)]
                days = defaultdict(float)
                for c, x in ev.items():
                    days[c[:10]] += x
                print("  1 contract, fee %s, maker %s: net %+.6f | mean per event %+.6f | PF %s | days %d, positive days %d" % (
                    "rounded to the cent per leg" if rounded else "unrounded", "0.0175 x p x (1 - p)" if bound else "0", sum(v), (sum(v) / len(v)) if v else 0.0, pf(v), len(days), sum(1 for d in days.values() if d > 0)))
    print("10 contract report: NOT implemented (text gap G10)")

if __name__ == "__main__":
    main()
