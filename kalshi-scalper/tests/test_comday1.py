import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import comday1 as C

CLOSE = 1_800_000_000 - (1_800_000_000 % 3600)


def test_t4_cdf_known_values():
    assert abs(C.t4_cdf(0.0) - 0.5) < 1e-12
    assert abs(C.t4_cdf(2.776) - 0.975) < 1e-3          # t(0.975, 4) = 2.776
    assert abs(C.t4_cdf(-1.0) + C.t4_cdf(1.0) - 1.0) < 1e-12


def test_p_yes_variance_matched_and_fat_tails():
    S, sg, H = 100.0, 0.001, 360
    sd = sg * math.sqrt(H)
    assert abs(C.p_yes(S, S, sg, H) - 0.5) < 1e-12
    far = S * math.exp(3 * sd)
    assert C.p_yes(S, far, sg, H) > C.p_yes(S, far, sg, H, "gauss")     # fatter wing
    near = S * math.exp(0.3 * sd)
    assert C.p_yes(S, near, sg, H) < 0.5


def test_fee_rounding():
    assert C.fee(0.5) == math.ceil(0.07 * 10 * 0.25 * 100) / 100 / 10
    assert abs(C.net(True, 0.1) - (0.9 - C.fee(0.1))) < 1e-12


def make_bars(n=200, step=0.0004):
    out = {}
    for i in range(n):
        out[CLOSE - 300 * (n - i)] = 100.0 * math.exp(step * (i % 2))
    return out


def test_sigma_min_scales_to_per_minute():
    b = make_bars()
    sg = C.sigma_min(b, CLOSE)
    assert abs(sg - 0.0004 / math.sqrt(5)) < 1e-9


def test_sigma_needs_returns():
    b = {k: v for k, v in make_bars().items() if k % 600 == 0}
    assert C.sigma_min(b, CLOSE) is None


def test_quote_at_staleness_and_two_sided():
    D = CLOSE - 360 * 60
    cs = [[D - 4000, 0.1, 0.2, None], [D - 600, 0.1, 0.12, None], [D + 120, 0.2, 0.3, None]]
    assert C.quote_at(cs, D) == (0.1, 0.12)                       # later than D+60 is ignored
    assert C.quote_at([[D - 4000, 0.1, 0.2, None]], D) is None    # too old
    assert C.quote_at([[D, 0.0, 0.2, None]], D) is None           # one sided


def test_sides_cheap_only_and_band():
    S, sg, H = 100.0, 0.001, 360
    sd = sg * math.sqrt(H)
    K = S * math.exp(1.0 * sd)
    got = C.sides_at(S, sg, H, K, (0.05, 0.10))
    assert [g[0] for g in got] == ["yes"]                          # NO side costs 0.95: never a candidate
    assert C.sides_at(S, sg, H, S * math.exp(6 * sd), (0.05, 0.10)) == []   # model prob outside [0.03, 0.97]
    assert all(g[1] <= 0.30 for g in C.sides_at(S, sg, H, K, (0.72, 0.90)))


def test_treated_ratio_and_cap():
    sides = [("a", "yes", 0.10, 0.31, 0.2), ("b", "yes", 0.10, 0.29, 0.2), ("c", "no", 0.05, 0.40, 0.3), ("d", "yes", 0.2, 0.9, 0.9),
             ("e", "yes", 0.1, 0.99, 0.9)]
    got = C.treated_picks(sides)
    assert len(got) == 2 and got[0][0] == "d"                      # largest edge first
    assert "e" not in [g[0] for g in got] and "b" not in [g[0] for g in got]


def test_split_dates_thirds_and_frozen():
    ds = ["2026-01-%02d" % i for i in range(1, 31)]
    dev, w1, w2, fr = C.split_dates(ds)
    assert len(dev) == 20 and len(fr) == 10 and w1 + w2 == dev and fr[0] > dev[-1]


def test_no_favourite_rule_in_code():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'src', 'scalper', 'comday1.py')).read()
    assert "ASK_LO, ASK_HI = 0.03, 0.30" in src and "0.85" not in src


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
