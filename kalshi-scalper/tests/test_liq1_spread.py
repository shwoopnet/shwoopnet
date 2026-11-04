import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import liq1_spread as L
from scalper import calib1 as c


def row(ev, t, spread, vol, ask=0.10, mk=None, look="T60"):
    return {"event": ev, "t": t, "spread_c": spread, "vol": vol, "ask": ask, "market": mk or ev + "-x", "look": look, "bk": c.ask_bucket(ask), "side": "yes"}


def test_features_cheap_only():
    assert L.quote_features(0.50, 0.52, 5) is None                  # no cheap side
    f = L.quote_features(0.04, 0.06, 7)
    assert f["side"] == "yes" and f["ask"] == 0.06 and abs(f["spread_c"] - 2.0) < 1e-6 and f["vol"] == 7.0
    f = L.quote_features(0.80, 0.84, None)                          # NO side at 20c, spread is the YES book's, vol None -> 0
    assert f["side"] == "no" and abs(f["ask"] - 0.2) < 1e-9 and abs(f["spread_c"] - 4.0) < 1e-6 and f["vol"] == 0.0
    assert L.quote_features(0.92, 0.95, 1)["ask"] == 0.08           # never the 95c favourite
    assert L.quote_features(0.0, 0.05, 1) is None                   # one sided


def test_fit_split_and_cuts():
    rows = [row(f"E{i}", 1000 + i, spread=float(i % 6 + 1), vol=float(i)) for i in range(30)]
    fit, oos = L.fit_split(rows)
    assert len(fit) == 20 and len(oos) == 10 and all(int(e[1:]) < 20 for e in fit)   # earliest two thirds
    cuts = L.fit_cuts(rows, fit)
    assert cuts["spread_lo"] <= cuts["spread_hi"] and cuts["vol_lo"] <= cuts["vol_hi"]
    assert cuts["vol_hi"] == sorted(float(i) for i in range(20))[int(20 * 2 / 3)]     # fitted on the fit set only, not on the last ten


def test_groups():
    cuts = {"spread_lo": 2.0, "spread_hi": 5.0, "vol_lo": 0.0, "vol_hi": 30.0}
    assert L.groups_for(row("a", 1, 1.0, 0.0), cuts) == ["TIGHT", "LOWV"]
    assert L.groups_for(row("a", 1, 5.0, 31.0), cuts) == ["WIDE", "HIGHV"]
    assert L.groups_for(row("a", 1, 3.0, 10.0), cuts) == []        # middle belongs to no group
    assert "HIGHV" not in L.groups_for(row("a", 1, 3.0, 30.0), cuts)   # strictly above the cut
    z = {"spread_lo": 2.0, "spread_hi": 5.0, "vol_lo": 0.0, "vol_hi": 0.0}
    assert "HIGHV" in L.groups_for(row("a", 1, 3.0, 1.0), z) and "HIGHV" not in L.groups_for(row("a", 1, 3.0, 0.0), z)


def test_cap_per_event_deterministic():
    rows = [row("E", 1, 1.0, 0.0, mk=f"M{i}") for i in range(5)] + [row("F", 1, 1.0, 0.0, mk="Z")]
    a = L.cap_per_event(rows)
    assert sum(1 for r in a if r["event"] == "E") == 2 and sum(1 for r in a if r["event"] == "F") == 1
    assert [r["market"] for r in a] == [r["market"] for r in L.cap_per_event(list(reversed(rows)))] or \
        sorted(r["market"] for r in a) == sorted(r["market"] for r in L.cap_per_event(list(reversed(rows))))


def test_verdict_rules():
    mk = lambda n, net, pf: {"n": n, "net": net, "pf": pf}
    assert L.verdict("TIGHT", mk(100, .01, 2), mk(100, .01, 2), mk(200, .01, 2)) == "LEAD"
    assert L.verdict("TIGHT", mk(100, .01, 2), mk(100, -.01, 2), mk(200, .0, 2)) == "FALSIFIED"      # one half negative
    assert L.verdict("TIGHT", mk(100, .01, 2), mk(100, .01, 1.2), mk(200, .01, 1.2)) == "FALSIFIED"  # PF under 1.5
    assert L.verdict("TIGHT", mk(40, .01, 2), mk(40, .01, 2), mk(80, .01, 2)) == "NOT_ENOUGH_DATA"   # under 150


def test_pf():
    rows = [{"net": 0.5}, {"net": -0.25}, {"net": -0.25}]
    assert abs(L.pf(rows) - 1.0) < 1e-9


if __name__ == "__main__":
    fs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fs:
        f()
    print(f"test_liq1_spread: {len(fs)} passed")
