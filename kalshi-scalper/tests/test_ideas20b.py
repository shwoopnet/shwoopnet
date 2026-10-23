import sys
sys.path.insert(0, "src")
from scalper import ideas20 as I
from scalper import ideas20b as B

def cd(end, bid, ask, vol=100.0, oi=1000.0):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": vol, "oi": oi, "last": ask}

close = 1_700_000_400                     # 2023-11-14 22:20:00 UTC; move to a :00 close
close = close - (close % 3600)            # on the hour
def mkt(cl, strike, res="yes"):
    return {"close": cl, "res": res, "strike": strike, "c": [cd(cl - 360 - 60 * k, 0.92, 0.93) for k in range(6, 0, -1)] + [cd(cl - 360, 0.92, 0.93)]}
mk = {f"M{k}": mkt(close - 900 * k, 70000.0 * (1 + 0.001 * k)) for k in range(0, 9)}
rules = dict((n, f) for n, _, f in B.rules(mk))
assert len(rules) == 20
m = mk["M0"]
c, e = I.at(m, 360)
assert rules["HOURCLOSE"](m, c, e, None) == ("yes", 0.93) and rules["HALFCLOSE"](m, c, e, None) is None
assert rules["STREAK3"](m, c, e, None) == ("yes", 0.93) and rules["STREAK3_OPP"](m, c, e, None) is None   # three earlier windows all yes
assert rules["ACTIVE"](m, c, e, None) is None                    # same volume as the previous window
assert rules["HIGHREG"](m, c, e, None) is None                   # 0.1% steps are a low regime
print("ok")
