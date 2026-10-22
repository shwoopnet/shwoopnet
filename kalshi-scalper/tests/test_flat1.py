import sys
sys.path.insert(0, "src")
from scalper import flat1 as T

row = lambda rng, rise, day="d1": {"x": [0.9, 0.01, rise, 0.0, 3.0, 0.9, rng], "day": day, "close_ts": 1, "net": 0.0, "stress": 0.0, "gross": 0.0}
rows = [row(0.01, 0.005), row(0.03, 0.0), row(0.01, 0.02), row(0.02, -0.01)]
flat, moving = T.split(rows)
assert len(flat) == 2 and len(moving) == 2, (len(flat), len(moving))     # rng5 <= .02 and |rise3| <= .01, edges included
print("ok")
