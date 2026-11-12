"""Synthetic test for poli2_count.py (made-up data, no Kalshi). Run: python3 test_poli2.py"""
import gzip, json, os, sys, tempfile, calendar
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import poli2_count as p
import kalshi_pull as kp

def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]]))
            rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

kp.check_job(p.build_s0())
s0 = {"series": [{"ticker": "KXAAA", "category": "Politics", "frequency": "weekly"}, {"ticker": "KXBBB", "category": "Politics", "frequency": "daily"}, {"ticker": "KXONE", "category": "Politics", "frequency": "one_off"}, {"ticker": "KXWX", "category": "Climate", "frequency": "daily"}]}
def mk(t, close, open_, vol, res="yes"):
    f = lambda x: datetime.utcfromtimestamp(x).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"ticker": t, "result": res, "close_time": f(close), "open_time": f(open_), "volume_fp": str(vol)}
live_close = calendar.timegm((2026, 10, 1, 0, 0, 0)); old_close = calendar.timegm((2026, 3, 1, 0, 0, 0))
with tempfile.TemporaryDirectory() as d0, tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
    mkrun(d0, p.build_s0(), {"series_politics": s0})
    assert p.politics_series(d0) == ["KXAAA", "KXBBB"]
    j1 = p.build_s1(d0); kp.check_job(j1); assert len(j1["requests"]) == 2 and "KXWX" not in j1["series_allowlist"]
    lists = {"live_KXAAA": {"markets": [mk("KXAAA-1", live_close, live_close - 86400 * 30, 5000), mk("KXAAA-LOW", live_close, live_close - 86400, 50),
                                         mk("KXAAA-HELD", calendar.timegm((2026, 11, 6, 0, 0, 0)), live_close, 9000), mk("KXAAA-VOID", live_close, live_close - 86400, 900, "")]},
             "live_KXBBB": {"markets": []}}
    mkrun(d1, j1, lists)
    mk_ = p.markets_from(d1); assert sorted(mk_) == ["KXAAA-1"], sorted(mk_)    # low volume, held out, unsettled all dropped
    j2 = p.build_s2(d1); kp.check_job(j2)
    assert j2["ticker_allowlist"] == ["KXAAA-1"] and not any(r["path"].startswith("/historical") for r in j2["requests"]) and any(r["path"] == "/markets/candlesticks" for r in j2["requests"])
    assert all(r["params"]["end_ts"] < p.HELD_OUT_FROM for r in j2["requests"])
    # candles: hourly from 2026-09-01 on; 22:00 ET quiet at 0.50; next 06:00 ET 0.60/0.62, 07:00 ET 0.60/0.62 (moved up 10c, stale proxy holds)
    from zoneinfo import ZoneInfo; NY = ZoneInfo("America/New_York")
    def candles(days, move_day_idx, stale_ok=True):
        out = []
        start = datetime(2026, 9, 1, 0, 0, tzinfo=NY)
        for h in range(days * 24):
            t = start + timedelta(hours=h); dd = t.date(); day_i = (dd - start.date()).days
            lvl = 0.50
            nxt_morning = (day_i - 1) in move_day_idx and (t.hour < 22 or True) and t.hour in (6, 7) or ((day_i - 1) in move_day_idx and t.hour >= 8) or (day_i in move_day_idx and t.hour == 22)
            if (day_i - 1) in move_day_idx and t.hour >= 0 and t.hour <= 21 and t.hour >= 7: lvl = 0.60
            if (day_i - 1) in move_day_idx and t.hour == 6: lvl = 0.60 if stale_ok else 0.55
            if (day_i - 1) in move_day_idx and t.hour == 7: lvl = 0.60
            out.append({"end_period_ts": int(t.timestamp()), "yes_bid": {"close_dollars": "%.4f" % (lvl - 0.01)}, "yes_ask": {"close_dollars": "%.4f" % (lvl + 0.01)}, "volume_fp": "300"})
        return out
    moves = set(range(10, 70, 1))       # a gap the morning after every one of these evenings
    cs = candles(80, moves)
    gaps = p.count_market("KXAAA-1", cs, None)
    assert len(gaps) > 0 and all(g["strict"] for g in gaps), len(gaps)
    # price band: a NO buy needs 0.10 to 0.90 -> a YES gap up to 0.60 buys YES at the 0.61 ask: in band
    assert all(g["date"] >= "2026-09-11" for g in gaps)
    loose = p.count_market("KXAAA-1", candles(80, moves, stale_ok=False), None)
    assert all(not g["strict"] for g in loose) and len(loose) == len(gaps)           # not-yet-followed proxy fails when 06:00 differs by 5c
    # liquidity: 7-day volume under 200 -> none
    thin = [dict(c, volume_fp="1") for c in cs]; assert p.count_market("KXAAA-1", thin, None) == []
    mkrun(d2, j2, {r["id"]: ({"markets": [{"market_ticker": "KXAAA-1", "candlesticks": cs}]} if r["path"] == "/markets/candlesticks" else {"candlesticks": cs}) for r in j2["requests"]})
    out = p.count([d2], d1); assert out["strict"]["gaps"] > 0 and out["markets_read"] >= 1, out
    G = lambda i, ser="S", dm=0.0: dict(date="2026-%02d-%02d" % (10 + i // 28, 1 + i % 28), series="%s%d" % (ser, i), ticker="T%d" % i, strict=True, loose=True, within_24h_of_close=False, spread=0.01 + dm, round_trip=0.045 + dm)
    t = p.tally([G(i) for i in range(100)])
    assert t["verdict"].startswith("COUNT CLEARS 40 series-mornings"), t["verdict"]
    assert t["strict"]["series_mornings"] == 100 and "NOT tested at hourly resolution" in t["premise_note"]
    # the unit is the series-morning: 100 markets of ONE series on ONE morning count once (several markets of one event moving together)
    t = p.tally([dict(G(0), ticker="T%d" % i, series="S0") for i in range(100)]); assert t["strict"]["series_mornings"] == 1 and t["strict"]["gaps"] == 100 and t["verdict"].startswith("CLOSED: fewer than 40 series-mornings"), t
    # 60 series-mornings is 30 per half: closed; the cost kill (median round trip above 5c) closes it even when the count clears
    assert p.tally([G(i) for i in range(60)])["verdict"].startswith("CLOSED: fewer than 40")
    assert p.tally([G(i, dm=0.02) for i in range(100)])["verdict"].startswith("CLOSED on cost: the median round trip at the entry hour is 6.5c"), p.tally([G(i, dm=0.02) for i in range(100)])["verdict"]
    # cost screen from politics recorder quote files, zero requests; lists answers carry no spreads (finalized markets show 0 and 1)
    qf = os.path.join(d1, "q.csv"); open(qf, "w").write("series,ticker,yes_bid,yes_ask\nKXAAA,A-1,0.48,0.52\nKXAAA,A-2,0.30,0.36\nKXAAA,A-3,0.0,0.05\nKXAAA,A-4,0.90,0.95\nKXOTH,O-1,0.40,0.60\n")
    cs_ = p.cost_screen([qf], {"KXAAA"}); assert cs_["quotes"] == 2 and cs_["distinct_markets"] == 2 and cs_["verdict"].startswith("CLOSED on cost: median round trip 8.3c") , cs_
    cs2 = p.cost_screen([qf]); assert cs2["quotes"] == 3
    assert p.cost_screen([qf], {"KXNONE"})["quotes"] == 0
    # the request cap drops the lowest-volume markets and says so
    big = {"live_KXAAA": {"markets": [mk("KXAAA-%d" % i, live_close + i, live_close - 86400 * 20 + i, 1000 + i) for i in range(10)]}, "live_KXBBB": {"markets": []}}
    p.BUDGET = 6; p.PACK = 1  # each live market alone in a batch
    with tempfile.TemporaryDirectory() as d3:
        mkrun(d3, j1, big); j3 = p.build_s2(d3); assert len(j3["requests"]) <= 4 and "dropped by the request cap: 6" in j3["notes"], j3["notes"]
    # no 24 hour exit: a market closing within 24 hours of the entry is excluded and counted (Desk B's point 4)
    near = [dict(x, no_exit=True) for x in gaps]
    tt = p.tally(near + [G(i) for i in range(100)]); assert tt["gaps_excluded_no_24h_exit"] == len(near) and tt["strict"]["series_mornings"] == 100
    try: p.count([d2]); raise SystemExit("count without the lists passed")
    except ValueError as e: assert "lists folder is required" in str(e)
print("poli2 synthetic tests passed")
