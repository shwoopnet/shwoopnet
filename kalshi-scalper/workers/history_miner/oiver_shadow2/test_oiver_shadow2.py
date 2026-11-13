"""Made-up data of EXPECTED_BY_HAND.md; prints MISMATCHES [] when oiver_shadow2.py agrees with the hand figures."""
import csv, gzip, math, os, sys, tempfile
from email.utils import formatdate
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oiver_shadow2 as S

BOOK = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + \
       ["yes_bid_sz_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
T = 1794744000
NOW = S.iso("2026-11-21T01:00:00Z")
K1B = ([(0.20, 100)], [(0.78, 50), (0.77, 50)])
W = {   # name: (close, oi, (yes levels, no levels), poll times before close)
    "K1": (T, 90000, K1B, (182.5, 180.5, 178.5)),
    "K2": (T + 900, 100000, ([(0.70, 10), (0.69, 30)], [(0.25, 200)]), (182.5, 180.5, 178.5)),
    "K3": (T + 1800, 95000, ([(0.10, 100)], [(0.88, 100)]), (182.5, 180.5, 176.0)),
    "K4": (T + 2700, None, ([(0.20, 100)], [(0.78, 100)]), (182.5, 180.5, 178.5)),
    "K5": (T + 3600, 50000, ([(0.20, 100)], [(0.78, 100)]), (182.5, 180.5, 178.5)),
    "K6": (T + 4500, 90000, ([], [(0.78, 100)]), (182.5, 180.5, 178.5)),
    "K7": (T + 5400, 90000, ([(0.20, 100)], [(0.78, 100)]), (195.5, 170.5)),
    "K8": (T + 6300, 90000, ([(0.03, 100)], [(0.94, 100)]), (182.5, 180.5, 178.5)),
    "K9": (T + 7200, 90000, ([(0.42, 100)], [(0.56, 100)]), (182.5, 180.5, 178.5)),
    "K10": (S.iso("2026-11-13T21:15:00Z"), 90000, K1B, (182.5, 180.5, 178.5)),
    "K12": (S.iso("2026-11-13T23:00:00Z"), 90000, K1B, (182.5, 180.5, 178.5)),
}


def isoz(e):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(e))


def row(name, close, x, yes, no):
    r = {c: "" for c in BOOK}
    r.update({"t_recv_ms": int(round(x * 1000)), "t_send_ms": int(round(x * 1000)) - 50, "server_date_header": formatdate(math.floor(x), usegmt=True),
              "ticker": "KXBTC15M-" + name, "series": "KXBTC15M", "close_time": isoz(close)})
    for i, (px, sz) in enumerate(yes, 1):
        r["yes_bid_px_%d" % i], r["yes_bid_sz_%d" % i] = px, sz
    for i, (px, sz) in enumerate(no, 1):
        r["no_bid_px_%d" % i], r["no_bid_sz_%d" % i] = px, sz
    return r


def make(base, results=None, extra_cov=None):
    d = tempfile.mkdtemp(dir=base)
    rows = []
    for n, (c, oi, (yes, no), pts) in W.items():
        rows += [row(n, c, c - s, yes, no) for s in pts]
    bp = os.path.join(d, "book15r6", "2026-11-15", "1200", "book.csv.gz"); os.makedirs(os.path.dirname(bp))
    with gzip.open(bp, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BOOK, lineterminator="\n"); w.writeheader(); w.writerows(rows)
    op = os.path.join(d, "oi.csv")
    with open(op, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["ticker", "oi_rise"])
        w.writerows(["KXBTC15M-" + n, oi] for n, (c, oi, b, p) in W.items() if oi is not None)
    res = results if results is not None else {"K1": "yes", "K9": "no", "K2": "no", "K3": "yes", "K12": ""}
    cp = os.path.join(d, "book15r6", "2026-11-15", "1200", "coverage.csv.gz")
    with gzip.open(cp, "wt", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["close_time", "series", "ticker", "result"])
        w.writerows([isoz(W[n][0]), "KXBTC15M", "KXBTC15M-" + n, v] for n, v in res.items())
        for t, v in (extra_cov or []):
            w.writerow(["", "KXBTC15M", t, v])
    return os.path.join(d, "log.csv"), op, [bp], [cp]


