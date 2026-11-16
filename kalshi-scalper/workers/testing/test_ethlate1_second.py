import calendar, math
import ethlate1_second as m
T = lambda *a: calendar.timegm(a)
close = T(2026, 11, 2, 15, 0, 0)
def mk(tk, c, res="yes"): return {tk: {"close_ts": c, "result": res}}
# the hand case: YES bid 0.08 ask 0.12
cand = {"K": {close - 120: (0.08, 0.12), close - 60: (0.20, 0.22)}}
es = m.entries(mk("K", close), cand); e = es[0]
assert e["side"] == "yes" and e["a"] == 12 and e["band"] == 2 and e["spread_c"] == 4 and abs(e["raw_ask"] - 0.12) < 1e-12
assert abs(m.cash(e, "H", 0.02, cand) - 8.51) < 1e-9 and abs(m.cash(dict(e, result="no"), "H", 0.02, cand) - (-1.49)) < 1e-9 and abs(m.cash(dict(e, result="void"), "H", 0.02, cand) - (-0.09)) < 1e-9 and abs(m.cash(e, "H", 0.01, cand) - 8.62) < 1e-9
assert abs(m.cash(e, "M60", 0.02, cand) - 0.20) < 1e-9
assert m.cash(e, "M60", 0.02, {"K": {close - 120: (0.08, 0.12)}}) is None and m.cash(e, "M60", 0.02, {"K": {close - 120: (0.08, 0.12), close - 61: (0.20, 0.22)}}) is None          # a missing minute is not replaced; no mark = no entry
assert m.cash(e, "M60", 0.02, {"K": {close - 120: (0.08, 0.12), close - 60: (0.22, 0.20)}}) is None          # an unsellable candle is no mark
# the NO side
cand_no = {"K": {close - 120: (0.88, 0.92), close - 60: (0.77, 0.79)}}; en = m.entries(mk("K", close), cand_no)[0]
assert en["side"] == "no" and en["a"] == 12 and en["band"] == 2 and abs(en["raw_ask"] - 0.12) < 1e-9 and abs(m.cash(en, "M60", 0.02, cand_no) - 0.30) < 1e-9
assert abs(m.cash(dict(en, result="no"), "H", 0.02, cand_no) - 8.51) < 1e-9
# cents, bands, edges
def band_of(bid, ask):
    r = m.entries(mk("K", close), {"K": {close - 120: (bid, ask)}}); return (r[0]["band"], r[0]["a"], r[0]["side"]) if r else None
assert band_of(0.03, 0.0499) == (1, 5, "yes") and band_of(0.03, 0.04) is None and band_of(0.30, 0.64) == (12, 64, "yes") and band_of(0.30, 0.6401) == (13, 65, "yes") and band_of(0.55, 0.64) == (9, 45, "no") and band_of(0.0, 0.1) is None
t2 = m.entries(mk("K", close), {"K": {close - 120: (0.49, 0.50)}})[0]; assert t2["side"] == "yes" and t2["a"] == 50          # yes 50c, no = ceil(51) = 51
t3 = m.entries(mk("K", close), {"K": {close - 120: (0.50, 0.51)}})[0]; assert t3["side"] == "no" and t3["a"] == 50          # yes 51c, no 50c
assert band_of(0.03, 0.97) is None          # yes 97c, no 97c: the cheap side is over 94c
assert m.entries(mk("K", close), {"K": {close - 119: (0.08, 0.12)}}) == []          # only the candle ending exactly at close - 120
assert m.entries(mk("K", close), {"K": {close - 120: (0.12, 0.08)}}) == []
assert m.cents(0.041 - 0.0) == 5 and m.cents(0.04) == 4          # whole cents rounded up
# spread cuts and classes
fe = [{"spread_c": s} for s in (1, 1, 2, 2, 3, 3, 4, 5, 9)]; cuts = m.spread_cuts(fe); assert cuts == (2, 3)
assert [m.klass(e, cuts) for e in fe] == ["low", "low", "low", "low", "mid", "mid", "high", "high", "high"]
# the split: the floor(D/2)-th distinct date
def day_es(days): return [{"day": d, "close_ts": d * 86400, "ticker": "t%d" % d} for d in days]
s, v, last = m.split(day_es(range(10, 29))); assert last == 18 and len(s) == 9 and len(v) == 10          # D = 19: floor(19/2) = 9 days SEARCH
s, v, last = m.split(day_es(range(10, 20))); assert last == 14 and len(s) == 5 and len(v) == 5
# the gate boundaries
base = {"n": 100, "events": 40, "pf2": 1.3, "h1": 1.0, "h2": 1.0, "days": 10, "per_day": 3.0}
assert m.passes(base) and m.passes(dict(base, per_day=0.1), search=False) and not m.passes(dict(base, per_day=0.1))          # 3 a day is a SEARCH gate only
assert not m.passes(dict(base, events=39), search=False)
for kill in ({"events": 39}, {"n": 99}, {"pf2": 1.299}, {"h1": 0.999}, {"h2": 0.999}, {"days": 9}, {"per_day": 2.99}, {"pf2": math.nan}): assert not m.passes(dict(base, **kill)), kill
assert m.bh({"a": 7.9e-9, "b": 0.5}, 6290756) == {"a"} and m.bh({"a": 8e-9}, 6290756) == set() and m.bh({"a": 0.05 / 6290756}, 6290756) == {"a"}
# a rigged run: 20 days x 10 strikes, cheap YES at 10c, nine winners a day (one loser on alternate days)
mkts, cds = {}, {}
for d in range(20):
    for j in range(10):
        c = T(2026, 10, 28 + 0, 15, 0, 0) + d * 86400 + j * 60; tk = "R%02d%02d" % (d, j); loser = (j == 0 and d % 2 == 0)
        mkts[tk] = {"close_ts": c, "result": "no" if loser else "yes"}; cds[tk] = {c - 120: (0.09, 0.10), c - 60: (0.30, 0.32)}
