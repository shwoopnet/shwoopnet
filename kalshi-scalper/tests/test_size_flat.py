import sys
sys.path.insert(0, "src")
from scalper import size_flat as T

row = lambda day, net, rng: {"x": [0.9, 0.01, 0.0, 0.0, 3.0, 0.9, rng], "day": day, "net": net, "close_ts": 1}
rows = [row("d1", 0.02, 0.1), row("d1", -0.5, 0.5), row("d2", 0.03, 0.1)]
d = T.daily(rows, 6)
assert abs(d["d1"][0] - (-0.48)) < 1e-9 and abs(d["d1"][1] - 0.12) < 1e-9, d      # A: 1 contract each; B: 6 on the flat one only
assert abs(d["d2"][1] - 0.18) < 1e-9, d
print("ok")
