"""Hand cases for fundx2_events.py: invented numbers only."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fundx2_events as F
A = lambda x, y: abs(x - y) < 1e-9
S0 = F.SEARCH_START
# cut points: 200 SEARCH prints 1..200 (times inside SEARCH); q 5 percent: ceil(10) = 10 -> lower = 10th smallest, upper = 10th largest
pr = [(S0 + 3600 * i, float(i + 1)) for i in range(200)]
lo, hi, n = F.cut_points(pr, 0.05); assert (lo, hi, n) == (10.0, 191.0, 200), (lo, hi, n)
lo, hi, n = F.cut_points(pr, 0.10); assert (lo, hi) == (20.0, 181.0)
# a print after SEARCH_END never enters the cut points (a huge later print changes nothing)
assert F.cut_points(pr + [(F.SEARCH_END + 5, 9999.0)], 0.05) == (10.0, 191.0, 200)
# under MIN_PRINTS: none
assert F.cut_points(pr[:119], 0.05) is None and F.cut_points(pr[:120], 0.05) is not None
# extreme: needs the sign too
assert F.extreme(191.0, (10.0, 191.0, 200)) == 1 and F.extreme(190.9, (10.0, 191.0, 200)) == 0 and F.extreme(10.0, (10.0, 191.0, 200)) == 0 and F.extreme(-3.0, (-3.0, 4.0, 200)) == -1
assert F.extreme(-5.0, (-3.0, 4.0, 200)) == -1 and F.extreme(3.0, (-3.0, 4.0, 200)) == 0 and F.extreme(1.0, None) == 0
# trades: SEARCH prints are 0.001..0.200; the VALIDATE print 0.5 is above the upper cut; hourly rows around it
H = 3600; V0 = F.SEARCH_END
sp = [(S0 + 3600 * i, (i + 1) / 1000.0) for i in range(200)]
rows = [(V0 + k * H, 99.0, 101.0, None, None, None) for k in range(40)]          # flat 99/101
rows[10] = (V0 + 10 * H, 98.0, 100.0, None, None, None); rows[19] = (V0 + 19 * H, 97.0, 99.0, None, None, None)
prints = sp + [(V0 + 5 * H, 0.5)]
tr = F.fundx2_trades({"KXBTCPERP": rows}, {"KXBTCPERP": prints}, (0.05, "fade", 8)); assert len(tr) == 1
t = tr[0]["trade"]; assert t["side"] == -1                           # longs pay, fade = short
assert t["entry_ts"] == V0 + 6 * H and A(t["entry"], 99.0)           # the row AFTER the signal row, the bid (short sells at the bid)
assert t["exit_ts"] == V0 + 14 * H and A(t["exit"], 101.0)           # 8 h later, near touch for a short = the ask
# follow takes the long side on the same print
tf = F.fundx2_trades({"KXBTCPERP": rows}, {"KXBTCPERP": prints}, (0.05, "follow", 8)); assert tf[0]["trade"]["side"] == 1 and A(tf[0]["trade"]["entry"], 101.0)
# the SEARCH window prints no trade in the validate read, and the search read trades only SEARCH prints
assert F.fundx2_trades({"KXBTCPERP": rows}, {"KXBTCPERP": sp}, (0.05, "fade", 8)) == []
# a ticker with under 120 SEARCH prints has no threshold and no trade (counted)
c = {}
import collections; c = collections.Counter()
assert F.fundx2_trades({"KXBTCPERP": rows}, {"KXBTCPERP": sp[:50] + [(V0 + 5 * H, 0.5)]}, (0.05, "fade", 8), cnt=c) == [] and sum(c.values()) == 1
# one position per ticker: a second extreme print inside the hold is skipped
t2 = F.fundx2_trades({"KXBTCPERP": rows}, {"KXBTCPERP": prints + [(V0 + 8 * H, 0.6)]}, (0.05, "fade", 8)); assert len(t2) == 1
# funding booked on prints after the entry up to the exit: the 0.6 print at +8h lies in (entry +6h, exit +14h]
assert A(t2[0]["funding"], 0.6)
# empty prints refuse
try: F.fundx2_trades({"KXBTCPERP": rows}, {}, (0.05, "fade", 8)); assert False
except SystemExit: pass
assert len(F.FUNDX2_CELLS) == 8
print("fundx2: ok")
