import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import ideas20d as D

def cd(end, bid, ask):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": 1.0, "oi": 1.0, "last": ask}

def mkt(h, mi, side_yes=True):
    close = int(datetime(2026, 10, 1, h, mi, tzinfo=timezone.utc).timestamp())
    q = (0.90, 0.91) if side_yes else (0.09, 0.10)
    return {"close": close, "res": "yes", "strike": 1.0, "c": [cd(close - 540, *q), cd(close - 360, *q)]}

btc, eth_same, eth_opp = mkt(13, 30), mkt(13, 30), mkt(13, 30, False)
eth_opp = {**eth_opp, "c": [cd(eth_opp["close"] - 540, 0.55, 0.56), cd(eth_opp["close"] - 360, 0.55, 0.56)]}      # the other coin is undecided: no favourite in the band
other = {"KXBTC15M": {btc["close"]: btc}, "KXETH15M": {eth_same["close"]: eth_same}}
R = dict(D.make_rules(other))
c, e = D.I.at(btc, 540)
band = (0.80, 0.93)
assert R["SESSION_12_18"](btc, c, e, band, 540, "KXBTC15M") == ("yes", 0.91) and R["SESSION_00_06"](btc, c, e, band, 540, "KXBTC15M") is None
assert R["US_OPEN"](btc, c, e, band, 540, "KXBTC15M") == ("yes", 0.91)          # a 13:30 close is inside 13:15 to 14:00
assert R["DATA_0830ET"](btc, c, e, band, 540, "KXBTC15M") == ("yes", 0.91)      # a 13:30 close is inside the widened set (12:30, 12:45, 13:00, 13:30, 13:45, 14:00)
assert R["CROSS_AGREE"](btc, c, e, band, 540, "KXBTC15M") == ("yes", 0.91) and R["CROSS_ALONE"](btc, c, e, band, 540, "KXBTC15M") is None
other2 = {"KXBTC15M": {btc["close"]: btc}, "KXETH15M": {eth_opp["close"]: eth_opp}}
R2 = dict(D.make_rules(other2))
assert R2["CROSS_ALONE"](btc, c, e, band, 540, "KXBTC15M") == ("yes", 0.91) and R2["CROSS_AGREE"](btc, c, e, band, 540, "KXBTC15M") is None
print("ok")
