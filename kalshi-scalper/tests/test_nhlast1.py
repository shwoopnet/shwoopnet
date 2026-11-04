import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import nhlast1 as n


def test_game_key_same_for_both_series():
    assert n.game_key("KXNHLAST-26JUN14CARVGK") == n.game_key("KXNHLPTS-26JUN14CARVGK")


def test_order_defers_goal_sample_games():
    evs = ["KXNHLAST-26JUN14CARVGK", "KXNHLAST-26JUN15BOSNYR", "KXNHLAST-26JUN16TORMTL"]
    plain = sorted(evs, key=n.game_key)
    o = n.order_games(evs, {plain[0]})
    assert o[-1] == plain[0] and o[:2] == plain[1:]


def test_e_fit_uses_first_two_thirds_only():
    G = [dict(scorers=s) for s in (4, 6, 100)]
    assert n.e_fit(G) == 5.0
    assert n.e_fit([]) != n.e_fit([])  # nan


def test_under_round():
    assert n.under_round(3.0, 3.5) and not n.under_round(3.5, 3.5)
