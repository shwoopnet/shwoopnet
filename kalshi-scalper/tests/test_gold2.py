import sys
sys.path.insert(0, "src")
from scalper import gold2 as T

rows = [{"x": [0.9, 0.004, 0.0, 0, 3, 0, 0.1]}, {"x": [0.9, 0.02, 0.2, 0, 1, 0, 0.5]}]
assert T.GROUPS["FLAT"](rows[0]) and not T.GROUPS["FLAT"](rows[1])
assert T.GROUPS["TIGHT"](rows[0]) and not T.GROUPS["TIGHT"](rows[1])
assert T.GROUPS["LONGBAND"](rows[0]) and not T.GROUPS["LONGBAND"](rows[1])
a, b = T.split(rows, T.GROUPS["TIGHT"])
assert len(a) == 1 and len(b) == 1
assert T.judge(rows, T.GROUPS["TIGHT"])["verdict"] == "NOT_ENOUGH_DATA"      # below the minimum group size
print("ok")
