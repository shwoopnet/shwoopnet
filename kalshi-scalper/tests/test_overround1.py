import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import overround1 as o


def test_structure():
    ok = ["E-T70", "E-B71.5", "E-B73.5", "E-B75.5", "E-T76"]
    assert o.structure_ok(ok)
    assert not o.structure_ok(ok[:3])                    # fewer than 4 outcomes
    assert not o.structure_ok(["E-4.1", "E-4.2", "E-4.3", "E-4.4"])   # a nested threshold ladder is not exclusive
    assert not o.structure_ok(["E-T1", "E-T2", "E-T3", "E-B1", "E-B2", "E-B3"])  # three T


def test_overround():
    assert o.overround([0.1, 0.3, 0.4, 0.3]) == 0.1
    assert o.overround([0.1, None, 0.4, 0.3]) is None    # an unquoted outcome: no overround
    assert o.overround([0.1, 0.2, 0.3]) is None          # under 4 outcomes
    assert o.yes_ask((0, 0.0, 0.01)) == 0.01 and o.yes_ask((0, 0.0, 1.0)) is None and o.yes_ask(None) is None


def test_terciles_and_pick():
    cuts = o.tercile_cuts(list(range(9)))
    assert cuts == (3.0, 6.0) and o.tercile(2, cuts) == "LOW" and o.tercile(3, cuts) == "MID" and o.tercile(6, cuts) == "HIGH"
    cands = [{"market": f"M{i}"} for i in range(5)]
    assert len(o.pick(cands)) == 2 and o.pick(cands) == o.pick(list(reversed(cands)))


def test_cut_on_first_two_thirds_only():
    recs = [{"look": "T1", "anchor": i, "event": f"e{i}", "ov": float(i), "cands": []} for i in range(60)]
    recs += [{"look": "T2", "anchor": i, "event": f"f{i}", "ov": 1.0, "cands": []} for i in range(5)]   # too few: dropped
    out = o.assign(recs)
    assert {r["look"] for r in out} == {"T1"}
    assert out[0]["cuts"] == (13.0, 26.0) and all(r["dev"] == (r["anchor"] < 40) for r in out)
    assert [r["terc"] for r in out[:3]] == ["LOW", "LOW", "LOW"] and out[-1]["terc"] == "HIGH"   # later, larger values do not move the cut


def test_verdict_rules():
    import numpy as np
    rng = np.random.default_rng(1)
    mk = lambda n, net, i0=0: [{"event": f"e{i}", "t": i, "net": net, "won": 0, "ask": 0.1, "date": "d"} for i in range(i0, i0 + n)]
    assert o.verdict(mk(100, 0.1), rng) == "NOT_ENOUGH_DATA"
    assert o.verdict(mk(200, -0.05), rng) == "FALSIFIED"
    rows = mk(100, 0.2) + mk(100, -0.01, 100)             # second half negative
    assert o.verdict(rows, rng) == "FALSIFIED"
    assert o.verdict(mk(200, 0.2), rng) == "LEAD_FOR_FORWARD_TEST"


def test_pf():
    rows = [{"net": 0.9}, {"net": -0.3}, {"net": -0.3}]
    assert abs(o.pf(rows) - 1.5) < 1e-9


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("overround1 tests ok")
