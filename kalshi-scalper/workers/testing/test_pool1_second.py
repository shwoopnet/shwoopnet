import math, datetime
import pool1_second as m, engine1_perps_second as p
def U(y, mo, d, hh, mi): return int(datetime.datetime(y, mo, d, hh, mi, tzinfo=datetime.timezone.utc).timestamp())
close = lambda a, b, tol=1e-6: abs(a - b) < tol
# H1/H2: a long with a vol scaled target, the hand figures
e = U(2026, 11, 16, 15, 0); a = 0.0005
def cd(mid, sp=0.005): return (mid - sp, mid + sp)
def base():
    s = {}
    for i in range(61):
        t = e - 3600 + 60 * i; mid = 99.995 * (math.exp(a) if i % 2 else 1.0); s[t] = cd(mid)
    s[e] = (99.99, 100.00)
    for k, b in ((1, 100.20), (2, 100.40), (3, 100.60)): s[e + 60 * k] = (b, b + 0.01)
    for k in range(4, 16): s[e + 60 * k] = (100.40, 100.41)
    return s
s = base(); sg = m.sigma(s, e); assert close(sg, 0.0005, 1e-9), sg
f = {e - 86400: 0.0, e + 150: 0.0001}
tr, c = m.rule_trades({"X": s}, {"X": f}, [("X", e, "long")], (2, 1, 15), 0.0002); t = tr[0]
assert t["exit_ts"] == e + 180 and close(t["gross"], 0.0055977) and close(t["funding"], 0.0001, 1e-12) and close(t["net"], 0.0030977), t
tr, c = m.rule_trades({"X": s}, {"X": {e - 86400: 0.0, e + 150: -0.0001}}, [("X", e, "long")], (2, 1, 15), 0.0002); assert close(tr[0]["net"], 0.0032977)   # funding sign
s2 = base(); s2[e + 60] = (99.70, 99.71)
tr, c = m.rule_trades({"X": s2}, {"X": f}, [("X", e, "long")], (2, 1, 15), 0.0002); assert tr[0]["exit_ts"] == e + 60 and close(tr[0]["gross"], -0.0033988), tr
# time stop with no hit: kt 2 reaches +180 only; with kt 100 no hit, time stop at +900 (bid 100.40 x 0.9998)
tr, c = m.rule_trades({"X": s}, {"X": f}, [("X", e, "long")], (2, 2, 15), 0.0002)      # k 2 stop and target 2: target 100.5678 hit at +180 too
assert tr[0]["exit_ts"] == e + 180
# no mark: the time stop candle after the name's last key
s3 = {k: v for k, v in base().items() if k <= e + 600}
assert m.rule_trades({"X": s3}, {"X": f}, [("X", e, "long")], (2, 1, 15), 0.0002)[1]["no_mark"] == 1          # e + 900 is after the last candle: no mark even though the +180 candle would hit
# vol needs 45 returns: remove 20 candles
s4 = base()
for i in range(10, 30): del s4[e - 3600 + 60 * i]
assert m.rule_trades({"X": s4}, {"X": f}, [("X", e, "long")], (2, 1, 15), 0.0002)[1]["no_vol"] == 1
# cooldown: a second entry at e + 120 while the first holds to e + 180 is blocked; one at e + 180 (>= exit end) is allowed (needs its own vol window, sigma from the same series)
for e2, want in ((e + 120, 1), (e + 180, 0)):
    s5 = base(); tr, c = m.rule_trades({"X": s5}, {"X": f}, [("X", e, "long"), ("X", e2, "long")], (2, 1, 15), 0.0002); assert c["blocked"] == want, (e2, c)
