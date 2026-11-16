import datetime, math, engine1_perps_second as p
def near(a, b, t=1e-9): return abs(a - b) < t
def ts(y, mo, d, h, mi): return int(datetime.datetime(y, mo, d, h, mi, tzinfo=datetime.timezone.utc).timestamp())
# ---- KXHAND (Desk A's published invented series; candle i ends at T0 + 60 i, T0 = Tuesday 2026-11-10 14:50 UTC so that i10 ends 15:00)
T0 = ts(2026, 11, 10, 14, 50); E = lambda i: T0 + 60 * i
mids = {i: 100.00 for i in range(41)}; mids.update({6: 100.02, 7: 100.04, 8: 100.06, 9: 100.08, 11: 100.10, 12: 100.30})
H = {}
for i in range(41):
    H[E(i)] = (round(mids[i] - 0.05, 6), round(mids[i] + 0.05, 6))
H[E(10)], H[E(13)] = (100.00, 100.10), (100.60, 100.70)
one = lambda e: (e, e + 1)
h = 0.0001
tr, c = p.rule_trades(H, None, "none", "long", "T3", h, entry_range=one(E(10)))
assert len(tr) == 1 and near(tr[0]["fill"], 100.11001, 1e-9) and near(tr[0]["exit"], 100.58994, 1e-9) and near(tr[0]["gross"], 0.004794026092, 1e-11) and near(tr[0]["net_taker"], 0.002394026092, 1e-11) and near(tr[0]["net_maker"], 0.004794026092 - 0.0010, 1e-11)
tr, c = p.rule_trades(H, None, "none", "long", "TS15", h, entry_range=one(E(10))); assert near(tr[0]["net_taker"], 0.002394026092, 1e-11) and tr[0]["exit_ts"] == E(13)
tr, c = p.rule_trades(H, None, "none", "short", "TS15", h, entry_range=one(E(10))); assert near(tr[0]["net_taker"], -0.00410032003, 1e-11) and near(tr[0]["exit"], 100.160015, 1e-9) and tr[0]["exit_ts"] == E(11) and near(tr[0]["fill"], 99.99, 1e-12)
tr, c = p.rule_trades(H, None, "none", "short", "T3", h, entry_range=one(E(10))); assert near(tr[0]["net_taker"], -0.00960142014, 1e-11) and near(tr[0]["gross"], -0.00720142014, 1e-11)
tr, c = p.rule_trades(H, None, "none", "long", "T30", h, entry_range=one(E(10))); assert near(tr[0]["exit"], 99.940005, 1e-9) and tr[0]["exit_ts"] == E(40)
tr, c = p.rule_trades(H, None, "none", "long", "T30", h, entry_range=one(E(11))); assert tr == [] and c["no_mark"] == 1
# features at i10: mom1 down, mom3 up, mom5 up, mom15 missing; spread class mid with cuts (9, 10); tod open
f = lambda name, e=E(10), cuts=(9.0, 10.0): p.feature(name, H, e, cuts)
assert [f("mom1_down"), f("mom1_up"), f("mom3_up"), f("mom3_down"), f("mom5_up"), f("mom5_down"), f("mom15_up"), f("mom15_down")] == [True, False, True, False, True, False, None, None]
assert [f("spread_low"), f("spread_mid"), f("spread_high")] == [False, True, False] and abs((100.10 - 100.00) / 100.05 * 1e4 - 9.995) < 1e-3
assert p.spread_cuts({i: (100 - s / 2e4 * 100, 100 + s / 2e4 * 100) for i, s in zip(range(1, 7), [8, 9, 9, 10, 12, 15])}, 0, 99) is not None
sp = {i: (100 - x / 2e4 * 100.0, 100 + x / 2e4 * 100.0) for i, x in zip(range(1, 7), [8, 9, 9, 10, 12, 15])}
cu = p.spread_cuts(sp, 0, 99); assert near(cu[0], 9.0, 1e-6) and near(cu[1], 10.0, 1e-6), cu
# time of day boundaries
for hh, mm, ss, want in ((15, 0, 0, "open"), (14, 29, 59, "pre"), (20, 0, 0, "close"), (21, 0, 0, "post"), (15, 30, 0, "mid"), (8, 59, 59, "post"), (9, 0, 0, "pre"), (14, 30, 0, "open"), (19, 59, 59, "mid"), (20, 59, 59, "close")):
    assert p.tod_class(T0 - 14 * 3600 - 50 * 60 + hh * 3600 + mm * 60 + ss) == want, (hh, mm, ss)
