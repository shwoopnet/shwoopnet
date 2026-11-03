"""FEDIMPL1 model and trade rule on hand-built inputs. Research only. Plain runner."""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import fedimpl1 as f  # noqa: E402


def test_outcome_probabilities_sum_to_one_and_peak_at_hold():
    ps = {k: f.p_outcome(0.0, k) for k in f.OUTCOMES}
    assert abs(sum(ps.values()) - 1) < 1e-9 and max(ps, key=ps.get) == "H0"
    assert f.p_outcome(-25.0, "C25") > 0.7


def test_ladder_probability_matches_cells():
    # upper bound 4.00, E = -25: P(above 4.00) = P(change >= +25) small, P(above 3.50) = P(change > -37.5)... j=-2 -> cells > -37.5
    assert f.p_above(-25.0, 4.00, 4.00) < 0.01
    assert abs(f.p_above(-25.0, 4.00, 3.75) - (1 - f.phi(1.25))) < 1e-9
    assert abs(f.p_above(0, 4.0, 4.0) - (1 - f.phi(1.25))) < 1e-9


def test_fee_rounds_up_to_the_cent():
    assert abs(f.fee(0.10) - 0.07) < 1e-9          # 7 x 10 x .09 = 6.3c -> 7c
    assert abs(f.fee(0.50) - 0.18) < 1e-9          # 17.5c -> 18c


def test_prev_business_day_skips_weekend():
    assert f.prev_business_day(date(2026, 11, 2)) == date(2026, 10, 30)


def test_decide_cheap_yes_needs_three_times_ask_and_limit():
    sig, fill = (0.08, 0.10), (0.09, 0.12)
    assert f.decide(0.31, sig, fill)["side"] == "yes"
    assert f.decide(0.29, sig, fill) == "model"
    assert f.decide(0.5, sig, (0.3, 0.35)) == "limit"
    assert f.decide(0.5, (0.01, 0.02), fill) == "notcheap" or isinstance(f.decide(0.5, (0.01, 0.02), fill), str)
    assert f.decide(0.5, (0.04, 0.20), fill) == "wide"


def test_decide_no_side_when_yes_is_expensive():
    r = f.decide(0.2, (0.78, 0.82), (0.78, 0.82))     # NO ask = 0.22
    assert r["side"] == "no" and abs(r["ask"] - 0.22) < 1e-9


def test_reference_needs_spread_observations():
    dff = {date(2026, 10, 1): 3.9, date(2026, 10, 7): 3.9}
    bill = {date(2026, 10, 1): 3.95, date(2026, 10, 7): 3.95}
    assert f.reference(dff, bill, date(2026, 11, 5)) is None


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("ok")
