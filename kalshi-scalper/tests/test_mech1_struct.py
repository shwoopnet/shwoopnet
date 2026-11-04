import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import mech1_struct as M
from scalper import calib1 as c


def row(**kw):
    r = {"event": "E1", "t": 1000, "ask": 0.10, "side": "yes", "spread_c": 2.0, "vol": 5.0, "market": "E1-5", "look": "T60", "look_ts": 1_790_000_000,
         "ref": None, "pmax": None, "first": None, "n_prior": 0, "ladder": None, "sib_n": 0, "sib_vols": []}
    r.update(kw)
    return r


def test_cheap_price_sides():
    assert M.cheap_price("yes", 0.04, 0.06) == 0.06 and M.cheap_price("no", 0.80, 0.84) == 0.2
    assert M.cheap_price("no", 0.0, 0.05) is None and M.cheap_price("yes", 0.0, 1.0) is None


def test_strike_key():
    assert M.strike_key("KXAAAGASD-26SEP30-4.4550") == 4.455 and M.strike_key("KX-26-T50") == 50.0 and M.strike_key("KXLALIGA-26NOV02DEPOSA-DEP") is None


def test_fee_waste():
    # p = 0.10, C = 10: exact 6.3 cents, rounded 7 -> 0.07c per contract waste
    assert abs(M.fee_waste_c(0.10) - 0.07) < 1e-9
    assert M.fee_waste_c(0.50) < 0.1 and all(M.fee_waste_c(p / 100) >= 0 for p in range(3, 31))


def test_path_fall_collapse_open():
    assert M.m_path_fall(row(ask=0.08, ref=0.12)) == (True, False)           # 0.08 <= 0.8 * 0.12 and 4c lower
    assert M.m_path_fall(row(ask=0.10, ref=0.11)) == (False, False)
    assert M.m_path_fall(row(ask=0.16, ref=0.12)) == (False, True)           # placebo: rose 25 percent
    assert M.m_path_fall(row(ask=0.10)) == (False, False)                      # no reference candle -> in neither arm
    assert M.m_peak_collapse(row(ask=0.08, pmax=0.20, n_prior=3))[0] and not M.m_peak_collapse(row(ask=0.08, pmax=0.20, n_prior=1))[0]
    assert M.m_peak_collapse(row(ask=0.08, pmax=0.09, n_prior=3)) == (False, True)
    assert M.m_vs_open(row(ask=0.05, first=0.12, n_prior=2)) == (True, False)


def test_round_and_spread():
    assert M.m_nonround(row(ask=0.07)) == (True, False) and M.m_nonround(row(ask=0.15)) == (False, True)
    assert M.m_spreadm(row(ask=0.15, spread_c=1.0)) == (True, False) and M.m_spreadm(row(ask=0.05, spread_c=1.0)) == (False, False)


def test_ladder():
    mk = [f"EV-26X-{k}" for k in (1, 2, 3, 4, 5)]
    q = {m: (0.5, 1.0) for m in mk}
    assert M.ladder_neighbours(mk[2], mk, q)[0:2] == (2, 5)
    assert M.ladder_neighbours(mk[0], mk[:4], q) is None                      # fewer than 5 markets
    assert M.ladder_neighbours(mk[0], mk[:4] + ["EV-26X-TEAM"], q) is None   # a non numeric suffix
    L = {"pos": 2, "n": 5, "nb": [0.35, 0.05]}
    assert M.m_interior(row(ladder=L)) == (True, False) and M.m_interior(row(ladder={"pos": 0, "n": 5, "nb": []})) == (False, True)
    assert M.m_shoulder(row(ladder=L, sib_n=5)) == (True, False) and M.m_shoulder(row(ladder={"pos": 4, "n": 5, "nb": [0.08]}, sib_n=5)) == (False, True)
    assert M.m_shoulder(row(ladder=L, sib_n=2)) == (False, False)


def test_time_and_split():
    # 2026-10-31 04:00 UTC is 00:00 EDT on a Saturday
    r = row(look_ts=1_793_419_200)
    assert M.et_parts(r) == (0, 5) and M.m_offhours(r)[0] and M.m_weekend(r)[0]
    rows = [row(event=f"E{i}", t=1000 + i, ask=0.1) for i in range(30)]
    d1, d2, te = M.split_events(rows)
    assert len(d1) == 10 and len(d2) == 10 and len(te) == 10 and all(int(e[1:]) >= 20 for e in te) and not (d1 & d2) and not (d1 & te)


def test_no_favourite_and_cap():
    rows = [row(event="E", market=f"E-{i}", ask=0.1) for i in range(5)]
    assert len(M.cap_per_event(rows)) == M.MAX_PER_EVENT
    assert M.CAP == 0.30 and all(p / 100 <= 0.30 for p in range(3, 31))


def test_judge():
    ok = {"n": 400, "net": 0.01, "lo": 0.002}
    part = {"n": 100, "net": 0.01, "lo": -0.01}
    assert M.judge("x", ok, part, part, part, ok) == "LEAD"
    assert M.judge("x", ok, dict(part, net=-0.001), part, part, ok) == "FALSIFIED"
    assert M.judge("x", ok, dict(part, n=10), part, part, ok) == "NOT_ENOUGH_DATA"
    assert M.judge("x", dict(ok, lo=-0.001), part, part, part, dict(ok, lo=-0.001)) == "FALSIFIED"
