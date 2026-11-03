import sys
sys.path.insert(0, "src")
from scalper import ladderarb1 as L

# smooth ladder: asks 0.40,0.30,0.20,0.10,0.05 (YES, strikes above spot), bids 1c under
def mk(asks):
    return {100.0 + 10 * i: (a - 0.01, a) for i, a in enumerate(asks)}
assert L.kink_triggers(mk([0.60, 0.40, 0.30, 0.20, 0.12, 0.07])) == []
# kink: middle ask 0.05 between 0.30 and 0.30 -> hat 0.30, ratio 6 -> fires on the Y side
q = mk([0.60, 0.40, 0.30, 0.05, 0.30, 0.20, 0.10])
t = [x for x in L.kink_triggers(q) if x[1] == "Y"]
assert len(t) == 1 and t[0][0] == 130.0 and abs(t[0][3] - 0.30) < 1e-9
# ask outside the band never triggers (2c, 31c)
assert L.kink_triggers(mk([0.9, 0.9, 0.02, 0.9, 0.9])) == []
# ratio exactly 3x triggers, just under does not
assert L.kink_triggers(mk([0.30, 0.30, 0.09, 0.30, 0.30]))  # 0.1 is a float edge (3*0.1 > 0.3), documented, not relied on
assert not [x for x in L.kink_triggers(mk([0.30, 0.30, 0.11, 0.30, 0.30])) if x[1] == "Y"]
# arb: ask(100) 0.20 <= bid(110) 0.25
qa = {100.0: (0.18, 0.20), 110.0: (0.25, 0.27), 120.0: (0.10, 0.12), 130.0: (0.05, 0.07), 90.0: (0.5, 0.52)}
a = L.arb_triggers(qa)
assert (100.0, "Y", 0.20, 0.25) in a and any(x[1] == "N" and x[0] == 110.0 for x in a) is False  # NO ask 0.75 is outside the band
# fewer than 5 strikes -> nothing; at most 2 per event
assert L.select({100.0: (0.1, 0.12), 110.0: (0.3, 0.2)}) == []
many = mk([0.30, 0.30, 0.05, 0.30, 0.04, 0.30, 0.03, 0.30])
assert len(L.select(many)) <= L.MAX_PER_EVENT
print("ok")
