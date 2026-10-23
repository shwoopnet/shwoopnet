import sys
sys.path.insert(0, "src")
from scalper import scan1 as T

r = {"x": [0.90, 0.01, 0.0, 0.0, 6.0, 0.9, 0.05], "series": "KXBTC15M", "side": "yes", "day": "2026-10-10", "close_ts": 1_760_000_000, "net": 0.01}
c = T.conds(r)
assert c["price"] == "p<.92" and c["spread"] == "spread<=1c" and c["rise3"] == "rise3 flat" and c["rng5"] == "rng5<.10" and c["tib"] == "tib5+" and c["dip"] == "dip>=.75"
assert c["class"] == "class btceth" and c["side"] == "side yes" and c["weekend"] == "weekend"          # 2026-10-10 is a Saturday
print("ok")

row = lambda spread, tib: {"x": [0.9, spread, 0.0, 0.0, float(tib), 0.9, 0.05]}
assert T.in_r(row(0.01, 2)) and T.in_r(row(0.0105, 4)) and not T.in_r(row(0.02, 3)) and not T.in_r(row(0.01, 1)) and not T.in_r(row(0.01, 5))
assert "NOT_ENOUGH_DATA" in T.scan2f([])
print("ok2")
