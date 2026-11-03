import math
from scalper import fxref1 as f

def test_p_at_the_money_is_half():
    assert abs(f.p_yes(1.1, 1.1, 0.0002) - 0.5) < 1e-12

def test_p_far_below_strike_small():
    assert f.p_yes(1.0, 1.01, 0.0002) < 0.001

def test_vol_needs_40_and_positive():
    assert f.vol_per_minute([1.0] * 30) is None
    assert f.vol_per_minute([1.0] * 70) is None
    c = [1.0 + 0.0001 * ((-1) ** i) for i in range(70)]
    assert f.vol_per_minute(c) > 0

def test_decide_cheap_side_and_ratio():
    assert f.decide(0.10, 0.92, 0.35)[0] == "yes"
    assert f.decide(0.10, 0.92, 0.25) is None          # 2.5x only
    assert f.decide(0.92, 0.10, 0.65)[0] == "no"       # no prob 0.35 >= 0.30
    assert f.decide(0.40, 0.62, 0.9) is None            # ask above hard limit, favourite never computed
    assert f.decide(0.02, 0.99, 0.5) is None            # below 3c

def test_net_and_fee():
    assert abs(f.fee_per_contract(0.5) - 0.018) < 1e-9
    assert f.net("yes", 0.1, "yes") > 0.8 and f.net("yes", 0.1, "no") < -0.1
