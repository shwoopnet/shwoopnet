import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import stocklad1 as S


def test_t_cdf_symmetry_and_normal_limit():
    assert abs(S.t_cdf(0, 5) - 0.5) < 1e-12
    assert abs(S.t_cdf(1.3, 7) + S.t_cdf(-1.3, 7) - 1) < 1e-9
    assert abs(S.t_cdf(1.96, 400) - 0.975) < 2e-3
    assert abs(S.t_cdf(2.015, 5) - 0.95) < 2e-3


def test_prob_above_monotone_and_atm():
    p = [S.prob_above(100, k, 0.02, 5, 5) for k in (90, 100, 110)]
    assert p[0] > p[1] > p[2]
    assert abs(p[1] - 0.5) < 0.01


def test_vol():
    closes = [100 * math.exp(0.01 * ((-1) ** i)) for i in range(25)]
    assert S.realised_vol(closes[:5]) is None
    assert 0.0 < S.realised_vol(closes) < 0.03


def test_pick_cheap_only_ratio_cap():
    c = [{"ask": 0.05, "p_side": 0.20}, {"ask": 0.05, "p_side": 0.12}, {"ask": 0.50, "p_side": 0.9},
         {"ask": 0.10, "p_side": 0.35}, {"ask": 0.20, "p_side": 0.7}, {"ask": 0.02, "p_side": 0.5}]
    out = S.pick(c)
    assert len(out) == 2 and all(0.03 <= x["ask"] <= 0.30 for x in out)
    assert out[0]["ask"] == 0.05 and out[0]["p_side"] == 0.20


if __name__ == '__main__':
    for k, v in list(globals().items()):
        if k.startswith('test_'):
            v()
    print('ok')
