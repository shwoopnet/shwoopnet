import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from datetime import datetime, timezone
from scalper import nflanytd1 as n


def test_split_event_and_alias():
    assert n.split_event("KXNFLANYTD-26FEB08SEANE")[1] == ("SEA", "NE")
    assert n.split_event("KXNFLANYTD-25SEP04DALPHI")[1] == ("DAL", "PHI")
    assert n.split_event("KXNFLANYTD-25NOV02LACJAC")[1] == ("LAC", "JAX")
    assert n.split_event("KXNFLANYTD-25NOV02WASLA")[1] == ("WSH", "LAR")
    assert n.split_event("KXNFLANYTD-25NOV02XXXYY") is None


def test_match_game_by_et_date_and_teams():
    ts = int(datetime(2025, 9, 5, 0, 20, tzinfo=timezone.utc).timestamp())  # Sep 4 8:20pm ET
    g = [("1", ts, "PHI", "DAL"), ("2", ts + 86400 * 3, "PHI", "DAL")]
    assert n.match_game("KXNFLANYTD-25SEP04DALPHI", g) == ("1", ts)
    assert n.match_game("KXNFLANYTD-25SEP04DALNYG", g) is None


def test_look_quote_and_cheap_bounds():
    cs = [(100, 0.10, 0.12), (870, 0.10, 0.14), (881, 0.2, 0.3), (900, 0.1, 0.12)]
    assert n.look_quote(cs, 1000) == (0.10, 0.14)
    assert n.look_quote([(100, 0.0, 0.5)], 1000) is None
    assert n.is_cheap(0.03) and n.is_cheap(0.30) and not n.is_cheap(0.31) and not n.is_cheap(0.02) and not n.is_cheap(None)


def test_pick_two_hash_not_price():
    rows = [dict(ticker=f"T{i}", ask=0.05 + i / 100) for i in range(6)]
    assert n.pick_two(rows) == n.pick_two(list(reversed(rows))) and len(n.pick_two(rows)) == 2


def test_terciles_clustered_verdict():
    assert n.terciles([1, 2, 3, 4, 5, 6]) == (3, 5)
    assert [n.tercile_of(x, (3, 5)) for x in (1, 3, 5, 9)] == [0, 1, 2, 2]
    T = [dict(game="a", date="d", ask=0.2, win=True), dict(game="b", date="d", ask=0.2, win=False)]
    assert n.clustered(T, "game")["clusters"] == 2 and n.clustered(T, "date")["clusters"] == 1
    assert n.verdict(100, [1, 1], 1, 2) == "NOT_ENOUGH_DATA"
    assert n.verdict(200, [1, 1], 1, 2) == "LEAD"
    assert n.verdict(200, [1, -1], 1, 2) == "FALSIFIED"
    assert n.verdict(200, [1, 1], 1, 1.2) == "FALSIFIED"
    assert n.verdict(200, [1, 1], -0.1, 2) == "FALSIFIED"


def test_count_td_scorers():
    summ = {"boxscore": {"players": [{"statistics": [
        {"name": "rushing", "labels": ["CAR", "YDS", "AVG", "TD"], "athletes": [{"athlete": {"id": "1"}, "stats": ["5", "20", "4", "1"]}, {"athlete": {"id": "2"}, "stats": ["5", "20", "4", "0"]}]},
        {"name": "receiving", "labels": ["REC", "YDS", "AVG", "TD"], "athletes": [{"athlete": {"id": "1"}, "stats": ["5", "20", "4", "1"]}, {"athlete": {"id": "3"}, "stats": ["5", "20", "4", "2"]}]},
        {"name": "passing", "labels": ["C/ATT", "YDS", "TD"], "athletes": [{"athlete": {"id": "9"}, "stats": ["1/2", "20", "3"]}]}]}]}}
    assert n.count_td_scorers(summ) == 2
