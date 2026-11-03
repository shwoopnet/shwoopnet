"""NEWLIST1 helpers on hand-built data. Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import newlist1 as n  # noqa: E402


def test_fee_rounds_up_per_order_of_ten():
    assert abs(n.fee_per_contract(0.5) - 0.018) < 1e-9       # 7% x 10 x .25 = 17.5c -> 18c -> 1.8c
    assert abs(n.fee_per_contract(0.1) - 0.007) < 1e-9       # 6.3c -> 7c
    assert abs(n.fee_per_contract(0.3) - 0.015) < 1e-9       # 14.7c -> 15c


def test_priced_rejects_the_empty_book():
    assert not n.priced(0.0, 0.99)
    assert not n.priced(0.0, 1.0)
    assert not n.priced(0.4, None)
    assert n.priced(0.05, 0.30)
    assert not n.priced(0.30, 0.30)


def test_side_entry_cheap_side_and_hard_limit():
    assert n.side_entry(0.10, 0.12, 0.05, 0.30) == ("yes", 0.12)
    s = n.side_entry(0.88, 0.90, 0.05, 0.30)               # NO ask = 1 - 0.88 = 0.12
    assert s[0] == "no" and abs(s[1] - 0.12) < 1e-9
    assert n.side_entry(0.40, 0.55, 0.05, 0.30) is None    # nothing cheap
    assert n.side_entry(0.02, 0.31, 0.05, 0.30) is None    # YES ask above the hard limit
    assert n.side_entry(0.60, 0.62, 0.85, 0.97) is None


def test_look_candle_is_first_in_window_and_never_later():
    cs = [(100, .1, .2), (200, .1, .2), (300, .1, .2)]
    assert n.look_candle(cs, 150, 250) == (200, .1, .2)
    assert n.look_candle(cs, 150, 200) is None
    assert n.look_candle(cs, 400, 500) is None


def test_late_candle_is_last_at_or_before_the_limit():
    cs = [(100, .1, .2), (200, .1, .2), (300, .1, .2)]
    assert n.late_candle(cs, 250) == (200, .1, .2)
    assert n.late_candle(cs, 50) is None


def test_trade_net_win_and_loss():
    net, win = n.trade_net("yes", 0.2, "yes")
    assert win == 1.0 and abs(net - (1 - 0.2 - n.fee_per_contract(0.2))) < 1e-9
    net, win = n.trade_net("no", 0.2, "yes")
    assert win == 0.0 and net < -0.2


def test_summarize_pf():
    rows = [("d1", 1, 0.8, 1.0, 0.2), ("d2", 1, -0.2, 0.0, 0.2), ("d3", 1, -0.2, 0.0, 0.2)]
    s = n.summarize(rows)
    assert s["n"] == 3 and abs(s["pf"] - 2.0) < 1e-6


if __name__ == "__main__":
    fails = 0
    for k, v in sorted(globals().items()):
        if k.startswith("test_"):
            try:
                v(); print("ok", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
