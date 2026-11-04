import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import props1 as p  # noqa: E402


def test_fee_and_net():
    assert p.fee(0.10) == math.ceil(0.07 * 10 * 0.09 * 100) / 100
    assert abs(p.net(True, 0.10) - (1 - 0.10 - p.fee(0.10) / 10)) < 1e-12
    assert p.net(False, 0.10) < -0.10


def test_norm_name_folds_accents_and_suffixes():
    assert p.norm_name("Nikola Jokić") == "nikola jokic"
    assert p.norm_name("Jaren Jackson Jr.") == p.norm_name("jaren jackson")


def test_nb_sf_matches_direct_sum_and_poisson_limit():
    mu, r = 4.0, 5.0
    direct = 1 - sum(math.exp(p.nb_logpmf(x, mu, r)) for x in range(0, 7))
    assert abs(p.nb_sf(6.5, mu, r) - direct) < 1e-9
    pois = 1 - sum(math.exp(-mu) * mu ** x / math.factorial(x) for x in range(0, 7))
    assert abs(p.nb_sf(6.5, mu, 1e6) - pois) < 1e-3
    assert p.nb_sf(-0.5, mu, r) == 1.0


def test_shrink_needs_three_priors_and_pulls_to_league():
    assert p.shrunk_mean([5, 6], 10.0, 4) is None
    mu = p.shrunk_mean([2, 2, 2], 10.0, 3)
    assert abs(mu - (6 + 30) / 6) < 1e-12


def test_fit_recovers_overdispersion_direction():
    import random
    rnd = random.Random(1)
    rows = []
    for _ in range(400):
        base = rnd.choice([2, 5, 9])
        prior = [base] * 10
        lam = base * rnd.choice([0.5, 1.0, 1.6])  # extra spread over what the prior says
        x = sum(1 for _ in range(60) if rnd.random() < lam / 60)
        rows.append((prior, x))
    best = p.fit_kr(rows, 5.0)
    assert best is not None and best[2] in p.RS and best[1] in p.KS
    assert best[2] <= 64


def test_cheap_side_band_and_no_side_price():
    assert p.cheap_side(0.07, 0.09) == ("yes", 0.09)
    s = p.cheap_side(0.80, 0.83)  # NO ask = 0.20
    assert s[0] == "no" and abs(s[1] - 0.20) < 1e-12
    assert p.cheap_side(0.45, 0.50) is None  # neither side cheap
    assert p.cheap_side(0.96, 0.98)[0] == "no"  # NO ask 0.04 is the cheap side
    assert p.cheap_side(0.995, 0.999) is None  # NO ask 0.005 is under the floor


def test_treated_needs_3x_and_caps_two_per_game():
    rows = [dict(ticker=f"T{i}", p_side=0.30, ask=0.09 + 0.01 * i, win=False) for i in range(5)]
    t = p.pick_trades(rows, True)
    assert len(t) == 2 and all(r["p_side"] >= 3 * r["ask"] for r in t)
    assert t[0]["ask"] <= t[1]["ask"]  # highest ratio first
    assert p.pick_trades([dict(ticker="X", p_side=0.2, ask=0.1, win=True)], True) == []
    assert len(p.pick_trades(rows, False)) == 2


def test_sample_is_outcome_blind_and_deterministic():
    tks = [f"M{i}" for i in range(100)]
    assert p.choose_sample(tks) == p.choose_sample(list(reversed(tks)))
    assert len(p.choose_sample(tks)) == 40


def test_cluster_stats_and_pf():
    n, m, se, z = p.cluster_stats({"a": [0.1, 0.1], "b": [-0.1], "c": [0.1]})
    assert n == 4 and abs(m - 0.05) < 1e-12 and se > 0
    assert p.profit_factor([0.5, -0.25]) == 2.0
    assert p.profit_factor([1.0]) == float("inf")


def test_parse_box_nba_and_nfl():
    nba = {"boxscore": {"players": [{"team": {"abbreviation": "MEM"}, "statistics": [{"labels": ["MIN", "PTS", "3PT", "REB", "AST"],
           "athletes": [{"athlete": {"id": "1", "displayName": "A B"}, "stats": ["30", "21", "3-5", "7", "4"]},
                        {"athlete": {"id": "2", "displayName": "C D"}, "stats": ["0", "0", "0-0", "0", "0"], "didNotPlay": True}]}]}]}}
    r = {x["aid"]: x for x in p.parse_box("NBA", nba)}
    assert r["1"]["played"] == 1 and r["1"]["tpm"] == 3 and r["1"]["pts"] == 21 and r["2"]["played"] == 0
    nfl = {"boxscore": {"players": [{"team": {"abbreviation": "PIT"}, "statistics": [
        {"name": "receiving", "labels": ["REC", "YDS"], "athletes": [{"athlete": {"id": "9", "displayName": "W R"}, "stats": ["4", "52"]}]},
        {"name": "rushing", "labels": ["CAR", "YDS"], "athletes": [{"athlete": {"id": "9", "displayName": "W R"}, "stats": ["1", "7"]}]}]}]}}
    x = p.parse_box("NFL", nfl)[0]
    assert x["rec"] == 4 and x["recyds"] == 52 and x["rshyds"] == 7 and x["played"] == 1


def test_event_date():
    assert p.event_date("KXNBAREB-26JUN13NYKSAS").day == 13


if __name__ == "__main__":
    fails = 0
    for k, v in sorted(globals().items()):
        if k.startswith("test_"):
            try:
                v()
                print("ok  ", k)
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("FAIL", k, repr(e))
    sys.exit(1 if fails else 0)
