import sys
sys.path.insert(0, "src")
from scalper import flat3 as T

assert T.LEFTS == (300, 420, 480, 540) and 360 not in T.LEFTS and 600 not in T.LEFTS     # 6 and 10 minutes are recorded elsewhere
print("ok")