# funding not booked: no prints
tr, c = m.rule_trades({"X": s}, {"X": {}}, [("X", e, "long")], (2, 1, 15), 0.0002); assert c["funding_not_booked"] == 1 and tr[0]["funding"] is None and "net" not in tr[0]
# H3 gap
D = {"X": {U(2026, 11, 13, 21, 0): cd(100.00), U(2026, 11, 16, 14, 31): cd(100.50)}}
for cls, n in ((30, 1), (60, 0), (100, 0)): assert len(m.gap_entries(D, cls, "follow", ["X"])[0]) == n
assert m.gap_entries(D, 30, "follow", ["X"])[0] == [("X", U(2026, 11, 16, 14, 31), "long")] and m.gap_entries(D, 30, "fade", ["X"])[0][0][2] == "short"
D2 = {"X": {U(2026, 11, 16, 14, 31): cd(100.50)}}; assert m.gap_entries(D2, 30, "follow", ["X"]) == ([], {"gap_missing": 1})          # no previous 16:00 candle
D3 = {"X": {U(2026, 11, 13, 21, 0): cd(100.00), U(2026, 11, 16, 14, 31): cd(100.50)}}; assert len(m.gap_entries(D3, 30, "follow", ["X"])[0]) == 1          # the latest earlier ET date with a 16:00 key (a Friday over a weekend)
# H4 ranking
e9 = U(2026, 11, 16, 14, 31); one = {"A": {e9: cd(100)}}
def ranked(rates, mode, names=None):
    fund = {n: {e9 - 3600: r} for n, r in rates.items()}; data = {n: {e9: cd(100)} for n in rates}
    return sorted((n, side) for n, _, side in m.rank_entries(data, fund, sorted(rates), "level", mode)[0])
assert ranked({"A": 3e-4, "B": 1e-4, "C": -1e-4, "D": -2e-4}, "fade") == [("A", "short"), ("B", "short"), ("C", "long"), ("D", "long")]
assert ranked({"A": 3e-4, "B": 1e-4, "C": -1e-4}, "follow") == [("A", "long"), ("C", "short")]
assert ranked({"A": 3e-4, "B": 1e-4}, "fade") == []
assert ranked({"B": 1e-4, "A": 1e-4, "C": 0.0}, "fade") == [("A", "short"), ("C", "long")]          # tie by ticker ascending: A is the top
# a print older than 36 h does not count; a print AT the entry does not count
old = {n: {e9 - 36 * 3600 - 1: 1e-4} for n in "ABC"}; assert m.rank_entries({n: {e9: cd(100)} for n in "ABC"}, old, list("ABC"), "level", "fade")[0] == []
at = {n: {e9: 1e-4} for n in "ABC"}; assert m.rank_entries({n: {e9: cd(100)} for n in "ABC"}, at, list("ABC"), "level", "fade")[0] == []
# change signal
fc = {"A": {e9 - 7200: 1e-4, e9 - 3600: 5e-4}, "B": {e9 - 7200: 1e-4, e9 - 3600: 2e-4}, "C": {e9 - 7200: 1e-4, e9 - 3600: 1e-4}, "D": {e9 - 7200: 1e-4, e9 - 3600: -1e-4}, "E": {e9 - 3600: 9e-4}}
got = sorted((n, sd) for n, _, sd in m.rank_entries({n: {e9: cd(100)} for n in fc}, fc, sorted(fc), "change", "fade")[0]); assert got == [("A", "short"), ("B", "short"), ("C", "long"), ("D", "long")], got          # E has no previous print: not ranked
# H5 carry
def carry_world():
    data, fund = {}, {}; rates = {"N1": 6e-4, "N2": -5e-4, "N3": 4e-4, "N4": -3e-4, "N5": 2e-4, "N6": -1e-4}
    T = U(2026, 11, 16, 14, 0)
    for n, r in rates.items():
        fund[n] = {T - 86400: r, T: 0.0}; data[n] = {T - 1800: (99.99, 100.01), T + 1800: (100.09, 100.11)}
    return data, fund, T
