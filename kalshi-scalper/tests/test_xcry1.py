import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import xcry1 as X

CLOSE = 1_800_000_000 - (1_800_000_000 % 900)
LOOK = CLOSE - 180


def btc_series(move, noise=0.0002):
    """1 minute klines (open_ts -> close) for 25 hours before the look; flat with tiny noise, then `move` (log) over the signal window."""
    out, p = {}, 100.0
    t0 = LOOK - 25 * 3600
    for t in range(t0, LOOK + 60, 60):
        end = t + 60
        if end > CLOSE - X.BACK_S and end <= LOOK:
            p *= math.exp(move / 3)       # three steps of the signal window
        else:
            p *= math.exp(noise * (1 if (t // 60) % 2 else -1))
        out[t] = p
    return out


def candles(bid, ask, vol=5.0):
    return [(LOOK - 240 + 60 * i, bid, ask, vol) for i in range(5)]


def test_trigger_up_follows_yes_when_cheap():
    d = X.decide(CLOSE, candles(0.30, 0.34), btc_series(0.01))
    assert d["trig"] and d["follow"] == ("yes", 0.34) and d["control"] is None  # NO costs 0.70, not cheap


def test_trigger_down_follows_no():
    d = X.decide(CLOSE, candles(0.60, 0.64), btc_series(-0.01))
    assert d["trig"] and d["follow"] == ("no", 0.40) and d["control"] is None   # YES at 0.64 is not cheap


def test_up_move_but_yes_expensive_means_no_follow_trade_and_a_control():
    d = X.decide(CLOSE, candles(0.60, 0.64), btc_series(0.01))
    assert d["trig"] and d["follow"] is None and d["control"] == ("no", 0.40)


def test_small_move_no_trigger():
    d = X.decide(CLOSE, candles(0.30, 0.34), btc_series(0.00001))
    assert d is not None and not d["trig"] and d["follow"] is None


def test_wide_spread_and_thin_volume_are_ineligible():
    assert X.decide(CLOSE, candles(0.30, 0.45), btc_series(0.01)) is None
    assert X.decide(CLOSE, candles(0.30, 0.34, vol=1.0), btc_series(0.01)) is None


def test_no_lookahead_future_klines_ignored():
    b = btc_series(0.01)
    z0 = X.btc_signal(b, CLOSE)
    for t in range(LOOK, LOOK + 600, 60):   # klines that end after the look
        b[t] = 1e6
    assert X.btc_signal(b, CLOSE) == z0


def test_missing_bitcoin_data_is_none():
    b = btc_series(0.01)
    for t in list(b)[:3000]:
        del b[t]
    assert X.btc_signal(b, CLOSE) is None


def test_verdict_words():
    good = dict(n=300, ev=20, pf=2.0, mean=3.0, z=6.0)
    bad = dict(n=300, ev=20, pf=1.0, mean=-1.0, z=0.0)
    S = {"W1": good, "W2": good, "W3": good}
    assert X.verdict(S, S, good, False)[0] == "NOT_YET_FALSIFIED"
    assert X.verdict({"W1": good, "W2": bad}, S, good, False)[0] == "FALSIFIED"
    assert X.verdict(S, S, dict(good, n=100), False)[0] == "NOT_ENOUGH_DATA"
    assert X.verdict(S, S, dict(good, z=2.0), False)[0] == "NOT_YET_FALSIFIED"


def test_payoff_ratio_and_universe():
    assert abs(X.payoff_ratio([("a", 60.0), ("b", -30.0), ("c", -30.0)]) - 2.0) < 1e-9
    assert not {"KXBTC15M", "KXETH15M", "KXDOGE15M", "KXGOLD15M"} & set(X.ASSETS)


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v(); print("ok", k)
