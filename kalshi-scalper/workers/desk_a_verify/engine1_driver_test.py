"""python3 -I engine1_driver_test.py : the driver on invented markets (small MIN_N and rule count so the arithmetic is checkable)."""
import os, sys, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_driver as D, engine1_enum as N, engine1_core as K, engine1_split as S
D.MIN_N = 3; D.MIN_SPD = 2.0     # the 3 a day gate is tested below at its real value
def mk(day, i, res="yes"):
    close = calendar.timegm((2026, 9, day, 12, 15 * i, 0))
    return {"series": "BTC", "ticker": "T%d_%d" % (day, i), "close": close, "result": res, "candles": [(close - 300, .89, .90, .9, 1, 10)]}
sd = [mk(1, i) for i in range(2)] + [mk(2, i) for i in range(3)] + [mk(3, i) for i in range(4)]       # SEARCH days Sep 1 to 3 (last SEARCH date 09-03)
vd = [mk(4, i) for i in range(2)] + [mk(5, i) for i in range(3)] + [mk(6, i) for i in range(4)]       # VALIDATE days Sep 4 to 6
assert all(S.phase("BTC", m["close"]) == "search" for m in sd) and all(S.phase("BTC", m["close"]) == "validate" for m in vd)
# group membership equals the enumerator's own entries() for the rule (300, band 18, favourite, none)
g = D.groups(sd, {300: (1, 1)}); items = g[(300, 18, "favourite", None)]
assert len(items) == 9 and all(N.entries(m["candles"], m["close"], 300, 18, "favourite", None)[0] is not None for m in sd)
assert (300, 2, "cheap", None) in g and (300, 18, "cheap", None) not in g and (300, 18, "favourite", ("spread", "low")) in g and not any(k[3] and k[3][0] == "oi3" for k in g)
# BH on known p-values: m = 10, alpha .05: p sorted .001 .004 .02 .5 -> thresholds .005 .01 .015 .02: passes the first two only
assert D.bh({"a": .001, "b": .004, "c": .02, "d": .5}, 10) == {"a", "b"} and D.bh({"a": .5}, 10) == set() and D.bh({}, 10) == set()
# run: one series; m = RULES_PER_SERIES patched to 1 so a z of 5.2 can pass
N.RULES_PER_SERIES = 1
rep = D.run({"arch": {"BTC": sd + vd, "ZZZ": [mk(1, 0)]}})
assert rep["no_split_constant"] == [("arch", "ZZZ")] and rep["combos_tried_m"] == 1 and rep["tried_by_series"] == {("arch", "BTC"): 1}, rep
assert rep["search_passes"] >= 1 and rep["validate_bar_passes"] >= 1 and rep["validate_passes"] >= 1, rep
sv = [x for x in rep["survivors"] if x["exit"] == "H" and x["bucket"] == 300 and x["band"] == 18 and x["side"] == "favourite" and x["filter"] is None]
assert len(sv) == 1 and sv[0]["n"] == 9 and sv[0]["days"] == 3 and sv[0]["family"].startswith("favourite-late"), sv
# hand value: 1c cash per entry at 10 contracts, paid .91: 10 x .09 - fee(10, .91) = .9 - .06 = .84; nine entries
agg = D.score_group(items, "H")[0][0.01]; assert abs(agg["net"] - 9 * 0.84) < 1e-9 and agg["pf"] == float("inf"), agg
# a loser in VALIDATE makes the rule fail the bar there (PF 1.3 not met when 5 of 9 lose)
bad = [mk(d, i, "no" if (d + i) % 2 else "yes") for d in (4, 5, 6) for i in range(3)]
rep2 = D.run({"arch": {"BTC": sd + bad}}); assert not [x for x in rep2["survivors"] if x["exit"] == "H" and x["band"] == 18 and x["side"] == "favourite" and x["filter"] is None], rep2["survivors"]
# a duplicate ticker in a later source is dropped
rep3 = D.run({"arch": {"BTC": sd + vd}, "nc": {"BTC": sd}}); assert rep3["duplicate_tickers_dropped"] == 9, rep3
assert rep["search_entries_total"] == 18 and rep["search_non_whole_cent_entries"] == 0 and rep["validate_entries_total"] == 18 and rep["validate_non_whole_cent_entries"] == 0, rep      # SEARCH markets only: 9 markets x 2 sides (yes, no), all whole-cent
odd = [dict(m, candles=[(m["close"] - 300, .89, .9049, .9, 1, 10)]) for m in sd]
r4 = D.run({"arch": {"BTC": odd}}); assert r4["search_non_whole_cent_entries"] == 9 and r4["search_entries_total"] == 18 and r4["validate_entries_total"] == 0, r4          # only the YES ask .9049 is not whole-cent; the NO ask 1 - .89 is
bl = rep["validate_bar_list"]; assert len(bl) == rep["validate_bar_passes"] and all(set(x) >= {"series", "bucket", "band", "side", "filter", "exit", "pf_1c", "pf_2c", "n", "days", "p", "family"} for x in bl) and {x["exit"] for x in bl} <= set(N.EXITS), bl[:1]
assert all(0 <= x["p"] <= 1 for x in bl)
# the REAL series strings map to the split keys (Auditor B, blocker 1)
real = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXNATGAS15M", "KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M", "KXSOL15M", "KXNEAR15M", "KXZEC15M", "KXPALLADIUM15M", "KXPLATINUM15M"]
miss = [r for r in real if D.short(r) not in S.LAST_SEARCH]; assert miss == [], miss
assert D.short("KXAUDUSD15M") == "AUDUSD" and "AUDUSD" not in S.LAST_SEARCH and D.short("KXUSDCAD15M") == "USDCAD" and "USDCAD" not in S.LAST_SEARCH and D.short("WTI") == "WTI"
r5 = D.run({"nc": {"KXAUDUSD15M": sd}, "arch": {"KXBTC15M": [dict(m, series="KXBTC15M") for m in sd + vd]}})
assert r5["no_split_constant"] == [("nc", "KXAUDUSD15M")] and list(r5)[0] == "no_split_constant" and r5["tried_by_series"] == {("arch", "KXBTC15M"): 1} and r5["validate_passes"] >= 1, r5
print("ALL OK")

