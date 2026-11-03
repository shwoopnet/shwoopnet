import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import approval1 as a  # noqa: E402


def test_fee_rounds_up_per_order():
    assert a.fee_per_contract(0.10) == math.ceil(0.07 * 10 * 0.09 * 100) / 100 / 10


def test_bracket_probabilities_sum_to_one():
    mu, sd = 39.0, 0.3
    p = a.p_yes("less", None, 38.5, mu, sd) + a.p_yes("between", 38.5, 39.5, mu, sd) + a.p_yes("greater", None, 39.5, mu, sd) if False else None
    below = a.p_yes("less", None, 38.5, mu, sd)
    mid = a.p_yes("between", 38.5, 39.4, mu, sd)
    above = a.p_yes("greater", 39.4, None, mu, sd)
    assert abs(below + mid + above - 1) < 1e-9


def test_value_inside_bracket():
    assert a.yes_by_value("between", 39.2, 39.2, 39.2) is True
    assert a.yes_by_value("less", None, 38.8, 38.8) is False
    assert a.yes_by_value("greater", 38.8, None, 38.9) is True


def test_only_cheap_sides_and_hard_limit():
    close = 10 * 86400
    m = {"q": {close - a.LOOK_BEFORE_S - 3600: (0.60, 0.80)}}   # yes ask .80 (not cheap), no ask .40 (not cheap)
    assert a.sides_at_look(m, close) == []
    m = {"q": {close - a.LOOK_BEFORE_S - 3600: (0.80, 0.85)}}   # no ask .20
    assert a.sides_at_look(m, close) == [("no", 0.2)]
    m = {"q": {close - a.LOOK_BEFORE_S - 3600: (0.70, 0.75)}}   # no ask .30 allowed, yes .75 not
    assert a.sides_at_look(m, close) == [("no", 0.3)]
    m = {"q": {close - a.LOOK_BEFORE_S - 3600: (0.69, 0.72)}}   # no ask .31 refused
    assert a.sides_at_look(m, close) == []


def test_no_quote_after_look():
    close = 10 * 86400
    m = {"q": {close - a.LOOK_BEFORE_S + 60: (0.90, 0.95)}}
    assert a.look_quote(m, close) is None
