#!/usr/bin/env python3
"""Tests for flips0x_second.py on INVENTED sqlite extracts (hand case FLIPS0X_SECOND_HAND_CASE.md)."""
import math, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flips0x_second as f
def mk(path, markets, candles):
    db = sqlite3.connect(path); db.execute("create table market(ticker text, series text, open_ts int, close_ts int, result text, strike real, src text)")
    db.execute("create table candle(ticker, end_ts, bid_c, ask_c, volume, oi)")
    for t, se, c, r in markets: db.execute("insert into market values (?,?,?,?,?,?,?)", (t, se, c - 900, c, r, 0.0, "l1b"))
    for row in candles: db.execute("insert into candle values (?,?,?,?,?,?)", row)
    db.commit(); db.close()
C = lambda k: 5000000 + 900 * k
mkts, cd = [], []
def win(k, series, result, mids, dec, lefts=None):
    t = "G%02d" % k; mkts.append((t, series, C(k), result)); lefts = lefts or [720, 660, 600, 540, 480, 420][-len(mids):]
    for left, m in zip(lefts, mids): cd.append((t, C(k) - left, round(m - .01, 4), round(m + .01, 4), 1, 0))
    cd.append((t, C(k) - 360, dec[0], dec[1], 1, 0))
UP = [.80, .82, .84, .86, .88, .90]
win(1, "KXXRP15M", "yes", UP, (.91, .92))
win(2, "KXXRP15M", "yes", [.80, .82, .84, .86, .84, .90], (.91, .92))
win(3, "KXGOLD15M", "yes", [.84, .86, .88], (.91, .92))
win(4, "KXDOGE15M", "no", [.18, .15, .12, .10, .08, .06], (.03, .04))
win(5, "KXGOLD15M", "no", [.80, .82, .8225, .84, .86, .88], (.90, .91))
win(6, "KXXRP15M", "yes", [.80, .82, .84, .836, .86, .88], (.89, .90))
win(7, "KXSILVER15M", "yes", UP, (.97, .98))
win(8, "KXSILVER15M", "yes", UP, (.79, .91))
win(9, "KXWTI15M", "yes", UP, (None, .92))
win(10, "KXWTI15M", "void", UP, (.91, .92))
mkts.append(("B", "KXBTC15M", C(11), "yes")); cd.append(("B", C(11) - 360, .91, .92, 1, 0)); cd.append(("G01", C(1) + 60, .1, .2, 1, 0))
near = lambda a, b: abs(a - b) < 1e-9
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x.sqlite"); mk(p, mkts, cd); r = f.run(p); c = r["counts"]
    assert (c["considered"], c["trades"], c["flips"], c["fewearlier"], c["band"], c["badquote"], c["nodecision"], c["excluded_result"], c["other_series_ignored"], c["candles_dropped_after_close"], c["candles_dropped_incomplete"]) == (9, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1), c
    for key, (pfa, neta, h1, n1, h2, n2) in {"h0.00": (1.94 / 9.16, -7.22, math.inf, 1.01, 0.93 / 9.16, -8.23), "h0.01": (1.67 / 9.26, -7.59, math.inf, 0.83, 0.84 / 9.26, -8.42), "h0.02": (1.39 / 9.35, -7.96, math.inf, 0.65, 0.74 / 9.35, -8.61)}.items():
        a = r["all"][key]; assert a["n"] == 4 and a["wins"] == 3 and near(a["pf"], pfa) and near(a["net"], neta) and a["half1_pf"] == h1 and near(a["half1_net"], n1) and near(a["half2_pf"], h2) and near(a["half2_net"], n2), (key, a)
    s = r["by_series_information_only"]; assert near(s["KXXRP15M"]["h0.01"]["net"], 1.49) and s["KXXRP15M"]["h0.01"]["pf"] == math.inf and near(s["KXXRP15M"]["h0.02"]["net"], 1.30) and s["KXDOGE15M"]["h0.01"]["n"] == 1 and near(s["KXDOGE15M"]["h0.01"]["net"], 0.18)
    assert near(s["KXGOLD15M"]["h0.01"]["net"], -9.26) and s["KXGOLD15M"]["h0.01"]["pf"] == 0.0 and near(s["KXGOLD15M"]["h0.02"]["net"], -9.35) and "KXSILVER15M" not in s
    assert r["counts_toward_20_to_30"] is False and "G0" not in str(r) and len(r["extract_sha256"]) == 64
