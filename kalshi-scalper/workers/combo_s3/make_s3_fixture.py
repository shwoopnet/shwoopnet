#!/usr/bin/env python3
"""MADE-UP combo-data trees for the S3 scorer hand cases (not Kalshi data). make_tree(root, kind) with kind in T120, K, K0, B."""
import csv, gzip, os
from datetime import datetime, timedelta, timezone
HDR = ["t_recv_ms", "ticker", "event_ticker", "close_time", "yes_bid", "yes_ask", "no_ask", "yes_bid_size", "volume", "legs", "leg_tickers"]
def make_tree(root, kind):
    base = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc); res = {}
    for s in range(12):
        t = base + timedelta(hours=2 * s); rows = []
        for j in range(10):
            i = s * 10 + j + 1; tk = "KXMVE-C%03d" % i
            close = "2026-11-14T10:00:00Z" if i <= 40 else "2026-11-16T10:00:00Z"
            rows.append([int(t.timestamp() * 1000), tk, "E%03d" % i, close, 0.19, 0.22, 0.79, 5, 3, 3, ""])
        d, hm = t.strftime("%Y-%m-%d"), t.strftime("%H%M"); p = os.path.join(root, "combo", d, hm); os.makedirs(p, exist_ok=True)
        with gzip.open(os.path.join(p, "quotes.csv.gz"), "wt", newline="") as f:
            w = csv.writer(f); w.writerow(HDR); w.writerows(rows)
    unres = set() if kind in ("K0", "B") else {10, 20, 30, 40} | set(range(42, 73, 2))
    rank = 0
    for i in range(1, 121):
        if i in unres: continue
        rank += 1
        if kind in ("K", "K0"): lose = rank <= 30
        elif kind == "B": lose = rank % 9 == 0
        else: lose = rank % 9 == 0 and rank <= 90
        res["KXMVE-C%03d" % i] = "yes" if lose else "no"
    p = os.path.join(root, "combo", "2026-11-17", "0010"); os.makedirs(p, exist_ok=True)
    with gzip.open(os.path.join(p, "results.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f); w.writerow(["ticker", "result"]); w.writerows(sorted(res.items()))
