import os, sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import spotd1


def mk(n=120, top=lambda i: "song a"):
    ms = []
    d0 = date(2025, 1, 1)
    for i in range(n):
        d = d0 + timedelta(days=i)
        e = "KXSPOTIFYD-" + d.strftime("%y%b%d").upper()
        st = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1, hours=20)
        for t in ("song a", "song b", "song c"):
            ms.append(dict(series="KXSPOTIFYD", event_ticker=e, ticker=e + "-" + t[-1].upper(), yes_sub_title=t.title(),
                           result="yes" if t == top(i) else "no", settlement_ts=st.isoformat().replace("+00:00", "Z")))
    return ms


def test_events_and_no_lookahead():
    ev = spotd1.events_of(mk(), ("KXSPOTIFYD",))
    assert len(ev) == 120
    P = spotd1.predictions(ev)
    assert P
    # the day before is not yet settled at the 00:00 UTC look (settles D+1 20:00), so a1 comes from D-2 or earlier
    e = sorted(P, key=lambda x: ev[x]["date"])[-1]
    L = P[e][0]
    assert all(v["settle"] <= L for v in [ev[x] for x in ev if ev[x]["date"] < ev[e]["date"] and ev[x]["settle"] <= L])
    assert ev[sorted(ev, key=lambda x: ev[x]["date"])[0]]["settle"] > 0


def test_persistent_title_gets_high_fair():
    P = spotd1.predictions(spotd1.events_of(mk(), ("KXSPOTIFYD",)))
    L, a, r = P[sorted(P)[-1]]
    assert a == ["songa"] and r[0] > 0.95


def test_burn_in():
    assert spotd1.predictions(spotd1.events_of(mk(40), ("KXSPOTIFYD",))) == {}


def test_entry_and_fee_and_thirds():
    assert spotd1.entry(0.9, 0.40, 0.45)[0] == "yes"
    assert spotd1.entry(0.1, 0.60, 0.65)[0] == "no"
    assert spotd1.entry(0.9, 0.40, 0.60) is None
    assert abs(spotd1.fee(0.5) - 0.018) < 1e-9  # 0.175 rounded up per order of 10
    w = spotd1.thirds([date(2025, 1, 1) + timedelta(days=i) for i in range(90)])
    assert w(date(2025, 1, 2)) == "W1" and w(date(2025, 4, 1)) == "W3"
