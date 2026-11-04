import math
from scalper import xi1


def test_fee_and_net():
    assert xi1.fee(0.10) == 0.07 * 0 + math.ceil(round(0.07 * 10 * 0.1 * 0.9 * 100, 9)) / 100
    assert abs(xi1.net(True, 0.10) - (0.9 - xi1.fee(0.10) / 10)) < 1e-12
    assert xi1.net(False, 0.10) < -0.10


def test_look_ask_respects_lead_and_validity():
    kick = 100000
    cs = [(kick - 1801 - 60, 0.05, 0.08), (kick - 1800, 0.06, 0.09), (kick - 1799, 0.0, 0.5), (kick - 600, 0.01, 0.02)]
    assert xi1.look_ask(cs, kick) == 0.09  # candle ending exactly 1800 s before is allowed; later ones are not
    assert xi1.look_ask([(kick - 1900, 0.0, 0.5)], kick) is None  # spread over 0.10 invalid


def test_cheap_band():
    assert xi1.cheap(0.03) and xi1.cheap(0.30) and not xi1.cheap(0.31) and not xi1.cheap(0.02) and not xi1.cheap(None)


def test_ticker_parsing():
    assert xi1.ticker_jersey("KXEPLGOAL-26SEP20FULMUN-MUNPDORGU13-1") == "13"
    assert xi1.ticker_jersey("KXUCLGOAL-26SEP10BMUBOG-BMUDDAIBE47-1") == "47"
    assert xi1.surname_key("Patrick Dorgu: 1+ goals") == "dorgu"
    assert xi1.norm("Müller") == "muller"


def test_position_group_and_minutes():
    assert xi1.pos_group("Attacking Midfielder") == "M" and xi1.pos_group("Center Forward") == "A"
    assert xi1.pos_group("Center Back") == "D" and xi1.pos_group("Goalkeeper") == "G"
    assert xi1.minutes_played(True, None, 4500.0) == 75.0
    assert xi1.minutes_played(True, None, None) == 90.0
    assert xi1.minutes_played(False, 4463.0, None) == 90.0 - 4463.0 / 60.0
    assert xi1.minutes_played(False, None, None) == 25.0


def test_model_shrinks_and_is_monotone():
    r = 0.30
    assert abs(xi1.shrunk_rate(0, 0, r) - r) < 1e-12  # no data: the position prior
    assert xi1.shrunk_rate(3, 270, r) > r > xi1.shrunk_rate(0, 270, r)
    assert 0 < xi1.p_goal(0.3, 80) < xi1.p_goal(0.6, 80) < 1


def test_pick_two_is_hash_ordered_and_price_blind():
    rows = [dict(ticker=f"T{i}", ask=0.1 + i / 100) for i in range(6)]
    a = xi1.pick_two_by_hash(rows)
    b = xi1.pick_two_by_hash([dict(ticker=r["ticker"], ask=0.3) for r in rows])
    assert [r["ticker"] for r in a] == [r["ticker"] for r in b] and len(a) == 2


def test_cluster_stats_and_halves_and_verdict():
    tr = [dict(ask=0.10, win=(i % 5 == 0), match=i // 2, date=i // 4, kick=1000 + i) for i in range(40)]
    st = xi1.cluster_stats(tr)
    assert st["n"] == 40 and abs(st["win"] - 0.2) < 1e-9 and st["se"] > 0
    h1, h2 = xi1.halves(tr)
    assert len(h1) + len(h2) == 40
    assert xi1.verdict(149, 80, 1, 1, 2, 1) == "NOT_ENOUGH_DATA"
    assert xi1.verdict(200, 59, 1, 1, 2, 1) == "NOT_ENOUGH_DATA"
    assert xi1.verdict(200, 80, 1, -1, 2, 1) == "FALSIFIED"
    assert xi1.verdict(200, 80, 1, 1, 1.4, 1) == "FALSIFIED"
    assert xi1.verdict(200, 80, 1, 1, 2.0, 1, beats_control=False) == "FALSIFIED"
    assert xi1.verdict(200, 80, 1, 1, 2.0, 0.1) == "LEAD"