data, fund, T = carry_world()
trA, cA = m.carry_trades(data, fund, sorted(data), "A", 0.0002); assert sorted(t["name"] for t in trA) == ["N1", "N2"], trA
trB, cB = m.carry_trades(data, fund, sorted(data), "B", 0.0002); assert sorted((t["name"], t["side"]) for t in trB) == [("N1", "short"), ("N2", "long"), ("N3", "short")]
t1 = [t for t in trB if t["name"] == "N1"][0]; assert t1["e"] == T - 1800 and t1["exit_ts"] == T + 1800
# the receiving short books a received print: print T carries rate 0.0 here, so funding 0; a short with a +rate print is a receipt
fund2 = {n: dict(f) for n, f in fund.items()}; fund2["N1"][T] = 6e-4
t1 = [t for t in m.carry_trades(data, fund2, sorted(data), "A", 0.0002)[0] if t["name"] == "N1"][0]; assert close(t1["funding"], -6e-4, 1e-12)
two = {n: fund[n] for n in ("N1", "N2")}; assert m.carry_trades({n: data[n] for n in two}, two, sorted(two), "A", 0.0002)[0] == []          # fewer than 3 names
z = {n: dict(f) for n, f in fund.items()}; z["N1"][T - 86400] = 0.0; assert "N1" not in [t["name"] for t in m.carry_trades(data, z, sorted(data), "B", 0.0002)[0]]          # a zero last rate never trades
# H6 gate
def mk(i, net, day): return {"name": "X", "e": i, "day": day, "funding": 0.0, "net": net}
seq = [(0.01, 0), (0.01, 0), (-0.01, 0), (0.01, 1), (0.01, 1), (-0.01, 1), (0.01, 2), (0.01, 2), (-0.01, 2), (0.01, 3), (0.01, 3), (-0.01, 3)]
tr = [mk(i, n, d) for i, (n, d) in enumerate(seq)]
ok, info = m.gate(tr, tr, 4); assert ok and close(info["pf_lo"], 2.0, 1e-9) and info["n"] == 12 and close(info["share"], 0.25, 1e-9), info
assert not m.gate(tr, tr, 5)[0]                 # 12 / 5 = 2.4 a day
assert not m.gate(tr[:11], tr[:11], 4)[0]       # 11 / 4 = 2.75 a day
bad = [mk(i, n, d) for i, (n, d) in enumerate([(0.01, 0)] * 8 + [(-0.01, 1)] * 4)]; assert not m.gate(bad, bad, 4)[0]          # first half all wins, second half all losses: the half fails
# a single day carrying more than 30% of the net
lump = [mk(0, 0.05, 0), mk(1, -0.01, 1), mk(2, 0.01, 1), mk(3, -0.01, 2), mk(4, 0.01, 2), mk(5, 0.0, 3)]; ok, info = m.gate(lump, lump, 1); assert info["share"] > 0.3 and not ok
pool = {"A": {U(2026, 11, 9 + d, 15, 0): cd(1) for d in range(5)}}; assert m.pool_names(pool, {"A": {1: 0, 2: 0}}) == ["A"] and m.pool_names(pool, {"A": {1: 0}}) == []
print("pool1 second tests passed")

# round 2 tests (mutation survivors)
# vol: 45 returns pass, 44 fail; a candle before e - 3600 never enters the window
def thin(n_interior, drop0):
    z = base()
    if drop0: del z[e - 3600]
    for i in range(1, n_interior + 1): del z[e - 3600 + 60 * 5 * i]
    return z
