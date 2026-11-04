import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import mech2_struct as X
from scalper import mech1_struct as M


def test_lists_and_threshold():
    assert len(X.TOP) == 7 and set(X.TOP).isdisjoint(X.NOT_SCORED) and set(X.TOP) | set(X.NOT_SCORED) <= set(M.MECH)
    assert X.qualifies((150, 200, 300)) and not X.qualifies((149, 200, 300)) and not X.qualifies((88, 400, 74))


def test_eligible_synthetic():
    rows = []
    for i in range(30):
        rows.append({"event": f"E{i}", "t": 1000 + i, "ask": 0.10, "side": "yes", "spread_c": 0.5, "vol": 1.0, "market": f"E{i}-1", "look": "T60",
                     "look_ts": 1_790_000_000, "ref": None, "pmax": None, "first": None, "n_prior": 0, "ladder": None, "sib_n": 0, "sib_vols": []})
    el = X.eligible(rows)
    assert sum(el["SPREADM"]) == 30 and sum(el["PATH_FALL"]) == 0 and not X.qualifies(el["SPREADM"])


def test_cheap_cap_guard():
    assert M.CAP == 0.30
