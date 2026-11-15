#!/usr/bin/env python3
"""Tests for xrpfav_second.py on INVENTED sqlite extracts (hand case XRPFAV_SECOND_HAND_CASE.md)."""
import math, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xrpfav_second as x
def mk(path, markets, candles):
    db = sqlite3.connect(path); db.execute("create table market(ticker text, series text, open_ts int, close_ts int, result text, strike real, src text)")
    db.execute("create table candle(ticker text, end_ts int, bid_c real, ask_c real, volume int, oi int)")
    for t, s, c, r in markets: db.execute("insert into market values (?,?,?,?,?,?,?)", (t, s, c - 900, c, r, 0.0, "l1b"))
    for row in candles: db.execute("insert into candle values (?,?,?,?,?,?)", row)
    db.commit(); db.close()
C = lambda k: 2000000 + 900 * k
mkts, cd = [], []
def win(k, result, quotes):
    t = "W%02d" % k; mkts.append((t, "KXXRP15M", C(k), result))
    for left, b, a in quotes: cd.append((t, C(k) - left, b, a, 1, 0))
for k, res, q in ((1, "yes", [(360, .90, .91), (600, .90, .91)]), (2, "yes", [(360, .07, .09), (600, .07, .09)]), (3, "yes", [(360, .08, .09), (600, .08, .09)]), (4, "yes", [(360, .87, .88), (600, .87, .88)]),
                  (5, "no", [(360, .87, .90), (600, .87, .90)]), (6, "yes", [(480, .90, .91)]), (7, "yes", [(400, .89, .90), (360, .50, .51), (640, .89, .90), (570, .50, .51)]),
                  (8, "yes", [(360, .0, .91), (600, .0, .91)]), (9, "yes", [(360, .90, None), (600, .90, None)]), (10, "void", [(360, .90, .91), (600, .90, .91)]), (11, "yes", [(360, .89, .91), (600, .89, .91)])):
    win(k, res, q)
cd.append(("W01", C(1) + 1, .1, .2, 1, 0)); mkts.append(("OTHER", "KXBTC15M", C(12), "yes"))
near = lambda a, b: abs(a - b) < 1e-9
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x.sqlite"); mk(p, mkts, cd)
    r6, r10 = x.run(p, "XRPFAV6"), x.run(p, "XRPFAV10")
    c = r6["counts"]; assert (c["windows"], c["trades"], c["band"], c["spread"], c["nocandle"], c["badquote"], c["excluded_result"], c["candles_dropped_after_close"], c["other_series_ignored"]) == (10, 4, 2, 1, 1, 2, 1, 1, 1), c
    c = r10["counts"]; assert (c["windows"], c["trades"], c["band"], c["spread"], c["nocandle"], c["badquote"], c["excluded_result"]) == (10, 5, 2, 0, 1, 2, 1), c
    for key, pf_, net, hf1, hf2, pf10, net10, h10a, h10b in (("h0.00", 2.80 / 9.26, -6.46, 0.84 / 9.26, math.inf, 2.80 / 18.33, -15.53, 0.84 / 9.26, 1.96 / 9.07),
                                                             ("h0.01", 2.51 / 9.35, -6.84, 0.74 / 9.35, math.inf, 2.51 / 18.51, -16.00, 0.74 / 9.35, 1.77 / 9.16),
                                                             ("h0.02", 2.23 / 9.44, -7.21, 0.65 / 9.44, math.inf, 2.23 / 18.70, -16.47, 0.65 / 9.44, 1.58 / 9.26)):
        a = r6[key]; assert a["n"] == 4 and a["wins"] == 3 and near(a["pf"], pf_) and near(a["net"], net) and near(a["half1_pf"], hf1) and a["half2_pf"] == hf2, (key, a)
        b = r10[key]; assert b["n"] == 5 and b["wins"] == 3 and near(b["pf"], pf10) and near(b["net"], net10) and near(b["half1_pf"], h10a) and near(b["half2_pf"], h10b), (key, b)
    assert r6["counts_toward_20_to_30"] is False and r10["counts_toward_20_to_30"] is False and "upper bound, not fill-checked" in r6["label"] and "KXXRP" not in str(r6) and "W0" not in str(r6) and len(r6["extract_sha256"]) == 64
    try: x.run(p, "NOPE"); raise AssertionError
    except SystemExit: pass
