import sys
sys.path.insert(0, "src")
from scalper import flat2 as T

row = lambda rng, rise: {"x": [0.9, 0.01, rise, 0.0, 3.0, 0.9, rng], "day": "d", "close_ts": 1, "net": 0.0}
flat, moving = T.split([row(0.15, 0.05), row(0.151, 0.0), row(0.1, -0.051), row(0.1, -0.05)])
assert len(flat) == 2 and len(moving) == 2, (len(flat), len(moving))
print("ok")
assert "NOT_ENOUGH_DATA" in T.flat2f([]), T.flat2f([])
print("ok2")
