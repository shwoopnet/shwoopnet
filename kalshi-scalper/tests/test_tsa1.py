import math
from datetime import date, timedelta

import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import tsa1


def series(n=130, g=1.05):
    s0 = date(2022, 1, 2)
    return {s0 + timedelta(days=7 * i): 2.0e6 * (g ** ((i % 52) / 52)) * (1.02 ** (i // 52)) for i in range(n)}


def test_centre_matches_exact_growth():
    A = series()
    s = date(2022, 1, 2) + timedelta(days=7 * 100)
    c = tsa1.centre(A, s)
    assert abs(c / A[s] - 1) < 0.02


def test_centre_none_when_missing():
    A = series()
    s = date(2022, 1, 2) + timedelta(days=7 * 100)
    del A[s - timedelta(days=21)]
    assert tsa1.centre(A, s) is None


def test_predictions_burn_in_and_fair_monotone():
    A = series()
    P = tsa1.predictions(A)
    assert P and all(len(v[1]) >= tsa1.MIN_ERR for v in P.values())
    s = sorted(P)[-1]
    c, errs = P[s]
    assert tsa1.fair(c, errs, c * 0.5) >= tsa1.fair(c, errs, c) >= tsa1.fair(c, errs, c * 2)
    assert tsa1.fair(c, errs, c * 0.5) > 0.95 and tsa1.fair(c, errs, c * 2) < 0.05


def test_entry_sides_and_spread():
    assert tsa1.entry(0.9, 0.40, 0.45)[0] == "yes"
    assert tsa1.entry(0.1, 0.60, 0.65) == ("no", 0.4)
    assert tsa1.entry(0.9, 0.30, 0.45) is None  # spread over 10c
    assert tsa1.entry(0.5, 0.48, 0.52) is None


def test_quote_uses_only_candles_before_look_and_fresh():
    L = 1_000_000
    cs = [(L - 7200, 0.4, 0.45), (L + 10, 0.1, 0.9), (L - 40000, 0.4, 0.5)]
    assert tsa1.quote(cs, L) == (0.4, 0.45)
    assert tsa1.quote([(L - 40000, 0.4, 0.5)], L) is None


def test_thirds_equal():
    ev = [date(2024, 1, 7) + timedelta(days=7 * i) for i in range(30)]
    w = tsa1.thirds(ev)
    from collections import Counter
    assert set(Counter(w(e) for e in ev).values()) == {10}


def test_strike_parse():
    assert tsa1.strike_of({"yes_sub_title": "Above 2,041,682"}) == 2041682
    assert tsa1.strike_of({"yes_sub_title": "Above 2.1 million"}) == 2.1e6
    assert tsa1.strike_of({"floor_strike": 2800000}) == 2.8e6


def test_look_is_monday_16utc():
    from datetime import datetime, timezone
    L = tsa1.look_ts(date(2026, 8, 30))
    d = datetime.fromtimestamp(L, timezone.utc)
    assert d.weekday() == 0 and d.hour == 16


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
