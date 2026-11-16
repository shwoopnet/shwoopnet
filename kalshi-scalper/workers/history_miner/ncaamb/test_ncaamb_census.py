"""python3 -I test_ncaamb_census.py : the guard and the counts, invented markets (price columns poisoned)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ncaamb_census as C
def mk(tk, ev, cl, occ=None, **extra):
    d = {"ticker": tk, "event_ticker": ev, "close_time": cl, "yes_bid_dollars": "0.4", "yes_ask_dollars": "0.6", "last_price_dollars": "0.5", "result": "yes", "volume_fp": "10"}
    if occ: d["occurrence_datetime"] = occ
    d.update(extra); return d
ms = [mk("KXNCAAMBGAME-26NOV17ABCD-AB", "KXNCAAMBGAME-26NOV17ABCD", "2026-11-17T23:00:00Z", "2026-11-18T01:00:00Z"),
      mk("KXNCAAMBGAME-26NOV17ABCD-CD", "KXNCAAMBGAME-26NOV17ABCD", "2026-11-17T23:00:00Z", "2026-11-18T01:00:00Z"),
      mk("KXNCAAMBGAME-26NOV17EFGH-EF", "KXNCAAMBGAME-26NOV17EFGH", "2026-11-18T01:00:00Z", "2026-11-18T03:00:00Z"),
      mk("KXNCAAMBTOTAL-26NOV17ABCD-140", "KXNCAAMBTOTAL-26NOV17ABCD", "2026-11-17T23:00:00Z"),
      mk("KXNBAGAME-X-A", "KXNBAGAME-X", "2026-11-17T23:00:00Z")]
r = C.census(ms)                                     # the price, size and result columns are never read (a read would raise)
g = r["KXNCAAMBGAME"]
assert g["markets"] == 3 and g["events"] == 2 and g["events_by_close_day_utc"] == {"2026-11-17": 1, "2026-11-18": 1} and abs(g["mean_events_per_close_day"] - 1.0) < 1e-12
assert r["KXNCAAMBTOTAL"]["events"] == 1 and r["KXNCAAMBSPREAD"]["markets"] == 0 and "KXNBAGAME" not in r
assert abs(g["markets_per_event"] - 1.5) < 1e-12 and g["events_by_schedule_day_utc"] == {"2026-11-18": 2}
for field in ("yes_bid_dollars", "yes_ask_dollars", "last_price_dollars", "result", "volume_fp"):
    try:
        C.Guarded(ms[0])[field]; assert False
    except AssertionError as e:
        assert "counts only" in str(e)
    try:
        C.Guarded(ms[0]).get(field); assert False
    except AssertionError as e:
        assert "counts only" in str(e)
print("counts and guard: ok")
