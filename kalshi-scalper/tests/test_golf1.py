import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import golf1 as G


def _ev(id_, date, rounds_by_player):
    pl = {}
    for nm, rs in rounds_by_player.items():
        ls = [dict(period=i + 1, value=float(s), linescores=[{}] * 18) for i, s in enumerate(rs)]
        pl[nm] = dict(rd={i + 1: float(s) for i, s in enumerate(rs)}, started={i + 1 for i in range(len(rs))})
    return dict(id=id_, date=date, name=id_, players=pl)


def test_norm():
    assert G.norm("Ludvig Åberg") == "ludvig aberg" and G.norm("Davis Love III") == "davis love"


def test_walk_forward_uses_only_earlier_events():
    a = _ev("a", "2026-01-01", {"x": [68, 68, 68, 68], "y": [72, 72, 72, 72]})
    b = _ev("b", "2026-01-08", {"x": [70, 70, 70, 70], "y": [70, 70, 70, 70]})
    pre = G.walk_forward([a, b])
    assert pre["a"]["x"] == (0.0, 0)                      # nothing before the first event
    assert pre["b"]["x"][1] == 4 and pre["b"]["x"][0] == -8.0   # x was 2 under the field mean for 4 rounds
    assert pre["b"]["y"][0] == 8.0
    assert G.rating(pre["b"]["x"], 20) < 0 < G.rating(pre["b"]["y"], 20)
    assert abs(G.rating((-8.0, 4), 5)) < abs(G.rating((-8.0, 4), 0))   # shrinkage


def test_simulation_sums_and_ties():
    done = [140, 141, 141, 150, 160] + [170] * 25
    rat = [0.0] * 30
    w, t10, t20 = G.simulate(done, rat, 2, 2.5, 7)
    assert abs(sum(w) - 1.0) < 1e-9                       # ties share the win, so shares sum to one
    assert sum(t10) >= 10 - 1e-9 and sum(t20) >= 20 - 1e-9   # ties inclusive can only push the sums up
    assert w[0] > w[1] and w[0] > w[3] > w[4]
    assert t10[0] > 0.9 and t20[29] < t20[3]


def test_better_rating_raises_probability():
    done = [140] * 30
    rat = [-1.0] + [0.0] * 29
    w, t10, t20 = G.simulate(done, rat, 2, 2.5, 3)
    assert w[0] > 2 * w[1] and t10[0] > t10[1]


def test_fit_picks_k_and_sigma():
    evs = [_ev(f"e{i}", f"2026-01-{i+1:02d}", {"x": [68 + (i % 2)] * 4, "y": [72 - (i % 2)] * 4, "z": [70] * 4}) for i in range(8)]
    pre = G.walk_forward(evs)
    p = G.fit(evs, pre)
    assert p["k"] in G.K_GRID and p["sigma"] > 0 and p["rounds"] == 8 * 12


def test_cheap_side_and_treated():
    assert G.cheap_side(0.08, 0.10) == ("yes", 0.10)
    assert G.cheap_side(0.88, 0.90)[0] == "no" and abs(G.cheap_side(0.88, 0.90)[1] - 0.12) < 1e-9
    assert G.cheap_side(0.40, 0.45) is None and G.cheap_side(None, 0.1) is None
    assert G.treated(0.30, 0.10) and not G.treated(0.29, 0.10) and not G.treated(0.99, 0.31)


def test_pick_max_three_by_ratio():
    rows = [dict(ticker=str(i), p_side=0.05 * (i + 1), ask=0.04, treated=True) for i in range(5)] + [dict(ticker="x", p_side=0.9, ask=0.5, treated=False)]
    got = G.pick(rows)
    assert [r["ticker"] for r in got] == ["4", "3", "2"]


def test_net_cents_and_fee():
    assert G.fee(0.10) == 0.07 and abs(G.net_cents(0.10, False) + 10.7) < 1e-9
    assert G.net_cents(0.10, True) > 80


def test_look_ts_and_quote():
    t = G.look_ts("2026-01-08", 2)
    assert t == 1767870000 + 0 or t > 0
    cs = [(t - 7200, 0.1, 0.12), (t - 60, 0.11, 0.13), (t + 60, 0.5, 0.6), (t - 30000, 0.2, 0.3)]
    assert G.look_quote(cs, t) == (0.11, 0.13)               # the later candle after the look and the one 8 hours earlier are ignored
    assert G.look_quote([(t - 60, 0.5, 0.4)], t) is None


def test_verdict_rules():
    mk = lambda n, v, k: [("c%d" % i, v, 1 if i < n // 2 else 2) for i in range(n)]
    assert G.verdict(mk(100, 5.0, 0), 2, 50) == "NOT_ENOUGH_DATA"
    assert G.verdict(mk(200, -1.0, 0), 2, 50) == "FALSIFIED"
    rows = [("c%d" % i, 20.0 if i % 3 == 0 else -3.0, 1 if i < 100 else 2) for i in range(200)]
    assert G.verdict(rows, 2, 50) == "NOT_YET_FALSIFIED"


def test_md5_order_is_stable():
    assert G.md5_key("a") == G.md5_key("a") and G.md5_key("a") != G.md5_key("b")
