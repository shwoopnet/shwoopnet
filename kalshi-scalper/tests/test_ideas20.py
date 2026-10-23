import sys
sys.path.insert(0, "src")
from scalper import ideas20 as T

def cd(end, bid, ask, vol=100.0, oi=1000.0, last=None):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": vol, "oi": oi, "last": last if last is not None else ask}

close = 1_700_000_000
cs = [cd(close - 360 - 60 * k, 0.90, 0.91, vol=100.0) for k in range(5, 0, -1)] + [cd(close - 360, 0.92, 0.93, vol=500.0)]
m = {"close": close, "res": "yes", "strike": 70000.0, "c": cs}
c, e = T.at(m, 360)
assert c["end"] == close - 360 and len(e) == 5
assert T.r01(m, c, e, None) == ("yes", 0.93)                    # 500 >= 3 x 100
assert T.r02(m, c, e, None) is None
assert T.r08(m, c, e, None) == ("yes", 0.93)                    # spread 1c now and before
assert T.r16(m, c, e, None) is not None                         # 70000 is a multiple of 1000
assert T.r13(m, c, e, 69000.0) is not None and T.r13(m, c, e, 69990.0) is None
rows = T.entries({"A": m}, 360, T.r01)
assert len(rows) == 1 and rows[0]["net"] > 0
assert T.judge(rows, "2000-01-01")["verdict"] == "NOT_ENOUGH_DATA"
assert abs(T.pf([{"net": 0.3}, {"net": -0.1}]) - 3.0) < 1e-9
assert len(T.RULES) == 20
print("ok")