# (Nov 16, the owner) the SEARCH gate of 3 signals a day and the income figure; m is NOT changed by the gate
D.MIN_SPD = 3.0
rg = D.run({"arch": {"BTC": sd + vd}})
assert rg["combos_tried_m"] == 1 and rg["search_passes"] == 0 and rg["validate_bar_list"] == [], rg          # 9 SEARCH entries in 3.03 days = 2.97 a day: dropped, nothing written up, m unchanged
D.MIN_SPD = 2.0
sdays = D.search_days([m["close"] for m in sd]); assert abs(sdays - (2 + 45 / 1440 + 1)) < 1e-9, sdays
vdays = D.validate_days([m["close"] for m in vd], "2026-09-03"); assert abs(vdays - (2 + 12.75 / 24)) < 1e-9, vdays      # Sep 4 00:00 to Sep 6 12:45
inc = D.income(agg, vdays)
assert abs(inc["signals_per_day"] - 9 / vdays) < 1e-9 and abs(inc["edge_cents_per_contract"] - 8.4) < 1e-9 and abs(inc["dollars_week"] - (9 / vdays) * 0.084 * 5 * 7) < 1e-9, inc      # 7.56 / 90 = 0.084 dollars a contract = 8.4 cents
top = rep["validate_bar_list"][0]; assert "income_1c" in top and "income_2c" in top and all(rep["validate_bar_list"][i]["income_1c"]["dollars_week"] >= rep["validate_bar_list"][i + 1]["income_1c"]["dollars_week"] for i in range(len(rep["validate_bar_list"]) - 1))
assert D.income({"n": 0, "net": 0}, 3.0)["dollars_week"] == 0.0
print("INCOME AND GATE OK")
