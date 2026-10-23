import sys
sys.path.insert(0, "src")
from scalper import live_improve as T

assert abs(T.improvement("y", 0.87, 0.88, 0.80) - 0.08) < 1e-12          # YES: seen ask 0.88, filled at 0.80 -> 8c cheaper
assert abs(T.improvement("n", 0.12, 0.13, 0.21) - 0.09) < 1e-12          # NO: seen bid 0.12 (NO ask 0.88), YES-side fill 0.21 -> NO cost 0.79 -> 9c cheaper
assert abs(T.improvement("n", 0.054, 0.055, 0.059) - 0.005) < 1e-12
assert [T.bucket(x) for x in (-0.01, 0.0, 0.004, 0.01, 0.02, 0.03, 0.08)] == [0, 0, 1, 1, 2, 2, 3]
assert abs(T.binom_tail(1, 2, 0.5) - 0.75) < 1e-12
print("ok")
