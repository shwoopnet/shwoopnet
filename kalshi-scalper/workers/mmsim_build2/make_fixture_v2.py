#!/usr/bin/env python3
"""Fixture v2 for build 2 under Amendment 4 (MADE-UP data). Usage: make_fixture_v2.py <out dir>"""
import csv, gzip, os, sys
from datetime import datetime, timezone
base = sys.argv[1]
d = os.path.join(base, "book", "2026-11-01", "1400"); os.makedirs(d, exist_ok=True)
def ms(h, m): return int(datetime(2026, 11, 1, h, m, tzinfo=timezone.utc).timestamp() * 1000)
bc = ["poll_ts_local_ms", "server_date_header", "ticker", "strike", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
C1, C2 = "2026-11-01T15:00:00Z", "2026-11-07T15:00:00Z"
def row(h, m, tk, st, ct, ypx, ysz, npx, nsz):
    r = {c: "" for c in bc}; r.update(poll_ts_local_ms=ms(h, m), server_date_header="not used", ticker=tk, strike=st, close_time=ct, yes_bid_px_1=ypx, yes_bid_sz_1=ysz, no_bid_px_1=npx, no_bid_sz_1=nsz); return r
rows = [row(14,10,"K-A",100000,C1,"0.40","5","0.55","3"), row(14,45,"K-A",100000,C1,"0.38","4","0.56","3"), row(14,20,"K-A",100000,C1,"0.40","5","0.54","3"), row(14,30,"K-A",100000,C1,"","","0.55","3"),
        row(14,10,"K-B",101000,C1,"0.60","2","",""), row(14,45,"K-B",101000,C1,"0.58","2","0.41","1"),
        row(14,10,"K-D",103000,C1,"0.30","1","0.65","1"), row(14,45,"K-D",103000,C1,"","","0.66","1"),
        row(14,10,"K-C",102000,C2,"0.50","5","0.45","5")]
with gzip.open(os.path.join(d, "book.csv.gz"), "wt", newline="") as f:
    w = csv.DictWriter(f, fieldnames=bc); w.writeheader(); w.writerows(rows)
tc = ["poll_ts_local_ms", "ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side", "trade_id"]
def tr(t, tk, hm, px, cnt, side): return dict(poll_ts_local_ms=0, ticker=tk, created_time="2026-11-01T%s:00Z" % hm, yes_price_dollars=px, count_fp=cnt, taker_outcome_side=side, trade_id=t)
trs = [tr("t1","K-A","14:15","0.40","6.00","no"), tr("t2","K-A","14:30","0.45","2.00","yes"), tr("t3","K-B","14:30","0.59","1.00","no"), tr("t4","K-D","14:20","0.29","1.00","no"), tr("t2","K-A","14:30","0.45","5.00","yes")]
with gzip.open(os.path.join(d, "trades.csv.gz"), "wt", newline="") as f:
    w = csv.DictWriter(f, fieldnames=tc); w.writeheader(); w.writerows(trs)
