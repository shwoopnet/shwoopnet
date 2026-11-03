import sys, os
from datetime import date, datetime, timedelta, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import count2 as c

CSV = "Time,F_Scale,Location,County,State,Lat,Lon,Comments\n1730,UNK,a,b,OH,1,2,x\n1850,UNK,a,b,PA,1,2,y\nTime,Speed,Location,County,State,Lat,Lon,Comments\n1200,60,w,w,w,1,2,z\n1300,70,w,w,w,1,2,z\nTime,Size,Location,County,State,Lat,Lon,Comments\n1400,100,h,h,h,1,2,q\n"

def test_parse_tornado_section():
    assert c.parse_tornado_rows(CSV) == 2
    assert c.parse_tornado_rows("Time,F_Scale,Location\nTime,Speed,x\n1,2,3\n") == 0

def test_pmf_sums():
    assert abs(sum(c.nb_pmf(30, 5, 800)) - 1) < 1e-6 and c.nb_pmf(0, 5, 3)[0] == 1.0

def test_strike_of():
    assert c.strike_of({"floor_strike": None, "rules_primary": "number of tornadoes in Jan is above 75 , then"}) == 75
    assert c.strike_of({"floor_strike": 12, "rules_primary": ""}) == 12

def test_strike_greater():
    pmf = [0.0] * 3 + [1.0]
    assert c.strike_prob({"strike_type": "greater", "floor_strike": 12}, 10, pmf) == 1.0
    assert c.strike_prob({"strike_type": "greater", "floor_strike": 13}, 10, pmf) == 0.0

def test_usable_and_look_dst():
    look = c.look_of(2026, 3)            # DST starts 2026-03-08
    assert c.usable(date(2026, 3, 14), look) and not c.usable(date(2026, 3, 15), look)
    look = c.look_of(2026, 11)           # DST ends 2026-11-01
    a, b = c.month_bounds(2026, 11)
    assert b - a == timedelta(days=30, hours=1)
    assert c.usable(date(2026, 11, 13), look) and not c.usable(date(2026, 11, 14), look)  # look is 23:30 EST on Nov 15

def test_no_ask_and_fee_and_cap():
    cand = [(100, 0.5, 0.40), (1000, 0.2, 0.7)]
    look = datetime.fromtimestamp(500, tz=timezone.utc)
    assert c.fills(cand, look, "yes") == (0.5, 0.2)
    assert abs(c.fills(cand, look, "no")[1] - 0.3) < 1e-9
    assert abs(c.fee(0.5) - 0.018) < 1e-9
    sel = c.select([("a", .9, .2), ("b", .5, .1), ("c", .4, .1), ("d", .1, .2)])
    assert len(sel) == 2 and sel[0][0] == "b" and all(r[0] != "d" for r in sel)

def test_split_frozen():
    ms = [{"event_ticker": "E%02d" % i, "close_time": "%04d-%02d-01T04:00:00Z" % (2023 + (i + 7) // 12, (i + 7) % 12 + 1)} for i in range(39)]
    dev, hold = c.split_events(ms)
    assert len(dev) == 26 and len(hold) == 13 and dev[-1][0] < hold[0][0]
