#!/usr/bin/env python3
"""MMSIM1 build 2, aligned to AMENDMENT 4 (rnd-queue MMSIM1_AMENDMENT_4.md, sha256 ba3cb90b022faea4). An independent Rule Q and Rule P simulator written from the
TEXT of MMSIM1_PROTOCOL.md, Amendment 3 and Amendment 4 only, by Idea Desk B; mmsim1.py, Desk A's port and mm_probe_prio2.py were NOT read.
DEVELOPMENT events only: there is NO held-out mode. It refuses any folder dated after 2026-11-08 and drops every row of an event closing at or after
PINNED_CUTOFF at load (counted, never simulated). Usage: python3 -I mmsim_build2.py <data_dir>. Standard library only."""
import csv, glob, gzip, math, os, sys
from collections import defaultdict
from datetime import datetime, timezone

PINNED_CUTOFF = "2026-11-07T15:00:00Z"
LAST_FOLDER = "2026-11-08"
POST_MS, FLAT_MS = 50 * 60 * 1000, 15 * 60 * 1000
EPS = 1e-9

def num(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None

def iso_epoch(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

def trade_epoch(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()

def load(data):
    """item 1: rows of one (close_time, ticker) merged from all files, sorted by poll_ts_local_ms (stable: file order breaks ties).
    item 5: trades per ticker in first-seen order, a later row with the same trade_id replaces the earlier one in place, then sorted (stable) by created_time string."""
    book, dropped = defaultdict(list), set()
    tdict, n_noid = {}, 0
    for f in sorted(glob.glob(os.path.join(data, "book", "*", "*"))):
        if f.split(os.sep)[-2] > LAST_FOLDER:
            continue                                           # refused: never opened
        bp = os.path.join(f, "book.csv.gz")
        if os.path.exists(bp):
            for r in csv.DictReader(gzip.open(bp, "rt")):
                if r["close_time"] >= PINNED_CUTOFF:
                    dropped.add(r["close_time"]); continue     # held-out event: counted, not kept
                book[(r["close_time"], r["ticker"])].append((float(r["poll_ts_local_ms"]), num(r["yes_bid_px_1"]), num(r["yes_bid_sz_1"]), num(r["no_bid_px_1"]), num(r["no_bid_sz_1"])))
        tp = os.path.join(f, "trades.csv.gz")
        if os.path.exists(tp):
            for r in csv.DictReader(gzip.open(tp, "rt")):
                tid = r["trade_id"] or ("noid", n_noid := n_noid + 1)
                tdict[tid] = (r["ticker"], r["created_time"], num(r["yes_price_dollars"]), num(r["count_fp"]) or 0.0, r["taker_outcome_side"])
    trades = defaultdict(list)
    for tk, ct, px, cnt, side in tdict.values():
        trades[tk].append((ct, trade_epoch(ct), px, cnt, side))
    for v in trades.values():
        v.sort(key=lambda x: x[0])
    for v in book.values():
        v.sort(key=lambda x: x[0])
    return book, trades, dropped

def ceil_cent(x):
    return math.ceil(round(round(x, 6) * 100, 9)) / 100.0

def mfee(p, bound, rounded):
    f = 0.0175 * p * (1 - p) if bound else 0.0
    return ceil_cent(f) if rounded else f

def tfee(s, rounded):
    f = 0.07 * s * (1 - s)
    return ceil_cent(f) if (rounded and f > 0) else f

def simulate(polls, tr, T, rule, cnt):
    post_ms, flat_ms = T * 1000 - POST_MS, T * 1000 - FLAT_MS
    first = next((r for r in polls if post_ms <= r[0] <= flat_ms), None)   # item 3 as corrected (20:10Z): the first row in [T-50, T-15], both ends inclusive
    if first is None or not (first[1] and first[1] > 0 and first[2] is not None and first[3] and first[3] > 0 and first[4] is not None):
        return None, {}, {}                                     # item 3: both sides above 0 with a readable size, else never posted
    orders = {"yes": (first[1], first[2]), "no": (first[3], first[4])}
    pt = first[0] / 1000.0
    legs = {}
    for side, (price, queue) in orders.items():
        want = price if side == "yes" else 1 - price
        fills, c = [], 0.0
        for ct, te, tp_, tc, ts in tr:
            if not (pt - EPS <= te <= flat_ms / 1000.0 + EPS):
                continue                                        # item 4: post <= t <= T - 15 min
            if (ts == "no" and side == "yes" or ts == "yes" and side == "no") and abs(tp_ - want) < EPS:
                c += tc
                if c >= queue + 1 - EPS:
                    fills.append((te, "queue", tc)); break
        if rule == "P":
            for ct, te, tp_, tc, ts in tr:
                if not (pt - EPS <= te <= flat_ms / 1000.0 + EPS):
                    continue
                thru = (ts == "no" and tp_ < price - EPS) if side == "yes" else (ts == "yes" and tp_ > (1 - price) + EPS)
                if thru:
                    fills.append((te, "through", tc)); break
            for r in polls:
                if not (first[0] < r[0] < flat_ms):             # item 4: the book condition is strict
                    continue
                px = r[1] if side == "yes" else r[3]
                if px is None:
                    cnt["blank"] += 1
                elif px == 0:
                    cnt["zero"] += 1
                if px is None or px < price - EPS:
                    fills.append((r[0] / 1000.0, "book", None)); break
        if fills:
            legs[side] = (price, min(fills, key=lambda x: x[0]))
    sale = {}
    if len(legs) == 1:
        side = next(iter(legs))
        last = [r for r in polls if r[0] <= flat_ms]            # item 6: the LAST row at or before T - 15 min
        px = (last[-1][1] if side == "yes" else last[-1][3]) if last else None
        if not px:                                              # item 7: blank or zero sells at 0, fee 0
            cnt["salenobid"] += 1; px = 0.0
        sale[side] = px
    return orders, legs, sale

def pnl(legs, sale, bound, rounded):
    if len(legs) == 2:
        return 1.0 - legs["yes"][0] - legs["no"][0] - mfee(legs["yes"][0], bound, rounded) - mfee(legs["no"][0], bound, rounded)
    if len(legs) == 1:
        side = next(iter(legs)); p = legs[side][0]; s = sale[side]
        return s - p - mfee(p, bound, rounded) - (tfee(s, rounded) if s > 0 else 0.0)
    return 0.0

def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    return "n/a" if not v else ("99.0" if neg == 0 else "%.2f (full %r)" % (pos / neg, pos / neg))

def main():
    book, trades, dropped = load(sys.argv[1])
    events = defaultdict(list)
    for (ct, tk) in book:
        events[ct].append(tk)
    print("development events %d | held-out events dropped at load (counted, never simulated) %d | strikes in the books %d [development only, no held-out mode]" % (len(events), len(dropped), len(book)))
    late = sum(1 for (ct, tk), pl in book.items() if next((r for r in pl if r[0] >= iso_epoch(ct) * 1000 - POST_MS), None) is not None and next((r for r in pl if r[0] >= iso_epoch(ct) * 1000 - POST_MS), None)[0] > iso_epoch(ct) * 1000 - FLAT_MS)
    print("strikes whose first row at or after T-50 is later than T-15 (not posted under item 3 as corrected): %d" % late)
    for rule in ("Q", "P"):
        cnt = defaultdict(int)
        sims = {ct: [simulate(book[(ct, tk)], trades.get(tk, []), iso_epoch(ct), rule, cnt) for tk in sorted(tks)] for ct, tks in events.items()}
        posted = [(o, l, s) for v in sims.values() for o, l, s in v if o]
        quotable = [ct for ct, v in sims.items() if any(o for o, _, _ in v)]
        fills = sum(len(l) for _, l, _ in posted)
        yes_f = sum(1 for _, l, _ in posted if "yes" in l); no_f = sum(1 for _, l, _ in posted if "no" in l)
        tf = [f for _, l, _ in posted for _, f in l.values() if f[1] != "book"]
        frac = sum(1 for f in tf if abs(f[2] - round(f[2])) > EPS)
        print("== Rule %s: quotable events %d | strikes with an order %d | orders %d | fills %d (yes %d, no %d; trade fills %d, fractional filling trades %d, book fills %d) | pairs %d | singles %d" % (
            rule, len(quotable), len(posted), 2 * len(posted), fills, yes_f, no_f, len(tf), frac, fills - len(tf), sum(1 for _, l, _ in posted if len(l) == 2), sum(1 for _, l, _ in posted if len(l) == 1)))
        print("   item 7: sales with a blank or zero bid (sold at 0) %d | item 8 (Rule P book condition, cells examined until each order's first qualifying row): blank %d, zero %d" % (cnt["salenobid"], cnt["blank"], cnt["zero"]))
        for rounded in (False, True):
            for bound in (False, True):
                ev = {ct: sum(pnl(l, s, bound, rounded) for o, l, s in v if o) for ct, v in sims.items() if ct in quotable}
                v = [ev[c] for c in sorted(ev)]
                days = defaultdict(float)
                for c, x in ev.items():
                    days[c[:10]] += x
                print("  1 contract, %s, maker %s: net %+.6f (full %r) | mean per event %+.6f | PF %s | days %d, positive days %d" % (
                    "fee rounded per order" if rounded else "fee unrounded (verdict figures)", "0.0175 x p x (1 - p)" if bound else "0", sum(v), sum(v), (sum(v) / len(v)) if v else 0.0, pf(v), len(days), sum(1 for d in days.values() if d > 0)))
    print("10 contract report: not produced (G10, information only)")

if __name__ == "__main__":
    main()
