import random
import sys
sys.path.insert(0, "src")
from scalper import size_s3 as T

e = {"gross": 0.07, "price": 0.93, "net": 0.0646}
rng = random.Random(1)
assert T.outcome(e, rng, False, 0.053) == 0.0646                       # unstressed: the recorded net
lost = sum(1 for _ in range(20000) if T.outcome(e, rng, True, 0.053) < 0)
assert 150 < lost < 450                                                # about 1.4% of wins turn into losses
print("ok")
