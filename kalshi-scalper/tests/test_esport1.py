import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import esport1 as E


def mk(series, ev, name, res, close, rules="", src="live"):
    return {"ticker": ev + name, "event_ticker": ev, "result": res, "open_time": "2026-01-01T00:00:00Z", "close_time": close,
            "yes_sub_title": name, "rules_primary": rules, "series": series, "src": src}


def test_parse_event_and_dst():
    s, n, dt = E.parse_event("KXCS2MAP-26NOV020700WINGDNK-2")
    assert n == 2 and s == 1793620800  # 07:00 EST = 12:00Z
    assert E.parse_event("KXCS2MAP-26MAY081500ISGMIBR.F-1")[1] == 1
    assert E.parse_event("junk") is None


def test_rule_start_matches():
    dt = E.parse_event("KXCS2MAP-26NOV020700WINGDNK-1")[2]
    assert E.rule_start_matches("originally scheduled for Nov 2, 2026 at 7:00 AM EST, then", dt)
    assert not E.rule_start_matches("originally scheduled for Nov 2, 2026 at 8:00 AM EST", dt)


def test_elo_walk_forward_no_leak():
    res = [(100, "A", "B"), (200, "A", "B")]
    e = E.Elo(res)
    e.advance(150)
    assert e.n["A"] == 1 and e.i == 1  # the t=200 map is not applied
    r1 = e.r["A"]
    e.advance(150)
    assert e.r["A"] == r1
    assert E.expected(1500, 1500) == 0.5


def test_burn_in_and_fair():
    res = [(i, "A", "B") for i in range(1, 8)]
    e = E.Elo(res)
    e.advance(3)
    assert e.fair("A", "B") is None
    e.advance(10)
    assert e.fair("A", "B") > 0.5


def test_entry_rule_and_spread():
    assert E.entry(0.70, 0.50, 0.55)[0] == "yes"
    assert E.entry(0.30, 0.50, 0.55)[0] == "no"
    assert E.entry(0.56, 0.50, 0.55) is None
    assert E.entry(0.90, 0.40, 0.55) is None  # spread over 10c


def test_quote_first_valid_in_window():
    st = 10000
    cs = [(st - 700, 0.4, 0.5), (st - 590, None, 0.5), (st - 500, 0.45, 0.5), (st - 100, 0.6, 0.7), (st + 30, 0.9, 0.95)]
    assert E.quote(cs, st) == (0.45, 0.5)
    assert E.quote([(st + 30, 0.4, 0.5)], st) is None


def test_universe_uses_only_earlier_results():
    ms = {}
    names = ("AAA", "BBB")
    # eight earlier maps (AAA beats BBB), settled long before the later event
    for i in range(8):
        ev = f"KXCS2MAP-26OCT0{i+1}0700AAABBB-2"
        for n in names:
            m = mk("KXCS2MAP", ev, n, "yes" if n == "AAA" else "no", f"2026-10-0{i+1}T13:00:00Z")
            ms[m["ticker"]] = m
    ev = "KXCS2MAP-26OCT200700AAABBB-1"
    rules = "originally scheduled for Oct 20, 2026 at 7:00 AM EDT"
    for n in names:
        m = mk("KXCS2MAP", ev, n, "yes" if n == "AAA" else "no", "2026-10-20T13:00:00Z", rules)
        ms[m["ticker"]] = m
    u = E.universe(ms)
    assert len(u) == 1 and next(iter(u.values()))["fair"] > 0.5
    # the same event with its result time before the entry would change nothing for itself: it is the target, not history
    tgt = next(iter(u.values()))
    assert tgt["event"] == ev


def test_thirds_and_brier():
    w = E.thirds(list(range(9)))
    assert [w(i) for i in (0, 3, 6)] == ["W1", "W2", "W3"]
    elig = {"x": ({"fair": 0.8, "res": "yes", "start": 1}, (0.5, 0.52))}
    mb, kb, n = E.brier(elig)
    assert n == 1 and mb < kb
