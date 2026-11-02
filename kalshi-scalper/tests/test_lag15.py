import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import lag15 as L

CLOSE = 1_800_000_000 - (1_800_000_000 % 900)
LOOK = CLOSE - 60


def klines(base=100.0, step=0.0, noise=0.05):
    """closes whose kline opens at LOOK-360 .. LOOK-60 (ends LOOK-300 .. LOOK) and some later ones."""
    out = {}
    for k in range(-8, 4):
        t = LOOK - 60 + 60 * k
        out[t] = base + step * k + (noise if k % 2 else -noise)
    return out


def candles(bid, ask, vol=5.0):
    return [(LOOK - 240 + 60 * i, bid, ask, vol) for i in range(5)]


def test_phi_and_fee():
    assert abs(L.phi(0) - 0.5) < 1e-12
    assert abs(L.fee(0.5) - math.ceil(0.07 * 10 * 0.25 * 100) / 100 / 10) < 1e-12   # 0.175 -> 0.18 for 10 contracts
    assert abs(L.fee(0.9) - 0.007) < 1e-9  # 0.063 -> 0.07 for 10 contracts


def test_sigma_none_when_minute_missing_and_positive_otherwise():
    assert L.sigma_per_s([1, 1, 1, 1, 1, None]) is None
    assert L.sigma_per_s([1, 1, 1, 1, 1, 1]) is None          # zero volatility: no trade
    assert L.sigma_per_s([100, 100.1, 100, 100.1, 100, 100.1]) > 0


def test_p_yes_monotone_in_spot():
    a = L.p_yes(100.0, 100.0, 1e-4)
    assert abs(a - 0.5) < 1e-9
    assert L.p_yes(100.2, 100.0, 1e-4) > a > L.p_yes(99.8, 100.0, 1e-4)


def test_buys_yes_when_spot_far_above_strike_and_ask_lags():
    k = klines(base=100.0)
    d = L.decide(CLOSE, 99.9, candles(0.55, 0.60), k, 0.03)
    assert d and d["side"] == "yes" and d["price"] == 0.60


def test_buys_no_when_spot_far_below_strike_and_bid_lags():
    k = klines(base=100.0)
    d = L.decide(CLOSE, 100.5, candles(0.40, 0.45), k, 0.03)
    assert d and d["side"] == "no" and abs(d["price"] - 0.60) < 1e-9


def test_cheap_side_is_banned():
    k = klines(base=100.0)
    d = L.decide(CLOSE, 99.9, candles(0.10, 0.15), k, 0.03)
    assert d and d["side"] is None and d["banned"]


def test_no_edge_when_quote_matches_model():
    k = klines(base=100.0)
    d = L.decide(CLOSE, 99.9, candles(0.97, 0.98), k, 0.03)
    assert d and d["side"] is None


def test_volume_rule_and_spread_rule():
    k = klines()
    assert L.decide(CLOSE, 99.9, candles(0.55, 0.60, vol=1.0), k, 0.03) is None   # 5 contracts total
    assert L.decide(CLOSE, 99.9, candles(0.40, 0.60), k, 0.03) is None            # spread 0.20


def test_no_lookahead_later_data_changes_nothing():
    k = klines()
    cs = candles(0.55, 0.60)
    base = L.decide(CLOSE, 99.9, cs, k, 0.03)
    k2 = dict(k)
    for t in list(k2):
        if t > LOOK - 60:           # klines opening after the one that ends at the look
            k2[t] = 1.0
    cs2 = cs + [(LOOK + 60, 0.01, 0.02, 99.0), (LOOK + 1, 0.30, 0.31, 99.0)]
    assert L.decide(CLOSE, 99.9, cs2, k2, 0.03) == base


def test_stale_quote_rejected():
    k = klines()
    old = [(LOOK - 400 + 60 * i, 0.55, 0.60, 5.0) for i in range(2)]
    assert L.decide(CLOSE, 99.9, old, k, 0.03) is None


def test_pnl_signs():
    assert L.pnl("yes", 0.60, "yes") > 0 > L.pnl("yes", 0.60, "no")
    assert L.pnl("no", 0.60, "no") > 0 > L.pnl("no", 0.60, "yes")
    assert L.pnl("yes", 0.6, "yes", 1.2) < L.pnl("yes", 0.6, "yes")


def test_overlap_share():
    assert L.overlap_share([0.9, 0.95, 0.5]) > 0.5
    assert L.overlap_share([0.5, 0.6, 0.9]) < 0.5
    assert L.overlap_share([]) == 0.0


def test_thirds_equal_by_date():
    w = L.thirds([f"2026-10-{d:02d}" for d in range(1, 10)])
    assert [w[f"2026-10-{d:02d}"] for d in (1, 3, 4, 6, 7, 9)] == ["W1", "W1", "W2", "W2", "W3", "W3"]


def mk(pf_, n=100, mean=3.0, z=6.0):
    return dict(n=n, ev=10, pf=pf_, mean=mean, z=z)


def test_verdicts():
    S = {w: mk(2.0) for w in ("W1", "W2", "W3")}
    P = mk(2.0, n=300, mean=3.0, z=6.0)
    assert L.verdict(S, S, 0.1, 0.2, True, P)[0] == "NOT_YET_FALSIFIED"
    assert L.verdict(S, S, 0.2, 0.1, True, P)[0] == "FALSIFIED"             # Brier worse
    S2 = dict(S, W2=mk(1.2))
    assert L.verdict(S2, S2, 0.1, 0.2, False, P)[0] == "FALSIFIED"
    assert L.verdict(S, S, 0.1, 0.2, True, mk(2.0, n=100))[0] == "NOT_ENOUGH_DATA"
    assert L.verdict(S, S, 0.2, 0.1, True, mk(2.0, n=100))[0] == "FALSIFIED"
    assert L.verdict(S, S, 0.1, 0.2, True, mk(2.0, n=300, z=2.0))[0] == "FALSIFIED"  # under the deflated bar


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
