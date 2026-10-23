import sys
sys.path.insert(0, "src")
from scalper import record_info as T

idx = {t: 100.0 for t in range(0, 20)}
idx.update({t: 100.05 for t in range(20, 40)})            # +5 bp step at second 20
j = T.jumps(idx, 10, 35)
assert len(j) == 1 and j[0][0] in range(20, 26) and j[0][1] > 0, j
polls = [{"t": 20_000 + i * 500, "bid": 0.50, "ask": 0.52} for i in range(4)] + [{"t": 22_000 + i * 500, "bid": 0.52, "ask": 0.54} for i in range(10)]
assert abs(T.follow_delay(polls, 20, 1) - 2.0) < 1e-9
assert T.follow_delay(polls, 20, -1) is None
print("ok")

base = [{"t": i * 500, "bid": 0.93, "ask": 0.94} for i in range(10)]
dip = base + [{"t": 5000, "bid": 0.88, "ask": 0.89}, {"t": 5500, "bid": 0.92, "ask": 0.93}] + [{"t": 6000 + i * 500, "bid": 0.93, "ask": 0.94} for i in range(4)]
assert T.dips(dip, True) == [5000], T.dips(dip, True)
assert T.dips(base, True) == []
nobounce = base + [{"t": 5000, "bid": 0.88, "ask": 0.89}] + [{"t": 5500 + i * 500, "bid": 0.88, "ask": 0.89} for i in range(8)]
assert T.dips(nobounce, True) == []            # a fall that stays down is not a dip and bounce
assert T.dips([{"t": q["t"], "bid": 1 - q["ask"], "ask": 1 - q["bid"]} for q in dip], False) == [5000]
print("ok2")
