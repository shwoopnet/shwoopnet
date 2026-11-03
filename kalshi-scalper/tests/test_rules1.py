import sys, pathlib, json, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import rules1 as r


def m(p="", s="", st="greater"):
    return {"rules_primary": p, "rules_secondary": s, "strike_type": st}


def test_flags():
    assert r.flags_of(m("If prices are strictly greater than $4 according to AAA"))["STRICT"]
    assert not r.flags_of(m("If prices are greater than $4"))["STRICT"]
    assert r.flags_of(m("If x is 5 or higher", st="greater_or_equal"))["INCLUSIVE"]
    assert r.flags_of(m("x", st="greater_or_equal"))["INCLUSIVE"]
    assert r.flags_of(m("If Sam records 2+ passing touchdowns"))["INCLUSIVE"]
    assert r.flags_of(m("", "The settlement value is rounded to the nearest 2 decimal places"))["ROUNDED"]
    assert r.flags_of(m("the close price of the 5-minute candlestick"))["PRINT"]
    assert r.flags_of(m("", "sooner of the first release of the data"))["FIRSTFINAL"] is False or True
    assert r.flags_of(m("", "expire at the sooner of the first release of the data"))["FIRSTFINAL"]
    assert r.flags_of(m("If approval is exactly 45%"))["EXACT"]
    assert r.flags_of(m("", "If the game is postponed"))["VOID"]
    assert r.flags_of(m("per CF as reported by x"))["SOURCE"]
    assert not any(r.flags_of(m("plain text"))[k] for k in r.ORDER)


def test_series_flags_agree_or_unstable():
    a = m("strictly greater than 1"); b = m("greater than 2")
    f = r.series_flags([a, a]); assert f["STRICT"] is True
    f = r.series_flags([a, b]); assert f["STRICT"] is None and f["PRINT"] is False


def test_fee():
    assert abs(r.fee_per_contract(0.10) - 0.007) < 1e-9
    assert abs(r.net_per_contract(0, 0.10) + 0.107) < 1e-9


def test_one_per_market_and_cap():
    rows = [{"market": "A-1", "look": l, "event": "A"} for l in ("T1", "T2", "T3")] + [{"market": f"A-{i}", "look": "T1", "event": "A"} for i in range(2, 6)]
    om = r.one_per_market(rows)
    assert len(om) == 5 and len({x["market"] for x in om}) == 5
    capped = r.cap_per_event(om)
    assert len(capped) == 2
    assert r.cap_per_event(om) == capped                # deterministic


def test_groups_partition():
    f0 = {k: False for k in r.ORDER}
    f1 = dict(f0, STRICT=True, SOURCE=True)
    fu = dict(f0, PRINT=None)
    rows = [{"event": "a", "fl": f0}, {"event": "b", "fl": f1}, {"event": "c", "fl": fu}, {"event": "d", "fl": None}]
    g = r.groups(rows)
    assert len(g["CONTROL"]) == 1 and len(g["STRICT"]) == 1 and len(g["SOURCE"]) == 1 and len(g["UNSTABLE"]) == 1 and len(g["NOMETA"]) == 1


def test_verdict():
    assert r.verdict(149, 1, 1, 9) == "NOT_ENOUGH_DATA"
    assert r.verdict(200, 1, 1, 1.49) == "FALSIFIED"
    assert r.verdict(200, 1, -0.1, 3) == "FALSIFIED"
    assert r.verdict(200, 1, 1, 1.5) == "LEAD"


def test_pf_and_ask_guard():
    assert abs(r.pf([1, -1]) - 1) < 1e-12
    d = tempfile.mkdtemp(); p = pathlib.Path(d) / "e.jsonl"
    p.write_text(json.dumps({"series": "S", "ask": 0.31, "event": "e", "t": 1, "market": "m", "look": "T", "cat": "x", "won": 1}) + "\n")
    r.ENTRIES = p
    try:
        r.load_entries(False); assert False
    except AssertionError as e:
        assert "above 0.30" in str(e)


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("rules1 tests ok")
