"""Made-up data of EXPECTED_BY_HAND.md; prints MISMATCHES [] when oiver_r6sizes.py agrees with the hand figures."""
import csv, gzip, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oiver_r6sizes as S

COLS = ["ticker", "event_ticker", "close_ts", "oi_180", "oi_360", "yes_bid", "yes_ask", "no_bid", "no_ask", "result"]
BOOK = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + \
       ["yes_bid_sz_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
W = {"A": "2026-10-28T23:45:00Z", "B": "2026-11-02T12:00:00Z", "C": "2026-11-03T08:15:00Z", "D": "2026-11-06T20:30:00Z"}


def tk(k):
    return "KXBTC15M-%s" % k


def rows_csv(path, extra=None):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(COLS)
        for k, c in list(W.items()) + (extra or []):
            w.writerow([tk(k), tk(k), S.iso(c), "590000.0", "500000.0", "0.2", "0.22", "0.78", "0.8", "yes"])


def brow(k, close_iso, secs_before, ybs, nbs):
    t = S.iso(close_iso) * 1000 - secs_before * 1000
    r = {c: "" for c in BOOK}
    r.update({"t_send_ms": t - 50, "t_recv_ms": t, "ticker": tk(k), "series": "KXBTC15M", "close_time": close_iso,
              "yes_bid_px_1": "0.2", "no_bid_px_1": "0.78", "yes_bid_sz_1": ybs, "no_bid_sz_1": nbs})
    return r


def book(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rs = [brow("B", W["B"], s, a, b) for s, a, b in ((195, 11, 12), (188, 21, 22), (181, 31, 32), (180, 41, 42), (179, 51, 52))]
    rs.append(brow("B", "2026-11-02T12:15:00Z", 180 + 900, 99, 99))      # decoy: B's ticker, another close_time, at exactly B's close - 180 s, after
                                                                          # the real row, so it would win the tie if close_time were not matched
    rs += [brow("C", W["C"], 200, 5, 5), brow("C", W["C"], 170, 6, 6), brow("D", W["D"], 185, "", 7)]
    with gzip.open(path, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BOOK, lineterminator="\n"); w.writeheader(); w.writerows(rs)


bad = []
d = tempfile.mkdtemp()
rows_csv(os.path.join(d, "rows.csv"))
bp = os.path.join(d, "book15r6", "2026-11-02", "1200", "book.csv.gz"); book(bp)
out = os.path.join(d, "out.csv")
counts = S.build(os.path.join(d, "rows.csv"), out, [bp])
got = {r["ticker"]: (r["yes_bid_size"], r["yes_ask_size"]) for r in csv.DictReader(open(out))}
if got != {tk("B"): ("41.0", "42.0"), tk("C"): ("", ""), tk("D"): ("", "7.0")}:
    bad.append(("sizes", got))
if counts != {"rows_in": 4, "before_r6": 1, "written": 3, "no_poll": 1, "missing_size": 1}:
    bad.append(("counts", counts))


def refused(fn, what, why):
    try:
        fn()
    except (S.Stop, SystemExit) as e:
        print("refused", what, "->", str(e)[:90])
        if why not in str(e):
            bad.append(("wrong reason", what, str(e)[:90]))
        return
    bad.append(("not refused", what))


late = os.path.join(d, "book15r6", "2026-11-09", "0000", "book.csv.gz"); book(late)
refused(lambda: S.build(os.path.join(d, "rows.csv"), out, [bp, late]), "R6 folder dated 2026-11-09", "not opened")
rows_csv(os.path.join(d, "rows2.csv"), [("E", "2026-11-09T00:00:00Z")])
refused(lambda: S.build(os.path.join(d, "rows2.csv"), out, [bp]), "input row closing 2026-11-09", "on or after 2026-11-09")
hd = os.path.join(d, "HELDOUT_x"); os.makedirs(hd)
refused(lambda: S.build(os.path.join(d, "rows.csv"), os.path.join(hd, "o.csv"), [bp]), "HELDOUT_ path", "HELDOUT")
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
