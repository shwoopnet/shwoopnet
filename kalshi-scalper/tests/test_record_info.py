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