assert m.sigma(thin(7, True), e) is not None and m.sigma(thin(8, True), e) is None and m.sigma(thin(8, False), e) is None and m.sigma(thin(7, False), e) is not None          # 45 and 46 returns pass, 44 and 43 fail
sx = base(); sx[e - 3660] = (149.0, 151.0); assert close(m.sigma(sx, e), 0.0005, 1e-9)
# carry cooldown: the second print's entry is exactly the first trade's exit end: allowed
T1 = U(2026, 11, 16, 14, 0); T2 = T1 + 3600
fw = {"N1": {T1 - 86400: 9e-4, T1: 8e-4, T2: 0.0}, "N2": {T1 - 86400: 7e-4, T1: 1e-4, T2: 0.0}, "N3": {T1 - 86400: 2e-4, T1: 1e-4, T2: 0.0}}
dw = {"N1": {T1 - 1800: (99.99, 100.01), T1 + 1800: (100.0, 100.02), T2 + 1800: (100.1, 100.12)}, "N2": {T1 - 1800: (99.99, 100.01), T1 + 1800: (100.0, 100.02)}, "N3": {T1 - 1800: (99.99, 100.01), T1 + 1800: (100.0, 100.02)}}
tr, c = m.carry_trades(dw, fw, sorted(dw), "B", 0.0002); assert sorted((t["name"], t["e"]) for t in tr) == [("N1", T1 - 1800), ("N1", T2 - 1800), ("N2", T1 - 1800)] and c["blocked"] == 0, (tr, c)
# carry net by hand: N1 short at bid 99.99 x 0.9998, leave ask 100.11 x 1.0002 style check on the first carry world
data, fund, T = carry_world(); trA, cA = m.carry_trades(data, fund, sorted(data), "A", 0.0002); t1 = [t for t in trA if t["name"] == "N1"][0]
assert close(t1["net"], (99.99 * 0.9998 - 100.11 * 1.0002) / (99.99 * 0.9998) - 0.0024, 1e-9) and close(t1["net_maker"], t1["gross"] - 0.001, 1e-12)
# carry zero last rate: only 2 names left, the day is skipped
zz = {n: dict(f_) for n, f_ in fund.items() if n in ("N1", "N2", "N3")}; zz["N3"][T - 86400] = 0.0; assert m.carry_trades({n: data[n] for n in zz}, zz, sorted(zz), "B", 0.0002)[0] == []
# gap exactly on the class edge counts
Dg = {"X": {U(2026, 11, 13, 21, 0): cd(100.00), U(2026, 11, 16, 14, 31): cd(100.30)}}; assert len(m.gap_entries(Dg, 30, "follow", ["X"])[0]) == 1
Du = {"X": {U(2026, 11, 13, 21, 0): (100.1, 100.0), U(2026, 11, 16, 14, 31): cd(100.50)}}; assert m.gap_entries(Du, 30, "follow", ["X"]) == ([], {"gap_missing": 1})          # an unusable previous candle skips
# change signal: a previous print more than 60 h before the latest does not count
fc2 = dict(fc); fc2["F"] = {e9 - 3600 - 61 * 3600: 0.0, e9 - 3600: 9e-2}
got = sorted(n for n, _, sd in m.rank_entries({n: {e9: cd(100)} for n in fc2}, fc2, sorted(fc2), "change", "fade")[0]); assert "F" not in got and got == ["A", "B", "C", "D"], got
# gate: each condition alone
def seqn(nets): return [{"name": "X", "e": i, "day": i, "funding": 0.0, "net": x} for i, x in enumerate(nets)]
W, L = 0.5, -0.5
good = seqn([W, W, W, W, W, L, W, W, W, W, L, L]); assert m.gate(good, good, 4)[0]
sec = seqn([W, W, W, W, W, L, W, W, W, L, L, L]); assert not m.gate(sec, sec, 4)[0]          # the second half PF 1.0 is under 1.3
fst = seqn([W, W, W, L, L, L, W, W, W, W, W, L]); assert not m.gate(fst, fst, 4)[0]          # the first half PF 1.0 is under 1.3
flat = seqn([W, L, W, L, W, L, W, L, W, L, W, L]); assert not m.gate(good, flat, 4)[0]          # hi net exactly 0: not positive
spread = seqn([0.04, -0.01] * 6); ok_s, info_s = m.gate(spread, spread, 4); assert ok_s and info_s["share"] < 0.3, info_s
lump = seqn([0.2] + [-0.01, 0.04] + [-0.01, 0.04] * 5)[:12]; ok_l, info_l = m.gate(lump, lump, 4); assert info_l["share"] > 0.3 and not ok_l, info_l          # one day above 30% of the net
days4 = {"A": {U(2026, 11, 9 + d, 15, 0): cd(1) for d in range(4)}}; assert m.pool_names(days4, {"A": {1: 0, 2: 0}}) == []
# round 3: signal 5, the window cut (spec v3.2)
CUT = m.CUTOFF
def series_at(e0, flat_after=True, ramp=True, n_after=1000):
    """candles from e0 - 3600 to e0 + n_after minutes: alternating mids (sigma 0.0005) with an upward ramp over the 30 minutes before e0 (ln 1.004 in total)"""
    s = {}; d = math.log(1.004) / 30
    for i in range(61 + n_after):
        t = e0 - 3600 + 60 * i; lm = math.log(100.0) + a * (i % 2) + (d * min(max(i - 30, 0), 30) if ramp else 0.0)
        mid = math.exp(lm); s[t] = cd(mid, 0.001)
    return s
E1 = U(2026, 11, 16, 15, 31)          # 10:31 ET
S = series_at(E1, n_after=300); Dt = {"X": S}
sg = m.sigma(S, E1); u = sg * math.sqrt(30); R = math.log(m.p.mid(S[E1]) / m.p.mid(S[E1 - 1800]))
assert abs(R) > u and abs(R) < 2 * u, (R, u)          # the hand case shape: R exceeds 1 u but not 2 u
for L, c, mode, want in ((30, 1, "trend", "long"), (30, 1, "rev", "short")):
    cs = m.trend_candidates(Dt, ["X"], L, c, mode)["X"]; assert cs and cs[0][0] == E1 and cs[0][1] == want and all(x[0] >= E1 for x in cs), cs[:2]
