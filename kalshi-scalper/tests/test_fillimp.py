import sys
sys.path.insert(0, "src")
from scalper import fillimp as T

assert T.bucket(None) == 0 and T.bucket(0.0) == 1 and T.bucket(0.004) == 2 and T.bucket(0.01) == 2 and T.bucket(0.02) == 3 and T.bucket(0.03) == 3 and T.bucket(0.08) == 4
assert abs(T.next_ask((0, 0.90, 0.92, 0, 0), "yes") - 0.92) < 1e-12 and abs(T.next_ask((0, 0.90, 0.92, 0, 0), "no") - 0.10) < 1e-12
assert abs(T.net_at(0.9, True) - (0.1 - T.fee(0.9))) < 1e-12 and abs(T.net_at(0.9, False) + (0.9 + T.fee(0.9))) < 1e-12
print("ok")
