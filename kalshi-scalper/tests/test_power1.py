import math

import numpy as np

from scalper import power1 as p


def test_fee_rounds_up_per_contract():
    assert abs(p.fee_dollars(0.5) - 0.018) < 1e-12  # 17.5c rounds up to 18c per 10, 1.8c each
    assert abs(p.fee_dollars(0.1) - 0.007) < 1e-12  # 6.3c -> 7c
    assert p.breakeven(0.1) > 0.1


def test_edge_and_n_are_inverses_and_power_is_80():
    sd, d, z = 0.3, 2.0, 5.27
    for n in (50, 150, 1000):
        e = p.edge_for_power(n, z, sd, d)
        assert abs(p.power_at(e, n, z, sd, d) - 0.8) < 1e-6
        assert abs(p.n_for_z(e, z, sd, d, 0.8) - n) < 1e-6
    # median run: expected z equals the bar at n_for_z
    n = p.n_for_z(0.02, 3.0, sd, d)
    assert abs(0.02 / p.se_mean(sd, n, d) - 3.0) < 1e-9


def test_simulation_matches_analytic_power_unclustered():
    rng = np.random.default_rng(1)
    a, n, z = 0.5, 400, 2.0
    sd = p.sd_trade(a)
    e = p.edge_for_power(n, z, sd, 1.0)
    o = p.simulate(a, e, n, 1.0, 0.0, 20000, rng)
    assert abs(o["z2"] - 0.8) < 0.03
    o0 = p.simulate(a, 0.0, n, 1.0, 0.0, 20000, rng)
    assert abs(o0["z2"] - p.nsf(2.0)) < 0.008


def test_simulation_matches_analytic_power_with_day_clusters():
    rng = np.random.default_rng(2)
    a, m, rho, G = 0.5, 10.0, 0.3, 60
    n = int(m * G)
    d = p.deff(m, rho)
    assert abs(d - 3.7) < 1e-12
    e = p.edge_for_power(n, 2.0, p.sd_trade(a), d)
    o = p.simulate(a, e, n, m, rho, 20000, rng)
    assert abs(o["z2"] - 0.8) < 0.06  # cluster-robust z is a little conservative at 60 clusters
    # ignoring the clustering would be wildly optimistic: the same edge with deff 1 would be 99% power
    assert p.power_at(e, n, 2.0, p.sd_trade(a), 1.0) > 0.97


def test_not_enough_data_probability():
    # Poisson(100) has P(N < 100) of about 0.487
    assert abs(p.p_not_enough(1.0, 1.0, 100, 100) - 0.4867) < 0.002
    assert p.p_not_enough(10.0, 1.0, 100, 100) == 0.0 or p.p_not_enough(10.0, 1.0, 100, 100) < 1e-12
    assert p.p_not_enough(0.01, 1.0, 100, 100) == 1.0 or p.p_not_enough(0.01, 1.0, 100, 100) > 0.999999
    # bunching: the same mean arriving 10 at a time is far likelier to fall short than one at a time
    assert p.p_not_enough(1.0, 10.0, 100, 80) > 10 * p.p_not_enough(1.0, 1.0, 100, 80)


def test_deflated_bar_false_positive_is_tiny():
    assert p.nsf(p.Z_DEFLATED) < 1e-6


def test_build_table_shape_and_headline_numbers():
    rows = p.build(sims=2000)
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(p.SPECS)
    byid = {r["id"]: r for r in rows}
    # the dormant tests cannot reach their floor in 120 days at any rate in their registered range
    for k in ("NOWCAST1", "FEDIMPL1", "COUNT1_weekly", "BARRIER1"):
        assert byid[k]["verdict_possible_120d"] == "no"
        assert byid[k]["p_ned_high"] > 0.99
    # a +2c edge cannot pass the 5.27 bar inside 120 days for any registered test
    for r in rows:
        if r["id"].startswith("REF") or r["id"] == "STRADDLE1":
            continue
        assert r["e80_527_120d"] == "" or r["e80_527_120d"] > 2.0, r["id"]
    assert abs(byid["MAKERTAIL1_comb"]["days_to_floor"] - 150 / 36) < 0.11
    # a zero-edge test does not pass the 5.27 bar in simulation (normal tail is 7e-8)
    for r in rows:
        if r["id"].startswith("USWEEP1"):
            # favourites at 92c lose rarely and in lumps: a run with no losing day makes a cluster-robust z infinite.
            # The registered z would be undefined there, so the high figure is a property of the statistic, not an edge.
            assert r["mc_z527_e0"] > 0.01
        else:
            assert r.get("mc_z527_e0", 0) < 0.01, r["id"]
