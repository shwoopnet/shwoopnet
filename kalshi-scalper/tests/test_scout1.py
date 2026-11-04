import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import scout1 as s  # noqa: E402


def test_fee_net():
    assert s.fee(0.10) == math.ceil(0.07 * 10 * 0.09 * 100) / 100
    assert abs(s.net(True, 0.10) - (1 - 0.10 - s.fee(0.10) / 10)) < 1e-12
    assert s.net(False, 0.10) < -0.10


def test_nb_sf_matches_direct_sum_and_poisson_limit():
    mu, r = 5.0, 6.0
    direct = 1 - sum(math.exp(s.nb_logpmf(x, mu, r)) for x in range(0, 8))
    assert abs(s.nb_sf(7.5, mu, r) - direct) < 1e-9          # strike 7.5 = "8+"
    pois = 1 - sum(math.exp(-mu) * mu ** x / math.factorial(x) for x in range(0, 8))
    assert abs(s.nb_sf(7.5, mu, 1e6) - pois) < 1e-3
    assert s.nb_sf(-0.5, mu, r) == 1.0


def test_shrink_and_opponent_factor():
    assert s.shrunk_mean([5, 6], 6.0, 4) is None
    assert abs(s.shrunk_mean([8, 8, 8], 4.0, 3) - 6.0) < 1e-12   # (24 + 12) / 6
    assert s.opp_factor([], 8.0, 1.0) == 1.0                      # no games: the league
    assert s.opp_factor([10] * 20, 8.0, 0.0) == 1.0               # gamma 0 switches the factor off
    hi = s.opp_factor([10] * 20, 8.0, 1.0)
    assert hi > 1.0 and abs(hi - ((200 + 80) / 30) / 8.0) < 1e-12


def test_parse_box_mlb_starters_and_team_k():
    summ = {"boxscore": {"players": [
        {"team": {"abbreviation": "ATH"}, "statistics": [
            {"type": "batting", "labels": ["H-AB", "AB", "R", "H", "RBI", "HR", "BB", "K"], "athletes": [], "totals": ["4-31", "31", "1", "4", "0", "0", "0", "12"]},
            {"type": "pitching", "labels": ["IP", "H", "R", "ER", "BB", "K"], "athletes": [
                {"athlete": {"id": 7, "displayName": "José Soriano Jr."}, "starter": True, "stats": ["6.2", "4", "1", "0", "1", "8"]},
                {"athlete": {"id": 8, "displayName": "Relief Guy"}, "starter": False, "stats": ["2.0", "0", "0", "0", "0", "2"]}]}]}]}}
    pit, tk = s.parse_box_mlb(summ)
    assert tk == {"ATH": 12.0}
    assert pit[0]["nm"] == "jose soriano" and pit[0]["starter"] == 1 and pit[0]["k"] == 8.0
    assert pit[1]["starter"] == 0 and pit[1]["k"] == 2.0


def test_event_date_and_cheap_side():
    assert s.event_date("KXMLBKS-26SEP031310TORCLE").date().isoformat() == "2026-09-03"
    assert s.cheap_side(0.04, 0.06) == ("yes", 0.06)
    assert s.cheap_side(0.84, 0.88) == ("no", 1 - 0.84)       # YES ask 0.88 is out of band, NO ask 0.16 is in
    assert s.cheap_side(0.40, 0.45) is None                   # both asks 0.45 / 0.60
    assert s.valid(0.04, 0.06) and not s.valid(0.01, 0.30) and not s.valid(None, 0.5)


def test_pick_trades_ratio_and_cap():
    rows = [dict(ticker=f"T{i}", p_side=p, ask=a) for i, (p, a) in enumerate([(0.40, 0.10), (0.25, 0.05), (0.20, 0.10), (0.95, 0.30)])]
    t = s.pick_trades(rows, True)
    assert [r["ticker"] for r in t] == ["T1", "T0"]            # ratios 5 and 4 pass, 2.0 fails, 3.17 ranks third; max 2 a game
    assert len(s.pick_trades(rows, False)) == 2


def test_split_and_stats():
    lab = s.split_labels(30)
    assert lab.count("FIT") == 20 and lab.count("T1") == 5 and lab.count("T2") == 5 and lab[0] == "FIT" and lab[-1] == "T2"
    n, m, se, z = s.cluster_stats({"a": [1.0, 1.0], "b": [-1.0]})
    assert n == 3 and abs(m - 1 / 3) < 1e-12
    assert s.profit_factor([2.0, -1.0, 1.0]) == 3.0


def test_fit_recovers_a_larger_mean_for_a_high_k_pitcher():
    rows = [([9, 10, 8, 9, 10], [6] * 5, 9)] * 40 + [([3, 4, 3, 4, 3], [6] * 5, 3)] * 40
    ll, k, r, g, n = s.fit_params(rows, 6.0, 6.0)
    assert n == 80 and k in s.KS_GRID and r in s.RS_GRID and g in s.GAMMAS
    assert k == 1                                              # least shrinkage fits two groups of different pitchers


def test_frozen_cut_constants():
    assert s.CUT_TS == 1791043200                              # 2026-10-03T16:00:00Z
    assert (s.LO, s.HI, s.RATIO, s.C, s.LEAD, s.MAXPER) == (0.03, 0.30, 3.0, 10, 300, 2)