# flips: the whole earlier path, the 0.004 edge and 0.0041
assert f.flips([.5, .6, .7]) == 0 and f.flips([.5, .6, .5]) == 1 and f.flips([.5, .6, .5, .6]) == 2 and f.flips([.5, .6, .5961]) == 0 and f.flips([.5, .6, .5959]) == 1 and f.flips([.84, .836, .86, .88]) == 0 and f.flips([.84, .8359, .86, .88]) == 1
assert f.flips([.5, .6, .6025, .5, .6]) == 2 and f.flips([.5, .5, .5]) == 0
# prices, fees, cap
assert f.fee_up_order(0.92) == 0.06 and f.fee_up_order(0.93) == 0.05 and f.fee_up_order(0.94) == 0.04 and f.fee_up_order(0.97) == 0.03 and f.fee_up_order(0.98) == 0.02 and f.fee_up_order(0.99) == 0.01 and f.fee_up_order(0.91) == 0.06 and f.fee_up_order(0.9) == 0.07
assert near(f.cash_of("yes", .98, "yes", .02), 10 * 0.01 - 0.01) and near(f.cash_of("no", .97, "no", 0.0), 0.27)
assert f.favourite(.87, .88) == ("yes", .88) and f.favourite(.86, .8799) is None and f.favourite(.96, .97) == ("yes", .97) and f.favourite(.97, .9701) is None and f.favourite(.03, .04) == ("no", .97)
assert f.valid_quote(.88, .98) and not f.valid_quote(.88, .9801) and f.valid_quote(.001, .05) and not f.valid_quote(.0009, .05)
# decision candle must end exactly 360 s before the close; only earlier loaded candles count
def one(mids, dec=(.91, .92), left=360):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "o.sqlite"); t = "Z"; rows = [(t, C(1) - l, round(m - .01, 4), round(m + .01, 4), 1, 0) for l, m in zip([720, 660, 600, 540, 480, 420][-len(mids):], mids)]
        rows.append((t, C(1) - left, dec[0], dec[1], 1, 0)); mk(p, [(t, "KXXRP15M", C(1), "yes")], rows); return f.run(p)["counts"]
assert one(UP)["trades"] == 1 and one(UP, left=361)["nodecision"] == 1 and one(UP, left=359)["nodecision"] == 1 and one([.84, .86, .88, .90])["trades"] == 1 and one([.86, .88, .90])["fewearlier"] == 1
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "n.sqlite"); mk(p, [], []); r = f.run(p); assert r["all"]["h0.01"]["n"] == 0 and r["all"]["h0.01"]["pf"] is None and r["counts_toward_20_to_30"] is False
assert one([.80, .82, .80, .84, .86, .88])["flips"] == 1 and one([.80, .82, .84, .86, .88, .90], dec=(.87, .89))["flips"] == 1          # an early flip and a flip caused by the decision candle both count
# odd n: halves are floor(n/2) and the rest by close time (n = 5: 2 and 3)
with tempfile.TemporaryDirectory() as d:
    m2, c2 = [], []
    for k in range(1, 6):
        t_ = "H%02d" % k; m2.append((t_, "KXXRP15M", C(k), "no" if k == 2 else "yes"))
        for left, m in zip([720, 660, 600, 540, 480, 420], UP): c2.append((t_, C(k) - left, round(m - .01, 4), round(m + .01, 4), 1, 0))
        c2.append((t_, C(k) - 360, .91, .92, 1, 0))
    p = os.path.join(d, "h.sqlite"); mk(p, m2, c2); r = f.run(p)["all"]["h0.00"]
    w, l = f.cash_of("yes", .92, "yes", 0.0), f.cash_of("yes", .92, "no", 0.0)
    assert r["n"] == 5 and near(r["half1_net"], w + l) and near(r["half2_net"], 3 * w) and near(r["half1_pf"], w / -l) and r["half2_pf"] == math.inf
print("flips0x build 2 tests passed")
