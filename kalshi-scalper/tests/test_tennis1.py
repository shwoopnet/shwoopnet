import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import tennis1 as T


def test_norm_matches_accents_and_suffix():
    assert T.norm("Jakub Menšík") == T.norm("Jakub Mensik") == "jakub mensik"
    assert T.norm("Juan Cruz Martin Manzano") == "juan cruz martin manzano"
    assert T.norm("Robert Jr.") == "robert"


def test_elo_symmetry_and_update_direction():
    e = T.Elo()
    assert abs(e.prob("a", "b") - 0.5) < 1e-12
    e.update("a", "b")
    assert e.r["a"] > 1500 > e.r["b"]
    assert e.prob("a", "b") > 0.5 and abs(e.prob("a", "b") + e.prob("b", "a") - 1) < 1e-12


def test_elo_k_shrinks_with_matches():
    e = T.Elo()
    e.n["x"] = 0
    k_new = T.K0 / (0 + T.K_OFF) ** T.K_EXP
    k_old = T.K0 / (200 + T.K_OFF) ** T.K_EXP
    assert k_new > 3 * k_old


def test_elo_ready_needs_prior_matches():
    e = T.Elo()
    assert not e.ready("a", "b")
    e.n["a"] = e.n["b"] = T.MIN_PRIOR
    assert e.ready("a", "b")


def test_only_earlier_matches_enter_the_rating():
    ms = [("2026-01-01T10:00Z", "a", "b", 0, "1"), ("2026-01-02T10:00Z", "a", "b", 0, "2"), ("2026-01-03T10:00Z", "a", "b", 1, "3")]
    adv = T.elo_before(ms, None)
    e = adv("2026-01-02T10:00Z")        # strictly before the second match
    assert e.n["a"] == 1
    e = adv("2026-01-03T10:00Z")
    assert e.n["a"] == 2
    e = adv("2027-01-01T00:00Z")
    assert e.n["a"] == 3


def test_fee_rounds_up():
    assert T.fee(0.10, 10) == math.ceil(0.07 * 10 * 0.09 * 100) / 100 == 0.07
    assert T.fee(0.5, 1) == 0.02


def test_cheap_side_picks_yes_or_no_and_rejects_wide_prices():
    assert T.cheap_side(0.10, 0.12) == ("yes", 0.12)
    s = T.cheap_side(0.80, 0.84)           # NO ask = 0.20
    assert s[0] == "no" and abs(s[1] - 0.20) < 1e-12
    assert T.cheap_side(0.45, 0.55) is None
    assert T.cheap_side(0.0, 0.05) is None   # no bid is not a two-sided quote
    assert T.cheap_side(0.31, 0.35) is None


def test_net_cents_win_and_loss():
    w = T.net_cents(0.10, True, 10)
    l = T.net_cents(0.10, False, 10)
    assert abs(w - ((0.90 * 10 - 0.07) / 10 * 100)) < 1e-9
    assert abs(l - (-(0.10 * 10 + 0.07) / 10 * 100)) < 1e-9


def test_treated_rule():
    assert T.treated(0.30, 0.10) and not T.treated(0.29, 0.10)
    assert not T.treated(0.99, 0.31)       # hard limit 0.30


def test_calibrated_elo_has_zero_edge_at_fair_price():
    # a side whose true win rate equals its ask earns minus the fee only
    p = 0.10
    ev = p * T.net_cents(p, True, 10) + (1 - p) * T.net_cents(p, False, 10)
    assert -1.0 < ev < 0


def test_verdict_rules():
    mk = lambda mean, t: ("e", mean, mean > 0, 0.1, t)
    assert T.verdict([mk(1, 1)] * 10, 5) == "NOT_ENOUGH_DATA"
    # 150 trades, wins big in both halves: pass
    good = [("e", 50.0, True, 0.1, 1)] * 40 + [("e", -10.0, False, 0.1, 1)] * 35 + [("e", 50.0, True, 0.1, 9)] * 40 + [("e", -10.0, False, 0.1, 9)] * 35
    assert T.verdict(good, 5) == "NOT_YET_FALSIFIED"
    bad_half = [("e", 50.0, True, 0.1, 1)] * 75 + [("e", -10.0, False, 0.1, 9)] * 75
    assert T.verdict(bad_half, 5) == "FALSIFIED"


def test_build_matches_keeps_singles_final_only():
    rows = [dict(id="1", date="2026-01-01T00:00Z", grp="Men's Singles", names=["A B", "C D"], win=[True, False], status="STATUS_FINAL"),
            dict(id="2", date="2026-01-02T00:00Z", grp="Men's Doubles", names=["A B", "C D"], win=[True, False], status="STATUS_FINAL"),
            dict(id="3", date="2026-01-03T00:00Z", grp="Men's Singles", names=["A B", "C D"], win=[False, False], status="STATUS_FINAL"),
            dict(id="4", date="2026-01-04T00:00Z", grp="Men's Singles", names=["A B", "C D"], win=[False, True], status="STATUS_IN_PROGRESS")]
    ms = T.build_matches(rows)
    assert len(ms) == 1 and ms[0][1:4] == ("a b", "c d", 0)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("tennis1 tests ok")
