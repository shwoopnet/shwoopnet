import calendar, math
import nbatotal_second as m, nbaladder_second as b
O = calendar.timegm((2026, 10, 25, 2, 30, 0)); assert O % 1800 == 0
D9 = O - 9 * 3600
def rung(t, strike, player="P", event="G1", open_time=None, close_time=None, result="yes", occ=None):
    return {"ticker": t, "event": event, "player": player, "strike": strike, "open_time": D9 - 30 * 3600 if open_time is None else open_time, "close_time": O + 3600 if close_time is None else close_time, "occ": O if occ is None else occ, "result": result}
def cd(bid, ask, v=0.0): return (bid, ask, v)
R1 = rung("T-1", 220); O_by = {"G1": O}
cs = {"T-1": {D9 - 60: cd(0.43, 0.45, 4), D9 - 3700: cd(0.46, 0.48, 0), D9 - 600: cd(0.4, 0.5, 6), D9 - 2000: cd(0.4, 0.5, 5), O - 12600: cd(0.50, 0.52)}}
kept, guarded, cnt = m.decisions([R1], cs, O_by, 9); d = kept[0]
assert abs(d["mv"] - (-0.03)) < 1e-9 and d["v1"] == 10 and d["v0"] == 5 and d["age"] == 30 * 3600 and not guarded
assert m.passes(d, "move_down") and not m.passes(d, "move_flat") and m.passes(d, "vol_rising") and m.passes(d, "age_old") and not m.passes(d, "age_young")
c, mk = m.cash(d, "yes", "H", cs); assert abs(c - 5.22) < 1e-9 and not mk
assert abs(m.cash(dict(d, r=dict(R1, result="no")), "yes", "H", cs)[0] - (-4.78)) < 1e-9
c, mk = m.cash(d, "yes", "M35", cs); assert mk and abs(c - (-0.06)) < 1e-9, c
cs2 = {"T-1": {k: v for k, v in cs["T-1"].items() if k != O - 12600}}; c, mk = m.cash(d, "yes", "M35", cs2); assert not mk and abs(c - 5.22) < 1e-9
# the in-play guard: the nearest earlier two-sided candle
g_pass = {"T-1": {D9 - 60: cd(0.43, 0.45), D9 - 4000: cd(0.42, 0.44)}}; g_fail = {"T-1": {D9 - 60: cd(0.43, 0.45), D9 - 4000: cd(0.27, 0.29)}}; g_one = {"T-1": {D9 - 60: cd(0.43, 0.45)}}
assert m.decisions([R1], g_pass, O_by, 9)[1] == [] and len(m.decisions([R1], g_fail, O_by, 9)[1]) == 1 and m.decisions([R1], g_fail, O_by, 9)[0] == [] and len(m.decisions([R1], g_one, O_by, 9)[0]) == 1
g_edge = {"T-1": {D9 - 60: cd(0.43, 0.45), D9 - 4000: cd(0.28, 0.30)}}; assert len(m.decisions([R1], g_edge, O_by, 9)[1]) == 1          # 0.44 - 0.29 = 0.15 exactly
g_just = {"T-1": {D9 - 60: cd(0.43, 0.45), D9 - 4000: cd(0.29, 0.31)}}; assert len(m.decisions([R1], g_just, O_by, 9)[1]) == 0          # 0.14
g_bad = {"T-1": {D9 - 60: cd(0.43, 0.45), D9 - 3000: cd(0.0, 0.0), D9 - 4000: cd(0.42, 0.44)}}; assert len(m.decisions([R1], g_bad, O_by, 9)[1]) == 0          # an unusable candle is not a two-sided candle
# the line is per game across players
rs = [rung("A218", 218, player="P1"), rung("A220", 220, player="P2"), rung("A222", 222, player="P3")]; mids = {"A218": (0.61, 0.63), "A220": (0.50, 0.52), "A222": (0.39, 0.41)}
dd = m.decisions(rs, {t: {D9 - 60: cd(*q)} for t, q in mids.items()}, O_by, 9)[0]; assert {x["r"]["strike"]: x["dist"] for x in dd} == {218: "below", 220: "at", 222: "above"}
# 60 minute move thresholds and anchor window [D - 3780, D - 3600]
def mv_of(a_t, a_q): return m.decisions([R1], {"T-1": {D9 - 60: cd(0.43, 0.45), a_t: a_q}}, O_by, 9)[0][0]["mv"]
assert mv_of(D9 - 3780, cd(0.46, 0.48)) is not None and mv_of(D9 - 3600, cd(0.46, 0.48)) is not None and mv_of(D9 - 3781, cd(0.46, 0.48)) is None and mv_of(D9 - 3599, cd(0.46, 0.48)) is None
assert m.passes({"mv": 0.03 - m.TOL}, "move_up") and m.passes({"mv": -0.03 + m.TOL}, "move_down") and not m.passes({"mv": 0.03 - m.TOL}, "move_flat") and m.passes({"mv": 0.0299}, "move_flat") and not m.passes({"mv": 0.0299}, "move_up")
assert m.passes({"age": 86399}, "age_young") and not m.passes({"age": 86400}, "age_young") and m.passes({"age": 86400}, "age_old")
# volume windows (D - 1800, D] and (D - 3600, D - 1800]
vv = {"T-1": {D9 - 60: cd(0.43, 0.45, 1), D9: cd(0.4, 0.5, 2), D9 - 1800: cd(0.4, 0.5, 8), D9 - 3600: cd(0.4, 0.5, 100), D9 - 1801: cd(0.4, 0.5, 3)}}; dv = m.decisions([R1], vv, O_by, 9)[0][0]; assert dv["v1"] == 3 and dv["v0"] == 11, dv
# the M35 guard: two consecutive two-sided candles in (O - 4 h, O - 3.5 h]
def mg(q1, q2, t1=O - 14000, t2=O - 13900): return m.m35_dropped([R1], {"T-1": {t1: q1, t2: q2}}, O_by)
assert mg(cd(0.39, 0.41), cd(0.55, 0.57)) == {"G1"} and mg(cd(0.39, 0.41), cd(0.54, 0.56)) == {"G1"} and mg(cd(0.39, 0.41), cd(0.53, 0.55)) == set()
assert mg(cd(0.39, 0.41), cd(0.54, 0.56)) == {"G1"} and mg(cd(0.39, 0.41), cd(0.53, 0.55)) == set()          # 0.15 exactly drops, 0.14 does not
assert mg(cd(0.39, 0.41), cd(0.55, 0.57), t1=O - 14400, t2=O - 13900) == set()          # a candle ending at O - 4 h is outside (O - 4 h, ...]
assert mg(cd(0.39, 0.41), cd(0.55, 0.57), t1=O - 14000, t2=O - 12600) == {"G1"} and mg(cd(0.39, 0.41), cd(0.55, 0.57), t1=O - 14000, t2=O - 12599) == set()
assert mg(cd(0.39, 0.41), cd(0.0, 0.0), t2=O - 13900) == set()
# cells and a smoke search; the M35 cells skip a dropped game, the H cells keep it
assert m.N_CELLS == 520 and len(m.CELLS) == 5
cells, cnt, surv = m.search([R1], cs); assert len(cells) == 520 and surv == set() and cells[(9, "H", 0.40, "yes", "none")]["n"] == 1 and cells[(9, "M35", 0.40, "yes", "none")]["n"] == 1 and cells[(4, "H", 0.40, "yes", "none")]["n"] == 0 and cnt["m35_dropped_games"] == 0
cs3 = {"T-1": {**cs["T-1"], O - 14000: cd(0.39, 0.41), O - 13900: cd(0.55, 0.57)}}
cells3, cnt3, _ = m.search([R1], cs3); assert cnt3["m35_dropped_games"] == 1 and cells3[(9, "H", 0.40, "yes", "none")]["n"] == 1 and cells3[(9, "M35", 0.40, "yes", "none")]["n"] == 0
cellsv, _, _ = m.search([R1], cs, validate_h_only=True); assert (9, "M35", 0.40, "yes", "none") not in cellsv and (9, "H", 0.40, "yes", "none") in cellsv
# guarded rungs are counted once per decision time (inplay_guard_9, _5, _4), not per cell
cg, cntg, _ = m.search([R1], g_fail); assert cntg["inplay_guard_9"] == 1 and cntg["inplay_guard_5"] == 0 and cg[(9, "H", 0.40, "yes", "none")]["n"] == 0 and "inplay_skipped" not in cg[(9, "H", 0.40, "yes", "none")]
assert m.m_total() == 6291180 and m.m_total(0) == 520
assert mg(cd(0.395, 0.405), cd(0.395 + 0.15 - 5e-10, 0.405 + 0.15 - 5e-10)) == {"G1"} and mg(cd(0.395, 0.405), cd(0.395 + 0.15 - 2e-9, 0.405 + 0.15 - 2e-9)) == set()          # the 1e-9 tolerance
for close, want in ((O - m.MARK + 120, -0.16), (O - m.MARK + 121, -0.06)):
    got = m.cash(dict(d, r=dict(R1, close_time=close)), "yes", "M35", cs)[0]; assert abs(got - want) < 1e-9, (close, got)          # sale leg 2c at <= 120 s from the mark
assert m.cash(dict(d, r=dict(R1, close_time=O - m.MARK)), "yes", "M35", cs)[1] is False and m.cash(dict(d, r=dict(R1, close_time=O - m.MARK + 1)), "yes", "M35", cs)[1] is True
seen = []; orig_bh = b.bh
b.bh = lambda cells, mt, q=0.05: (seen.append(mt), orig_bh(cells, mt, q))[1]
m.search([R1], cs); m.search([R1], cs, carried=0); b.bh = orig_bh; assert seen == [6291180, 520], seen
assert m.JOINT_M_NEW == 1770 and m.m_total(6290660, m.JOINT_M_NEW) == 6292430 and m.m_total() == 6291180
seen.clear(); b.bh = lambda cells, mt, q=0.05: (seen.append(mt), orig_bh(cells, mt, q))[1]
m.search([R1], cs, m_new=m.JOINT_M_NEW); b.bh = orig_bh; assert seen == [6292430], seen
print("nbatotal second tests passed")