# fees, cap
assert x.fee_up_order(0.91) == 0.06 and x.fee_up_order(0.92) == 0.06 and x.fee_up_order(0.93) == 0.05 and x.fee_up_order(0.94) == 0.04 and x.fee_up_order(0.88) == 0.08 and x.fee_up_order(0.89) == 0.07 and x.fee_up_order(0.90) == 0.07
assert near(x.cash_of("yes", 0.98, "yes", 0.02), 10 * 0.01 - 0.01) and near(x.cash_of("yes", 0.91, "yes", 0.0), 0.84) and near(x.cash_of("no", 0.92, "yes", 0.01), -9.35)
# range edges
def one(rule, left, b=0.90, a=0.91):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "e.sqlite"); mk(p, [("Z", "KXXRP15M", C(1), "yes")], [("Z", C(1) - left, b, a, 1, 0)]); return x.run(p, rule)["counts"]
assert one("XRPFAV6", 400)["trades"] == 1 and one("XRPFAV6", 330)["trades"] == 1 and one("XRPFAV6", 401)["nocandle"] == 1 and one("XRPFAV6", 329)["nocandle"] == 1
assert one("XRPFAV10", 570)["trades"] == 1 and one("XRPFAV10", 640)["trades"] == 1 and one("XRPFAV10", 641)["nocandle"] == 1 and one("XRPFAV10", 569)["nocandle"] == 1
assert one("XRPFAV6", 360, .91, .9201)["band"] == 1 and one("XRPFAV6", 360, .87, .88)["trades"] == 1 and one("XRPFAV6", 360, .86, .8799)["band"] == 1 and one("XRPFAV6", 360, .89, .91)["trades"] == 1 and one("XRPFAV6", 360, .89, .9101)["spread"] == 1
assert one("XRPFAV10", 600, .60, .9201)["band"] == 1 and one("XRPFAV10", 600, .60, .9199)["trades"] == 1 and one("XRPFAV6", 360, .90, .90)["badquote"] == 1 and one("XRPFAV6", 360, .90, 1.0)["badquote"] == 1
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "n.sqlite"); mk(p, [("Z", "KXXRP15M", C(1), "yes")], []); r = x.run(p, "XRPFAV6"); assert r["counts"]["nocandle"] == 1 and r["h0.01"]["n"] == 0 and r["h0.01"]["pf"] is None and r["counts_toward_20_to_30"] is False
# passing set: 40 trades at p 0.88, 39 wins
with tempfile.TemporaryDirectory() as d:
    m2, c2 = [], []
    for k in range(1, 61):
        t = "P%02d" % k; m2.append((t, "KXXRP15M", C(k), "no" if k in (7, 40) else "yes")); c2.append((t, C(k) - 360, 0.87, 0.88, 1, 0))
    p = os.path.join(d, "p.sqlite"); mk(p, m2, c2); r = x.run(p, "XRPFAV6")
    w1, l1 = x.cash_of("yes", 0.88, "yes", 0.01), x.cash_of("yes", 0.88, "no", 0.01)
    assert r["counts"]["trades"] == 60 and near(r["h0.01"]["pf"], 58 * w1 / (2 * -l1)) and r["counts_toward_20_to_30"] is (r["h0.01"]["pf"] >= 1.3 and r["h0.01"]["half1_pf"] >= 1.0 and r["h0.01"]["half2_pf"] >= 1.0 and r["h0.02"]["pf"] >= 1.0)
with tempfile.TemporaryDirectory() as d:          # a candle ending exactly at the close is kept (never counted dropped), one second after is dropped
    p = os.path.join(d, "c.sqlite"); mk(p, [("Z", "KXXRP15M", C(1), "yes")], [("Z", C(1), .9, .91, 1, 0)]); assert x.run(p, "XRPFAV6")["counts"]["candles_dropped_after_close"] == 0
print("xrpfav build 2 tests passed")
