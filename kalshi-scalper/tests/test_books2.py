import math
from scalper import books2 as b


def test_probabilities():
    assert abs(b.p_total_over(48.5, 48.5, 10) - 0.5) < 1e-9
    assert abs(b.p_total_over(58.5, 48.5, 10) - (1 - b.phi(1))) < 1e-9
    # home favoured by 7.5 (S = -7.5): mu = 7.5; P(home wins by over 7.5) = 0.5; away needs margin < -7.5
    assert abs(b.p_margin_over(7.5, 7.5, 13) - 0.5) < 1e-9
    assert b.p_margin_over(-0.5 + 7.5, -7.5, 13) < 0.5


def test_side_prob_and_cheap_side():
    assert abs(b.side_prob("N", 0.2) - 0.8) < 1e-12 and b.side_prob("Y", 0.2) == 0.2
    assert b.cheap_side((0.05, 0.08)) == ("Y", 0.08)
    s, a = b.cheap_side((0.93, 0.96))
    assert s == "N" and abs(a - 0.07) < 1e-9
    assert b.cheap_side((0.45, 0.50)) is None
    assert b.cheap_side((0.0, 0.02)) is None  # under 3c


def test_look_excludes_late_and_invalid():
    c = {1000: (0.2, 0.25), 1500: (0.3, 0.35), 1900: (0.4, 0.45), 1850: (0.2, 0.5)}
    assert b.look(c, 1620) == (0.3, 0.35)  # 1500 <= 1620-120; 1850 is wide, 1900 is late
    assert b.look(c, 1000) is None


def test_fit_sd_and_pick_treated():
    assert abs(b.fit_sd([3, -4]) - math.sqrt(12.5)) < 1e-9
    rows = [dict(ask=0.05, p=0.20), dict(ask=0.10, p=0.20), dict(ask=0.06, p=0.19), dict(ask=0.20, p=0.5), dict(ask=0.07, p=0.30)]
    got = b.pick_treated(rows)
    assert [r["ask"] for r in got] == [0.07, 0.05]  # ratios 4.29, 4.0, 3.17 (3rd cut), 2.5 and 2.0 ineligible
    assert b.pick_treated([dict(ask=0.1, p=0.29)]) == []


def test_net_and_zstat():
    assert abs(b.net(True, 0.10) - (1 - 0.10 - b.fee(0.10) / 10)) < 1e-9
    assert b.zstat([1, 1]) is None
    assert b.zstat([1.0, 2.0, 3.0]) > 0
