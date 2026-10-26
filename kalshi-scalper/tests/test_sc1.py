import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import sc1 as M

def c(end, bid, ask, vol=500.0): return (end, bid, ask, vol)
base = 1_000_000
# a 6c jump in the mid at minute 3 on a tight book is an event; the next jump 3 minutes later is inside the 10 minute quiet period
cs = [c(base + 60 * i, 0.50, 0.51) for i in range(3)] + [c(base + 180, 0.57, 0.58)] + [c(base + 240 + 60 * i, 0.58, 0.59) for i in range(15)]
cs[6] = c(base + 360, 0.64, 0.65)
ev = list(M.events_for(cs))
assert ev == [3], ev
# a wide spread, a thin minute or a mid outside 0.15 to 0.85 is not an event
assert list(M.events_for([c(base, 0.50, 0.51), c(base + 60, 0.60, 0.66)])) == []
assert list(M.events_for([c(base, 0.50, 0.51), c(base + 60, 0.57, 0.58, 50.0)])) == []
assert list(M.events_for([c(base, 0.10, 0.11), c(base + 60, 0.17, 0.18)])) == []
# the fill is the closing quote of the NEXT minute: after a jump up at index 3, MOM buys YES at the ask of minute 4 and sells at the bid k minutes later
cs2 = [c(base + 60 * i, 0.50, 0.51) for i in range(3)] + [c(base + 180, 0.57, 0.58), c(base + 240, 0.60, 0.61), c(base + 300, 0.61, 0.62), c(base + 360, 0.62, 0.63)]
a = M.trade(cs2, 3, "MOM", 2, True)
assert abs(a - (0.62 - 0.61 - M.fee(0.61) - M.fee(0.62))) < 1e-9, a
f = M.trade(cs2, 3, "FADE", 2, True)       # buys NO: pays 1 - bid(minute 4) = 0.40, sells at 1 - ask(minute 6) = 0.37
assert abs(f - (0.37 - 0.40 - M.fee(0.40) - M.fee(0.37))) < 1e-9, f
assert M.trade(cs2, 3, "MOM", 5, True) is None      # a needed minute is missing
print("sc1 tests ok")
