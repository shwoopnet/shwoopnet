from scalper import enter1 as e


def test_fee():
    assert e.fee(0.5) == 0.02 and e.fee(0.1) == 0.01


def test_p_above_monotone_and_clipped():
    a = e.p_above(100, 90, 1.0, 10)
    b = e.p_above(120, 90, 1.0, 10)
    assert a > b and 0.01 <= b <= a <= 0.99
    assert e.p_above(50, 90, 1.0, 0) == 0.99 and e.p_above(200, 90, 1.0, 0) == 0.01


def test_decide_ratio_and_limit():
    assert e.decide(0.50, 0.10, 0.90) == ("yes", 0.10)
    assert e.decide(0.50, 0.20, 0.90) is None
    assert e.decide(0.90, 0.95, 0.31) is None
    assert e.decide(0.10, 0.90, 0.20) == ("no", 0.20)
    assert e.decide(0.05, 0.40, 0.25) == ("no", 0.25)


def test_pnl():
    assert abs(e.pnl(0.2, True) - (0.8 - e.fee(0.2))) < 1e-9