res = m.run(mkts, cds); assert res["entries"] == 200 and res["search_n"] == 100 and res["validate_n"] == 100 and len(res["rules"]) == 96 and res["m"] == 6290756
r = res["rules"][(2, "none", "H")]; assert r[0]["n"] == 100 and r[1]["n"] == 100 and r[0]["per_day"] == 10.0, r
assert (2, "none", "H") in res["search_passes"] and (2, "none", "H") in res["validate_passes"] and (2, "none", "H") in res["survivors"], res["survivors"]
assert (2, "none", "M60") in res["validate_passes"] and (3, "none", "H") not in res["search_passes"] and res["rules"][(3, "none", "H")][0]["n"] == 0
assert res["cuts"] == (1, 1) and res["rules"][(2, "low", "H")][0]["n"] == 100 and res["rules"][(2, "mid", "H")][0]["n"] == 0
# round 2
tie = m.entries(mk("K", close), {"K": {close - 120: (0.45, 0.55)}})[0]; assert tie["side"] == "yes" and tie["a"] == 55 and tie["band"] == 11          # yes 55c = no 55c: a tie goes to YES
assert band_of(0.06, 0.94) == (18, 94, "yes") and band_of(0.05, 0.95) is None and band_of(0.045, 0.941) is None          # a = 94 enters, 95 does not
assert m.entries(mk("K", close), {"K": {close - 120: (0.08, 0.121)}})[0]["spread_c"] == 5          # whole cents rounded UP
cand_f = {"K": {close - 120: (0.08, 0.12), close - 60: (0.02, 0.04)}}; ef = m.entries(mk("K", close), cand_f)[0]
assert abs(m.cash(ef, "M60", 0.02, cand_f) - (10 * 0.01 - 1.40 - 0.09 - m.core.fee_up_order(0.01, 10))) < 1e-9          # the sale floor 0.01
o1 = {"day": 1, "close_ts": 100, "ticker": "Z", "result": "yes", "side": "yes", "raw_ask": 0.10}; o2 = {"day": 1, "close_ts": 200, "ticker": "A", "result": "no", "side": "yes", "raw_ask": 0.10}
st = m.stats([o1, o2], "H", {}, 1); assert abs(st["pf2"] - 8.72 / 1.28) < 1e-9 and abs(st["pf1"] - 8.83 / 1.17) < 1e-9 and st["h1"] == math.inf and st["h2"] == 0.0          # 2c primary; halves by close_ts then ticker (Z before A)
# a rule that passes SEARCH and fails VALIDATE is not a validate pass
mk2 = dict(mkts); mk2 = {tk: dict(v, result=("no" if v["close_ts"] >= T(2026, 10, 28, 15, 0, 0) + 10 * 86400 else v["result"])) for tk, v in mkts.items()}
r2 = m.run(mk2, cds); assert (2, "none", "H") in r2["search_passes"] and (2, "none", "H") not in r2["validate_passes"] and r2["survivors"] == []
# 100 entries from fewer than 40 hourly closes do not pass (the 40 event floor), the same entries from 100 closes do
mk3, cd3 = {}, {}
for d in range(20):
    for j in range(10):
        c = T(2026, 10, 28, 15, 0, 0) + d * 86400 + (0 if j < 5 else 3600); tk = "S%02d%02d" % (d, j); mk3[tk] = {"close_ts": c, "result": "no" if (j == 0 and d % 2 == 0) else "yes"}; cd3[tk] = {c - 120: (0.09, 0.10), c - 60: (0.30, 0.32)}
r3 = m.run(mk3, cd3); assert r3["rules"][(2, "none", "H")][0]["n"] == 100 and r3["rules"][(2, "none", "H")][0]["events"] == 20 and (2, "none", "H") not in r3["search_passes"]
assert res["rules"][(2, "none", "H")][0]["events"] == 100
flags = []; orig_p = m.passes; m.passes = lambda s, search=True: (flags.append(search), orig_p(s, search))[1]
m.run(mkts, cds); m.passes = orig_p; assert False in flags and True in flags
# events = distinct closes of the SCORED trades (Auditor B): an M60 entry with no mark is in neither n nor events
ev_es = [{"day": 1, "close_ts": 1000 * (i % 3 + 1), "ticker": "E%d" % i, "result": "yes", "side": "yes", "raw_ask": 0.10} for i in range(6)]
ev_c = {"E0": {1000 - 60: (0.2, 0.3)}, "E1": {2000 - 60: (0.2, 0.3)}}          # only E0 (close 1000) and E1 (close 2000) have a mark
assert m.stats(ev_es, "M60", ev_c, 1)["events"] == 2 and m.stats(ev_es, "M60", ev_c, 1)["n"] == 2 and m.stats(ev_es, "H", ev_c, 1)["events"] == 3
print("ethlate1 second tests passed")
