"""python3 -I engine1_perps_lanes_test.py : hand cases for the lanes 1 and 6 engine (invented numbers, not data)."""
import os, sys, calendar, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_perps_lanes as L, engine1_poolperps as Q, engine1_perps as P
close = lambda a, b, t=1e-9: abs(a - b) < t
# maker fill, long: rests at the entry bid 100.00; tick 0.01; an ask of 100.01 is NOT through; 99.99 is
by = {0: (100.00, 100.02), 60: (99.98, 100.01), 120: (99.97, 99.99), 180: (99.0, 99.02)}
assert L.maker_fill(by, 0, "long", 2, 0.01) == (120, 100.00) and L.maker_fill(by, 0, "long", 1, 0.01) is None
# a short rests at the ask 100.02 and needs a bid at or above 100.03
bys = {0: (100.00, 100.02), 60: (100.02, 100.04), 120: (100.03, 100.05)}
assert L.maker_fill(bys, 0, "short", 2, 0.01) == (120, 100.02) and L.maker_fill(bys, 0, "short", 1, 0.01) is None
# run_leg, maker target: long fill 100, kt 1, u 0.005 -> target 100.5; a bid of 100.50 is not through (needs 100.51)
b = {0: (100.0, 100.1), 60: (100.20, 100.3), 120: (100.50, 100.6), 180: (100.51, 100.6)}
g, tx, why, mk = L.run_leg(b, 0, 100.0, "long", 1, 1, 5, 0.0002, 0.005, 10 ** 6, maker_target=True, tick=0.01)
assert (tx, why, mk) == (180, "target", True) and close(g, 0.005)
g, tx, why, mk = L.run_leg(b, 0, 100.0, "long", 1, 1, 5, 0.0002, 0.005, 10 ** 6, maker_target=False)         # taker target: the bid 100.50 reaches it, leaves at bid x (1 - h)
assert (tx, why, mk) == (120, "target", False) and close(g, 100.50 * (1 - 0.0002) / 100.0 - 1)
b2 = {0: (100.0, 100.1), 60: (99.4, 99.5)}
g, tx, why, mk = L.run_leg(b2, 0, 100.0, "long", 1, 1, 5, 0.0002, 0.005, 10 ** 6, maker_target=True); assert why == "stop" and not mk and close(g, 99.4 * 0.9998 / 100 - 1)
# TT single trade, the spec's hand case shape: ask 100.00, h 0.0002 -> fill 100.02; kt 2, ks 1, u 0.003; bids +1 100.20, +2 100.40, +3 100.70 (target 100.02 x 1.006 = 100.62012)
bt = {0: (99.9, 100.0), 60: (100.20, 100.3), 120: (100.40, 100.5), 180: (100.70, 100.8)}
r = L.single_trade(bt, {}, 0, "long", (2, 1, 3), 0.0002, 0.003, 10 ** 6, "TT")
ex = 100.70 * 0.9998; assert close(r["gross"], ex / 100.02 - 1) and close(r["net"], ex / 100.02 - 1 - 0.0024) and r["why"] == "target" and r["flag"] == "funding not booked"
# ME: maker entry fills (ask 99.98 <= 100.0 - ... use the long case of the first test), fee 5 bp in, 12 bp out
bm = {0: (100.00, 100.02), 60: (99.98, 99.99), 120: (100.30, 100.40), 180: (100.70, 100.8)}
r = L.single_trade(bm, {}, 0, "long", (1, 1, 3), 0.0002, 0.004, 10 ** 6, "ME", 2, 0.01)
assert r["t0"] == 60 and close(r["net"], r["gross"] - 0.0005 - 0.0012), r
assert L.single_trade({0: (100.0, 100.02), 60: (100.0, 100.03)}, {}, 0, "long", (1, 1, 3), 0.0002, 0.004, 10 ** 6, "ME", 2, 0.01) == ("skip", "maker entry not filled")
# MM: target fills as maker, 5 bp in and 5 bp out
bmm = {0: (100.00, 100.02), 60: (99.98, 99.99), 120: (100.30, 100.40), 180: (100.90, 101.0)}
r = L.single_trade(bmm, {}, 0, "long", (1, 1, 3), 0.0002, 0.005, 10 ** 6, "MM", 2, 0.01)
assert r["why"] == "target" and close(r["gross"], 0.005) and close(r["net"], 0.005 - 0.001), r
# funding: a long pays a positive print strictly between entry and exit end
fd = {30: 0.0001, 100: 0.0001, 200: 0.0001, 300: 0.0001}
r = L.single_trade(bt, {k: v for k, v in fd.items()}, 0, "long", (2, 1, 3), 0.0002, 0.003, 10 ** 6, "TT")      # prints 30 and 100 are inside (0, 180)
assert close(r["adj"], -0.0002), r["adj"]
# pair TT: long B ask 50.00, short A bid 100.00, h 0; later A ask 99.00, B bid 50.50: R = 0.01 + 0.01 = 0.02; us 0.005, kt 2 -> target 0.01 reached; 4 taker fees on 1 unit each = 0.0048; net = (0.02 - 0.0048) / 2
cand = {"A": {0: (100.0, 100.2), 60: (98.9, 99.0)}, "B": {0: (49.9, 50.0), 60: (50.5, 50.6)}}
r = L.pair_trade(cand, {}, 0, "B", "A", 2, 1, 3, 0.0, 0.005, 10 ** 6, "TT")
assert r["why"] == "target" and close(r["gross"], 0.02) and close(r["fee"], 0.0048) and close(r["net"], (0.02 - 0.0048) / 2) and close(r["net_units"], 0.0152), r
# pair ME: both legs must fill; A is a short resting at ask 100.2 (needs a later bid >= 100.21), B a long at bid 49.9 (needs a later ask <= 49.89)
ticks = {"A": 0.01, "B": 0.01}
assert L.pair_trade(cand, {}, 0, "B", "A", 2, 1, 3, 0.0, 0.005, 10 ** 6, "ME", 2, ticks) == ("skip", "maker entry not filled (both legs must fill)")
# margin and liquidation: net 0.01 per unit, page max 4.0, 50% of it = 2x: margin 0.5 -> 2 % of margin; liquidation 1/2 - 0.045 = 0.455
mv = L.margin_view([(0.01, ("KXNVDAPERP",))], lambda n: 4.0, None)
assert close(mv["50%"]["mean_pct_of_margin_per_trade"], 2.0) and close(mv["50%"]["mean_liq_distance_pct"], 45.5)
# gold at 17.4x: the Head's example, about 1.28 % of buffer (1/17.4 = 5.747 % minus 4.47 %)
mg = L.margin_view([(0.01, ("KXGOLDPERP",))], lambda n: 34.8, None); assert close(mg["50%"]["mean_liq_distance_pct"], (1 / 17.4 - 0.0447) * 100, 1e-9) and 1.2 < mg["50%"]["mean_liq_distance_pct"] < 1.35
mn = L.margin_view([(0.01, ("KXNVDAPERP",))], lambda n: 50.0, None); assert mn["50%"]["mean_liq_distance_pct"] < 0 and mn["50%"]["no_buffer_names"] == ["KXNVDAPERP"]                                               # 1/25 = 4 % < 4.5 %: no buffer
# a trade that touches a name with no page max is not shown (no default), and its names are listed
mz = L.margin_view([(0.01, ("KXNVDAPERP",)), (0.01, ("KXXOMPERP",))], lambda n: 4.0 if n == "KXNVDAPERP" else None, None)
assert mz["50%"]["trades_shown"] == 1 and mz["50%"]["trades_without_page_max_not_shown"] == 1 and mz["50%"]["names_without_page_max"] == ["KXXOMPERP"] and close(mz["50%"]["mean_pct_of_margin_per_trade"], 2.0)
mz = L.margin_view([(0.01, ("KXXOMPERP",))], lambda n: None, None); assert mz["10%"]["label"] == "no page max, not shown" and mz["10%"]["mean_pct_of_margin_per_trade"] is None
mz = L.margin_view([(0.02, ("A", "B"))], lambda n: 4.0, None)                                                   # a pair: net 0.02 / (1/2 + 1/2 margins at 50% of 4x = 2x) = 2 % of margin
assert close(mz["50%"]["mean_pct_of_margin_per_trade"], 2.0)
# interest credit: a 30 minute hold at 3.5 % APY
ic = L.interest_credit([1800]); assert close(ic["credit_pct_of_margin_per_trade_at_3.5pct_apy"], 3.5 * 1800 / (365 * 86400), 1e-15)
# relative strength: 3 names, A up 1 % over 30 minutes to 10:31 ET, B and C flat
d0 = P.et_day0(calendar.timegm((2026, 11, 9, 17, 0, 0))); e = d0 + 10 * 3600 + 31 * 60; t0 = e - 1800
cs = {"A": {t0: (99.99, 100.01), e: (100.99, 101.01)}, "B": {t0: (99.99, 100.01), e: (99.99, 100.01)}, "C": {t0: (99.99, 100.01), e: (99.99, 100.01)}}
ev = L.rs_events(cs, {"b": ["A", "B", "C"]}, lambda nm, t: 0.002)
assert (e, "A", "long") in ev["rs:30:1:follow"] and (e, "A", "short") in ev["rs:30:1:revert"] and (e, "A", "long") in ev["rs:30:2:follow"]
assert not ev.get("rs:60:1:follow")                                          # no candle 60 minutes back
# pairs: A jumps 3 % at 10:31 ET against a quiet baseline; the cheap leg (C) is long and the rich leg (A) short
cp = {"A": {}, "C": {}}
for k in range(-300, 1):                                                      # one candle a minute from 05:31 to 10:31 ET
    t = e + 60 * k; n = (-1) ** k * 0.01
    cp["A"][t] = (100.0 + n - 0.01 + (3.0 if k == 0 else 0.0), 100.0 + n + 0.01 + (3.0 if k == 0 else 0.0)); cp["C"][t] = (49.99, 50.01)
