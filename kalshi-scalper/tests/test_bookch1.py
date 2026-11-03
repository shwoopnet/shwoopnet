"""BOOKCH1 evaluator on synthetic books (no recorder data, no outcome). Research only."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import bookch1 as b  # noqa: E402
from scalper.fwdeval import NoData  # noqa: E402
from scalper.quote2b import Poll  # noqa: E402

CLOSE = 1_800_000_000


def poll(t, yb=(0.70,), ybs=(10,), nb=(0.25,), nbs=(100,)):
    """YES bid 0.70 -> NO ask 0.30; NO bid 0.25 -> YES ask 0.75: the cheaper side is NO (ask 0.30)."""
    return Poll(t, yb, ybs, nb, nbs)


def book(cheap_bids=(40, 30, 20, 10, 10), other_bids=(10, 10, 5, 5, 5), early_cheap=(40, 30, 20, 10, 10), fill_size=50):
    """NO is cheaper. NO bids are the cheap side's bids (nb), YES bids are the other side's (yb)."""
    ys = [0.70, 0.69, 0.68, 0.67, 0.66]
    ns = [0.25, 0.24, 0.23, 0.22, 0.21]
    early = poll(CLOSE - 360, ys, other_bids, ns, early_cheap)
    look = poll(CLOSE - 180.5, ys, other_bids, ns, cheap_bids)
    # NO ask = 1 - best YES bid = 0.30; the size at the NO ask is the best YES bid size
    fill = poll(CLOSE - 178.9, ys, (fill_size,) + tuple(other_bids[1:]), ns, cheap_bids)
    return [early, look, fill]


def hist(values, key="ratio", start=CLOSE - 86_000, step=900):
    return {start + i * step: {"side": "no", "ask": 0.3, key: v} for i, v in enumerate(values)}


def test_cheaper_side_and_s5():
    p = poll(1)
    assert b.cheaper(p) == ("no", pytest.approx(0.30))
    assert b.cheaper(Poll(1, (0.5,), (1,), (0.5,), (1,))) is None       # equal asks
    assert b.cheaper(Poll(1, (), (), (0.5,), (1,))) is None             # missing bid
    assert b.s5([1, 2, 3, 4, 5, 6]) == 15


def test_look_stats_ratio_and_drop():
    st = b.look_stats(book(cheap_bids=(30, 20, 10, 5, 5), early_cheap=(40, 30, 20, 10, 10)), CLOSE)
    assert st["side"] == "no" and st["ratio"] == pytest.approx(70 / 35)
    assert st["drop"] == pytest.approx((70 - 110) / 110)


def test_quantile_type7():
    assert b.quantile([1, 2, 3, 4], 0.5) == 2.5
    assert b.quantile([0, 10], 0.1) == 1.0
    assert b.quantile(list(range(100)), 2 / 3) == pytest.approx(66.0)


def test_history_window_and_minimum():
    h = hist([1.0] * 47)
    assert b.trailing_cut(h, CLOSE, "ratio", 2 / 3) is None            # 47 < 48
    h = hist([1.0] * 48)
    assert b.trailing_cut(h, CLOSE, "ratio", 2 / 3) == 1.0
    # a window that closed after T-900 (the previous window) or before T-86400 is not used
    h[CLOSE - 600] = {"ratio": 999.0}
    h[CLOSE - 90_000] = {"ratio": 999.0}
    assert b.trailing_cut(h, CLOSE, "ratio", 2 / 3) == 1.0


def test_ratio_trigger_and_trade():
    bk = book()                                                        # R = 110/35 = 3.14
    d, why = b.decide(bk, CLOSE, hist([1.0] * 48))
    assert why == "trade" and d["side"] == "no" and d["entry"] == pytest.approx(0.30) and d["t"] == pytest.approx(CLOSE - 178.9)
    d, why = b.decide(bk, CLOSE, hist([5.0] * 48))                      # below the tertile cut
    assert d is None and why == "below tertile"
    d, why = b.decide(bk, CLOSE, hist([3.14285714285714286] * 48))      # strictly above, a tie is not
    assert d is None


def test_nodata_not_no_trade():
    with pytest.raises(NoData):
        b.forward_eval({"series": "KXBTC15M", "close_ts": CLOSE, "polls": book()}, {"_history": hist([1.0] * 10)})
    with pytest.raises(NoData):                                        # no look poll
        b.forward_eval({"series": "KXBTC15M", "close_ts": CLOSE, "polls": [poll(CLOSE - 400)]}, {"_history": hist([1.0] * 48)})
    with pytest.raises(NoData):                                        # no fill poll within 20 s
        b.forward_eval({"series": "KXBTC15M", "close_ts": CLOSE, "polls": book()[:2]}, {"_history": hist([1.0] * 48)})


def test_band_and_size_gates():
    # cheaper side ask 0.60 is out of band: no trade
    ys, ns = [0.40], [0.45]
    pl = [Poll(CLOSE - 360, ys, [10], ns, [10]), Poll(CLOSE - 181, ys, [10], ns, [100]), Poll(CLOSE - 179, ys, [50], ns, [100])]
    assert b.decide(pl, CLOSE, hist([0.1] * 48))[0] is None
    # thin fill: fewer than 10 contracts at the ask
    assert b.decide(book(fill_size=9), CLOSE, hist([1.0] * 48))[1] == "fill out of band or thin"
    # ask under 5c
    ys, ns = [0.97], [0.01]
    pl = [Poll(CLOSE - 360, ys, [10], ns, [10]), Poll(CLOSE - 181, ys, [10], ns, [100]), Poll(CLOSE - 179, ys, [50], ns, [100])]
    assert b.decide(pl, CLOSE, hist([0.1] * 48))[1] == "ask out of band"


def test_withdrawal_alternative():
    bk = book(cheap_bids=(10, 10, 5, 5, 5), early_cheap=(40, 30, 20, 10, 10))    # D = (35-110)/110 = -0.68
    d, why = b.decide(bk, CLOSE, hist([-0.2] * 48, key="drop"), "withdrawal")
    assert why == "trade" and d["side"] == "no"
    assert b.decide(bk, CLOSE, hist([-0.9] * 48, key="drop"), "withdrawal")[0] is None   # not below the 10th percentile
    flat = book()                                                                         # D = 0: not a withdrawal
    assert b.decide(flat, CLOSE, hist([0.5] * 48, key="drop"), "withdrawal")[1] == "no withdrawal"


def test_no_lookahead_in_stats():
    base = book()
    st1 = b.look_stats(base, CLOSE)
    st2 = b.look_stats(base + [poll(CLOSE - 60, ybs=(1,) * 5, nbs=(999,) * 5, yb=(0.7,), nb=(0.25,))], CLOSE)
    assert st1 == st2                                                  # polls after the look change nothing


def test_forward_eval_interface_and_market_filter():
    w = {"series": "KXBTC15M", "close_ts": CLOSE, "polls": book()}
    r = b.forward_eval(w, {"_history": hist([1.0] * 48)})
    assert r["side"] == "no" and r["exit"] is None and abs(r["entry"] - 0.30) < 1e-9
    assert b.forward_eval(dict(w, series="KXETH15M"), {"_history": hist([1.0] * 48)}) is None
    assert b.forward_eval(dict(w, series="KXXRP15M"), {"_history": hist([1.0] * 48), "series": "KXBTC15M"}) is None
