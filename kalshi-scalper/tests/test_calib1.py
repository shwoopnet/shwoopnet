import sys, pathlib, json, tempfile
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import calib1 as c


def row(cat, bk, ev, t, won, ask):
    return {"cat": cat, "bk": bk, "event": ev, "t": t, "won": won, "ask": ask, "net": c.net_per_contract(bool(won), ask), "date": str(t // 86400), "life": "D", "ttc": "1-6h", "market": ev + "-x", "look": "T60"}


def test_fee_and_net():
    assert abs(c.fee_per_contract(0.10) - 0.007) < 1e-9          # 0.07*10*0.1*0.9 = 0.063 -> 7c / 10
    assert abs(c.net_per_contract(False, 0.10) - (-0.10 - 0.007)) < 1e-9
    assert abs(c.net_per_contract(True, 0.10) - (0.9 - 0.007)) < 1e-9


def test_buckets():
    assert c.ask_bucket(0.02) is None and c.ask_bucket(0.31) is None
    assert c.ask_bucket(0.03) == 0 and c.ask_bucket(0.0499) == 0 and c.ask_bucket(0.05) == 1
    assert c.ask_bucket(0.10) == 2 and c.ask_bucket(0.15) == 3 and c.ask_bucket(0.20) == 4 and c.ask_bucket(0.30) == 4
    assert c.ask_bucket(0.55) is None and c.ask_bucket(0.97) is None            # nothing above 0.30 can be bucketed


def test_cheap_side_only():
    assert c.cheap_side(0.0, 0.05) is None                    # one sided: no quote
    assert c.cheap_side(0.04, 0.06) == ("yes", 0.06)
    assert c.cheap_side(0.80, 0.84) == ("no", 0.2)             # NO ask = 1 - bid
    assert c.cheap_side(0.50, 0.52) is None                    # no cheap side
    assert c.cheap_side(0.92, 0.95) == ("no", 0.08)         # the cheap side of a 92/95 quote is the NO at 8c, never the 95c YES


def test_event_and_buckets():
    assert c.event_of("KXHIGHNY-26OCT22-T70") == "KXHIGHNY-26OCT22"
    assert c.ttc_bucket(30) == "<=1h" and c.ttc_bucket(100) == "1-6h" and c.ttc_bucket(5000) == ">3d"
    assert c.life_class(3600) == "H" and c.life_class(86400) == "D" and c.life_class(10 * 86400) == "W"
    assert c.norm_cat("Elections") == "Politics"


def test_split_and_clusters():
    rows = [row("A", 1, f"E{i}", i, 0, 0.07) for i in range(10) for _ in range(3)]
    a, b = c.split_halves(rows)
    assert len(a) == 15 and len(b) == 15 and {r["event"] for r in a} == {f"E{i}" for i in range(5)}
    g = c.event_groups(rows)
    assert len(g) == 10 and g["E0"][1] == 3                    # three strikes of one event are ONE cluster


def test_bootstrap_ci_and_lead_rule():
    rng = np.random.default_rng(1)
    # a planted edge: 40 events per half, win 40% at price 0.10 -> clearly positive in both halves
    rows = []
    for i in range(80):
        rows.append(row("A", 1, f"E{i}", i, 1 if i % 5 < 2 else 0, 0.10))
    a, b = c.split_halves(rows)
    sa, sb = c.stats(a, rng), c.stats(b, rng)
    assert sa["events"] == 40 and sa["net"] > 0 and sa["lo"] > 0 and sa["lo"] <= sa["net"] <= sa["hi"]
    assert c.verdict(sa, sb) == "LEAD"
    # a null: win 5% at price 0.10 is negative after fee -> no lead
    rows = [row("A", 1, f"E{i}", i, 1 if i % 20 == 0 else 0, 0.10) for i in range(80)]
    a, b = c.split_halves(rows)
    sa, sb = c.stats(a, rng), c.stats(b, rng)
    assert c.verdict(sa, sb) == "NEGATIVE_OR_NO_EDGE"
    # too few events per half
    rows = [row("A", 1, f"E{i}", i, 1, 0.10) for i in range(40)]
    a, b = c.split_halves(rows)
    assert c.verdict(c.stats(a, rng), c.stats(b, rng)) == "NOT_ENOUGH_DATA"


def test_one_event_many_strikes_is_not_many_independent_events():
    rng = np.random.default_rng(2)
    # 3 events, 100 strikes each, all winners: n is 300 but only 3 independent events
    rows = [row("A", 1, f"E{e}", e, 1, 0.10) for e in range(3) for _ in range(100)]
    s = c.stats(rows, rng)
    assert s["n"] == 300 and s["events"] == 3
    a, b = c.split_halves(rows)
    assert c.verdict(c.stats(a, rng), c.stats(b, rng)) == "NOT_ENOUGH_DATA"


def test_score_end_to_end_synthetic():
    d = pathlib.Path(tempfile.mkdtemp())
    c.OUT = d
    c.WORKERS = d
    c.REGISTERED_CATEGORIES[:] = ["A", "B"]
    rows = [row("A", 1, f"E{i}", i, 1 if i % 5 < 2 else 0, 0.10) for i in range(80)]
    rows += [row("B", 2, f"F{i}", i, 0, 0.12) for i in range(80)]
    rows += [row("Z", 0, f"G{i}", i, 0, 0.04) for i in range(5)]
    (d / "entries.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = c.score()
    assert len(out["grid"]) == 10 and len(out["pooled"]) == 20
    leads = [(g["cat"], g["bucket"]) for g in out["leads"]]
    assert leads == [("A", "5-10c")], leads
    assert [o["cat"] for o in out["other_categories"]] == ["Z"]
    try:
        c.score()
        assert False, "second run must refuse"
    except SystemExit:
        pass


def test_no_favourite_entry_can_be_written():
    for bad in (0.31, 0.5, 0.85, 0.97):
        assert c.ask_bucket(bad) is None


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("test_calib1 OK")