# orb and sess on the same series
assert [p.feature("orb_up", H, E(i), None) for i in (10, 11, 12)] == [False, True, True] and p.feature("orb_down", H, E(11), None) is False
assert [p.feature("sess_high", H, E(i), None) for i in (10, 11, 12, 13, 14)] == [False, True, True, True, False] and [p.feature("sess_low", H, E(i), None) for i in (10, 11, 12, 13)] == [False] * 4
# an empty window is missing: no earlier candle in it
assert p.feature("sess_high", {E(0): H[E(0)]}, E(0), None) is None and p.feature("orb_up", {T0 + 3600: (100.0, 100.1)}, T0 + 3600, None) is None
# cooldown: T3 none at 1 bp relative gives entries i0 and i30 only; T30 one trade and 11 no-mark entries (they do not block)
tr, c = p.rule_trades(H, None, "none", "long", "T3", h); assert [t["e"] for t in tr] == [E(0), E(30)] and all(near(t["net_taker"], -0.00359928, 2e-8) for t in tr)
tr, c = p.rule_trades(H, None, "none", "long", "T30", h); assert [t["e"] for t in tr] == [E(0)] and c["no_mark"] == 11 and near(tr[0]["net_taker"], -0.00359928, 2e-8)
# boundary clip
tr, c = p.rule_trades(H, None, "none", "long", "T30", h, entry_range=one(E(0)), boundary=E(30)); assert tr == [] and c["clipped"] == 1
tr, c = p.rule_trades(H, None, "none", "long", "T30", h, entry_range=one(E(0)), boundary=E(31)); assert len(tr) == 1 and c["clipped"] == 0
# ---- KXHAND2 (Tuesday 2026-11-10; candle i ends 14:40 UTC + i min; mid 100.00 except i60 100.50, i240 99.60, i380 101.00, Wednesday 14:31 102.00)
U0 = ts(2026, 11, 10, 14, 40); G = lambda i: U0 + 60 * i
m2 = {i: 100.00 for i in range(381)}; m2.update({60: 100.50, 240: 99.60, 380: 101.00})
S = {G(i): (round(m2[i] - 0.01, 6), round(m2[i] + 0.01, 6)) for i in range(381)}
wed = ts(2026, 11, 11, 14, 31); S[wed] = (101.99, 102.01)
assert G(380) == ts(2026, 11, 10, 21, 0)
for ex, want in (("T60", 0.0043976806), ("T240", -0.0045978205), ("TC", 0.0093951812), ("TO", 0.0193901825)):
    tr, c = p.rule_trades(S, None, "none", "long", ex, 0.0002, entry_range=one(G(0))); assert len(tr) == 1 and near(tr[0]["gross"], want, 1e-9) and near(tr[0]["fill"], 100.030002, 1e-9), (ex, tr)
