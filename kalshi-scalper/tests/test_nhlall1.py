import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import nhlall1 as n


def test_look_quote_uses_last_valid_before_lead():
    cs = [(100, 0.10, 0.12), (870, 0.10, 0.14), (881, 0.2, 0.9), (900, 0.1, 0.12)]
    assert n.look_quote(cs, 1000) == (0.10, 0.14)  # 880 is the cut; 881 is too late; 900 too late
    assert n.look_quote([(100, 0.0, 0.5)], 1000) is None  # spread over 0.10


def test_pick_two_is_by_hash_not_price():
    rows = [dict(ticker=f"T{i}", ask=0.1 + i / 100) for i in range(6)]
    a = n.pick_two(rows)
    b = n.pick_two(list(reversed(rows)))
    assert a == b and len(a) == 2


def test_terciles_and_assignment():
    cuts = n.terciles([1, 2, 3, 4, 5, 6])
    assert cuts == (3, 5)
    assert [n.tercile_of(x, cuts) for x in (1, 3, 5, 9)] == [0, 1, 2, 2]


def test_clustered_net_and_verdict():
    T = [dict(game="a", date="d", ask=0.2, win=True), dict(game="b", date="d", ask=0.2, win=False)]
    r = n.clustered(T, "game")
    assert r["n"] == 2 and r["clusters"] == 2
    assert n.clustered(T, "date")["clusters"] == 1
    assert n.verdict(100, [1, 1], 1, 2) == "NOT_ENOUGH_DATA"
    assert n.verdict(200, [1, 1], 1, 2) == "LEAD"
    assert n.verdict(200, [1, -1], 1, 2) == "FALSIFIED"
    assert n.verdict(200, [1, 1], 1, 1.2) == "FALSIFIED"
    assert n.verdict(200, [1, 1], -0.1, 2) == "FALSIFIED"


def test_terciles_frozen_and_old_block_size():
    import json, pathlib
    old = json.load(open(pathlib.Path(__file__).resolve().parents[1] / "workers" / "NHLALL1_FIRST61.json"))
    assert len(old) == 61 and n.CUTS == (2.75, 3.66) and n.OLD_TRADES == 122
