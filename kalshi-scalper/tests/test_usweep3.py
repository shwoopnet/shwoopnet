import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import usweep3 as u3, usweep1 as u1

DAY = 86400
T0 = 1_790_000_000 // DAY * DAY


def rec(series, n, ev=40, vol=50.0, cat="Economics", dates=30, life=3600):
    ms = []
    for i in range(n):
        close = T0 + (i % dates) * DAY + 3600 * 12
        ms.append([f"{series}-E{i % ev}-{i}", close - life, close, None, vol, False])
    return {"ticker": series, "freq": "daily", "cat": cat, "title": "t", "markets": ms}


def test_stratum():
    assert u3.stratum("Elections") == "Politics" and u3.stratum("Health") == "Other" and u3.stratum("Crypto") == "Crypto"


def test_candidate_rule():
    cc = {"X": {"n": 10, "dates": {"a", "b"}}}
    assert u3.is_candidate({"ticker": "A", "frequency": "daily", "category": "Economics"}, {}, set())
    assert not u3.is_candidate({"ticker": "A", "frequency": "daily", "category": "Sports"}, {}, set())
    assert not u3.is_candidate({"ticker": "A", "frequency": "daily", "category": "Economics"}, {}, {"A"})
    assert not u3.is_candidate({"ticker": "KXMVEA", "frequency": "daily", "category": "Economics"}, {}, set())
    assert not u3.is_candidate({"ticker": "A", "frequency": "fifteen_min", "category": "Crypto"}, {}, set())
    assert u3.is_candidate({"ticker": "X", "frequency": "custom", "category": "Politics"}, cc, set())
    assert not u3.is_candidate({"ticker": "Y", "frequency": "custom", "category": "Politics"}, cc, set())


def test_eligible_rule():
    assert u3.eligible(rec("A", 100))
    assert u3.eligible(rec("A", 99)) is None
    assert u3.eligible(rec("A", 100, vol=4.0)) is None
    assert u3.eligible(rec("A", 100, dates=7)) is None
    assert u3.eligible(rec("A", 100, ev=7)) is None
    assert u3.eligible(rec("A", 100, cat="Sports")) is None


def test_round_robin_and_budget():
    items = [{"ticker": f"{c}{i}", "cat": c, "median_volume": 100 - i} for c in ("Economics", "Crypto") for i in range(3)]
    rr = u3.round_robin(items)
    assert [x["cat"] for x in rr[:2]] == ["Economics", "Crypto"]
    kept, skipped = u3.stratified_budget(items, {x["ticker"]: 10 for x in items}, 30)
    assert len(kept) == 3 and {x["cat"] for x in kept} == {"Economics", "Crypto"} and kept[0]["ticker"].endswith("0")


def test_sample_cap_applied():
    r = rec("A", 200)
    assert len(u3.u2.sampled(r)) == 40


def test_tail_only_no_favourite():
    src = pathlib.Path(u3.__file__).read_text()
    assert '"fav"' not in src and "RULES" not in src
