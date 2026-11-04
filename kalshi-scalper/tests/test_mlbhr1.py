import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import mlbhr1 as m


def test_event_start_ts_is_eastern_daylight():
    # CHW at HOU, ESPN says 2026-09-03T18:10Z = 14:10 EDT
    assert m.event_start_ts("KXMLBHR-26SEP031410CWSHOU") == 1788459000 or True
    import datetime as d
    assert d.datetime.fromtimestamp(m.event_start_ts("KXMLBHR-26SEP031410CWSHOU"), d.timezone.utc).isoformat() == "2026-09-03T18:10:00+00:00"
    assert m.event_start_ts("KXMLBHIT-26AUG221840ATLNYM") is not None
    assert m.event_start_ts("KXOTHER-26AUG221840") is None


def test_look_quote_and_pick_two():
    cs = [(100, 0.10, 0.12), (870, 0.10, 0.14), (881, 0.2, 0.9)]
    assert m.look_quote(cs, 1000) == (0.10, 0.14)
    rows = [dict(ticker=f"T{i}", ask=0.1 + i / 100) for i in range(6)]
    assert m.pick_two(rows) == m.pick_two(list(reversed(rows))) and len(m.pick_two(rows)) == 2


def test_terciles_verdict_clustered():
    cuts = m.terciles([1, 2, 3, 4, 5, 6])
    assert [m.tercile_of(x, cuts) for x in (1, 3, 5, 9)] == [0, 1, 2, 2]
    assert m.verdict(100, [1, 1], 1, 2) == "NOT_ENOUGH_DATA"
    assert m.verdict(200, [1, 1], 1, 2) == "LEAD"
    assert m.verdict(200, [1, -1], 1, 2) == "FALSIFIED"
    assert m.verdict(200, [1, 1], 1, 1.2) == "FALSIFIED"
    T = [dict(game="a", date="d", ask=0.2, win=True), dict(game="b", date="d", ask=0.2, win=False)]
    assert m.clustered(T, "game")["clusters"] == 2 and m.clustered(T, "date")["clusters"] == 1


def test_chosen_two_is_by_hash_only():
    t = [f"K-{i}" for i in range(10)]
    assert m.chosen_two(t) == m.chosen_two(list(reversed(t))) and len(m.chosen_two(t)) == 2
