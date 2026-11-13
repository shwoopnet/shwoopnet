"""Tests of nc15_wheel_replay.py on INVENTED rows only (Desk A, Nov 13 2026). python3 -I nc15_wheel_replay_test.py"""
import os, sys, csv, gzip, tempfile, io, time, calendar
from email.utils import format_datetime
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nc15_wheel_replay as N
COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
COVC = ["close_time", "series", "ticker", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "first_recv_ms", "last_recv_ms", "book_rows", "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]
iso = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BASE = N.SHEET_COMMIT_TS + 86400            # first close 1 day after the sheet
def book(tk, ser, close, t, yes=((0.40, 50), (0.39, 50)), no=((0.55, 5), (0.54, 5)), recv_shift=0.0):
    r = dict(t_send_ms=int(t * 1000) - 100, t_recv_ms=int((t + recv_shift) * 1000), server_date_header=format_datetime(datetime.fromtimestamp(t - 0.5, timezone.utc), usegmt=True), ticker=tk, series=ser, close_time=iso(close))
    for i in range(1, 6):
        yp = yes[i - 1] if i <= len(yes) else (None, None); npr = no[i - 1] if i <= len(no) else (None, None)
        r["yes_bid_px_%d" % i], r["yes_bid_sz_%d" % i] = (yp if yp[0] is not None else ("", "")); r["no_bid_px_%d" % i], r["no_bid_sz_%d" % i] = (npr if npr[0] is not None else ("", ""))
    return r
def write(root, rows, cov):
    d = os.path.join(root, "2026-11-14", "0000"); os.makedirs(d, exist_ok=True)
    for name, cols, data in (("book", COLS, rows), ("coverage", COVC, cov)):
        w = io.StringIO(); cw = csv.DictWriter(w, cols); cw.writeheader()
        for r in data: cw.writerow({c: r.get(c, "") for c in cols})
        with gzip.open(os.path.join(d, name + ".csv.gz"), "wt") as f: f.write(w.getvalue())
    open(os.path.join(root, "MADE_UP_DATA"), "w").write("x")
def run_case(rows, cov, now=None, series=N.ADMITTED, since=N.SHEET_COMMIT_TS):
    with tempfile.TemporaryDirectory() as t:
        write(t, rows, cov); return N.replay(t, series, since, now=now)
def cov(tk, ser, close, result="yes"): return dict(close_time=iso(close), series=ser, ticker=tk, polls=100, ok_polls=100, result=result)
S, TK = "KXCOPPER15M", "KXCOPPER15M-26NOV14A-X"; C = BASE; D = C - 600
# 1 fillable, worse-of-two, fee, cash: YES depth 50/50 vs NO 5/5 -> imb5 = (100-10)/110 = 0.818 > 0.5, buys YES. NO bids 0.55 (ask .45) and 0.54 (ask .46): sizes 5 and 5 -> 10 contracts at <= limit .46
rows = [book(TK, S, C, D - 5), book(TK, S, C, D), book(TK, S, C, D + 5)]
recs, rs = run_case(rows, [cov(TK, S, C, "yes")], now=C + 1000)
assert len(recs) == 1 and recs[0]["status"] == "fillable", recs
r = recs[0]; assert r["side"] == "yes" and abs(r["ask"] - 0.45) < 1e-9 and abs(r["limit"] - 0.46) < 1e-9 and abs(r["price"] - 0.455) < 1e-9, r      # signal poll is D (last at or before D); second poll D+5; walked = (0.45*5+0.46*5)/10
assert r["fee"] == N.fee_up_order(0.455) and abs(r["cash"] - (10 * (1 - 0.455) - r["fee"])) < 1e-9 and r["result"] == "scored" and r["win"] == 1; print("T1 fillable, walked price, fee, cash OK", r["price"], r["fee"], round(r["cash"], 4))
# 2 worse of two: second poll NO bid 0.54 / 0.53 -> walked (0.46*5 + 0.47*5)/10 = 0.465 > 0.455 ; but limit .46 means second offers only 5 <= .46 -> a MISS
rows = [book(TK, S, C, D), book(TK, S, C, D + 5, no=((0.54, 5), (0.53, 5)))]
recs, rs = run_case(rows, [cov(TK, S, C)], now=C + 1000); assert recs[0]["status"] == "miss", recs; print("T2 second poll does not offer 10 at or under the limit: miss OK")
rows = [book(TK, S, C, D), book(TK, S, C, D + 5, no=((0.55, 5), (0.54, 3), (0.53, 2)))]    # second walked: asks .45 x5, .46 x3, .47 x2 -> .4570; at or under limit .46 only 8 -> miss
recs, rs = run_case(rows, [cov(TK, S, C)], now=C + 1000); assert recs[0]["status"] == "miss"
rows = [book(TK, S, C, D, no=((0.55, 6), (0.54, 6))), book(TK, S, C, D + 5, no=((0.55, 4), (0.54, 6), (0.53, 5)))]   # first walks .45x6 .46x4 = .454; second .45x4 .46x6 = .456 (offers 10 at <= .46): fill = the higher .456
recs, rs = run_case(rows, [cov(TK, S, C)], now=C + 1000); assert recs[0]["status"] == "fillable" and abs(recs[0]["price"] - 0.456) < 1e-9, recs; print("T2b worse of the two walked prices OK (0.456)")
# 3 second poll too late -> not fill-checked ; no next poll -> not fill-checked
rows = [book(TK, S, C, D), book(TK, S, C, D + 7)]; recs, rs = run_case(rows, [cov(TK, S, C)], now=C + 1000); assert recs[0]["status"] == "not fill-checked"
rows = [book(TK, S, C, D)]; recs, rs = run_case(rows, [cov(TK, S, C)], now=C + 1000); assert recs[0]["status"] == "not fill-checked"; print("T3 later than 6 s or no next poll: not fill-checked OK")
# 4 not in the cell (|imb5| < .5), ask band, side NO
rows = [book(TK, S, C, D, yes=((0.40, 30),), no=((0.55, 25),)), book(TK, S, C, D + 5)]; recs, rs = run_case(rows, [cov(TK, S, C)]); assert not recs and rs["not in the cell"] == 1
rows = [book(TK, S, C, D, no=((0.05, 5), (0.04, 5))), book(TK, S, C, D + 5)]; recs, rs = run_case(rows, [cov(TK, S, C)]); assert not recs and rs["ask outside 0.10 to 0.90"] == 1          # ask 0.95
rows = [book(TK, S, C, D, yes=((0.40, 5),), no=((0.55, 50), (0.54, 50))), book(TK, S, C, D + 5, yes=((0.40, 5),), no=((0.55, 50), (0.54, 50)))]   # imb5 negative: buys NO, ask = 1 - yes bid = .60
recs, rs = run_case(rows, [cov(TK, S, C, "no")], now=C + 1000); assert recs[0]["side"] == "no" and abs(recs[0]["ask"] - 0.60) < 1e-9 and recs[0]["status"] == "miss"                                      # NO ladder: YES bids 0.40 x5 only: 5 contracts: miss
print("T4 cell, band, NO side OK")
# 5 sheet's commit time: a decision instant before it does not count
recs, rs = run_case([book(TK, S, C, D), book(TK, S, C, D + 5)], [cov(TK, S, C)], since=D + 1); assert not recs and rs["before the sheet's commit time"] == 1; print("T5 decision before the commit time not counted OK")
# 6 results: pending, void after 7 days, loss
rows = [book(TK, S, C, D), book(TK, S, C, D + 5)]
recs, rs = run_case(rows, [cov(TK, S, C, "")], now=C + 3600); assert recs[0]["result"] == "pending"
recs, rs = run_case(rows, [cov(TK, S, C, "")], now=C + 7 * 86400 + 1); assert recs[0]["result"] == "void" and abs(recs[0]["cash"] + recs[0]["fee"]) < 1e-9
recs, rs = run_case(rows, [cov(TK, S, C, "no")], now=C + 3600); assert recs[0]["win"] == 0 and abs(recs[0]["cash"] - (-10 * recs[0]["price"] - recs[0]["fee"])) < 1e-9; print("T6 pending, void (fee only), loss OK")
# 7 a series not admitted (EUR/USD withdrawn) is ignored; offset: shifted receive clock still finds the poll
E = "KXEURUSD15M"; recs, rs = run_case([book("KXEURUSD15M-26NOV14A-X", E, C, D), book("KXEURUSD15M-26NOV14A-X", E, C, D + 5)], [cov("KXEURUSD15M-26NOV14A-X", E, C)]); assert not recs
rows = [book(TK, S, C, D, recv_shift=3.0), book(TK, S, C, D + 5, recv_shift=3.0)]          # t_recv 3 s late and the header says the same: offset = -3, exchange time unchanged
recs, rs = run_case(rows, [cov(TK, S, C)], now=C + 1000); assert recs and recs[0]["status"] == "fillable"; print("T7 withdrawn series ignored; receive clock shift handled by the offset OK")
# 8 (audit items B and C): a final non-yes/no value is void at once; replay() itself refuses a HELDOUT_ folder
recs, rs = run_case([book(TK, S, C, D), book(TK, S, C, D + 5)], [cov(TK, S, C, "void")], now=C + 60); assert recs[0]["result"] == "void" and abs(recs[0]["cash"] + recs[0]["fee"]) < 1e-9
with tempfile.TemporaryDirectory() as t0:
    d = os.path.join(t0, "HELDOUT_X"); os.makedirs(d)
    try: N.replay(d); raise AssertionError("HELDOUT folder was read")
    except SystemExit: pass
print("T8 void at once; replay() refuses HELDOUT_ OK")
print("ALL OK")