assert m.trend_candidates(Dt, ["X"], 30, 2, "trend")["X"] == []          # 2 u is not reached at the first candle
assert m.trend_candidates(Dt, ["X"], 60, 1, "trend")["X"][0][0] == E1          # L = 60 at 10:31 has its lookback exactly at the 09:31 candle: allowed
# window edges: no candidate before 10:31 ET or after 15:30 ET even where the move qualifies
S2 = series_at(U(2026, 11, 16, 15, 30)); assert all(x[0] >= E1 for x in m.trend_candidates({"X": S2}, ["X"], 30, 1, "trend")["X"]) and m.trend_candidates({"X": S2}, ["X"], 30, 1, "trend")["X"][0][0] > U(2026, 11, 16, 15, 30)
E_late = U(2026, 11, 16, 20, 30)          # 15:30 ET: inside; 15:31 outside
S3 = series_at(E_late, n_after=5); cs3 = m.trend_candidates({"X": {**S3, U(2026, 11, 16, 14, 31): cd(100.0)}}, ["X"], 30, 1, "trend")["X"]; assert cs3 and cs3[-1][0] == E_late and max(S3) > E_late, cs3[-2:]
# a lookback before 09:31 ET gives no signal: e = 10:31 ET but the series starts after 09:31 so the L = 60 lookback is missing
S4 = {t: v for t, v in S.items() if t > E1 - 3600}; assert m.trend_candidates({"X": S4}, ["X"], 60, 1, "trend")["X"] == [] or m.trend_candidates({"X": S4}, ["X"], 60, 1, "trend")["X"][0][0] > E1
# cooldown (hand-listed candidates on a long flat series): E1 taken (exit +900), E1 + 60 and E1 + 840 skipped (open position), E1 + 900 taken (e >= exit end)
cs = m.trend_candidates(Dt, ["X"], 30, 1, "trend"); u1 = cs["X"][0][2]; ex = (2, 2, 15)
hand = {"X": [(E1, "long", u1), (E1 + 60, "long", u1), (E1 + 840, "long", u1), (E1 + 900, "long", u1), (E1 + 960, "short", u1)]}
tr, c = m.trend_trades(Dt, {"X": {E1 - 86400: 0.0, E1 + 5400: 0.0}}, hand, ex, 0.0002)
assert [(t["e"] - E1, t["exit_ts"] - E1) for t in tr] == [(0, 900), (900, 1800)], [(t["e"] - E1, t["exit_ts"] - E1) for t in tr]
assert len(cs["X"]) > 1 and all(q[0] < E1 + 900 for q in cs["X"])          # the real series only qualifies inside the first ten minutes
# no mark at the first candle opens nothing and the scan goes on to the next candle
S5 = dict(S); del S5[E1 + 900]
tr, c = m.trend_trades({"X": S5}, {"X": {E1 - 86400: 0.0, E1 + 5400: 0.0}}, m.trend_candidates({"X": S5}, ["X"], 30, 1, "trend"), ex, 0.0002); assert c["no_mark"] >= 1 and tr[0]["e"] == E1 + 60, (tr[0]["e"] - E1, c)
# the cut: entry or exit end at or after 2026-11-17T00:00Z is dropped and counted; the day does not count as a trading date
Ec = CUT - 300; Sc = series_at(Ec, n_after=40)
trc, cc = m.rule_trades({"X": Sc}, {"X": {Ec - 86400: 0.0, Ec + 7200: 0.0}}, [("X", Ec, "long")], (2, 1, 15), 0.0002); assert trc == [] and cc["window_dropped"] == 1          # exit end = CUT + 600
Ec2 = CUT - 1500; Sc2 = series_at(Ec2, n_after=60)
trc, cc = m.rule_trades({"X": Sc2}, {"X": {Ec2 - 86400: 0.0, Ec2 + 7200: 0.0}}, [("X", Ec2, "long")], (2, 1, 15), 0.0002); assert len(trc) == 1 and cc["window_dropped"] == 0          # exit end CUT - 600
Sd = series_at(CUT + 60, n_after=40); trc, cc = m.rule_trades({"X": Sd}, {"X": {CUT - 86400: 0.0, CUT + 7200: 0.0}}, [("X", CUT + 60, "long")], (2, 1, 15), 0.0002); assert trc == [] and cc["window_dropped"] == 1          # an entry at or after the cut
assert m.trading_dates({"X": {CUT + 14 * 3600 + 31 * 60 - 86400 + 86400: cd(1.0)}}) == []          # a 09:31 ET candle on 2026-11-17 is not a trading date (its end is after the cut)
print("pool1 second round 3 tests passed")
