"""MECHOI1 on synthetic data: record building, thresholds, statistics, bootstrap determinism and the decision rule. Research only."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import mechoi1 as M  # noqa: E402

CT = 1_800_000_900


def cs(level=100_000.0, doi=0.0, yes=(0.20, 0.22), fill=(0.20, 0.22), mid_oi=None):
    c = {CT - 360: (0.20, 0.22, 100.0, level), CT - 300: (0.20, 0.22, 100.0, mid_oi[0] if mid_oi else level + doi / 3),
         CT - 240: (0.20, 0.22, 100.0, mid_oi[1] if mid_oi else level + 2 * doi / 3),
         CT - 180: (yes[0], yes[1], 100.0, level + doi), CT - 120: (fill[0], fill[1], 100.0, level + doi + 5)}
    for t in range(60, 901, 60):
        c.setdefault(CT - t, (0.20, 0.22, 100.0, level + doi))
    return c


def test_record_yes_first_fill_and_win():
    r = M.build_record("T", CT, "yes", cs(doi=90_000.0, yes=(0.20, 0.22), fill=(0.24, 0.26)), 70000.0)
    assert r["yes"] == 1 and r["d"] == 1 and abs(r["fill"] - 0.26) < 1e-9 and r["win"] == 1.0 and r["doi"] == 90_000.0


def test_record_no_side_when_yes_expensive():
    r = M.build_record("T", CT, "yes", cs(yes=(0.78, 0.80), fill=(0.78, 0.80)), 70000.0)
    # NO ask = 1 - 0.78 = 0.22 -> NO side, the YES result means a loss
    assert r["yes"] == 0 and r["d"] == -1 and r["win"] == 0.0


def test_no_cheaper_side_no_record():
    assert M.build_record("T", CT, "yes", cs(yes=(0.49, 0.51), fill=(0.49, 0.51)), 70000.0) is None


def test_concentration_share():
    r = M.build_record("T", CT, "no", cs(level=100_000.0, doi=90_000.0, mid_oi=(160_000.0, 190_000.0)), 70000.0)
    assert r["d3"] == [60_000.0, 30_000.0, 0.0]
    A = M.arrays([dict(r, spot_ok=False, post=float("nan"), sigmv=float("nan"), gap=float("nan"), sigw=float("nan"))])
    assert abs(A["share"][0] - 60 / 90) < 1e-9 and bool(A["lumpy"][0])


def test_sigma_and_spot():
    K = {CT - 60 * i - 60: 70000.0 * math.exp(0.0001 * ((-1) ** i) * 1) for i in range(0, 200)}
    s = M.sigma_min(K, CT)
    assert s > 0 and math.isfinite(s)
    assert M.spot_at(K, CT) == K[CT - 60]
    assert math.isnan(M.sigma_min({}, CT))


def _recs(n_days=20, per_day=24, seed=1, edge=0.0, vol_mult=1.0):
    """Synthetic records: a trigger (doi large) subset whose win prob = fill + edge and whose |post| move is vol_mult larger."""
    rng = np.random.default_rng(seed)
    out = []
    for dday in range(n_days):
        for k in range(per_day):
            trig = rng.random() < 0.25
            fill = 0.25
            win = float(rng.random() < fill + (edge if trig else 0.0))
            d = 1 if rng.random() < 0.5 else -1
            post = rng.normal(0, 0.0010 * (vol_mult if trig else 1.0))
            out.append({"day": f"2026-09-{dday + 1:02d}", "ct": 1_790_000_000 + dday * 86400 + k * 900, "d": d, "yes": 1 if d > 0 else 0,
                        "fill": fill, "win": win, "doi": 120_000.0 if trig else 1_000.0, "ask180": 0.25, "ask360": 0.25,
                        "spr180": 0.02, "spr360": 0.02, "d3": [40_000.0, 40_000.0, 40_000.0] if trig else [300.0, 300.0, 400.0],
                        "spot_ok": True, "post": post, "sigmv": rng.normal(0, 0.001), "gap": rng.normal(-0.001, 0.001), "sigw": 0.001})
    return out


def test_masks_fixed():
    recs = _recs()
    A = M.arrays(recs)
    rise, drop, base, _ = M.masks(A, recs, "fixed")
    assert rise.sum() > 50 and drop.sum() == 0 and (rise & base).sum() == 0 and (rise | base).all()


def test_relative_threshold_uses_only_past_and_needs_history():
    recs = _recs(n_days=4, per_day=96)
    hi, lo10 = M.trailing_thr(recs)
    assert np.isnan(hi[0]) and np.isfinite(hi[-1])
    # a record's own doi never enters its threshold: change the last doi, the last threshold does not move
    recs2 = [dict(r) for r in recs]
    recs2[-1]["doi"] = 9e9
    hi2, _ = M.trailing_thr(recs2)
    assert hi2[-1] == hi[-1]


def test_vol_ratio_recovered_and_no_edge_means_zero_excess():
    recs = _recs(n_days=40, per_day=40, vol_mult=1.6, edge=0.0)
    A = M.arrays(recs)
    rise, _, base, _ = M.masks(A, recs, "fixed")
    S = M.boot(A, M.make_ctx(A, rise, base), reps=200)
    assert 1.4 < S["R_post"][0] < 1.8 and S["R_post"][1] > 1.2
    assert abs(S["exc_diff"][0]) < 0.04 and S["exc_diff"][1] < 0.0 < S["exc_diff"][2] or abs(S["exc_diff"][0]) < 0.04


def test_edge_recovered_and_bootstrap_deterministic():
    recs = _recs(n_days=40, per_day=40, edge=0.10)
    A = M.arrays(recs)
    rise, _, base, _ = M.masks(A, recs, "fixed")
    ctx = M.make_ctx(A, rise, base)
    a, b = M.boot(A, ctx, reps=100), M.boot(A, ctx, reps=100)
    assert a["exc_diff"] == b["exc_diff"]
    assert 0.06 < a["exc_diff"][0] < 0.14 and a["exc_diff"][1] > 0.0
    assert a["share_unch_t"][0] == 1.0 and a["spread_diff"][0] == 0.0


def test_decide_lines():
    base = {k: (0.0, -1.0, 1.0) for k in ("R_post", "lean_post", "lean_sig", "exc_yes_t", "exc_no_t", "far_near_t", "dsplit_t", "exc_dpos_t",
                                         "unch_split_t", "exc_unch_t", "spread_diff", "lumpy_split_t", "exc_lumpy_t")}
    S = dict(base)
    S["R_post"] = (1.4, 1.2, 1.7); S["lean_post"] = (0.02, -0.1, 0.1); S["exc_yes_t"] = (0.05, 0, 0.1); S["exc_no_t"] = (0.04, 0, 0.1)
    S["far_near_t"] = (0.05, -0.02, 0.1)
    assert M.decide(S)["M1"] == "SUPPORTED"
    S["R_post"] = (1.4, 0.9, 1.7)
    assert M.decide(S)["M1"] == "LEANING"
    S["exc_no_t"] = (0.0, -0.1, 0.1)
    assert M.decide(S)["M1"] == "NOT SUPPORTED"
    S["unch_split_t"] = (0.08, 0.01, 0.15); S["exc_unch_t"] = (0.06, 0, 0.1); S["spread_diff"] = (0.0, -0.01, 0.01)
    assert M.decide(S)["M3"] == "SUPPORTED"
    S["spread_diff"] = (0.02, 0.0, 0.03)
    assert M.decide(S)["M3"] == "LEANING"
    S["lumpy_split_t"] = (0.08, -0.01, 0.15); S["exc_lumpy_t"] = (0.06, 0, 0.1)
    assert M.decide(S)["M4"] == "LEANING"
    S["lean_post"] = (0.2, 0.05, 0.3); S["lean_sig"] = (0.3, 0.1, 0.5); S["dsplit_t"] = (0.1, 0, 0.2); S["exc_dpos_t"] = (0.06, 0, 0.1)
    assert M.decide(S)["M2"] == "SUPPORTED"


def test_holdout_dates_split():
    d = [f"d{i:02d}" for i in range(90)]
    a, b, c = M.split_dates(d)
    assert len(a) == len(b) == len(c) == 30 and a[-1] < b[0] and b[-1] < c[0]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
