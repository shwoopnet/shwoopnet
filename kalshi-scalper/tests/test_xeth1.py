import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import xeth1 as X

LOOK = 1_800_000_000 - (1_800_000_000 % 3600) - X.LEAD


def series(move, base=100.0, noise=0.0003):
    """1 minute klines for 25 hours before the look; flat with tiny alternating noise, then `move` (log) over the last 10 minutes."""
    out, p = {}, base
    t0 = LOOK - 25 * 3600
    for t in range(t0, LOOK, 60):
        end = t + 60
        if end > LOOK - X.BACK:
            p *= math.exp(move / 10)
        else:
            p *= math.exp(noise * (1 if (t // 60) % 2 else -1))
        out[t] = p
    return out


def test_trigger_up_when_eth_flat():
    g, side, S = X.classify(series(0.02), series(0.0), LOOK)
    assert (g, side) == ("TRIG", "up")


def test_trigger_down_and_eth_wrong_way_counts():
    g, side, _ = X.classify(series(-0.02), series(0.004), LOOK)   # ETH moved up, against BTC
    assert (g, side) == ("TRIG", "down")


def test_followed_is_group_f():
    g, side, _ = X.classify(series(0.02), series(0.02), LOOK)
    assert (g, side) == ("F", "up")


def test_no_trigger_is_none_with_sign():
    g, side, _ = X.classify(series(0.0), series(0.0), LOOK)
    assert g == "NONE" and side in ("up", "down", None)


def test_missing_data_gives_none():
    assert X.classify({}, series(0.0), LOOK) is None


def test_near_strikes_move_side_only():
    ms = [(f"T{k}", float(k)) for k in range(90, 111)]
    up = X.near_strikes(ms, 100.5, "up")
    assert [m[1] for m in up] == [101, 102, 103, 104, 105, 106]
    dn = X.near_strikes(ms, 100.5, "down")
    assert [m[1] for m in dn] == [100, 99, 98, 97, 96, 95]


def test_cheap_price_and_choose():
    assert X.cheap_price("up", 0.10, 0.12) == 0.12
    assert abs(X.cheap_price("down", 0.10, 0.12) - 0.90) < 1e-9
    assert X.cheap_price("up", 0.0, 0.12) is None
    q = {"a": (0.05, 0.06), "b": (0.2, 0.22), "c": (0.28, 0.30), "d": (0.40, 0.42), "e": (0.01, 0.02)}
    assert X.choose(q, "up") == ["c", "b"]      # d above 0.30 and e under 0.03 are out; highest price first
    qd = {"a": (0.70, 0.72), "b": (0.80, 0.82)}  # NO costs 0.30 and 0.20
    assert X.choose(qd, "down") == ["a", "b"]


def test_fill_hard_limit():
    assert X.fill("up", 0.28, 0.30) == 0.30
    assert X.fill("up", 0.29, 0.31) is None
    assert X.fill("up", None, 0.2) is None


def test_trade_and_fee():
    t = X.trade("up", 0.20, "yes")
    assert t["won"] and abs(t["pnl10"] - (10 - 2.0 - X.fee(0.20))) < 1e-9
    t = X.trade("down", 0.20, "yes")      # NO bought, result yes -> loss
    assert not t["won"] and abs(t["pnl10"] + 2.0 + X.fee(0.20)) < 1e-9
    assert X.fee(0.5) == 0.18 and X.fee(0.1) == 0.07


def test_verdict_not_enough_and_falsified():
    z = {"n": 10, "pf": 3.0, "pfx": 2.5, "mean": 5.0, "z": 1.0, "win": .3, "price": .2, "days": 5}
    tr = {"H1": z, "H2": z, "ALL": z}
    assert X.verdict(tr, tr, 40)[0] == "NOT_ENOUGH_DATA"
    big = dict(z, n=200)
    bad = dict(big, pf=0.8, pfx=0.7, mean=-3.0)
    w, why = X.verdict({"H1": big, "H2": bad, "ALL": big}, {"H1": z, "H2": z, "ALL": z}, 40)
    assert w == "FALSIFIED" and why
    w, _ = X.verdict({"H1": big, "H2": big, "ALL": big}, {"H1": dict(z, mean=1.0), "H2": dict(z, mean=1.0), "ALL": z}, 40)
    assert w == "NOT_YET_FALSIFIED"


def test_halves_and_holdout():
    ds = [f"2026-09-{d:02d}" for d in range(1, 31)]
    w = X.thirds(ds)
    assert sum(1 for v in w.values() if v == "W3") == 10
    h = X.dev_halves([d for d in ds if w[d] != "W3"])
    assert sorted(set(h.values())) == ["H1", "H2"]


def test_no_favourite_side_function():
    assert not [n for n in dir(X) if "fav" in n.lower()]


if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try:
                f(); print("ok", n)
            except Exception as e:
                import traceback; traceback.print_exc(); fails += 1; print("FAIL", n, e)
    sys.exit(1 if fails else 0)
