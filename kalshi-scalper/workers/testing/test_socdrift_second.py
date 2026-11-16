import calendar
import socdrift_second as m, nbaladder_second as b
T = lambda *a: calendar.timegm(a)
EV = "KXEPLGAME-26OCT04ARSCHE"; O = T(2026, 10, 4, 19, 30, 0); K = O - 3 * 3600
assert K == T(2026, 10, 4, 16, 30, 0)
D6, D12, D24, MH, KH = T(2026, 10, 4, 10, 0, 0), T(2026, 10, 4, 4, 0, 0), T(2026, 10, 3, 16, 0, 0), T(2026, 10, 4, 14, 0, 0), T(2026, 10, 4, 16, 0, 0)
def rung(out="ARS", event=EV, occ=None, open_time=None, close_time=None, result="yes"):
    return {"ticker": "%s-%s" % (event, out), "event": event, "outcome": out, "open_time": T(2026, 9, 30, 0, 0, 0) if open_time is None else open_time, "close_time": O + 2 * 3600 if close_time is None else close_time, "occ": O if occ is None else occ, "result": result}
def cd(bid, ask, v=0.0): return (bid, ask, v)
H = rung(); tk = H["ticker"]
cs = {tk: {D6: cd(0.46, 0.48, 5), T(2026, 10, 4, 4, 0, 0): cd(0.43, 0.45), T(2026, 10, 4, 3, 0, 0): cd(0.40, 0.42), T(2026, 10, 4, 9, 0, 0): cd(0.4, 0.5, 4), T(2026, 10, 4, 8, 0, 0): cd(0.4, 0.5, 3), T(2026, 10, 4, 7, 0, 0): cd(0.4, 0.5, 2), T(2026, 10, 4, 6, 0, 0): cd(0.4, 0.5, 2), T(2026, 10, 4, 5, 0, 0): cd(0.4, 0.5, 2), MH: cd(0.52, 0.54)}}
O_by, c0 = m.games([H]); assert O_by == {EV: O} and c0 == {"clock_dropped_games": 0}
assert m.floor_hour(K - 6 * 3600) == D6 and m.floor_hour(K - 12 * 3600) == D12 and m.floor_hour(K - 24 * 3600) == D24 and m.floor_hour(K - 2 * 3600) == MH and m.floor_hour(K) == KH
dec, cnt = m.decisions([H], cs, O_by, 6); d = dec[0]
assert d["D"] == D6 and d["Mh"] == MH and abs(d["mv"] - 0.03) < 1e-9 and d["v1"] == 12 and d["v0"] == 6 and not d["tie"] and abs(d["spread"] - 0.02) < 1e-9, d
assert m.passes(d, "move_up") and not m.passes(d, "move_down") and not m.passes(d, "move_flat") and m.passes(d, "spread2") and m.passes(d, "spread4") and m.passes(d, "vol_rise") and not m.passes(d, "vol_notrise") and m.passes(d, "team") and not m.passes(d, "tie")
assert abs(m.cash(d, "yes", "H", cs)[0] - 4.92) < 1e-9 and abs(m.cash(dict(d, r=dict(H, result="no")), "yes", "H", cs)[0] - (-5.08)) < 1e-9
c, mk = m.cash(d, "yes", "M2", cs); assert mk and abs(c - (-0.16)) < 1e-9, c
cs2 = {tk: {k: v for k, v in cs[tk].items() if k != MH}}; c, mk = m.cash(d, "yes", "M2", cs2); assert not mk and abs(c - 4.92) < 1e-9
assert not m.cash(dict(d, r=dict(H, close_time=MH)), "yes", "M2", cs)[1] and m.cash(dict(d, r=dict(H, close_time=MH + 1)), "yes", "M2", cs)[1]          # close_time must be later than Mh
assert not m.cash(dict(d, D=MH), "yes", "M2", cs)[1]          # and Mh later than D
assert m.cash(dict(d, r=dict(H, close_time=D6 + 120)), "yes", "H", cs)[0] != m.cash(dict(d, r=dict(H, close_time=D6 + 121)), "yes", "H", cs)[0]
# close - D <= 120: entry 2c (paid 0.50, fee ceil(17.5) = 18): 10 - 5.00 - 0.18 = 4.82
assert abs(m.cash(dict(d, r=dict(H, close_time=D6 + 120)), "yes", "H", cs)[0] - 4.82) < 1e-9
# and the exit haircut follows the entry's 2c: M2 with close - D <= 120 needs close > Mh, so use close - Mh <= 120 instead: sale 2c
c, mk = m.cash(dict(d, r=dict(H, close_time=MH + 120)), "yes", "M2", cs); assert mk and abs(c - (10 * 0.50 - 4.90 - 0.18 - m.core.fee_up_order(0.50, 10))) < 1e-9, c
c, mk = m.cash(dict(d, r=dict(H, close_time=MH + 121)), "yes", "M2", cs); assert mk and abs(c - (-0.16)) < 1e-9
assert abs(m.cash(d, "yes", "H", cs, "two")[0] - (10 - 5.0 - 0.18)) < 1e-9 and abs(m.cash(d, "yes", "H", cs, "weekly", 5)[0] - (5 - 2.45 - m.core.fee_up_order(0.49, 5))) < 1e-9
# the clock check
assert m.games([rung(occ=O + 600)])[0] == {} and m.games([rung(occ=O + 900)])[0] != {} and m.games([rung(), rung("TIE", occ=O + 900)])[0] == {}
far = rung(occ=T(2026, 10, 7, 1, 0, 0)); assert m.games([far])[0] == {} and m.games([rung(occ=T(2026, 10, 6, 0, 0, 0))])[0] != {} and m.games([rung(occ=T(2026, 10, 6, 0, 15, 0))])[0] == {}          # 2 days from midnight Oct 4 is Oct 6 00:00
assert m.ticker_midnight(EV) == T(2026, 10, 4, 0, 0, 0)
# bands
for ask, band, want in ((0.10, (0.10, 0.25), True), (0.25, (0.10, 0.25), False), (0.25, (0.25, 0.40), True), (0.85, (0.70, 0.85), True), (0.8501, (0.70, 0.85), False), (0.70, (0.55, 0.70), False), (0.70, (0.70, 0.85), True), (0.0999, (0.10, 0.25), False)): assert m.in_band(ask, band) == want, (ask, band)
# decisions: not_open, closed_by_D, no_quote, anchor and entry windows
assert m.decisions([dict(H, open_time=D6 + 1)], cs, O_by, 6)[1]["not_open"] == 1 and len(m.decisions([dict(H, open_time=D6)], cs, O_by, 6)[0]) == 1 and m.decisions([dict(H, close_time=D6)], cs, O_by, 6)[1]["closed_by_D"] == 1
assert m.decisions([H], {tk: {D6 - 3600: cd(0.46, 0.48)}}, O_by, 6)[1]["no_quote"] == 1 and m.decisions([H], {tk: {D6 - 3599: cd(0.46, 0.48)}}, O_by, 6)[0][0]["t"] == D6 - 3599
anc = lambda t: m.decisions([H], {tk: {D6: cd(0.46, 0.48), t: cd(0.43, 0.45)}}, O_by, 6)[0][0]["mv"]
assert anc(D6 - 6 * 3600) is not None and anc(D6 - 6 * 3600 - 1) is not None and anc(D6 - 7 * 3600) is None and anc(D6 - 7 * 3600 + 1) is not None and anc(D6 - 6 * 3600 + 1) is None
vv = {tk: {D6: cd(0.46, 0.48, 1), D6 - 3 * 3600: cd(0.4, 0.5, 8), D6 - 3 * 3600 + 1: cd(0.4, 0.5, 2), D6 - 6 * 3600: cd(0.4, 0.5, 100), D6 - 6 * 3600 + 1: cd(0.4, 0.5, 4)}}; dv = m.decisions([H], vv, O_by, 6)[0][0]; assert dv["v1"] == 3 and dv["v0"] == 12, dv
tie = rung("TIE"); assert m.decisions([tie], {tie["ticker"]: {D6: cd(0.46, 0.48)}}, O_by, 6)[0][0]["tie"] is True
for mv, want in ((-0.02, "move_down"), (0.02, "move_up"), (0.0, "move_flat"), (0.0199, "move_flat"), (-0.0199, "move_flat")): assert [f for f in ("move_down", "move_flat", "move_up") if m.passes({"mv": mv}, f)] == [want], mv
assert m.passes({"spread": 0.02}, "spread2") and not m.passes({"spread": 0.0201}, "spread2") and m.passes({"spread": 0.04}, "spread4") and not m.passes({"spread": 0.0401}, "spread4") and m.passes({"v1": 3, "v0": 3}, "vol_notrise")
# live guard: Kh and Kh - 1 h on any outcome
lg = {tk: {KH - 3600: cd(0.33, 0.35), KH: cd(0.49, 0.51)}}; assert m.live_guard([H], lg, O_by) == {EV} and m.live_guard([H], {tk: {KH - 3600: cd(0.35, 0.37), KH: cd(0.49, 0.51)}}, O_by) == set() and m.live_guard([H], {tk: {KH - 7200: cd(0.1, 0.12), KH: cd(0.49, 0.51)}}, O_by) == set()
lg2 = {tk: {KH - 3600: cd(0.33, 0.35)}, EV + "-TIE": {KH - 3600: cd(0.1, 0.12), KH: cd(0.3, 0.32)}}; assert m.live_guard([H, rung("TIE")], lg2, O_by) == {EV}          # any outcome of the game
# m2 guard per D: consecutive two-sided candles in (D, Mh]
mg = lambda off, c: m.m2_guard([H], {tk: c}, O_by, off)
big = {T(2026, 10, 4, 11, 0, 0): cd(0.39, 0.41), T(2026, 10, 4, 12, 0, 0): cd(0.55, 0.57)}
assert mg(6, big) == {EV} and mg(6, {T(2026, 10, 4, 11, 0, 0): cd(0.39, 0.41), T(2026, 10, 4, 12, 0, 0): cd(0.54, 0.56)}) == {EV} and mg(6, {T(2026, 10, 4, 11, 0, 0): cd(0.39, 0.41), T(2026, 10, 4, 12, 0, 0): cd(0.535, 0.555)}) == set()
assert mg(6, {D6: cd(0.39, 0.41), T(2026, 10, 4, 11, 0, 0): cd(0.55, 0.57)}) == set()          # a candle ending at D is outside (D, Mh]
assert mg(6, {MH: cd(0.55, 0.57), T(2026, 10, 4, 13, 0, 0): cd(0.39, 0.41)}) == {EV} and mg(6, {MH: cd(0.55, 0.57), MH + 3600: cd(0.39, 0.41)}) == set()          # Mh included, after Mh not
assert mg(12, {T(2026, 10, 4, 8, 0, 0): cd(0.2, 0.22), T(2026, 10, 4, 9, 0, 0): cd(0.5, 0.52)}) == {EV} and mg(6, {T(2026, 10, 4, 8, 0, 0): cd(0.2, 0.22), T(2026, 10, 4, 9, 0, 0): cd(0.5, 0.52)}) == set()          # per D
# cells, divisor, header and a smoke search
assert m.N_CELLS == 600 and abs(m.DAYS_WINDOW - 42.1203588) < 1e-6 and m.m_total() == 6291260 and m.m_total(6290660, 1770) == 6292430
cells, cnt, surv = m.search([H], cs); assert len(cells) == 600 and surv == set() and cells[(6, "H", 0.40, "yes", "none")]["n"] == 1 and cells[(6, "M2", 0.40, "yes", "none")]["n"] == 1 and cells[(24, "H", 0.40, "yes", "none")]["n"] == 0 and cells[(12, "H", 0.40, "yes", "none")]["n"] == 1 and cnt["no_quote_24h"] == 1 and cnt["live_guard_dropped_m2"] == 0
cl = {**cs, tk: {**cs[tk], KH - 3600: cd(0.33, 0.35), KH: cd(0.49, 0.51)}}; cells_l, cnt_l, _ = m.search([H], cl); assert cnt_l["live_guard_dropped_m2"] == 1 and cells_l[(6, "H", 0.40, "yes", "none")]["n"] == 1 and cells_l[(6, "M2", 0.40, "yes", "none")]["n"] == 0
cg = {**cs, tk: {**cs[tk], T(2026, 10, 4, 11, 0, 0): cd(0.39, 0.41), T(2026, 10, 4, 12, 0, 0): cd(0.55, 0.57)}}; cells_g, cnt_g, _ = m.search([H], cg); assert cnt_g["m2_dropped_games"] == 1 and cells_g[(6, "M2", 0.40, "yes", "none")]["n"] == 0 and cells_g[(6, "H", 0.40, "yes", "none")]["n"] == 1
assert abs(cells[(6, "H", 0.40, "yes", "none")]["weekly5"] - (5 - 2.45 - m.core.fee_up_order(0.49, 5)) / (m.DAYS_WINDOW / 7)) < 1e-9
seen = []; ob = b.bh; b.bh = lambda c, mt, q=0.05: (seen.append(mt), ob(c, mt, q))[1]
m.search([H], cs); m.search([H], cs, m_new=1770); b.bh = ob; assert seen == [6291260, 6292430], seen
e2 = 0.02 - m.TOL; assert m.passes({"mv": e2}, "move_up") and not m.passes({"mv": e2}, "move_flat") and m.passes({"mv": -e2}, "move_down") and not m.passes({"mv": -e2}, "move_flat")
assert not m.passes({"v1": 3, "v0": 3}, "vol_rise") and m.passes({"v1": 3, "v0": 3}, "vol_notrise")
mid_pair = lambda diff: {T(2026, 10, 4, 11, 0, 0): cd(0.395, 0.405), T(2026, 10, 4, 12, 0, 0): cd(0.395 + diff, 0.405 + diff)}
assert mg(6, mid_pair(0.15 - 5e-10)) == {EV} and mg(6, mid_pair(0.15 - 2e-9)) == set()          # the 1e-9 tolerance of the M2 guard
lgp = lambda diff: {tk: {KH - 3600: cd(0.395, 0.405), KH: cd(0.395 + diff, 0.405 + diff)}}
assert m.live_guard([H], lgp(0.15 - 5e-10), O_by) == {EV} and m.live_guard([H], lgp(0.15 - 2e-9), O_by) == set()          # and of the live guard
print("socdrift second tests passed")