# an entry at or after 21:00 has no TC mark; TO from Friday and Saturday is Monday 14:31
tr, c = p.rule_trades(S, None, "none", "long", "TC", 0.0002, entry_range=one(G(380))); assert tr == [] and c["no_mark"] == 1
mon = ts(2026, 11, 16, 14, 31)
assert p.next_open_ts(ts(2026, 11, 13, 16, 0)) == mon and p.next_open_ts(ts(2026, 11, 14, 12, 0)) == mon and p.next_open_ts(ts(2026, 11, 15, 12, 0)) == mon and p.next_open_ts(ts(2026, 11, 10, 22, 0)) == wed and p.next_open_ts(ts(2026, 11, 16, 3, 0)) == ts(2026, 11, 17, 14, 31)
# cooldown: T60 entries at i0 and i60 and later (every 60 minutes); TC: i0 only (the next entry must end at or after 21:00)
tr, c = p.rule_trades(S, None, "none", "long", "T60", 0.0002); assert [t["e"] for t in tr] == [G(0), G(60), G(120), G(180), G(240), G(300)] and c["no_mark"] >= 1
tr, c = p.rule_trades(S, None, "none", "long", "TC", 0.0002); assert [t["e"] for t in tr] == [G(0)]
tr, c = p.rule_trades(S, None, "none", "long", "T240", 0.0002); assert [t["e"] for t in tr] == [G(0)]          # G(240) has no T240 mark (the series ends at G(380))
# ---- funding (KXFUND: Tuesday, every candle 99.99 / 100.01, h 0)
F0 = ts(2026, 11, 10, 20, 50); FS = {F0 + 60 * i: (99.99, 100.01) for i in range(31)}; FS[ts(2026, 11, 10, 21, 10)] = (99.99, 100.01)
fr = {day(F0): 0.0002} if (day := p.day) else None
tr, c = p.rule_trades(FS, None, "none", "long", "T30", 0.0, entry_range=one(F0), funding=fr); assert near(tr[0]["net_taker"], -0.00279998, 1e-9) and near(tr[0]["funding"], 0.0002)
tr, c = p.rule_trades(FS, None, "none", "short", "T30", 0.0, entry_range=one(F0), funding=fr); assert near(tr[0]["net_taker"], -0.00240002, 1e-9) and near(tr[0]["funding"], -0.0002)
tr, c = p.rule_trades(FS, None, "none", "long", "T10", 0.0, entry_range=one(F0), funding=fr); assert near(tr[0]["net_taker"], -0.00259998, 1e-9) and tr[0]["funding"] == 0.0          # exit exactly at 21:00 pays nothing
tr, c = p.rule_trades(FS, None, "none", "long", "T10", 0.0, entry_range=one(F0 + 600), funding=fr); assert near(tr[0]["net_taker"], -0.00259998, 1e-9)          # entered at 21:00: the print is not strictly after
tr, c = p.rule_trades(FS, None, "none", "long", "T30", 0.0, entry_range=one(F0), funding={}); assert len(tr) == 1 and tr[0]["funding"] is None and "net_taker" not in tr[0] and c["funding_not_booked"] == 1 and p.booked(tr) == []
tr, c = p.rule_trades(FS, None, "none", "long", "T30", 0.0, entry_range=one(F0), funding=None); assert c["funding_not_booked"] == 1
# three prints over a weekend: a Friday 20:50 long held to Monday 14:31 crosses Fri, Sat, Sun prints
W0 = ts(2026, 11, 13, 20, 50); mon = ts(2026, 11, 16, 14, 31); WS = {W0: (99.99, 100.01), mon: (99.99, 100.01)}
fw = {day(W0): 0.0001, day(W0) + 1: 0.0002, day(W0) + 2: 0.0004}
tr, c = p.rule_trades(WS, None, "none", "long", "TO", 0.0, entry_range=one(W0), funding=fw); assert len(tr) == 1 and near(tr[0]["funding"], 0.0007)
fw2 = dict(fw); del fw2[day(W0) + 1]
tr, c = p.rule_trades(WS, None, "none", "long", "TO", 0.0, entry_range=one(W0), funding=fw2); assert tr[0]["funding"] is None
# statistics, gate, BH
mk = lambda nets, days: [{"e": i, "day": d, "funding": 0.0, "net_taker": x, "net_maker": x} for i, (x, d) in enumerate(zip(nets, days))]
t = mk([2.0, -1.0, 2.0, -1.0], [0, 0, 1, 1]); s = p.stats(t); assert s["n"] == 4 and s["pf"] == 2.0 and s["h1"] == 2.0 and s["h2"] == 2.0 and s["trade_days"] == 2 and near(s["net"], 2.0)
assert p.stats(t)["z"] is None and p.stats(mk([1.0, 1.0], [0, 1]))["z"] is None and near(p.stats(mk([3.0, -1.0, 1.0, -1.0], [0, 0, 1, 1]))["z"], 1.0)          # day sums 2 and 0: mean 1, sd sqrt 2, se 1
big = mk([2.0, -1.0] * 50, [i // 10 for i in range(100)]); assert p.gate(big, big) is True and p.gate(big[:98], big[:98]) is False and p.gate(mk([2.0, -1.0] * 50, [i // 20 for i in range(100)]), big) is False          # 100 trades on 10 days: n 98 and 5 days fail
assert p.gate(big, mk([1.0, -1.0] * 50, [i // 10 for i in range(100)])) is True and p.gate(big, mk([1.0, -1.01] * 50, [i // 10 for i in range(100)])) is False and p.gate(mk([1.29, -1.0] * 50, [i // 10 for i in range(100)]), big) is False and p.gate(mk([1.3, -1.0] * 50, [i // 10 for i in range(100)]), big) is True
assert near(p.p_upper(0.0), 0.5) and abs(p.p_upper(1.6448536269514722) - 0.05) < 1e-9 and p.p_upper(None) is None
assert p.bh({"a": 0.001, "b": 0.04, "c": 0.5}, 3) == {"a"} and p.bh({"a": 0.001, "b": 0.02, "c": 0.5}, 3) == {"a", "b"} and p.bh({"a": 0.03, "b": 0.03}, 2) == {"a", "b"} and p.bh({"a": 0.026, "b": 0.5}, 2) == set() and p.bh({"a": 0.04}, 1000) == set() and p.bh({"a": 0.00004}, 1000) == {"a"}

# ---- edges found by mutation: cooldown at exactly the previous exit, boundary on a VALIDATE entry, orb and sess edges, zero momentum, distinct cut values, TS no-trigger fallback, missing counts
Fri = ts(2026, 11, 13, 20, 50); Mon = ts(2026, 11, 16, 14, 31); Tue = ts(2026, 11, 17, 14, 31)
TO = {Fri: (99.99, 100.01), Mon: (99.99, 100.01), Tue: (99.99, 100.01)}
tr, c = p.rule_trades(TO, None, "none", "long", "TO", 0.0, funding={d: 0.0 for d in range(day(Fri), day(Tue) + 1)}); assert [t["e"] for t in tr] == [Fri, Mon] and tr[0]["exit_ts"] == Mon and tr[1]["exit_ts"] == Tue          # the entry at exactly the previous exit is allowed
tr, c = p.rule_trades(H, None, "none", "long", "T3", h, entry_range=(E(1), E(2)), boundary=E(0)); assert len(tr) == 1 and c["clipped"] == 0          # a VALIDATE entry is never clipped
ob = {ts(2026, 11, 10, 14, 30): (104.99, 105.01)}; ob.update({ts(2026, 11, 10, 14, 31) + 60 * i: (99.99, 100.01) for i in range(30)}); ob[ts(2026, 11, 10, 15, 1)] = (100.99, 101.01)
ob2 = dict(ob); ob2[ts(2026, 11, 10, 15, 0)] = (100.99, 101.01)          # the entry candle ending 15:00 itself (above everything in 14:31 to 14:59): not allowed before 15:01
assert p.feature("orb_up", ob2, ts(2026, 11, 10, 15, 0), None) is False and p.feature("orb_up", ob, ts(2026, 11, 10, 15, 1), None) is True          # not before 15:01; the 14:30 candle is outside the window
se = {ts(2026, 11, 10, 14, 31): (99.99, 100.01), ts(2026, 11, 10, 14, 32): (100.99, 101.01), ts(2026, 11, 10, 14, 34): (100.99, 101.01)}
assert p.feature("sess_high", se, ts(2026, 11, 10, 14, 34), None) is False and p.feature("sess_low", se, ts(2026, 11, 10, 14, 34), None) is False          # equal to the extreme is neither high nor low
zm = {ts(2026, 11, 10, 14, 50): (99.99, 100.01), ts(2026, 11, 10, 14, 51): (99.99, 100.01)}
assert p.feature("mom1_up", zm, ts(2026, 11, 10, 14, 51), None) is False and p.feature("mom1_down", zm, ts(2026, 11, 10, 14, 51), None) is False          # exactly 0 matches neither
sp2 = {i: (100 - x / 2e4 * 100.0, 100 + x / 2e4 * 100.0) for i, x in zip(range(1, 7), [8, 9, 10, 11, 12, 15])}; cu2 = p.spread_cuts(sp2, 0, 99); assert near(cu2[0], 9.0, 1e-6) and near(cu2[1], 11.0, 1e-6), cu2
q9 = {1: (100 - 9 / 2e4 * 100.0, 100 + 9 / 2e4 * 100.0)}; q11 = {1: (100 - 11 / 2e4 * 100.0, 100 + 11 / 2e4 * 100.0)}
assert [p.feature(n, q9, 1, cu2) for n in ("spread_low", "spread_mid", "spread_high")] == [True, False, False] and [p.feature(n, q11, 1, cu2) for n in ("spread_low", "spread_mid", "spread_high")] == [False, True, False]          # equal to c1 is low, equal to c2 is mid
FL = {E(i): (99.95, 100.05) for i in range(41)}
tr, c = p.rule_trades(FL, None, "none", "long", "TS15", h, entry_range=one(E(0))); assert len(tr) == 1 and tr[0]["exit_ts"] == E(30)          # no trigger: the T30 mark
tr, c = p.rule_trades(H, None, "mom15_up", "long", "T3", h); assert c["missing_feature"] == 15          # i0 to i14 have no candle 15 minutes back
mk2 = lambda nets: [{"e": i, "day": i, "funding": 0.0, "net_taker": x, "net_maker": x} for i, x in enumerate(nets)]
s5 = p.stats(mk2([2.0, 2.0, -1.0, 1.0, 1.0])); assert s5["h1"] == math.inf and near(s5["h2"], 2.0)          # floor(5/2) = 2 in the first half
assert p.gate(mk([2.0, -1.0] * 49 + [2.0], [i // 10 for i in range(99)]), mk([2.0, -1.0] * 49 + [2.0], [i // 10 for i in range(99)])) is False and p.gate(mk([2.0, -1.0] * 50, [i // 12 for i in range(100)]), big) is False          # 99 trades and 9 days fail
nb = [{"e": 1, "day": 0, "funding": None}]; assert p.stats(nb)["n"] == 0
assert len(p.FILTERS) == 21 and len(p.EXITS) == 10 and len(set(p.FILTERS)) == 21
print("engine1 perps second tests passed")
