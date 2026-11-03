import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import settle1 as S

CLOSE = 1_800_000_000 - (1_800_000_000 % 900)


def flat_klines(price=100.0, drift_after_open=0.0):
    """R(t) = close of the bar opening at t-60, for bar opens from CLOSE-960-4000 to CLOSE."""
    k = {}
    for t in range(CLOSE - 5040, CLOSE + 1, 60):
        k[t] = price
    return k


def test_fee_rounds_up():
    assert abs(S.fee(0.5) - 0.018) < 1e-12      # 0.175 -> 0.18 for ten contracts
    assert abs(S.fee(0.9) - 0.007) < 1e-12


def test_no_signal_without_open_bar_or_vol():
    assert S.signal({}, CLOSE, 180) is None
    k = flat_klines()
    assert S.signal(k, CLOSE, 180) is None      # sigma 0 and x 0


def test_signal_direction_and_scale():
    k = {}
    for i, t in enumerate(range(CLOSE - 5040, CLOSE + 1, 60)):
        k[t] = 100.0 + (0.01 if i % 2 else -0.01)   # noise only
    # push the price up after the open print (open print is the bar opening at CLOSE-960)
    for t in range(CLOSE - 900, CLOSE + 1, 60):
        k[t] = 100.5
    x, sigma, z = S.signal(k, CLOSE, 180)
    assert x > 0 and z > 1 and sigma > 0
    for t in range(CLOSE - 900, CLOSE + 1, 60):
        k[t] = 99.5
    x2, _, z2 = S.signal(k, CLOSE, 180)
    assert x2 < 0 and z2 < -1


def test_quote_needs_exact_candle_and_two_sides():
    t = CLOSE - 120
    assert S.quote({t: (0.2, 0.25)}, t) == (0.2, 0.25)
    assert S.quote({t: (0.2, 0.25)}, t + 60) is None
    assert S.quote({t: (0.0, 0.25)}, t) is None
    assert S.quote({t: (0.2, 1.0)}, t) is None
    assert S.quote({t: (0.1, 0.25)}, t) is None  # spread 0.15


def test_fill_uses_candle_one_minute_after_look_and_side():
    k = {}
    for i, t in enumerate(range(CLOSE - 5040, CLOSE + 1, 60)):
        k[t] = 100.0 + (0.01 if i % 2 else -0.01)
    for t in range(CLOSE - 900, CLOSE + 1, 60):
        k[t] = 100.5
    c = {CLOSE - 180 + 60: (0.20, 0.25)}
    d = S.decide(k, c, CLOSE, 180)
    assert d["side"] == "yes" and d["price"] == 0.25
    for t in range(CLOSE - 900, CLOSE + 1, 60):
        k[t] = 99.5
    d = S.decide(k, c, CLOSE, 180)
    assert d["side"] == "no" and abs(d["price"] - 0.80) < 1e-12
    assert S.decide(k, {CLOSE - 180: (0.2, 0.25)}, CLOSE, 180) is None   # the signal minute's own candle is not used


def test_pnl_and_stats():
    assert abs(S.pnl("yes", 0.25, "yes") - (0.75 - S.fee(0.25)) * 100) < 1e-9
    assert abs(S.pnl("yes", 0.25, "no") - (-0.25 - S.fee(0.25)) * 100) < 1e-9
    s = S.stats([("a", "yes", 0.25, "yes"), ("b", "yes", 0.25, "no")])
    assert s["n"] == 2 and s["win"] == 0.5


def test_thirds_by_date():
    t = S.thirds(["d1", "d2", "d3", "d4", "d5", "d6"])
    assert [t[d] for d in ("d1", "d2", "d3", "d4", "d5", "d6")] == ["W1", "W1", "W2", "W2", "W3", "W3"]


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("settle1 tests ok")
