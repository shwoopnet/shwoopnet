import math
from scalper import barrier1 as b

def test_touch_is_twice_terminal():
    # terminal above prob = N(-d); touch = 2N(-d)
    S, K, s, T = 100.0, 110.0, 0.8, 30 / 365
    d = math.log(K / S) / (s * math.sqrt(T))
    assert abs(b.touch_prob(S, K, s, T) - 2 * b.ncdf(-d)) < 1e-12
    assert b.touch_prob(S, K, s, 1e-9) < 1e-6
    assert b.touch_prob(S, S * 1.0000001, s, T) > 0.99

def test_fee_rounds_up():
    assert abs(b.fee_per_contract(0.5) - 0.018) < 1e-9   # 0.07*10*.25=0.175 -> 0.18 per 10
    assert abs(b.fee_per_contract(0.10) - 0.007) < 1e-9

def test_decide():
    assert b.decide("cheap", 0.10, 0.09, 0.25) == ("yes", 0.10)
    assert b.decide("cheap", 0.10, 0.09, 0.19) is None
    assert b.decide("cheap", 0.31, 0.30, 0.9) is None
    d = b.decide("rich", 0.95, 0.90, 0.05); assert d[0] == "no" and abs(d[1] - 0.10) < 1e-9
    assert b.decide("rich", 0.95, 0.90, 0.85) is None

def test_net():
    assert b.net_per_contract("yes", 0.1, "yes") > 0.8
    assert b.net_per_contract("yes", 0.1, "no") < -0.1

def test_event_end_not_market_close():
    import datetime as dt
    assert b.event_end("KXBTCMAXMON-BTC-26SEP30") == int(dt.datetime(2026, 10, 1, 4, tzinfo=dt.timezone.utc).timestamp())
