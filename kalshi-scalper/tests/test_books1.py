import json, math
from scalper import books1 as b


def test_implied_and_devig():
    assert abs(b.implied(100) - 0.5) < 1e-9
    assert abs(b.implied(-200) - 2 / 3) < 1e-9
    h, a = b.devig(-110, -110)
    assert abs(h - 0.5) < 1e-9 and abs(h + a - 1) < 1e-9
    h, a = b.devig(-260, 210)
    assert abs(h + a - 1) < 1e-9 and 0.68 < h < 0.70


def test_fee_and_net():
    assert b.fee(0.05) == 0.04  # 0.7*0.0475=0.03325 -> 0.04
    assert abs(b.net(True, 0.10) - (1 - 0.10 - b.fee(0.10) / 10)) < 1e-9
    assert b.net(False, 0.10) < -0.10


def test_pick():
    assert b.pick(0.2, 0.8, (0.1, 0.12), (0.85, 0.9)) == ("H", 0.12, 0.2)
    assert b.pick(0.2, 0.8, (0.1, 0.12), (0.1, 0.12)) is None  # tie
    assert b.pick(0.5, 0.5, (0.4, 0.45), (0.5, 0.55)) is None  # not cheap
    assert b.pick(0.5, 0.5, (0.0, 0.02), (0.9, 0.99)) is None  # under 3c


def test_look_last_before_lead():
    ch = {100: (0.1, 0.12), 200: (0.1, 0.12), 300: (0.1, 0.12)}
    ca = {100: (0.8, 0.85), 200: (0.8, 0.85), 300: (0.0, 0.9)}
    assert b.look(ch, ca, 200 + b.LEAD) == 200
    assert b.look(ch, ca, 300 + b.LEAD) == 200  # 300 invalid (wide)


def test_moneylines(tmp_path):
    p = tmp_path / "1.json"
    p.write_text(json.dumps({"items": [{"homeTeamOdds": {"close": {"moneyLine": {"american": "-140"}}},
                                         "awayTeamOdds": {"close": {"moneyLine": {"american": "+130"}}}}]}))
    assert b.moneylines(p) == (-140.0, 130.0)
    assert b.moneylines(tmp_path / "x.json") is None
