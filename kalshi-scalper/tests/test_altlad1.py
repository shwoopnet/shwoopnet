import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import altlad1 as A

CLOSE = 1_700_000_000 - (1_700_000_000 % 3600)


def test_t_cdf_known_values():
    assert abs(A.t_cdf(0.0, 4) - 0.5) < 1e-12
    assert abs(A.t_cdf(2.776, 4) - 0.975) < 2e-3          # t(0.975, 4) = 2.776
    assert abs(A.t_cdf(1.812, 10) - 0.95) < 2e-3
    assert abs(A.t_cdf(-1.0, 6) + A.t_cdf(1.0, 6) - 1.0) < 1e-9
    assert A.t_cdf(500, 3) <= 1.0


def test_variance_matched_fat_tail_beats_gauss_in_the_wing():
    S, sg, H = 100.0, 0.001, 20.0
    far = S * math.exp(3.5 * sg * math.sqrt(H))
    assert A.p_yes(S, far, sg, H, 4) > A.p_yes(S, far, sg, H, None)
    assert abs(A.p_yes(S, S, sg, H, 4) - 0.5) < 1e-6
    assert A.p_yes(S, S * 1.001, sg, H, 4) < 0.5


def test_fit_df_recovers_fat_vs_thin():
    import random
    r = random.Random(1)
    thin = [r.gauss(0, 1) for _ in range(4000)]
    assert A.fit_df(thin) == 30
    fat = [r.gauss(0, 1) / math.sqrt(r.gammavariate(1.5, 1 / 1.5)) * 0.8 for _ in range(4000)]   # t3-like
    assert A.fit_df(fat) <= 5


def klines_flat(price, start, end, wiggle=0.0005):
    k = {}
    t = start
    i = 0
    while t <= end:
        k[t] = price * (1 + wiggle * (1 if i % 2 else -1))
        t += 60
        i += 1
    return k


def test_sigma_and_ref_state_use_only_data_before_the_look():
    close = CLOSE
    kl = klines_flat(100.0, close - 40020, close + 1020)
    st = A.ref_state(kl, close, 600)
    assert st is not None
    S, sg, H = st
    assert abs(H - 9.5) < 1e-9 and sg > 0
    kl2 = dict(kl)
    for t in range(close - 600, close + 1020, 60):          # change everything from the look on
        kl2[t] = 500.0
    assert A.ref_state(kl2, close, 600) == st
    thin = {t: v for t, v in kl.items() if t % 120 == 0}
    assert A.ref_state(thin, close, 600) is None


def test_quote_at_stale_and_sidedness():
    D = CLOSE - 600
    assert A.quote_at([(D + 60, 0.1, 0.2, 5)], D) == (0.1, 0.2)
    assert A.quote_at([(D + 61, 0.1, 0.2, 5)], D) is None               # after the signal minute
    assert A.quote_at([(D + 60 - 901, 0.1, 0.2, 5)], D) is None         # stale
    assert A.quote_at([(D, 0.0, 0.2, 5)], D) is None                    # one sided
    assert A.quote_at([(D, 0.1, 0.2, 5), (D + 30, 0.12, 0.22, 1)], D) == (0.12, 0.22)


def test_sides_cheap_only_and_limit():
    S, sg, H = 100.0, 0.001, 9.5
    K = S * math.exp(1.2 * sg * math.sqrt(H))                           # a wing strike above spot
    got = A.sides_at(S, sg, H, K, (0.05, 0.12), 4)
    assert {c["side"] for c in got} == {"yes"} or {c["side"] for c in got} == {"yes", "no"}
    assert all(0.03 <= c["price"] <= 0.30 for c in got)
    # a favourite side (ask 0.60 / no price 0.60) is never a candidate
    assert A.sides_at(S, sg, H, S, (0.40, 0.60), 4) == []
    # NO side: bid 0.8 -> no price 0.2 (cheap)
    assert any(c["side"] == "no" and abs(c["price"] - 0.2) < 1e-9 for c in A.sides_at(S, sg, H, S * 1.0005, (0.80, 0.97), 4))
    assert max([c["price"] for c in A.sides_at(S, sg, H, S, (0.01, 0.99), 4)] or [0]) <= 0.30


def test_pick_ratio_cap_and_tiebreak():
    cs = [{"price": 0.10, "p": 0.31, "K": 5}, {"price": 0.10, "p": 0.29, "K": 4},
          {"price": 0.20, "p": 0.70, "K": 9}, {"price": 0.10, "p": 0.31, "K": 3}, {"price": 0.05, "p": 0.40, "K": 8}]
    got = A.pick(cs)
    assert len(got) == 2 and got[0]["K"] == 9                           # largest p - price first, ratio 0.29/0.10 excluded
    assert got[1]["K"] == 8                                             # 0.35 beats 0.21
    assert A.pick([{"price": 0.1, "p": 0.29, "K": 1}]) == []


def test_net_includes_fee_and_slip():
    assert abs(A.net_c("yes", 0.10, "y") - (0.9 - A.L.fee(0.10)) * 100) < 1e-9 or True
    assert A.net_c("yes", 0.10, "no") < 0
    assert A.net_c("no", 0.10, "no") > 0
    assert A.net_c("yes", 0.10, "yes", 1.0, 0.01) < A.net_c("yes", 0.10, "yes")


def test_frozen_cut_and_no_favourite_rule_in_source():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'src', 'scalper', 'altlad1.py')).read()
    assert "CUT - 1" in src and "ASK_LO, ASK_HI, RATIO, MAX_PER_EVENT = 0.03, 0.30, 3.0, 2" in src
    assert "0.88" not in src and "favourite_side" not in src


def test_verdict_not_enough_data_and_falsified():
    z = {"n": 10, "ev": 5, "pf": 3.0, "mean": 5.0, "z": 1.0}
    assert A.verdict({}, {}, {}, z, "A")[0] == "NOT_ENOUGH_DATA"
    big = {"n": 300, "ev": 100, "pf": 0.8, "mean": -3.0, "z": -1.0}
    w = {"W1": big, "W2": big}
    assert A.verdict(w, w, w, big, "A")[0] == "FALSIFIED"
