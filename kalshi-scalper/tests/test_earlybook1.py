from scalper import earlybook1 as e


def test_devig_sums_to_one():
    h, a = e.devig(-150, 130)
    assert abs(h + a - 1) < 1e-12 and h > a


def test_look_at_picks_last_valid_before_lead():
    c = {100: (0.1, 0.12), 200: (0.1, 0.12), 300: (0.0, 0.5)}
    assert e.look_at(c, 400, 100) == 200
    assert e.look_at(c, 400, 250) == 100


def test_treated_needs_ratio_band_and_same_side():
    rows = [dict(ask=.10, q_open=.31, open_same_side=True), dict(ask=.10, q_open=.31, open_same_side=False),
            dict(ask=.40, q_open=1.5, open_same_side=True), dict(ask=.10, q_open=.29, open_same_side=True)]
    assert len(e.treated(rows)) == 1


def test_score_flags_not_enough():
    rows = [dict(ticker="a", ask=.1, q_open=.4, open_same_side=True, st=1)]
    assert "NOT_ENOUGH_DATA: under 150 treated" in e.score(rows, {"a": True}, "x")
