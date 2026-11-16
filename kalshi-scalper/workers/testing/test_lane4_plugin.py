import calendar, math
import lane4_plugin as m, engine1_perps_second as p
T = lambda *a: calendar.timegm(a)
close = lambda a, b, tol=1e-6: abs(a - b) < tol
def q(b, a): return (b, a)
def first(rule, data, funding=None, under=None, h=0.0002):
    tr, cnt = m.score(rule, data, funding, under or {}, h); return tr, cnt
# A: weekend (Friday 16:00 ET to Monday 09:31 ET), the F3 hand figures; 4 booked prints
fri, mon = T(2026, 11, 6, 21, 0, 0), T(2026, 11, 9, 14, 31, 0)
dA = {"X": {fri: q(100.60, 100.70), mon: q(100.90, 101.00)}}; fA = {"X": {T(2026, 11, 6, 21, 0, 0): 1e-4, T(2026, 11, 7, 21, 0, 0): 1e-4, T(2026, 11, 8, 21, 0, 0): 1e-4, T(2026, 11, 9, 21, 0, 0): 1e-4}}
tr, c = first(("A", "weekend", "long"), dA, fA); t = tr[0]
assert len(tr) == 1 and t["e"] == fri and t["exit_ts"] == mon and close(t["gross"], 0.0015854) and close(t["funding"], 0.0002, 1e-12) and close(t["net_taker"], -0.0010146) and close(t["net_maker"], 0.0015854 - 0.001 - 0.0002)
assert first(("A", "weeknight", "long"), dA, fA)[0] == [] and first(("A", "weekend", "short"), dA, fA)[0][0]["side"] == "short"
# weeknight: Monday 16:00 ET to Tuesday 09:31 ET
monc, tue = T(2026, 11, 9, 21, 0, 0), T(2026, 11, 10, 14, 31, 0); dW = {"X": {monc: q(100.0, 100.1), tue: q(100.2, 100.3)}}
assert len(first(("A", "weeknight", "long"), dW)[0]) == 1 and first(("A", "weekend", "long"), dW)[0] == []
# a Saturday or missing/crossed candle: no trade, a crossed exit is no mark
assert first(("A", "weekend", "long"), {"X": {fri: q(100.60, 100.70), mon: q(101.0, 100.9)}}, fA)[1]["no_mark"] == 1
# B1 (N = 15): the hand figures
d10 = lambda hh, mm: T(2026, 11, 10, hh, mm, 0)
dB = {"X": {d10(14, 31): q(99.99, 100.01), d10(14, 46): q(100.29, 100.31), d10(15, 16): q(100.60, 100.61)}}
fB = {"X": {T(2026, 11, 9, 21, 0, 0): 0.0, T(2026, 11, 10, 21, 0, 0): 0.0}}
tr, c = first(("B1", 15, 20, "follow", "T30"), dB, fB); t = tr[0]
assert len(tr) == 1 and t["side"] == "long" and t["e"] == d10(14, 46) and t["exit_ts"] == d10(15, 16) and close(t["gross"], 0.00249) and close(t["net_taker"], 0.00009)
tr, c = first(("B1", 15, 20, "fade", "T30"), dB, fB); assert tr[0]["side"] == "short" and close(tr[0]["gross"], -0.0035922)
assert first(("B1", 15, 40, "follow", "T30"), dB, fB)[0] == [] and first(("B1", 5, 20, "follow", "T30"), dB, fB)[0] == []          # 30 bp is under 40, and no N = 5 candle
# B2 and B3
dB2 = {"X": {d10(20, 0): q(99.99, 100.01), d10(20, 30): q(99.69, 99.71), d10(21, 1): q(99.50, 99.52)}}
tr, c = first(("B2", 20, "follow", "T1601"), dB2, fB); assert len(tr) == 1 and tr[0]["side"] == "short" and tr[0]["e"] == d10(20, 30) and tr[0]["exit_ts"] == d10(21, 1)
assert first(("B2", 20, "fade", "T1601"), dB2, fB)[0][0]["side"] == "long" and first(("B2", 40, "follow", "T1601"), dB2, fB)[0] == []
tr, c = first(("B3", "long"), dB2, fB); assert len(tr) == 1 and tr[0]["e"] == d10(20, 30)
# C: the funding window, the hand figures (receive side)
T1 = d10(21, 0); dC = {"X": {T1 - 1800: q(100.00, 100.10), T1 + 1800: q(100.18, 100.20)}}; fC = {"X": {T1 - 86400: 0.0004, T1: 0.0003}}
tr, c = first(("C", 30, 30, "receive"), dC, fC); t = tr[0]
assert len(tr) == 1 and t["side"] == "short" and close(t["gross"], -0.0024007) and close(t["funding"], -0.0003, 1e-12) and close(t["net_taker"], -0.0045007), t
assert first(("C", 30, 30, "long"), dC, fC)[0][0]["side"] == "long" and first(("C", 30, 30, "short"), dC, fC)[0][0]["side"] == "short"
assert first(("C", 30, 30, "receive"), dC, {"X": {T1 - 86400: 0.0, T1: 0.0003}})[0] == [] and first(("C", 30, 30, "receive"), dC, {"X": {T1 - 86400: -0.0004, T1: 0.0003}})[0][0]["side"] == "long"
assert m.schedule_T({"X": 1}.get("Y")) == [] and m.schedule_T({5: 0, 3: 0}) == [3 + 86400, 5 + 86400]          # T is the previous print plus 24 h, one per print
# cooldown: two prints an hour apart with x = 15, y = 60: the second entry is inside the first hold
T2 = T1 + 3600; dCC = {"X": {T1 - 900: q(100.0, 100.1), T1 + 3600: q(100.0, 100.1), T2 - 900: q(100.0, 100.1), T2 + 3600: q(100.0, 100.1)}}; fCC = {"X": {T1 - 86400: 1e-4, T2 - 86400: 1e-4, T1: 1e-4, T2: 1e-4}}
tr, c = first(("C", 15, 60, "long"), dCC, fCC); assert c["blocked"] == 1 and len(tr) == 1, (c, len(tr))
# the entry equal to the previous exit end is allowed: T2 - 15 min = T1 + 45 min vs exit T1 + 60 min is blocked; with y = 45 the exit is T1 + 45 min and the entry at the same instant is allowed
dEq = {"X": {T1 - 900: q(100.0, 100.1), T1 + 2700: q(100.0, 100.1), T2 + 2700: q(100.0, 100.1)}}; tr, c = first(("C", 15, 45, "long"), dEq, fCC); assert c["blocked"] == 0 and len(tr) == 2, (c, len(tr))
# A2: the OPENGAP entry with the underlying
mon9, tue10 = T(2026, 11, 9, 21, 0, 0), d10(14, 31)
dG = {"X": {mon9: q(99.99, 100.01), d10(14, 25): q(99.995, 100.005), tue10: q(100.45, 100.55), tue10 + 1800: q(100.80, 100.90), T(2026, 11, 10, 21, 0, 0): q(101.0, 101.1)}}; uG = {"X": {p.et_local_day(tue10): (101.0, 100.0)}}
fG = {"X": {T(2026, 11, 9, 21, 0, 0): 0.0, T(2026, 11, 10, 21, 0, 0): 0.0}}
tr, c = first(("A2", "tuefri", 100, "follow", "T30"), dG, fG, uG); t = tr[0]
assert len(tr) == 1 and t["side"] == "long" and close(t["gross"], 0.0020854) and t["e"] == tue10
assert first(("A2", "tuefri", 100, "fade", "T30"), dG, fG, uG)[0][0]["side"] == "short" and first(("A2", "mon", 100, "follow", "T30"), dG, fG, uG)[0] == []
uG2 = {"X": {p.et_local_day(tue10): (100.6, 100.0)}}          # g = 0.006 - 0 = 60 bp: over 40, under 100
assert len(first(("A2", "tuefri", 40, "follow", "T30"), dG, fG, uG2)[0]) == 1 and first(("A2", "tuefri", 100, "follow", "T30"), dG, fG, uG2)[0] == []
assert first(("A2", "tuefri", 100, "follow", "TC"), dG, fG, uG)[0][0]["exit_ts"] == T(2026, 11, 10, 21, 0, 0)
# boundary: an exit at or after 2026-11-17T00:00Z is dropped and counted; funding not booked is counted
dBd = {"X": {T(2026, 11, 16, 21, 0, 0): q(100.0, 100.1), T(2026, 11, 17, 14, 31, 0): q(100.0, 100.1)}}; fBd = {"X": {T(2026, 11, 16, 21, 0, 0): 0.0, T(2026, 11, 17, 21, 0, 0): 0.0}}
tr, c = first(("A", "weeknight", "long"), dBd, fBd); assert tr == [] and c["boundary"] == 1
tr, c = first(("A", "weekend", "long"), dA, None); assert len(tr) == 1 and tr[0]["funding"] is None and c["funding_not_booked"] == 1 and "net_taker" not in tr[0]
# rules and the gate
assert len(m.rules()) == 101 and m.M_NEW == 101
def mkt(i, net, day): return {"name": "N", "e": i, "day": day, "funding": 0.0, "net_taker": net, "net_maker": net}
good = [mkt(i, 0.01 if i % 4 else -0.004, i // 5) for i in range(100)]
assert m.gate(good, good, "net_taker", 20) and not m.gate(good, good, "net_taker", 40)          # 100 / 40 = 2.5 a day
for kill in (good[:99], [mkt(i, 0.01 if i % 4 else -0.004, i // 20) for i in range(100)]): assert not m.gate(kill, kill, "net_taker", 20), len(kill)
weak = [mkt(i, 0.01 if i % 2 else -0.0095, i // 5) for i in range(100)]; assert not m.gate(weak, weak, "net_taker", 20)          # PF 1.05
bad_half = [mkt(i, -0.01 if i < 50 else 0.02, i // 5) for i in range(100)]; assert not m.gate(bad_half, bad_half, "net_taker", 20)          # the first half is all losses
# round 2
wide = {"X": {mon9: q(99.99, 100.01), d10(14, 25): q(99.995, 100.005), tue10: q(100.0, 101.0), tue10 + 1800: q(100.80, 100.90)}}; uW = {"X": {p.et_local_day(tue10): (100.6, 100.0)}}          # g = 60 bp, half spread fraction 0.00498: 2 x half = 99.5 bp
assert first(("A2", "tuefri", 40, "follow", "T30"), wide, fG, uW)[0] == []
uW2 = {"X": {p.et_local_day(tue10): (101.2, 100.0)}}; assert len(first(("A2", "tuefri", 40, "follow", "T30"), wide, fG, uW2)[0]) == 1          # 120 bp passes both
# A2 on a Monday: the previous day is the Friday (no candle on Saturday and Sunday); the loop walks back to it
fri6, mon9a = T(2026, 11, 6, 21, 0, 0), T(2026, 11, 9, 14, 31, 0)
dM = {"X": {fri6: q(99.99, 100.01), T(2026, 11, 9, 14, 25, 0): q(99.995, 100.005), mon9a: q(100.45, 100.55), mon9a + 1800: q(100.80, 100.90)}}; uM = {"X": {p.et_local_day(mon9a): (101.0, 100.0)}}; fM = {"X": {T(2026, 11, 6, 21, 0, 0): 0.0, T(2026, 11, 9, 21, 0, 0): 0.0}}
assert len(first(("A2", "mon", 100, "follow", "T30"), dM, fM, uM)[0]) == 1 and first(("A2", "tuefri", 100, "follow", "T30"), dM, fM, uM)[0] == []
assert m.trading_days({"X": {T(2026, 11, 16, 14, 31, 0): q(1, 2), T(2026, 11, 17, 14, 31, 0): q(1, 2), T(2026, 11, 10, 14, 31, 0): q(1, 2), T(2026, 11, 10, 14, 32, 0): q(1, 2)}}) == 2          # the cut and only the 09:31 ET candle
# receive uses the LATEST prior rate
fR = {"X": {T1 - 2 * 86400: 0.0004, T1 - 86400: -0.0004, T1: 0.0003}}; assert first(("C", 30, 30, "receive"), dC, fR)[0][0]["side"] == "long"
# gate boundaries: n 100, 10 days, 3 a day (ndays 33 passes at 3.03, 34 fails at 2.94), the halves of each haircut separately
g10 = [mkt(i, 0.01 if i % 4 else -0.004, i // 10) for i in range(100)]; assert len(set(t["day"] for t in g10)) == 10
assert m.gate(g10, g10, "net_taker", 33) and not m.gate(g10, g10, "net_taker", 34) and not m.gate(g10[:99], g10[:99], "net_taker", 33)
g9 = [mkt(i, 0.01 if i % 4 else -0.004, i // 12) for i in range(100)]; assert len(set(t["day"] for t in g9)) == 9 and not m.gate(g9, g9, "net_taker", 33)
assert not m.gate(good, bad_half, "net_taker", 20) and not m.gate(bad_half, good, "net_taker", 20) and m.gate(good, good, "net_taker", 20)
assert m.pf([t["net_taker"] for t in weak]) < 1.3 and m.gate(good, weak, "net_taker", 20)          # the secondary PF only needs 1.0
# BH uses m_carried + 101
seen = []; ob = p.bh; p.bh = lambda pv, mt, q=0.05: (seen.append(mt), ob(pv, mt, q))[1]
m.run({"X": {}}, {}, {}, m_carried=6290660); p.bh = ob; assert seen == [6290761, 6290761], seen
# T is the SCHEDULE (previous print + 24 h), not the day's own print: a print that lands 10 minutes late does not move the window
fLate = {"X": {T1 - 86400: 0.0004, T1 + 600: 0.0003}}; trL, cL = first(("C", 30, 30, "receive"), dC, fLate); assert len(trL) == 1 and trL[0]["e"] == T1 - 1800 and trL[0]["exit_ts"] == T1 + 1800
assert m.schedule_misses(fLate["X"]) == 1 and m.schedule_misses(fC["X"]) == 0 and m.schedule_misses({"X": 1}.get("Y")) == 0
# cash holidays and early closes (forward days): Thanksgiving 2026-11-26 is no ET weekday for the rules, 2026-11-27 closes early
L25, L26, L27 = p.et_local_day(T(2026, 11, 25, 12, 0, 0)), p.et_local_day(T(2026, 11, 26, 12, 0, 0)), p.et_local_day(T(2026, 11, 27, 12, 0, 0))
assert m.next_weekday(L25) == L27 and not m.is_session(L26) and m.is_session(L27)
dH = {"X": {m.et_end(L25, 16, 0): q(100.0, 100.1), m.et_end(L27, 9, 31): q(100.2, 100.3), m.et_end(L26, 9, 31): q(100.4, 100.5), m.et_end(L27, 15, 30): q(100.0, 100.1), m.et_end(L27, 16, 1): q(100.0, 100.1)}}
cut0 = m.CUT; m.CUT = 2 ** 40          # a forward read has a later cut
trH, cH = m.score(("A", "weeknight", "long"), dH, None, {}, 0.0002); assert [(t["e"], t["exit_ts"]) for t in trH] == [(m.et_end(L25, 16, 0), m.et_end(L27, 9, 31))]          # the exit skips the holiday
assert m.score(("B3", "long"), dH, None, {}, 0.0002)[0] == []          # early close day: no B3 or B2
m.CUT = cut0
# EDT and EST days: 16:00 ET is 20:00Z on 2026-10-30 (EDT) and 21:00Z on 2026-11-02 (EST)
L30, L2 = p.et_local_day(T(2026, 10, 30, 12, 0, 0)), p.et_local_day(T(2026, 11, 2, 12, 0, 0))
assert m.et_end(L30, 16, 0) == T(2026, 10, 30, 20, 0, 0) and m.et_end(L2, 16, 0) == T(2026, 11, 2, 21, 0, 0) and m.et_end(L30, 9, 31) == T(2026, 10, 30, 13, 31, 0) and m.et_end(L2, 9, 31) == T(2026, 11, 2, 14, 31, 0)
print("lane4 plugin tests passed")
