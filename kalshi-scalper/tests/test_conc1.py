import sys
sys.path.insert(0, "src")
from scalper import conc1 as C

assert C.lean(0.9, 0.92) == "yes" and C.lean(0.05, 0.07) == "no" and C.lean(0.45, 0.55) is None
e = lambda s, side, t=1: {"series": s, "side": side, "close_ts": t, "net": 0.0, "stress": 0.0, "gross": 0.0, "day": "d"}
q = {(1, "KXETH15M"): (0.9, 0.92), (1, "KXXRP15M"): (0.05, 0.07), (1, "KXDOGE15M"): (0.5, 0.52), (2, "KXETH15M"): (0.9, 0.92), (3, "KXBTC15M"): (0.5, 0.5)}
ents = [e("KXBTC15M", "yes", 1), e("KXBTC15M", "yes", 2), e("KXBTC15M", "yes", 3), e("KXBTC15M", "yes", 4)]
agree, dis = C.classify(ents, q)
assert [x["close_ts"] for x in dis] == [1], dis          # XRP leans no against a yes entry
assert [x["close_ts"] for x in agree] == [2], agree      # ETH leans yes; windows 3 (neutral) and 4 (no data) are unused
print("ok")

# CONC2-F: the verdict line runs on a tiny fixture and uses only days from FRESH_FROM
mk = [("t1", "KXBTC15M", [(100 - 360 + 0, 0.90, 0.92)], 100, "yes")]
line = C.conc2f(mk)
assert line.startswith("CONC2-F") and "NOT_ENOUGH_DATA" in line, line
print("ok2")
