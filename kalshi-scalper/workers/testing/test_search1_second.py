#!/usr/bin/env python3
"""Tests for search1_second.py on INVENTED sqlite extracts (hand case SEARCH1_SECOND_HAND_CASE.md)."""
import math, os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import search1_second as s
def mk(path, markets, candles):
    db = sqlite3.connect(path); db.execute("create table market(ticker text, series text, open_ts int, close_ts int, result text, strike real, src text)")
    db.execute("create table candle(ticker, end_ts, bid_c, ask_c, volume, oi)")
    for t, se, c, r in markets: db.execute("insert into market values (?,?,?,?,?,?,?)", (t, se, c - 900, c, r, 0.0, "l1b"))
    for row in candles: db.execute("insert into candle values (?,?,?,?,?,?)", row)
    db.commit(); db.close()
CUT = 1790467200
C = lambda k: (CUT - 20000 + 900 * k) if k <= 3 else (CUT + 1000 + 900 * k)
mk_, cd = [], []
def win(k, result, cands, series="KXBTC15M"):
    t = "S%02d" % k; mk_.append((t, series, C(k), result))
    for left, b, a in cands: cd.append((t, C(k) - left, b, a, 1, 0))
HIGH = [(360, .97, .98)]
win(1, "yes", [(420, .97, .98), (360, .97, .98), (240, .97, .98)])
win(2, "no", [(420, .01, .02), (360, .02, .03), (240, .56, .59)], "KXETH15M")
win(3, "no", [(420, .96, .97), (300, .96, .97)])
win(4, "yes", [(420, .50, .52)])
win(5, "yes", [(360, .97, .98)])
win(6, "yes", [(420, .97, .98), (300, None, .98)])
win(7, "yes", [(420, .97, .98), (30, .50, .52)])
win(8, "yes", [(420, .97, .98), (20, .30, .32)])
win(9, "yes", [(420, .98, .995)])
win(10, "yes", [(420, .95, 1.00)])
win(11, "yes", [(420, .86, .98)])
win(12, "void", [(420, .97, .98)])
mk_.append(("X", "KXXRP15M", C(5), "yes")); cd.append(("X", C(5) - 420, .97, .98, 1, 0)); cd.append(("S01", C(1) + 5, .1, .2, 1, 0))
near = lambda a, b: abs(a - b) < 1e-9
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x.sqlite"); mk(p, mk_, cd); r = s.run(p, CUT); c = r["counts"]
    assert (c["considered"], c["trades"], c["nocandle"], c["badquote"], c["band"], c["incomplete_market"], c["excluded_result"], c["other_series_ignored"], c["sl50_exits"], c["candles_dropped_after_close"]) == (10, 6, 1, 2, 1, 1, 1, 1, 2, 1), c
    exp = {"h0.00": (0.45 / 20.71, -20.26, 0.18 / 15.71, -15.53, 0.27 / 5.00, -4.73), "h0.01": (0.27 / 21.09, -20.82, 0.09 / 15.90, -15.81, 0.18 / 5.19, -5.01), "h0.02": (0.27 / 21.38, -21.11, 0.09 / 16.09, -16.00, 0.18 / 5.29, -5.11)}
    for key, (pfa, neta, h1, n1, h2, n2) in exp.items():
        a = r["all"][key]; assert a["n"] == 6 and a["wins"] == 3 and near(a["pf"], pfa) and near(a["net"], neta) and near(a["half1_pf"], h1) and near(a["half1_net"], n1) and near(a["half2_pf"], h2) and near(a["half2_net"], n2), (key, a)
    for key, (dpf, dnet, cpf, cnet) in {"h0.00": (0.18 / 15.71, -15.53, 0.27 / 5.00, -4.73), "h0.01": (0.09 / 15.90, -15.81, 0.18 / 5.19, -5.01), "h0.02": (0.09 / 16.09, -16.00, 0.18 / 5.29, -5.11)}.items():
        dd = r["discovery_information_only"][key]; assert dd["n"] == 3 and near(dd["pf"], dpf) and near(dd["net"], dnet) and dd["half1_pf"] == math.inf and dd["half2_pf"] == 0.0, (key, dd)
        cc = r["confirmation"][key]; assert near(cc["pf"], cpf)
        assert cc["n"] == 3 and near(cc["net"], cnet) and cc["half1_pf"] == 0.0 and cc["half2_pf"] == math.inf, (key, cc)
    assert r["counts_toward_20_to_30_on_confirmation"] is False and "S0" not in str(r) and "KXBTC" not in str(r) and len(r["extract_sha256"]) == 64
