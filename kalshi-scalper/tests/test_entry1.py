import sys
sys.path.insert(0, "src")
from scalper import entry1 as T

train = {("KXA", 600): [0.02] * 200, ("KXA", 360): [0.01] * 200, ("KXB", 600): [0.05] * 100, ("KXB", 360): [0.01] * 200}
pick = T.choose(train)
assert pick == {"KXA": 600, "KXB": 360}, pick                # KXB's 600 has only 100 entries: not eligible, stays at 360
r = lambda s, left, day, net: {"series": s, "left": left, "day": day, "net": net, "stress": net}
test = [r("KXA", 600, "d1", 0.03), r("KXA", 360, "d1", 0.01), r("KXA", 600, "d2", 0.02), r("KXA", 360, "d2", 0.00), r("KXB", 360, "d1", 9.0)]
m, z, nd, nch = T.stat(test, pick)
assert nch == 1 and nd == 2 and abs(m - 0.02) < 1e-9, (m, nd, nch)      # only KXA changed; KXB's rows are ignored
print("ok")
