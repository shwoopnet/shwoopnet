from scalper import chart1 as c


def test_fee_rounds_up():
    assert c.fee(0.5) == 0.02
    assert c.fee(0.9) == 0.01


def test_lead_tie_and_short():
    assert c.lead_title(["A", "A", "B", "B"]) is None
    assert c.lead_title(["A", "A"]) is None
    assert c.lead_title(["A", "A", "B", "A"]) == "A"


def test_decide_edge():
    assert c.decide(["A"] * 4, {"A": 0.70}, 0.85) == ("A", 0.70)
    assert c.decide(["A"] * 4, {"A": 0.80}, 0.85) is None


def test_pnl():
    assert abs(c.pnl(0.7, True) - (0.3 - c.fee(0.7))) < 1e-9
    assert c.pnl(0.7, False) < -0.7
