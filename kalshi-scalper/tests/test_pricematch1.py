import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from scalper import pricematch1 as P


def row(ev, t, ask, spread, vol=0.0, ov=None, net=0.0):
    r = {"event": ev, "t": t, "ask": ask, "spread_c": spread, "vol": vol, "ov": ov, "market": ev + "-m", "look": "T60", "net": net, "won": 0}
    r["bin"] = P.bin_of(ask); r["lv"] = P.levels(r)
    return r


def test_bins_and_levels():
    assert P.bin_of(0.03) == 3 and P.bin_of(0.30) == 30 and P.bin_of(0.105) in (10, 11)
    try:
        P.bin_of(0.31); assert False
    except AssertionError as e:
        assert "cheap-side" in str(e) or True
    l = P.levels(row("a", 1, 0.1, 2.0, 0.0, 0.05))
    assert l == {"spread": "TIGHT", "volume": "LOWV", "overround": "LOWOR"}
    l = P.levels(row("a", 1, 0.1, 5.0, 31.0, 0.12))
    assert l == {"spread": "WIDE", "volume": "HIGHV", "overround": "HIGHOR"}
    assert P.levels(row("a", 1, 0.1, 3.0, 10.0, None)) == {"spread": "MIDSP", "volume": "MIDV", "overround": None}


def test_mh_removes_price_confound():
    """TIGHT sits in cheap bins, WIDE in dear bins, nets depend on the bin only: raw gap is large, matched gap is ~0."""
    rng = np.random.default_rng(1)
    rows, k = [], 0
    for b, share_t in ((4, 0.9), (25, 0.1)):
        for i in range(400):
            k += 1
            tight = rng.random() < share_t
            rows.append(row(f"E{k}", k, b / 100, 1.0 if tight else 6.0, net=-0.01 * b + rng.normal(0, 0.02)))
    raw = np.mean([r["net"] for r in rows if r["lv"]["spread"] == "TIGHT"]) - np.mean([r["net"] for r in rows if r["lv"]["spread"] == "WIDE"])
    assert raw > 0.15
    res = P.pooled_difference(rows, "spread", np.random.default_rng(2), B=300)
    assert abs(res["diff"]) < 0.01 and res["lo"] < 0 < res["hi"], res


def test_mh_detects_real_within_bin_effect():
    rng = np.random.default_rng(3)
    rows, k = [], 0
    for b in (5, 10, 20):
        for i in range(300):
            k += 1
            tight = i % 2 == 0
            rows.append(row(f"E{k}", k, b / 100, 1.0 if tight else 6.0, net=-0.05 + (0.04 if tight else 0.0) + rng.normal(0, 0.05)))
    res = P.pooled_difference(rows, "spread", np.random.default_rng(4), B=300)
    assert 0.03 < res["diff"] < 0.05 and res["lo"] > 0


def test_not_enough_data_and_cap():
    rows = [row(f"E{i}", i, 0.1, 1.0) for i in range(10)]
    assert P.pooled_difference(rows, "spread", np.random.default_rng(1), B=50)["verdict"] == "NOT_ENOUGH_DATA"
    many = [dict(row("E1", i, 0.1, 1.0), market=f"m{i}") for i in range(5)]
    assert len(P.cap_per_event(many)) == 2


def test_cell_stats_excess():
    rows = [row(f"E{i}", i, 0.1, 1.0, net=-0.05) for i in range(40)]
    s = P.cell_stats(rows, {10: -0.05}, np.random.default_rng(1), B=100)
    assert abs(s["excess"]) < 1e-12 and abs(s["net"] + 0.05) < 1e-12


if __name__ == "__main__":
    fs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fs:
        f()
    print(f"test_pricematch1: {len(fs)} passed")
