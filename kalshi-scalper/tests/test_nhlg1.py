import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import nhlg1 as n  # noqa: E402


def test_fee_net():
    assert n.fee(0.10) == math.ceil(0.07 * 10 * 0.09 * 100) / 100
    assert n.net(False, 0.10) < -0.10
    assert abs(n.net(True, 0.10) - (1 - 0.10 - n.fee(0.10) / 10)) < 1e-12


def test_poisson_tail():
    mu = 0.4
    assert abs(n.pois_ge(1, mu) - (1 - math.exp(-mu))) < 1e-12
    assert abs(n.pois_ge(2, mu) - (1 - math.exp(-mu) * (1 + mu))) < 1e-12
    assert n.pois_ge(0, mu) == 1.0
    assert n.pois_ge(1, mu) > n.pois_ge(2, mu) > n.pois_ge(3, mu)


def test_shrunk_rate_and_factor():
    assert n.shrunk_rate([1, 0, 0, 1], 0.2, 10) is None           # under 5 earlier games
    r = n.shrunk_rate([1, 0, 0, 0, 1], 0.2, 10)                   # (2 + 2) / 15
    assert abs(r - 4 / 15) < 1e-12
    assert n.def_factor([], 3.0, 1.0) == 1.0
    assert n.def_factor([5] * 20, 3.0, 0.0) == 1.0
    assert abs(n.def_factor([4] * 20, 3.0, 1.0) - ((80 + 30) / 30) / 3.0) < 1e-12


def test_only_last_twenty_games_count():
    old = [1] * 30 + [0] * 20
    assert n.shrunk_rate(old, 0.2, 0) == 0.005                     # the 30 old goals are outside the window


def test_fit_recovers_signal():
    rows = [([0, 0, 0, 0, 0, 0], [3] * 10, 0)] * 50 + [([1, 1, 1, 1, 1, 1], [3] * 10, 1)] * 50
    _, k, g, cnt = n.fit_params(rows, 0.3, 3.0)
    assert cnt == 100 and k == 5                                   # low shrinkage fits players with a clear rate


def test_cheap_side_never_favourite():
    assert n.cheap_side(0.05, 0.08) == ("yes", 0.08)
    s = n.cheap_side(0.80, 0.85)                                   # YES is 85c; NO costs 1 - bid = 20c
    assert s is not None and s[0] == "no" and abs(s[1] - 0.20) < 1e-12
    assert n.cheap_side(0.45, 0.50) is None                        # both sides above 30c


def test_pick_trades_two_per_game_ratio_and_control():
    rows = [dict(ticker=f"T{i}", ask=0.10, p_side=0.10 * r) for i, r in enumerate([4, 2.9, 3.0, 5, 3.5])]
    t = n.pick_trades(rows, True)
    assert [r["ticker"] for r in t] == ["T3", "T0"] and len(t) == 2
    assert len(n.pick_trades(rows, False)) == 2


def test_event_and_ticker_parsing():
    assert n.event_teams("KXNHLGOAL-26NOV03UTATOR") == ("UTA", "TOR")
    assert n.event_teams("KXNHLGOAL-26MAR01TBLNJD") == ("TBL", "NJD")
    assert n.player_team("KXNHLGOAL-26NOV03UTATOR-TORJROSLOVIC96-3") == "TOR"
    assert n.event_date("KXNHLGOAL-26NOV03UTATOR").day == 3
    assert n.norm_name("Mitch Marner Jr.") == "mitch marner"
    assert n.team_code("TB") == "TBL"


def test_split_thirds():
    lab = n.split_labels(9)
    assert lab == ["FIT"] * 6 + ["T1", "T2", "T2"]


def test_parse_box_skaters_only_with_toi():
    keys = ["blockedShots", "timeOnIce", "goals", "shotsTotal"]
    summ = {"boxscore": {"players": [{"team": {"abbreviation": "MTL"}, "statistics": [
        {"keys": keys, "athletes": [
            {"athlete": {"id": 1, "displayName": "Cole Caufield"}, "stats": ["0", "17:03", "2", "5"]},
            {"athlete": {"id": 2, "displayName": "Sat Out"}, "stats": ["0", "0:00", "0", "0"]}]},
        {"keys": ["saves", "timeOnIce"], "athletes": [{"athlete": {"id": 3, "displayName": "Goalie"}, "stats": ["20", "60:00"]}]}]}]}}
    rows = n.parse_box(summ)
    assert len(rows) == 1 and rows[0]["goals"] == 2 and rows[0]["shots"] == 5 and rows[0]["toi"] == 17 * 60 + 3 and rows[0]["nm"] == "cole caufield"


def test_cluster_stats_and_pf():
    cs = n.cluster_stats({"a": [1.0, 1.0], "b": [-1.0]})
    assert cs[0] == 3 and abs(cs[1] - 1 / 3) < 1e-12
    assert n.profit_factor([2, -1]) == 2 and n.profit_factor([1]) == float("inf")