# per-window figures
near2 = lambda a, b: abs(a - b) < 1e-9
assert near2(s.cash_of("yes", .98, None, "yes", 0.0), 0.18) and near2(s.cash_of("yes", .98, None, "yes", .01), 0.09) and near2(s.cash_of("yes", .98, None, "yes", .02), 0.09) and near2(s.cash_of("yes", .995, None, "yes", 0.0), 0.09)
assert near2(s.cash_of("no", .99, .41, "no", 0.0), -5.98) and near2(s.cash_of("no", .99, .41, "no", .01), -6.08) and near2(s.cash_of("no", .99, .41, "no", .02), -6.18)
assert near2(s.cash_of("yes", .98, .50, "yes", 0.0), -5.00) and near2(s.cash_of("yes", .98, .50, "yes", .01), -5.19) and near2(s.cash_of("yes", .98, .50, "yes", .02), -5.29)
assert near2(s.cash_of("yes", .97, None, "no", 0.0), -9.73) and near2(s.cash_of("yes", .97, None, "no", .02), -9.91)
assert near2(s.cash_of("no", .99, 0.0, "no", .02), 10 * (0.01 - 0.99) - 0.01 - s.fee_up_order(0.01))          # exit price floor 0.01
# valid_quote edges
assert s.valid_quote(.001, .05) and not s.valid_quote(.0009, .05) and s.valid_quote(.9, .999) and not s.valid_quote(.9, .9991) and not s.valid_quote(.5, .4) and s.valid_quote(.88, .98) and not s.valid_quote(.88, .9801) and s.valid_quote(.87, .97)
assert s.favourite(.97, .995) == ("yes", .995) and s.favourite(.97, .9951) is None and s.favourite(.96, .97) == ("yes", .97) and s.favourite(.01, .02) == ("no", .99)
# entry candle must end exactly at 420; the SL50 window edges
def one(cands, res="yes"):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "o.sqlite"); mk(p, [("Z", "KXBTC15M", C(5), res)], [("Z", C(5) - l, b, a, 1, 0) for l, b, a in cands]); return s.run(p, CUT)["counts"]
assert one([(421, .97, .98)])["nocandle"] == 1 and one([(419, .97, .98)])["nocandle"] == 1 and one([(420, .97, .98)])["trades"] == 1
assert one([(420, .97, .98), (31, .50, .52)])["sl50_exits"] == 1 and one([(420, .97, .98), (29, .50, .52)])["sl50_exits"] == 0 and one([(420, .97, .98), (300, .5001, .52)])["sl50_exits"] == 0 and one([(420, .97, .98), (300, .5, .52)])["sl50_exits"] == 1
assert one([(420, .97, .98), (420, .01, .02)])["sl50_exits"] == 0          # the entry candle itself is never a later candle
# a NO position exits on the flipped candle: ask close 0.55 gives NO bid 0.45
assert one([(420, .01, .02), (300, .50, .55)])["sl50_exits"] == 1 and one([(420, .01, .02), (300, .50, .45)])["sl50_exits"] == 0
# a null-bid candle ending after the close does not put a market out
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "n.sqlite"); mk(p, [("Z", "KXBTC15M", C(5), "yes")], [("Z", C(5) - 420, .97, .98, 1, 0), ("Z", C(5) + 60, None, .98, 1, 0)]); c = s.run(p, CUT)["counts"]; assert c["incomplete_market"] == 0 and c["trades"] == 1 and c["candles_dropped_after_close"] == 1
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "e.sqlite"); mk(p, [], []); r = s.run(p, CUT); assert r["all"]["h0.01"]["n"] == 0 and r["all"]["h0.01"]["pf"] is None and r["counts_toward_20_to_30_on_confirmation"] is False
assert one([(420, .96, .965)])["band"] == 1 and one([(420, .96, .97)])["trades"] == 1 and one([(420, .985, .9951)])["band"] == 1 and one([(420, .985, .995)])["trades"] == 1          # band edges 0.97 and 0.995 inclusive
with tempfile.TemporaryDirectory() as d:          # a close exactly at the cut belongs to the confirmation set (closes before the cut are discovery)
    p = os.path.join(d, "k.sqlite"); mk(p, [("Z", "KXBTC15M", CUT, "yes")], [("Z", CUT - 420, .97, .98, 1, 0)]); r = s.run(p, CUT); assert r["confirmation"]["h0.00"]["n"] == 1 and r["discovery_information_only"]["h0.00"]["n"] == 0
    r = s.run(p, CUT + 1); assert r["confirmation"]["h0.00"]["n"] == 0 and r["discovery_information_only"]["h0.00"]["n"] == 1
print("search1 build 2 tests passed")
