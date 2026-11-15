#!/usr/bin/env python3
"""Tests for oirel_second.py on INVENTED sqlite extracts (hand case OIREL_SECOND_HAND_CASE.md)."""
import math, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oirel_second as o
def mk(path, markets, candles):
    db = sqlite3.connect(path); db.execute("create table market(ticker text, series text, open_ts int, close_ts int, result text, strike real, src text)")
    db.execute("create table candle(ticker text, end_ts int, bid_c real, ask_c real, volume int, oi int)")
    for t, s, c, r in markets: db.execute("insert into market values (?,?,?,?,?,?,?)", (t, s, c - 900, c, r, 0.0, "l1b"))
    for row in candles: db.execute("insert into candle values (?,?,?,?,?,?)", row)
    db.commit(); db.close()
C = lambda k: 1000000 + 900 * k
mkts, cd = [], []
def win(name, k, result, back, sig, fill, extra=()):
    mkts.append((name, "KXBTC15M", C(k), result)); c = C(k)
    if back is not None: cd.append((name, c - 360, None, None, 1, back[2]) if len(back) == 3 else (name, c - 360, back[0], back[1], 1, back[2]))
    if sig is not None: cd.append((name, c - 180, sig[0], sig[1], 1, sig[2]))
    if fill is not None: cd.append((name, c - 120, fill[0], fill[1], 1, 0))
    for e in extra: cd.append((name,) + e)
win("A", 1, "yes", (0.2, 0.22, 2000), (0.20, 0.22, 2535), (0.20, 0.22))
win("B", 2, "yes", (0.2, 0.22, 2000), (0.09, 0.11, 2536), (0.09, 0.10), extra=((C(2) + 60, 0.98, 0.99, 1, 9999),))
win("C", 3, "no", (0.5, 0.6, 1000), (0.55, 0.57, 1300), (0.52, 0.54), extra=((C(3) + 900, 0.1, 0.2, 1, 1),))
win("D", 4, "no", (0.5, 0.6, 1000), (0.20, 0.22, 1300), (0.24, 0.25))
win("E", 5, "yes", None, (0.20, 0.22, 1300), (0.24, 0.25))
win("F", 6, "yes", (0.5, 0.6, 0), (0.20, 0.22, 1300), (0.24, 0.25))
win("G", 7, "yes", (0.5, 0.6, 1000), (0.48, 0.52, 1300), (0.48, 0.52))
win("H", 8, "yes", (0.5, 0.6, 1000), (None, 0.30, 1300), (0.24, 0.25))
win("I", 9, "yes", (0.5, 0.6, 1000), (0.39, 0.41, 1300), None)
win("J", 10, "yes", (0.5, 0.6, 1000), (0.09, 0.11, 1300), (0.96, 0.98))
win("L", 11, "void", (0.5, 0.6, 1000), (0.09, 0.11, 1300), (0.19, 0.20))
mkts.append(("OTHER", "KXETH15M", C(12), "yes"))
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x.sqlite"); mk(p, mkts, cd); r = o.run(p, C(4) + 1); c = r["counts"]
    assert (c["windows"], c["trades"], c["nodata"], c["nofire"], c["nottwo"], c["noside"], c["voids"], c["candles_dropped_after_close"], c["other_series_ignored"]) == (11, 5, 3, 1, 1, 1, 1, 2, 1), c
    near = lambda a, b: abs(a - b) < 1e-9
    for key, pf_, net, h1pf, h1net, h2pf, h2net, dpf, dnet, vpf, vnet in (("h0.00", 14.13 / 2.76, 11.37, math.inf, 13.95, 0.18 / 2.76, -2.58, 13.95 / 2.64, 11.31, 1.5, 0.06),
                                                                  ("h0.01", 13.84 / 2.86, 10.98, math.inf, 13.75, 0.09 / 2.86, -2.77, 13.75 / 2.74, 11.01, 0.75, -0.03),
                                                                  ("h0.02", 13.63 / 2.97, 10.66, math.inf, 13.54, 0.09 / 2.97, -2.88, 13.54 / 2.84, 10.70, 0.09 / 0.13, -0.04)):
        x = r[key]; assert near(x["pf"], pf_) and near(x["net"], net) and x["half1_pf"] == h1pf and near(x["half1_net"], h1net) and near(x["half2_pf"], h2pf) and near(x["half2_net"], h2net), (key, x)
        assert x["discovery_n"] == 3 and x["validation_n"] == 2 and near(x["discovery_pf"], dpf) and near(x["discovery_net"], dnet) and near(x["validation_pf"], vpf) and near(x["validation_net"], vnet), (key, x)
    assert r["counts_toward_20_to_30"] is False and "upper bound, not fill-checked" in r["label"] and "per-order rounded" in r["label"] and len(r["extract_sha256"]) == 64
    assert "A" not in str(r) and "KXBTC" not in str(r)