pe = L.pair_events(cp, {"b": ["A", "C"]})
assert any(x[0] == e and x[3] == "C" and x[4] == "A" for x in pe["pair:120:3"]) and any(x[0] == e for x in pe["pair:240:2"]), {k: len(v) for k, v in pe.items()}
# eligibility: a name with fewer than 5 trading days is dropped and printed; a basket under 3 names is dropped
cc = {n: {d0 + 86400 * i + 600: (99.9, 100.1) for i in range(5)} for n in ("X1", "X2", "X3")}; cc["X4"] = {d0 + 600: (99.9, 100.1)}
kept, dropped = L.eligible(cc, {"b1": ("X1", "X2", "X3", "X4"), "b2": ("X1", "X4")}); assert kept == {"b1": ["X1", "X2", "X3"]} and len(dropped) == 3, (kept, dropped)
# smoke: the whole report on a small synthetic market runs and has every column
random.seed(7); cand, fund = {}, {}
days = [P.et_day0(calendar.timegm((2026, 11, 9 + i, 17, 0, 0))) for i in range(2)]
for nm in ("KXAAA", "KXBBB", "KXCCC"):
    by = {}; px = 100.0
    for dd in days:
        for k in range(9 * 60 + 31, 16 * 60 + 1):
            px *= math.exp(random.gauss(0, 0.0004)); t = dd + k * 60; by[t] = (px * 0.9999, px * 1.0001)
    cand[nm] = by; fund[nm] = {days[0] + 16 * 3600: 0.0001, days[1] + 16 * 3600: 0.0001}
