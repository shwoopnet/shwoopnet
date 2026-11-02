import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import hourly1 as H

CLOSE = 1_800_000_000 - (1_800_000_000 % 3600)
LOOK = CLOSE - H.LOOK_S


def klines(base=100.0, noise=0.05, missing=None):
    out = {}
    for k in range(-70, 3):
        t = LOOK - 60 + 60 * k
        out[t] = base + (noise if k % 2 else -noise)
    if missing is not None:
        out.pop(LOOK - 60 + 60 * missing)
    return out


def candles(bid, ask, vol=5.0):
    return [(LOOK - 240 + 60 * i, bid, ask, vol) for i in range(5)]


def test_p_above_is_monotone_and_near_half_at_the_money():
    s = 1e-4
    a = H.p_above(100.0, 100.0, s)
    assert 0.49 < a < 0.5
    assert H.p_above(100.0, 99.0, s) > a > H.p_above(100.0, 101.0, s)


def test_sigma_needs_61_closes_and_is_positive():
    assert H.sigma_per_s([1.0] * 61) is None
    assert H.sigma_per_s([100 + (0.1 if i % 2 else 0) for i in range(60)]) is None
    assert H.sigma_per_s([100 + (0.1 if i % 2 else 0) for i in range(61)]) > 0


def test_missing_minute_means_no_model():
    k = klines(missing=-10)
    elig, best, _ = H.decide_event(CLOSE, [("T1", 100.0)], {"T1": candles(0.40, 0.45)}, k, 0.08)
    assert elig == [] and best is None


def test_far_strike_is_ignored_and_liquidity_rule_applies():
    k = klines()
    elig, _, _ = H.decide_event(CLOSE, [("FAR", 110.0)], {"FAR": candles(0.40, 0.45)}, k, 0.08)
    assert elig == []
    elig, _, _ = H.decide_event(CLOSE, [("T", 100.0)], {"T": candles(0.40, 0.45, vol=1.0)}, k, 0.08)
    assert elig == []
    elig, _, _ = H.decide_event(CLOSE, [("T", 100.0)], {"T": candles(0.30, 0.45)}, k, 0.08)   # spread over 0.10
    assert elig == []


def test_cheap_quote_gives_a_yes_trade_and_best_is_the_largest_edge():
    k = klines()
    # the model p at 99.9 is about 0.57; an ask of 0.40 is a bigger edge than 0.45
    elig, best, _ = H.decide_event(CLOSE, [("A", 99.9), ("B", 99.9)], {"A": candles(0.36, 0.45), "B": candles(0.31, 0.40)}, k, 0.08)
    assert len(elig) == 2 and best["tk"] == "B" and best["side"] == "yes"


def test_no_side_and_price_ban():
    k = klines()
    _, best, _ = H.decide_event(CLOSE, [("A", 100.0)], {"A": candles(0.62, 0.70)}, k, 0.08)
    assert best["side"] == "no" and abs(best["price"] - 0.38) < 1e-9
    _, best, banned = H.decide_event(CLOSE, [("A", 100.0)], {"A": candles(0.92, 0.96)}, k, 0.08)   # NO costs 0.08 < 0.20
    assert best is None and banned == 1


def test_no_look_ahead_in_spot_or_quote():
    k = klines()
    c = {"A": candles(0.30, 0.40) + [(LOOK + 60, 0.01, 0.02, 99.0)]}
    k2 = dict(k); k2[LOOK] = 1.0; k2[LOOK + 60] = 1.0           # klines opening at/after the look end after it
    a = H.decide_event(CLOSE, [("A", 100.0)], c, k, 0.08)
    b = H.decide_event(CLOSE, [("A", 100.0)], {"A": candles(0.30, 0.40)}, k2, 0.08)
    assert a == b
