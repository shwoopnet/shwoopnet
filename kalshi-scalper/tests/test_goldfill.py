"""GOLDFILL fill engine on a synthetic fixture (no market data)."""
from scalper.goldfill import rest_fill, side_events, summarize_path, limit_for


def test_queue_then_through():
    ev = side_events("yes", [(10, 0.90, 3, -1), (20, 0.90, 4, -1), (40, 0.899, 1, -1)])
    f = rest_fill(0.90, 5, 5, 1, ev, [], 300)["fills"]
    s = summarize_path(f, 1, 5)
    assert s[30] == 2 and s[60] == 5 and f[-1][3] == "through"


def test_no_side_mapping_and_ask_lifted():
    ev = side_events("no", [(10, 0.08, 3, 1)])          # a taker buys YES at 0.08 = sells NO at 0.92 into our NO bid
    assert rest_fill(0.92, 2, 0, 1, ev, [], 300)["fills"][0][3] == "at"
    ev = side_events("no", [(10, 0.085, 1, -1)])        # a taker buys NO at 0.915: an ask under our 0.92 bid existed
    assert rest_fill(0.92, 2, 9, 1, ev, [], 300)["fills"][0][3] == "ask_lifted"


def test_trades_before_live_and_moving_away_do_not_fill():
    ev = side_events("yes", [(0.5, 0.80, 50, -1), (10, 0.91, 50, -1)])
    assert rest_fill(0.90, 1, 0, 1, ev, [(20, 0.95)], 300)["fills"] == []


def test_limits():
    assert limit_for("IN1C", 0.93, 0.925) == 0.92 and limit_for("IN01", 0.93, 0.929) == 0.929 and limit_for("BID", 0.93, 0.92) == 0.92