# fee ceiling, cap, strictness, close-edge candle
assert o.fee_up_order(0.10) == 0.07 and o.fee_up_order(0.12) == 0.08 and o.fee_up_order(0.22) == 0.13 and o.fee_up_order(0.99) == 0.01 and o.fee_up_order(0.98) == 0.02 and o.fee_up_order(0.5) == 0.18
assert o.fee_up_order(0.25) == 0.14 and o.fee_up_order(0.48) == 0.18
assert abs(o.cash_of("yes", 0.98, "yes", 0.02)[0] - (10 * 0.01 - 0.01)) < 1e-12 and o.cash_of("yes", 0.98, "yes", 0.02)[1] == 0.99
assert o.cash_of("no", 0.2, "void", 0.02) == (-0.13, 0.22, True)
assert not (0.2675 > o.RTHR) and 0.268 > o.RTHR and not (o.RTHR > o.RTHR)
with tempfile.TemporaryDirectory() as d:          # a candle ending exactly at the close is kept; one second after is dropped
    p = os.path.join(d, "y.sqlite"); mk(p, [("Z", "KXBTC15M", C(1), "yes")], [("Z", C(1), 0.1, 0.2, 1, 5), ("Z", C(1) + 1, 0.1, 0.2, 1, 5)]); assert o.run(p, 0)["counts"]["candles_dropped_after_close"] == 1
with tempfile.TemporaryDirectory() as d:          # empty: n 0, no crash
    p = os.path.join(d, "z.sqlite"); mk(p, [("Z", "KXBTC15M", C(1), "yes")], []); r = o.run(p, 0); assert r["counts"]["nodata"] == 1 and r["h0.01"]["n"] == 0 and r["h0.01"]["pf"] is None and r["counts_toward_20_to_30"] is False
# a passing set: 40 trades, 36 wins; both halves and 2c pass
with tempfile.TemporaryDirectory() as d:
    m2, c2 = [], []
    for k in range(1, 41):
        t = "W%02d" % k; m2.append((t, "KXBTC15M", C(k), "yes" if k % 10 else "no")); c = C(k)
        c2 += [(t, c - 360, 0.5, 0.6, 1, 1000), (t, c - 180, 0.09, 0.11, 1, 1300), (t, c - 120, 0.09, 0.10, 1, 0)]
    p = os.path.join(d, "w.sqlite"); mk(p, m2, c2); r = o.run(p, C(21)); assert r["counts"]["trades"] == 40 and r["counts_toward_20_to_30"] is True and r["h0.01"]["wins"] == 36 and r["h0.01"]["discovery_n"] == 20
    assert abs(r["h0.01"]["pf"] - (36 * 8.83) / (4 * 1.17)) < 1e-9 and abs(r["h0.01"]["net"] - (36 * 8.83 - 4 * 1.17)) < 1e-9
# boundaries: signal YES ask exactly 0.05 and 0.50 are in; a locked fill candle is not two-sided
def one(sig, fill, result="yes"):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "q.sqlite"); c = C(1); mk(p, [("Q", "KXBTC15M", c, result)], [("Q", c - 360, 0.5, 0.6, 1, 1000), ("Q", c - 180, sig[0], sig[1], 1, 1300), ("Q", c - 120, fill[0], fill[1], 1, 0)]); return o.run(p, 0)["counts"]
assert one((0.04, 0.05), (0.04, 0.05))["trades"] == 1 and one((0.04, 0.0499), (0.04, 0.05))["noside"] == 1 and one((0.49, 0.50), (0.49, 0.50))["trades"] == 1 and one((0.49, 0.5001), (0.49, 0.5))["noside"] == 1
assert one((0.20, 0.22), (0.25, 0.25))["nottwo"] == 1 and one((0.20, 0.22), (0.27, 0.25))["nottwo"] == 1 and one((0.20, 0.22), (0.25, 1.0))["nottwo"] == 1
# 2c fails while 1c passes (price near the cap): 142 trades at p 0.97 raw, 2 losses, one in each half
with tempfile.TemporaryDirectory() as d:
    m2, c2 = [], []
    for k in range(1, 145):
        t_ = "V%03d" % k; m2.append((t_, "KXBTC15M", C(k), "no" if k in (10, 100) else "yes")); c = C(k)
        c2 += [(t_, c - 360, 0.5, 0.6, 1, 1000), (t_, c - 180, 0.09, 0.11, 1, 1300), (t_, c - 120, 0.96, 0.97, 1, 0)]
    p = os.path.join(d, "v.sqlite"); mk(p, m2, c2); r = o.run(p, 0)
    assert r["counts"]["trades"] == 144 and r["h0.01"]["pf"] >= 1.3 - 1e-9 and r["h0.01"]["half1_pf"] >= 1.0 and r["h0.01"]["half2_pf"] >= 1.0 and r["h0.02"]["pf"] < 1.0 and r["counts_toward_20_to_30"] is False, r["h0.02"]
print("oirel build 2 tests passed")
