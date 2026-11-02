import math
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import wtiw1


def test_parse_strikes():
    assert wtiw1.parse_strike("$99.00 to $99.99") == ("range", 99.0, 99.99, 0.01)
    assert wtiw1.parse_strike("4.67% or above") == ("above", 4.67, None, 0.01)
    assert wtiw1.parse_strike("161.500 to 161.749")[3] == 0.001
    assert wtiw1.parse_strike("$78.0 or below")[0] == "below"
    assert wtiw1.parse_strike("nonsense") is None


def test_fair_partition_sums_to_one_normal():
    st = [("below", 4.40, None, 0.01), ("range", 4.41, 4.60, 0.01), ("above", 4.61, None, 0.01)]
    tot = sum(wtiw1.fair("level", 4.5, 0.05, 5, s) for s in st)
    assert abs(tot - 1) < 1e-9


def test_fair_lognormal_median():
    f = wtiw1.fair("log", 100.0, 0.02, 5, ("above", 100.0, None, 0.01))
    assert abs(f - 0.5) < 0.01


def test_vol_and_level_needs_20_changes_and_ignores_future():
    s = {date(2024, 1, 1 + i): 100 + i for i in range(25)}
    assert wtiw1.vol_and_level(s, date(2024, 1, 10), "log") is None
    d0, x0, sig = wtiw1.vol_and_level(s, date(2024, 1, 22), "level")
    assert d0 == date(2024, 1, 22) and sig == 0.0


def test_weekdays_between():
    assert wtiw1.weekdays_between(date(2026, 8, 28), date(2026, 9, 4)) == 5
    assert wtiw1.weekdays_between(date(2026, 8, 28), date(2026, 8, 31)) == 1


def test_entry_fee_and_spread():
    assert wtiw1.entry(0.5, 0.30, 0.32) == ("yes", 0.32)
    assert wtiw1.entry(0.5, 0.30, 0.45) is None
    assert wtiw1.entry(0.2, 0.60, 0.62) == ("no", 0.4)


def test_quote_not_before_open_or_after_look():
    cs = [(100, 0.4, 0.5), (200, 0.45, 0.5), (400, 0.2, 0.3)]
    assert wtiw1.quote(cs, 300, 150) == (0.45, 0.5)
    assert wtiw1.quote(cs, 300, 250) is None
