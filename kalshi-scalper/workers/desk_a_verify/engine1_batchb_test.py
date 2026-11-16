import os, sys, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_batchb as B, engine1_driver as D, engine1_enum as N
D.MIN_N = 3; D.MIN_SPD = 2.0
def close(day, i): return calendar.timegm((2026, 9, day, 12, 15 * i, 0))
def alt(day, i, res="yes", ser="KXETH15M"):
    c = close(day, i); return {"series": ser, "ticker": "%s-%d_%d" % (ser, day, i), "close": c, "result": res, "candles": [(c - 300, .89, .90, .9, 1, 10)]}
def btc(day, i, a, b):
    c = close(day, i); return {"series": "KXBTC15M", "ticker": "KXBTC15M-%d_%d" % (day, i), "close": c, "result": "yes", "candles": [(c - 480, a - .01, a + .01, a, 1, 10), (c - 300, b - .01, b + .01, b, 1, 10)]}
days = [1, 2, 3, 4, 5, 6]; shape = {1: 2, 2: 3, 3: 4, 4: 2, 5: 3, 6: 4}
alts = [alt(d, i) for d in days for i in range(shape[d])]
btcs = [btc(d, i, .50, .55) for d in days for i in range(shape[d])]                      # BTC mid up by .05 in every window
idx = B.btc_index(btcs)
assert abs(B.btcmom3(idx[close(1, 0)], close(1, 0) - 300) - 0.05) < 1e-12 and B.btcmom3(idx[close(1, 0)], close(1, 0) - 100) is None
st = D.collections.Counter(); g = B.groups_x(alts[:9], idx, st)
items = g[(300, 18, "favourite", ("btcmom3", "up"))]; assert len(items) == 9 and not any(k[3][1] != "up" for k in g)
assert (300, 2, "cheap", ("btcmom3", "up")) in g and not st                                                   # cheap side at 10c is band 2
nb = [m for m in btcs if m["close"] != close(1, 0)]; st2 = D.collections.Counter(); g2 = B.groups_x(alts[:2], B.btc_index(nb), st2)
assert len(g2[(300, 18, "favourite", ("btcmom3", "up"))]) == 1 and st2["no btc candle"] == 1, st2             # a window with no BTC market is skipped and counted
down = [btc(d, i, .55, .50) for d in days for i in range(shape[d])]; g3 = B.groups_x(alts[:9], B.btc_index(down), st)
assert (300, 18, "favourite", ("btcmom3", "down")) in g3 and (300, 18, "favourite", ("btcmom3", "up")) not in g3
N.RULES_PER_SERIES = 1; B.RULES_PER_SERIES_X = 1                                                              # patched so a z of 5.2 can pass in the tiny fixture
rep = B.run_x({"KXETH15M": alts, "KXBTC15M": btcs, "KXZZZ15M": alts}, prior_m=0, m_full=0)
assert rep["no_split_constant"] == ["KXZZZ15M"] and rep["tries_this_spec"] == 1 and rep["tried_by_series"] == {"KXETH15M": 1}, rep
assert rep["search_passes"] >= 1 and rep["validate_bar_passes"] >= 1, rep
r = [x for x in rep["validate_bar_list"] if x["exit"] == "H" and x["bucket"] == 300 and x["band"] == 18 and x["side"] == "favourite"][0]
assert r["filter"] == ["btcmom3", "up"] and r["n"] == 9 and r["series"] == "KXETH15M" and "income_1c" in r, r
assert "KXBTC15M" not in rep["tried_by_series"]                                                              # Bitcoin itself is never a target
print("ENGB4XBTC OK")
