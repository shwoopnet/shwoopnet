import math

from scalper import soccerelo1 as e


def test_p3_sums_to_one_and_symmetry():
    h, d, a = e.p3(1500, 1500, 0, 1.0)
    assert abs(h + d + a - 1) < 1e-12 and abs(h - a) < 1e-12 and abs(d - 1 / 3) < 1e-9
    h2, d2, a2 = e.p3(1600, 1500, 0, 1.0)
    assert h2 > h and a2 < a


def test_home_advantage_and_draw_param():
    h, _, a = e.p3(1500, 1500, 80, 1.0)
    assert h > a
    assert e.p3(1500, 1500, 0, 1.4)[1] > e.p3(1500, 1500, 0, 0.6)[1]


def test_update_conserves_and_moves_toward_result():
    rh, ra = e.update(1500, 1500, "H", 0, 1.0, 20)
    assert rh > 1500 and abs((rh + ra) - 3000) < 1e-9
    rh, ra = e.update(1500, 1500, "A", 0, 1.0, 20)
    assert rh < 1500
    rh, ra = e.update(1500, 1500, "D", 0, 1.0, 20)
    assert abs(rh - 1500) < 1e-9


def test_prediction_needs_five_games_and_is_walk_forward():
    ms = [dict(start=1000 + i, lg="x", home="A", away="B", res="H", key=str(i)) for i in range(8)]
    out, R = e.run_elo(ms, 60, 1.0, 20)
    assert [p is None for _, p in out][:5] == [True] * 5 and out[6][1] is not None
    ms2 = [dict(m) for m in ms]
    ms2[7]["res"] = "A"
    out2, _ = e.run_elo(ms2, 60, 1.0, 20)
    assert out[7][1] == out2[7][1]


def test_fit_runs():
    ms = [dict(start=i * 8000, lg="x", home="T%d" % (i % 6), away="T%d" % ((i + 1) % 6), res="H" if i % 3 else "D", key=str(i)) for i in range(300)]
    ll, ha, nu, k, n = e.fit(ms)
    assert math.isfinite(ll) and n > 0


def test_treated_rule():
    cand = {"T-H": {900: (0.05, 0.07)}, "T-A": {900: (0.80, 0.82)}}
    row = dict(event="E", espn=dict(start=1100), elo={"T-H": 0.30, "T-A": 0.10})
    out = e.treated_rows([row], cand)
    by = {x["t"]: x for x in out}
    assert by["T-H"]["treated"] and by["T-H"]["side"] == "Y"
    assert by["T-A"]["side"] == "N" and abs(by["T-A"]["ask"] - 0.20) < 1e-9 and not by["T-A"]["treated"] is False  # NO on the home side at 20c, elo 0.90 >= 0.60


def test_look_lead_120s():
    cand = {"T-H": {1000: (0.05, 0.07)}}
    row = dict(event="E", espn=dict(start=1100), elo={"T-H": 0.30})
    assert e.treated_rows([row], cand) == []
