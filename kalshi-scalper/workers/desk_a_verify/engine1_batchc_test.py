"""python3 -I engine1_batchc_test.py : hand cases for the batch C features and the rule counts (invented numbers, not data)."""
import os, sys, calendar, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_batchc as C, engine1_enum as N
# rule counts per spec equal the frozen specs' tries
ALL = ["KX%s15M" % x for x in "BTC ETH GOLD DOGE XRP BNB HYPE SOL NEAR ZEC SILVER WTI COPPER NATGAS EURUSD GBPUSD USDJPY PALLADIUM PLATINUM".split()]
cnt = {k: 13 * 18 * 4 * 6 * C.SPECS[k][2] * len(C.wall(k, ALL)) for k in C.SPECS}
assert cnt == {"ENGC1ETHMOM": 303264, "ENGC2OIACC": 320112, "ENGC3TOD": 426816, "ENGC4GOLDX": 151632} and sum(cnt.values()) == 1201824, cnt
assert "KXETH15M" not in C.wall("ENGC1ETHMOM", ALL) and len(C.wall("ENGC4GOLDX", ALL)) == 9 and "KXGOLD15M" not in C.wall("ENGC4GOLDX", ALL)
# oiacc: (oi_e - oi_e-180) - (oi_e-180 - oi_e-360)
e = 10000
mk = lambda a, b, c: {e - 360: (e - 360, .5, .6, None, 1, a), e - 180: (e - 180, .5, .6, None, 1, b), e: (e, .5, .6, None, 1, c)}
assert C.oiacc(mk(100, 110, 130), e) == 10 and C.oiacc(mk(100, 110, 120), e) == 0 and C.oiacc(mk(100, 120, 130), e) == -10
m = mk(100, 110, 130); m[e - 360] = (e - 360, .5, .6, None, 1, None); assert C.oiacc(m, e) is None
m = mk(100, 110, 130); del m[e - 180]; assert C.oiacc(m, e) is None
assert N.cls(10) == "up" and N.cls(0) == "flat" and N.cls(-10) == "down"
# time of day, America/Chicago with DST: 2026-11-09 (CST, UTC-6) and 2026-10-15 (CDT, UTC-5)
t = lambda *a: calendar.timegm(a)
assert C.todct(t(2026, 11, 9, 11, 59, 0)) == "ct00" and C.todct(t(2026, 11, 9, 12, 0, 0)) == "ct06" and C.todct(t(2026, 11, 9, 17, 59, 0)) == "ct06" and C.todct(t(2026, 11, 9, 18, 0, 0)) == "ct12" and C.todct(t(2026, 11, 10, 0, 0, 0)) == "ct18" and C.todct(t(2026, 11, 10, 5, 59, 0)) == "ct18" and C.todct(t(2026, 11, 10, 6, 0, 0)) == "ct00"
assert C.todct(t(2026, 10, 15, 10, 59, 0)) == "ct00" and C.todct(t(2026, 10, 15, 11, 0, 0)) == "ct06"      # CDT: 11:00Z is 06:00 CT
# cross-series: one gold-like market at close 100000, bucket 360 (e = 99640), other market's mid 0.50 at e - 180 and 0.60 at e: up
close = 100000; e = close - 360
cand = [(close - 840 + 60 * i, 0.40, 0.45, 0.42, 1.0, 10.0) for i in range(0, 15)]
cand = [c for c in cand if c[0] != e] + [(e, 0.20, 0.22, 0.21, 1.0, 10.0)]
mkt = {"series": "KXBTC15M", "ticker": "KXBTC15M-X", "close": close, "result": "yes", "candles": sorted(cand)}
oth = {close: {e - 180: (e - 180, .49, .51, 0, 0, 0), e: (e, .59, .61, 0, 0, 0)}}
g = C.groups_c([mkt], "ethmom3", oth)
assert (360, 4, "cheap", ("ethmom3", "up")) in g and (360, 4, "yes", ("ethmom3", "up")) in g and not any(k[3][1] != "up" for k in g), sorted(g)[:3]       # yes ask 0.22 -> 22c, band 22 // 5 = 4
st = collections.Counter(); g2 = C.groups_c([mkt], "ethmom3", {close: {e: (e, .59, .61, 0, 0, 0)}}, st); assert not g2 and st["missing feature"] >= 1      # a missing e - 180 candle: no entry, counted
g3 = C.groups_c([mkt], "todct", None); assert all(k[3][0] == "todct" for k in g3) and {k[3][1] for k in g3} == {C.todct(e)}
print("ENGINE1 BATCH C OK")
