#!/usr/bin/env python3
"""Tests for qr1_jumpfade.py on INVENTED sqlite extracts (hand case QR1_JUMPFADE_REGISTRATION.md)."""
import math, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qr1_jumpfade as q
def mk(path, markets, candles):
    db = sqlite3.connect(path); db.execute("create table market(ticker text, series text, open_ts int, close_ts int, result text, strike real, src text)")
    db.execute("create table candle(ticker, end_ts, bid_c, ask_c, volume, oi)")
    for t, se, c, r in markets: db.execute("insert into market values (?,?,?,?,?,?,?)", (t, se, c - 900, c, r, 0.0, "l1b"))
    for row in candles: db.execute("insert into candle values (?,?,?,?,?,?)", row)
    db.commit(); db.close()
C = lambda k: 1790380800 + 86400 * (k - 1) + 43200
mk_, cd = [], []
def win(k, series, result, p, d):
    t = "J%02d" % k; mk_.append((t, series, C(k), result))
    if p is not None: cd.append((t, C(k) - 660, p[0], p[1], 1, 0))
    if d is not None: cd.append((t, C(k) - 600, d[0], d[1], 1, 0))
win(1, "KXXRP15M", "no", (.49, .51), (.60, .62)); win(2, "KXSILVER15M", "no", (.60, .62), (.49, .51)); win(3, "KXXRP15M", "yes", (.49, .51), (.58, .60)); win(4, "KXXRP15M", "yes", (.49, .51), (.59, .61))
win(5, "KXXRP15M", "yes", (.49, .51), (.57, .63)); win(6, "KXXRP15M", "yes", (.79, .81), (.94, .96)); win(7, "KXXRP15M", "yes", None, (.60, .62)); win(8, "KXXRP15M", "yes", (.49, .51), (None, .62))
win(9, "KXXRP15M", "yes", (.50, .50), (.60, .62)); win(10, "KXXRP15M", "void", (.49, .51), (.60, .62))
cd.append(("J01", C(1) + 60, .1, .2, 1, 0))
near = lambda a, b: abs(a - b) < 1e-9
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x.sqlite"); mk(p, mk_, cd); r = q.run(p); c = r["counts"]
    assert (c["considered"], c["trades"], c["nofire"], c["spread"], c["band"], c["noprevious"], c["nodecision"], c["badquote"], c["excluded_result"], c["candles_dropped_after_close"], c["candles_dropped_incomplete"]) == (9, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1), c
    for key, (pfa, neta, n1, n2) in {"h0.00": (5.83 / 9.55, -3.72, 5.83, -9.55), "h0.01": (5.73 / 9.76, -4.03, 5.73, -9.76), "h0.02": (5.62 / 9.96, -4.34, 5.62, -9.96)}.items():
        a = r["pooled_information_only"][key]; assert a["n"] == 3 and a["wins"] == 1 and near(a["pf"], pfa) and near(a["net"], neta) and a["half1_pf"] == math.inf and near(a["half1_net"], n1) and a["half2_pf"] == 0.0 and near(a["half2_net"], n2), (key, a)
    zz = r["standard_group"]; assert near(zz["h0.00"]["day_clustered_z"], 0.1544554455445545) and near(zz["h0.01"]["day_clustered_z"], 0.13353115727002973) and near(zz["h0.02"]["day_clustered_z"], 0.11287128712871285) and zz["h0.01"]["trade_days"] == 2
    assert r["c11_group"]["h0.01"]["day_clustered_z"] is None and r["c11_group"]["h0.01"]["trade_days"] == 1 and near(r["pooled_information_only"]["h0.01"]["day_clustered_z"], -0.3785713459764245) and r["pooled_information_only"]["h0.01"]["trade_days"] == 3
    assert r["tries_in_deflation_ledger"] == 2 and "second build equal at 1e-9" in r["ledger_note"]
    s = r["standard_group"]; assert s["h0.01"]["n"] == 2 and near(s["h0.01"]["pf"], 5.73 / 4.38) and near(s["h0.01"]["net"], 1.35) and near(s["h0.02"]["pf"], 5.62 / 4.48) and near(s["h0.02"]["net"], 1.14) and s["h0.01"]["half1_pf"] == math.inf and s["h0.01"]["half2_pf"] == 0.0
    cc = r["c11_group"]; assert cc["h0.01"]["n"] == 1 and cc["h0.01"]["wins"] == 0 and s["pass_standard"] is False and cc["pass_c11"] is False and r["PASS"] is False
    f2, l3 = r["first_two_thirds_of_days_information_only"], r["last_third_of_days_information_only"]
    assert f2["h0.00"]["n"] == 2 and near(f2["h0.00"]["pf"], 5.83 / 5.28) and near(f2["h0.00"]["net"], 0.55) and near(f2["h0.01"]["pf"], 5.73 / 5.38) and near(f2["h0.02"]["net"], 0.14) and l3["h0.00"]["n"] == 1 and l3["h0.00"]["pf"] == 0.0 and near(l3["h0.02"]["net"], -4.48)
    assert r["evidence"]["standard_group"] == "no evidence at n = 2" and r["evidence"]["c11_group"] == "no evidence at n = 1" and "J0" not in str(r) and "XRP" in str(r["by_series_information_only"]) is not None and len(r["extract_sha256"]) == 64
