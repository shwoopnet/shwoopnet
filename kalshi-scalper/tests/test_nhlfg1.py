import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import nhlfg1 as n


def test_gid_is_event_suffix_shared_by_series():
    assert n.gid_of("KXNHLFIRSTGOAL-26JUN14CARVGK") == n.gid_of("KXNHLGOAL-26JUN14CARVGK") == "26JUN14CARVGK"


def test_clustered_uses_game_and_date():
    T = [dict(game="a", date="d", ask=0.2, win=True), dict(game="b", date="d", ask=0.2, win=False), dict(game="b", date="d", ask=0.1, win=False)]
    assert n.clustered(T, "game")["clusters"] == 2 and n.clustered(T, "date")["clusters"] == 1


def test_candidate_trades_needs_ladder_and_caps_two(tmp_path):
    c = n.sqlite3.connect(":memory:")
    c.executescript(n.SCHEMA)
    for i in range(9):
        c.execute("INSERT INTO rung VALUES(?,?,?,?)", (f"T{i}", "FG", "G", 1.0))
        c.execute("INSERT INTO candle VALUES(?,?,?,?)", (f"T{i}", 100, 0.08, 0.10))
    assert n.candidate_trades(c, "FG", "G", 1000) == 2
    c.execute("DELETE FROM candle WHERE ticker IN ('T0','T1')")
    assert n.candidate_trades(c, "FG", "G", 1000) == 0  # 7 valid quotes, under 8
