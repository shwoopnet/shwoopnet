import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import model1 as M
from scalper import calib1 as c


def row(ev, t, ask=0.10, mk=None, look="T60", spread=2.0, vol=0.0, cat="Economics", series="S1", side="yes"):
    return {"event": ev, "t": t, "ask": ask, "market": mk or ev + "-x", "look": look, "bk": c.ask_bucket(ask), "spread_c": spread, "vol": vol,
            "cat": cat, "series": series, "life": "D", "side": side}


def test_split_is_time_ordered_and_disjoint():
    rows = [row(f"E{i}", 1000 + i) for i in range(30)]
    tr, te, ifit, ival, order = M.split_events(rows)
    assert len(tr) == 20 and len(te) == 10 and not (tr & te)
    assert max(int(e[1:]) for e in tr) < min(int(e[1:]) for e in te)       # train strictly earlier than test
    assert ifit | ival == tr and not (ifit & ival) and max(int(e[1:]) for e in ifit) < min(int(e[1:]) for e in ival)


def test_logit_learns_a_signal_and_gbt_too():
    rng = np.random.default_rng(1)
    n = 3000
    x = rng.normal(size=(n, 3))
    p = 1 / (1 + np.exp(-(1.5 * x[:, 0] - 0.5)))
    y = (rng.random(n) < p).astype(float)
    w = M.fit_logit(x, y, 1.0)
    assert w[1] > 1.0 and abs(w[2]) < 0.3
    pr = M.predict_logit(w, x)
    assert M.log_loss(pr, y) < M.log_loss(np.full(n, y.mean()), y) - 0.05
    g = M.GBT(2, 60, lr=0.1, min_leaf=50, l2=10.0, bins=16).fit(x, y)
    assert M.log_loss(g.predict(x), y) < M.log_loss(np.full(n, y.mean()), y) - 0.05


def test_models_find_nothing_in_pure_noise():
    rng = np.random.default_rng(2)
    n = 4000
    x = rng.normal(size=(n, 4))
    y = (rng.random(n) < 0.1).astype(float)
    tr, te = slice(0, 3000), slice(3000, n)
    w = M.fit_logit(x[tr], y[tr], 10.0)
    assert M.log_loss(M.predict_logit(w, x[te]), y[te]) > M.log_loss(np.full(1000, y[tr].mean()), y[te]) - 0.01


def test_select_margin_cap_and_tiebreak():
    rows = [row("E1", 1, 0.10, "E1-a"), row("E1", 1, 0.10, "E1-b"), row("E1", 1, 0.10, "E1-c"), row("E2", 2, 0.10, "E2-a")]
    p = np.array([0.15, 0.20, 0.17, 0.115])
    assert M.select(rows, p, 0.02) == [0, 1, 2][:0] + [1, 2]          # E1 keeps its 2 largest margins; E2 margin 1.5c is below 2c
    assert M.select(rows, np.array([0.12, 0.0, 0.0, 0.0]), 0.02) == []   # margin must EXCEED 2c strictly
    assert M.select(rows, np.array([0.15, 0.2, 0.17, 0.115]), 0.04) == [1, 2]


def test_permutation_keeps_bucket_counts():
    rng = np.random.default_rng(3)
    y = (rng.random(500) < 0.2).astype(float)
    bk = rng.integers(0, 5, 500)
    yp = M.perm_outcomes(y, bk, rng)
    for b in range(5):
        assert yp[bk == b].sum() == y[bk == b].sum()
    assert (yp != y).any()


def test_features_cheap_only_and_spec_from_train():
    rows = [row(f"E{i}", i, ask=0.05 + 0.01 * (i % 10), cat="Sports" if i % 2 else "Economics", series=f"S{i % 3}") for i in range(600)]
    sp = M.Spec(rows)
    X, Z = sp.matrix(rows)
    assert X.shape[1] == len(sp.names) and abs(Z[:, 0].mean()) < 1e-9
    assert M.look_minutes("T1440") == 1440 and M.look_minutes("late") == 180 and M.look_minutes("A3h") is None


def test_frozen_rows_dropped(tmp_path=None):
    assert M.FROZEN_FROM == 1791043200


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("test_model1 ok")
