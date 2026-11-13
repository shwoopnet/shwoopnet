#!/usr/bin/env python3
"""ROUNDCOUNT: a zero-try count of quotes only (Idea Desk C, Nov 13, 2026). [research]

Asked by the Head of R&D (19:25Z): on R6 and NC15 books OUTSIDE every registered held-out window, measure
(a) resting size and quote presence at round prices (10c, 25c, 50c, 75c, 90c) against neighbouring cents, and
(b) weekend against weekday staleness (time between book changes).

Reads book.csv files only (quote levels). Never reads trades, coverage (it has results) or any result field.

GUARD (from HELDOUT_REGISTRY.md on rnd-queue, Table 2 and the dated corrections, read Nov 13):
- R6 (quote-data, book15r6/): the earliest held-out date on its five series is 2026-11-03 (KXBTC15M
  2026-11-03T16:00Z; gold 11-03; XRP 11-04; Ethereum and Dogecoin 11-06), and NEWH9, NEWH12, NEWH13 hold
  closes before 2026-10-30. Allowed: rows with t_recv_ms in [2026-10-30T00:00Z, 2026-11-03T00:00Z) AND a
  market close_time in the same span. Folders dated outside 2026-10-30..2026-11-02 are never opened.
- NC15 (nc-data, nc15/): every series but KXAUDUSD15M has a held-out from 2026-11-03 to 11-05, before NC15
  began (Nov 11). Allowed: KXAUDUSD15M rows only, closes before 2026-11-19 (its earliest held-out date).
  Other series' rows are skipped by ticker before any field is parsed (counted, never inspected).
Usage: python3 -I roundcount.py <dir of book.csv.gz files laid out as r6/<date>/<run>/book.csv.gz and nc15/<date>/<run>/book.csv.gz>
"""
import csv, gzip, io, os, sys, json
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def ms(s): return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000)
R6_LO, R6_HI = ms("2026-10-30T00:00:00Z"), ms("2026-11-03T00:00:00Z")
R6_DATES = {"2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02"}
NC_SERIES, NC_HI = "KXAUDUSD15M", ms("2026-11-19T00:00:00Z")
ROUND = (10, 25, 50, 75, 90)
CT = ZoneInfo("America/Chicago")

def cents(p): return int(round(float(p) * 100))

def main(root):
    size = {k: defaultdict(float) for k in ("r6", "nc15")}   # resting contracts at each cent (YES-bid and NO-bid levels)
    pres = {k: defaultdict(int) for k in ("r6", "nc15")}     # level-observations at each cent
    best = {k: defaultdict(int) for k in ("r6", "nc15")}     # best YES bid at each cent
    skipped = defaultdict(int)
    last = {}                                                # ticker -> (book tuple, t of last change)
    gaps = {"weekday": [], "weekend": []}
    for src in ("r6", "nc15"):
        base = os.path.join(root, src)
        if not os.path.isdir(base): continue
        for date in sorted(os.listdir(base)):
            if src == "r6" and date not in R6_DATES:
                skipped["r6_folder_outside_window"] += 1; continue
            for run in sorted(os.listdir(os.path.join(base, date))):
                f = os.path.join(base, date, run, "book.csv.gz")
                if not os.path.exists(f): continue
                with gzip.open(f, "rt") as fh:
                    rd = csv.reader(fh); hdr = next(rd); ix = {h: i for i, h in enumerate(hdr)}
                    for row in rd:
                        if src == "nc15" and row[ix["series"]] != NC_SERIES:
                            skipped["nc15_other_series_row"] += 1; continue
                        t = int(row[ix["t_recv_ms"]]); close = ms(row[ix["close_time"]])
                        if src == "r6" and not (R6_LO <= t < R6_HI and R6_LO <= close < R6_HI):
                            skipped["r6_row_outside_window"] += 1; continue
                        if src == "nc15" and not (close < NC_HI):
                            skipped["nc15_row_outside_window"] += 1; continue
                        levels = []
                        for side in ("yes", "no"):
                            for j in range(1, 6):
                                p, q = row[ix["%s_bid_px_%d" % (side, j)]], row[ix["%s_bid_sz_%d" % (side, j)]]
                                if p and q:
                                    c = cents(p); size[src][c] += float(q); pres[src][c] += 1; levels.append((side, c, q))
                        yb = row[ix["yes_bid_px_1"]]
                        if yb: best[src][cents(yb)] += 1
                        if src == "r6":
                            tk = row[ix["ticker"]]; book = tuple(levels)
                            if tk in last:
                                pb, pt = last[tk]
                                if book != pb:
                                    d = datetime.fromtimestamp(t / 1000, timezone.utc).astimezone(CT)
                                    gaps["weekend" if d.weekday() >= 5 else "weekday"].append(t - pt)
                                    last[tk] = (book, t)
                            else:
                                last[tk] = (book, t)
    def ratio(d, c):
        nb = [d.get(c + k, 0) for k in (-2, -1, 1, 2)]
        m = sum(nb) / 4
        return None if m == 0 else round(d.get(c, 0) / m, 3)
    out = {"skipped_unopened": dict(skipped)}
    for src in ("r6", "nc15"):
        out[src] = {"round_size_ratio_vs_neighbours": {c: ratio(size[src], c) for c in ROUND},
                    "round_presence_ratio_vs_neighbours": {c: ratio(pres[src], c) for c in ROUND},
                    "best_bid_at_round_ratio_vs_neighbours": {c: ratio(best[src], c) for c in ROUND},
                    "size_all_cents_median": None}
        vals = sorted(v for c, v in size[src].items() if 5 <= c <= 95 and c not in ROUND)
        out[src]["size_all_cents_median"] = vals[len(vals) // 2] if vals else None
        out[src]["level_observations"] = sum(pres[src].values())
    def q(xs, p): xs = sorted(xs); return None if not xs else xs[int(p * (len(xs) - 1))]
    out["staleness_ms_between_book_changes_r6"] = {k: {"n": len(v), "median": q(v, .5), "p90": q(v, .9)} for k, v in gaps.items()}
    print(json.dumps(out, indent=1, sort_keys=True))

if __name__ == "__main__":
    main(sys.argv[1])
