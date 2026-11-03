import math
from scalper import perpoi1 as P


def test_fee():
    assert P.fee(0.5, 10) == 0.18
    assert P.fee(0.1, 10) == 0.07


def test_pick_direction_and_limit():
    c = [(101, 0.20, 0.25), (102, 0.10, 0.12), (103, 0.02, 0.04), (99, 0.80, 0.85), (98, 0.90, 0.95)]
    assert P.pick(c, 1, 100, "A") == (101, "yes", 0.25)   # nearest = highest price under 0.30
    assert P.pick(c, -1, 100, "A")[1] == "no" and abs(P.pick(c, -1, 100, "A")[2] - 0.20) < 1e-9  # 1-0.80
    assert P.pick([(101, 0.4, 0.45)], 1, 100, "A") is None  # above hard limit


def test_pick_b_lower():
    c = [(101, 0.20, 0.25), (99, 0.90, 0.95)]
    s = P.pick(c, 0, 100, "B")
    assert s[1] == "no" and abs(s[2] - 0.10) < 1e-9


def test_surge_uses_only_past_and_needs_history():
    n = 9 * 1440
    oi = [100.0] * n
    c = [50.0 + 0.0 * i for i in range(n)]
    t0 = 0
    assert P.surge_at(t0, c, oi, 60 * 100) is None   # not enough history
    # jump in last 10 minutes and price up
    t = 60 * (n - 5)
    i = (t - 60 - t0) // 60
    oi2 = list(oi); c2 = list(c)
    for j in range(i - 5, i + 1):
        oi2[j] = 300.0; c2[j] = 51.0
    for j in range(i + 1, n):   # future must not matter
        oi2[j] = 0.0
    s, d, spot = P.surge_at(t0, c2, oi2, t)
    assert s and d == 1


def test_pnl():
    pn, w = P.pnl("yes", 0.2, 101, "yes", 10)
    assert w and abs(pn - (10 - 2 - P.fee(0.2, 10))) < 1e-9
    pn, w = P.pnl("no", 0.2, 101, "yes", 10)
    assert not w and pn < 0