bad = []
root = tempfile.mkdtemp()
log, op, bps, cps = make(root)
o = S.run(log, op, "2026-11-13T22:00:00Z", bps, cps, now=NOW)
exp_counts = {"windows": 11, "before_count_from": 1, "no_oi": 1, "oi_below": 1, "not_two_sided": 1, "no_poll": 1, "cheap": 1, "out_of_band": 0, "signals": 5,
              "miss_no_second_look": 1, "miss_depth": 1, "filled": 3, "void": 1, "scored": 2}
if o["counts"] != exp_counts:
    bad.append(("counts", o["counts"]))
P = o["parent"]
if (P["n"], P["wins"], P["losses"], P["pf"], P["net"], P["mean"], P["label"], P["block_bar_met"]) != (2, 1, 1, 1.677596, 0.31, 0.155, "no evidence at n = 2", False):
    bad.append(("parent", P))
for k, n, pfv, net, skips in (("SPREAD", 2, 1.677596, 0.31, {"spread_wide": 1}), ("CAP30", 1, "inf", 0.7675, {"above_cap": 1}), ("DEPTH", 2, 1.677596, 0.31, {"depth_thin": 1})):
    q = o[k]
    if (q["n"], q["pf"], q["net"], q["skips"]) != (n, pfv, net, skips):
        bad.append((k, q["n"], q["pf"], q["net"], q["skips"]))
lg = {r["ticker"]: r for r in csv.DictReader(open(log))}
if lg["KXBTC15M-K12"]["result"] != "void" or lg["KXBTC15M-K12"]["cash"] != "-0.0125" or lg["KXBTC15M-K1"]["cash"] != "0.7675" or lg["KXBTC15M-K9"]["cash"] != "-0.4575":
    bad.append(("log", {t: (r["result"], r["cash"]) for t, r in lg.items()}))
if lg["KXBTC15M-K2"]["fill"] != "miss_depth" or lg["KXBTC15M-K3"]["fill"] != "miss_no_second_look" or lg["KXBTC15M-K2"]["CAP30"] != "pass":
    bad.append(("log fills", lg["KXBTC15M-K2"], lg["KXBTC15M-K3"]))


def refused(fn, what, why):
    try:
        fn()
    except (S.Stop, SystemExit) as e:
        print("refused", what, "->", str(e)[:90])
        if why not in str(e):
            bad.append(("wrong reason", what, str(e)[:90]))
        return
    bad.append(("not refused", what))


refused(lambda: S.run(log, op, "2026-11-13T22:00:00Z", bps, cps, now=S.iso("2026-11-20T23:00:00Z")), "block read on Nov 20", "refused before")
refused(lambda: S.run(log, op, None, bps, cps, now=NOW), "OI source not named", "not named")
l2, o2, b2, c2 = make(root, results={"K1": "yes", "K2": "no", "K3": "yes", "K12": ""})
refused(lambda: S.run(l2, o2, "2026-11-13T22:00:00Z", b2, c2, now=NOW), "K9 blank under 7 days", "block waits")
l3, o3, b3, c3 = make(root, results={"K1": "yes", "K9": "maybe", "K12": ""})
refused(lambda: S.run(l3, o3, "2026-11-13T22:00:00Z", b3, c3, now=NOW), "result maybe", "result 'maybe'")
l4, o4, b4, c4 = make(root, extra_cov=[("KXBTC15M-K1", "no")])
refused(lambda: S.run(l4, o4, "2026-11-13T22:00:00Z", b4, c4, now=NOW), "conflicting results", "disagree")
hd = os.path.join(root, "HELDOUT_x"); os.makedirs(hd)
l5, o5, b5, c5 = make(hd)
refused(lambda: S.run(l5, o5, "2026-11-13T22:00:00Z", b5, c5, now=NOW), "HELDOUT_ path", "HELDOUT")
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