# prices and cash
assert q.fee_up_order(0.40) == 0.17 and q.fee_up_order(0.41) == 0.17 and q.fee_up_order(0.42) == 0.18 and q.fee_up_order(0.51) == 0.18 and q.fee_up_order(0.52) == 0.18 and q.fee_up_order(0.53) == 0.18 and q.fee_up_order(0.43) == 0.18
assert near(q.cash_of("no", .40, "no", 0.0), 5.83) and near(q.cash_of("no", .40, "no", .02), 5.62) and near(q.cash_of("yes", .51, "no", .01), -5.38) and near(q.cash_of("yes", .98, "yes", .02), 0.09)
# decide edges
def one(p, d, left_d=600, left_p=660):
    with tempfile.TemporaryDirectory() as dd:
        pp = os.path.join(dd, "o.sqlite"); mk(pp, [("Z", "KXXRP15M", C(1), "yes")], [("Z", C(1) - left_p, p[0], p[1], 1, 0), ("Z", C(1) - left_d, d[0], d[1], 1, 0)]); return q.run(pp)["counts"]
assert one((.49, .51), (.59, .61))["trades"] == 1 and one((.49, .51), (.5899, .6099))["nofire"] == 1 and one((.49, .51), (.60, .62))["trades"] == 1
assert one((.49, .51), (.50, .70))["spread"] == 1 and one((.49, .51), (.58, .62))["trades"] == 1 and one((.49, .51), (.58, .6201))["spread"] == 1
assert one((.49, .51), (.60, .62), left_d=601)["nodecision"] == 1 and one((.49, .51), (.60, .62), left_p=661)["noprevious"] == 1 and one((.49, .51), (.60, .62), left_p=659)["noprevious"] == 1
assert one((.80, .82), (.49, .51))["trades"] == 1 and one((.20, .22), (.30, .32))["band"] == 1 and one((.20, .22), (.09, .11))["trades"] == 1 and one((.20, .22), (.08, .09))["band"] == 1 and one((.20, .22), (.32, .34))["band"] == 1
# jump down buys YES at the ask: band 0.10 to 0.60 on the ask; ask 0.61 is out
assert one((.70, .72), (.59, .61))["band"] == 1 and one((.70, .72), (.58, .60))["trades"] == 1
# the passing sets: 120 standard trades with 1c PF >= 1.3, both halves >= 1.0, 2c PF >= 1.0; C11 group needs 2c
def many(series, wins, losses, price_no=.40, alt=False):
    with tempfile.TemporaryDirectory() as dd:
        pp = os.path.join(dd, "m.sqlite"); ms, cs = [], []
        for k in range(1, wins + losses + 1):
            t = "M%03d" % k; res = ("no" if k % 2 else "yes") if alt else ("no" if (k % (wins + losses) < wins) else "yes"); ms.append((t, series, C(k), res)); cs += [(t, C(k) - 660, .49, .51, 1, 0), (t, C(k) - 600, .60, .62, 1, 0)]
        mk(pp, ms, cs); return q.run(pp)
rr = many("KXXRP15M", 99, 21); assert rr["counts"]["trades"] == 120 and rr["standard_group"]["pass_standard"] is True and rr["PASS"] is True and rr["c11_group"]["pass_c11"] is False
rc = many("KXSILVER15M", 99, 21); assert rc["c11_group"]["pass_c11"] is True and rc["standard_group"]["pass_standard"] is False and rc["PASS"] is True
rl = many("KXXRP15M", 60, 60); assert rl["PASS"] is False and rl["standard_group"]["pass_standard"] is False
rs = many("KXXRP15M", 50, 49); assert rs["standard_group"]["pass_standard"] is False and rs["evidence"]["standard_group"] == "no evidence at n = 99"
# 1c passes but 2c does not reach 1.3: 60 wins and 60 losses interleaved (1c PF 1.3419, 2c PF 1.2831)
ra = many("KXXRP15M", 60, 60, alt=True); b1, b2 = ra["standard_group"]["h0.01"], ra["standard_group"]["h0.02"]
assert abs(b1["pf"] - 60 * 5.73 / (60 * 4.27)) < 1e-9 and abs(b2["pf"] - 60 * 5.62 / (60 * 4.38)) < 1e-9 and ra["standard_group"]["pass_standard"] is True and ra["PASS"] is True
rb = many("KXSILVER15M", 60, 60, alt=True); assert rb["c11_group"]["pass_c11"] is False and rb["PASS"] is False
rh = many("KXHYPE15M", 99, 21); assert rh["c11_group"]["pass_c11"] is True and rh["standard_group"]["h0.01"]["n"] == 0
rn = many("KXNEAR15M", 99, 21); assert rn["standard_group"]["pass_standard"] is True and rn["c11_group"]["h0.01"]["n"] == 0
zt = [{"tk": "a", "day": "d1", "cash": {0.01: 1.0}}, {"tk": "b", "day": "d1", "cash": {0.01: 2.0}}, {"tk": "c", "day": "d2", "cash": {0.01: -1.0}}]; zv, zd = q.zday(zt, 0.01)
assert zd == 2 and abs(zv - 0.5) < 1e-12          # two trades on one day are one cluster: day sums 3 and -1
print("qr1 tests passed")
