"""Hand case P1 to P7 of FIT_POLISH_NOTE_NOV14.md (invented numbers, no Kalshi data). Run: python3 -I test_fit_polish.py"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import socderiv2_model as M

def mids(lh, la, lines):
    return list(M.winner_probs(lh, la)), [(L, M.p_total_over(lh, la, L)) for L in lines]

def refine_only(wm, tm):
    real = M.polish
    M.polish = lambda lh, la, v, *_: (lh, la, v, 0, False, False)
    try:
        return M.fit(wm, tm)
    finally:
        M.polish = real

def grad(lh, la, wm, tm, h=1e-6):
    return ((M.sse(lh + h, la, wm, tm) - M.sse(lh - h, la, wm, tm)) / (2 * h), (M.sse(lh, la + h, wm, tm) - M.sse(lh, la - h, wm, tm)) / (2 * h))

L3 = (1.5, 2.5, 3.5)
# P1 exact data
wm, tm = mids(1.37, 0.83, L3); a, b, v, it, cap, ob = M.fit(wm, tm)
assert abs(a - 1.37) < 1e-9 and abs(b - 0.83) < 1e-9 and v < 1e-20 and not cap and it < 200 and not ob, (a, b, v, it, cap, ob)
# P2 noisy data
wm2 = [wm[0] + 0.012, wm[1] - 0.007, wm[2] - 0.005]; tm2 = [(L, m + e) for (L, m), e in zip(tm, (0.009, -0.011, 0.004))]
a2, b2, v2, it2, cap2, ob2 = M.fit(wm2, tm2); v2r = refine_only(wm2, tm2)[2]
g = grad(a2, b2, wm2, tm2)
assert abs(g[0]) < 1e-10 and abs(g[1]) < 1e-10 and v2 <= v2r and not cap2 and it2 < 200 and not ob2, (g, v2, v2r, it2, cap2)
# P3 grid-off valley
wm3, tm3 = mids(2.9137, 0.4071, L3); a3, b3, _, it3, cap3, ob3 = M.fit(wm3, tm3)
assert abs(a3 - 2.9137) < 1e-9 and abs(b3 - 0.4071) < 1e-9 and not cap3 and it3 < 200 and not ob3, (a3, b3, it3, cap3)
# P5 cap forced to 1
M.POLISH_CAP = 1
r5 = M.fit(wm2, tm2)
assert r5[3] == 1 and r5[4] is True and r5[2] <= v2r, r5
M.POLISH_CAP = 200
# P6 40-goal sums at (4.0, 0.5)
h6, d6, a6 = M.winner_probs(4.0, 0.5)
def pm(l, n): return math.exp(-l) * l ** n / math.factorial(n)
home_ref = math.fsum(pm(0.5, j) * pm(4.0, i) for j in range(81) for i in range(j + 1, 81))
assert abs(h6 + d6 + a6 - 1) < 1e-15 and abs(h6 - home_ref) < 1e-15, (h6 + d6 + a6, h6 - home_ref)
# P7 P(total <= 2) at 2.2: an exact partial sum, unchanged from MAXG 20
assert abs(M.cdf(2.2, 2) - math.fsum(pm(2.2, n) for n in range(3))) < 1e-16
# B1 to B3: the box edge (the Head's final spec 07:10Z)
wb1, tb1 = mids(0.01, 1.2, L3); r = M.fit(wb1, tb1)
assert r[0] == 0.01 and abs(r[1] - 1.2) < 1e-9 and r[5] is True and r[2] < 1e-20 and not r[4], r
for true_, lo_hi in (((0.003, 1.5), 0.01), ((6.4, 0.8), 6.0)):
    wb, tb = mids(*true_, L3); r = M.fit(wb, tb)
    gy = (M.sse(r[0], r[1] + 1e-6, wb, tb) - M.sse(r[0], r[1] - 1e-6, wb, tb)) / 2e-6
    assert r[0] == lo_hi and r[5] is True and abs(gy) < 1e-10 and not r[4], (true_, r, gy)
print("B1 to B3: ok")
print("P1 to P7: ok; iterations", it, it2, it3, "flags", M.POLISH_FLAGS)

# per-game format (the Head's 02:59Z spec, 06:32Z settlement): booleans True/False, floats repr, blanks empty, fixed column order
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import socderiv2 as S2
p = os.path.join(tempfile.mkdtemp(), "x.csv")
S2.write_pergame(p, [dict(game_key="KXEPLGAME-X", fit_iters=2, cap_hit=False, rate_home=1.37, rate_away=0.1 + 0.2, sse=1e-20, leg_ticker="L", leg_type="btts", strike="",
                          model_value=0.5, market_mid=0.49, gap=0.5 - 0.49, side="yes", edge=0.5 - 0.42, fires=True),
                     dict(game_key="KXEPLGAME-X", fit_iters="", cap_hit="", rate_home="", rate_away="", sse="", leg_ticker="M", leg_type="team_total", strike=1.5,
                          model_value="", market_mid="", gap="", side="", edge="", fires=False)])
assert open(p).read() == ("game_key,fit_iters,cap_hit,rate_home,rate_away,sse,leg_ticker,leg_type,strike,model_value,market_mid,gap,side,edge,fires\n"
                          "KXEPLGAME-X,2,False,1.37,0.30000000000000004,1e-20,L,btts,,0.5,0.49,0.010000000000000009,yes,0.08000000000000002,True\n"
                          "KXEPLGAME-X,,,,,,M,team_total,1.5,,,,,,False\n")
print("per-game format: ok")