rep = L.evaluate_lanes(cand, fund, lambda n: (None if n == "KXCCC" else 4.0), 6290660, baskets={"b": ("KXAAA", "KXBBB", "KXCCC")}, min_days=1)
assert len(rep["rules"]) == 144 and rep["m_new"] == 144 and "6290804" in rep["header"].replace(",", "").replace(" ", "") or "6290804" in rep["header"].replace(",", ""), rep["header"]
assert all(set(o["columns"]) == ({"TT", "ME2", "ME5"} if o["signal"].startswith("pair") else {"TT", "ME2", "ME5", "MM2", "MM5"}) for o in rep["rules"])
assert all("candidate_blocked_no_page_max" in c and "names_traded_without_page_max" in c for o in rep["rules"] for c in o["columns"].values())
assert any(c["names_traded_without_page_max"] == ["KXCCC"] for o in rep["rules"] for c in o["columns"].values())
assert all("events" in c and c["signals_after_cooldown"] == c["signals"] and c["events"] >= c["signals"] and "maker_only_rule" in c for o in rep["rules"] for c in o["columns"].values())
assert all(len({c["maker_only_rule"] for c in o["columns"].values()}) == 1 for o in rep["rules"])        # the rule-level flag is the same on every column of a rule
print("ENGPERPS LANES OK; header:", rep["header"][:80])
