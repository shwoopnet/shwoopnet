import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import earnpr1 as e


def test_clean_and_in_release():
    t = e.clean_text("<p>Revenue grew; <b>Tariffs</b> weighed. AI&nbsp;demand&#8217;s up.</p>")
    assert e.in_release("Tariff", t) and e.in_release("tariffs", t)
    assert e.in_release("AI", t) and not e.in_release("Cloud", t)
    assert not e.in_release("tar", t)            # whole words only
    assert e.in_release("Free cash flow / FCF", "free cash flow was strong")
    assert e.in_release("Free cash flow / FCF", "fcf was strong") 


def test_call_time():
    assert e.call_time(1000, 1500) == (1000, "sched") and e.call_time(1000, 800) == (800, "sched") and e.call_time(None, 900) == (900, "proxy")


def test_stem():
    assert e.stem_of("Tariffs / Tariff") == "tariff" and e.stem_of("Class") == "class" and e.stem_of("AI") == "ai"


def test_match_filing_window_and_latest():
    occ = e.ts("2026-08-25T14:00:00Z")
    f = [("a", "2026-08-25T11:30:00.000Z"), ("b", "2026-08-24T11:30:00.000Z"), ("c", "2026-08-10T11:30:00.000Z"), ("d", "2026-08-25T20:00:00.000Z")]
    assert e.match_filing(occ, f)[0] == "a" and e.match_filing(occ, f[2:3]) is None and e.match_filing(occ, f[3:]) is None


def test_look_needs_both_margins():
    acc, occ = 1000, 1000 + 3600
    c = [(1000 + 300, .1, .12), (1000 + 700, .1, .12), (1000 + 2000, .1, None), (occ - 300, .1, .12), (occ - 700, .2, .15)]
    assert e.look_quote(c, acc, occ) == (1700, .1, .12)   # 700 s after filing is the last valid one at least 10 min before the call
    assert e.look_quote(c[:1], acc, occ) is None


def test_model_shrinks_and_falls_back():
    rows = [("x", True, True)] * 8 + [("x", True, False)] * 2 + [("y", True, False)] * 2 + [("z", False, False)] * 9
    r = e.fit_model(rows)
    assert abs(r("x", True) - (8 + 2 * (8.5 / 12.0 if False else r("q", True))) / 12) < 1e-9
    assert r("y", True) == r("q", True)          # under MIN_CELL falls back to the pooled rate
    assert r("z", False) < 0.1


def test_net_and_pf_and_cluster():
    assert abs(e.trade_net(0.2, True) - (0.8 - e.fee(0.2))) < 1e-12 and e.trade_net(0.2, False) < -0.2
    assert e.pf([1, -1]) == 1 and e.pf([1]) == float("inf")
    m, z, n = e.cluster_z([("a", 1), ("a", 1), ("b", 3), ("c", 2)])
    assert n == 3 and z > 0


def test_verdict_rules():
    T = [dict(ev=i, net=0.5 if i % 4 else -0.2, half=1 + i % 2) for i in range(200)]
    C = [dict(ev=i, net=-0.05, half=1) for i in range(500)]
    assert e.verdict(T, C, 10, 0.9, 100) == "NOT_RUNNABLE" and e.verdict(T, C, 60, 0.3, 100) == "NOT_RUNNABLE"
    assert e.verdict(T[:100], C, 60, 0.9, 100) == "NOT_ENOUGH_DATA" and e.verdict(T, C, 60, 0.9, 30) == "NOT_ENOUGH_DATA"
    assert e.verdict(T, C, 60, 0.9, 100) == "NOT_YET_FALSIFIED"
    bad = [dict(ev=i, net=-0.1, half=1 + i % 2) for i in range(200)]
    assert e.verdict(bad, C, 60, 0.9, 100) == "FALSIFIED"


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("earnpr1 tests ok")
