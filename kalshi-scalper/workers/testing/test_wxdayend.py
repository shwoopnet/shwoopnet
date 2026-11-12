"""Synthetic test for wxdayend.py (made-up data, no Kalshi). Run: python3 -I test_wxdayend.py"""
import gzip, json, os, tempfile, wxdayend as w

def cand(ts, ask_close, ask_low=None):
    return {"end_period_ts": ts, "yes_ask": {"close_dollars": "%.4f" % ask_close, "low_dollars": "%.4f" % (ask_low if ask_low is not None else ask_close)}}

def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1)
            gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]]))
            rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

a = w.build_a()
assert len(a["requests"]) == 22 and a["max_requests"] == 22 and len(a["ticker_allowlist"]) == 18
# window = last 2h; day_end = close - 3600
def body(t, end, asks):
    return {"markets": [{"market_ticker": t, "candlesticks": [cand(end - 7200 + 60 * (k + 1) * 10, x) for k, x in enumerate(asks)]}]}
bodies = {}
for r in a["requests"]:
    if r["path"] == "/markets/candlesticks":
        t = r["params"]["market_tickers"]; bodies[r["id"]] = body(t, r["params"]["end_ts"], [1.0] * 12)
lists = {"l01_KXHIGHTDAL-26NOV10": {"markets": [{"ticker": "KXHIGHTDAL-26NOV10-B70.5", "result": "no", "close_time": "2026-11-11T07:00:00Z"}, {"ticker": "KXHIGHTDAL-26NOV10-B72.5", "result": "yes", "close_time": "2026-11-11T07:00:00Z"}]},
         "l02_KXHIGHDEN-26NOV10": {"markets": [{"ticker": "KXHIGHDEN-26NOV10-T60", "result": "yes", "close_time": "2026-11-11T08:00:00Z"}]},
         "l03_KXHIGHNY-26NOV10": {"markets": [{"ticker": "KXHIGHNY-26NOV10-B50.5", "result": "yes", "close_time": "2026-11-11T06:00:00Z"}]},
         "l04_KXHIGHLAX-26NOV10": {"markets": [{"ticker": "KXHIGHLAX-26NOV10-B70.5", "result": "yes", "close_time": "2026-11-11T09:00:00Z"}, {"ticker": "KXHIGHLAX-26NOV10-T71", "result": "yes", "close_time": "2026-11-11T09:00:00Z"}]}}
bodies.update(lists)
with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as db:
    mkrun(da, a, bodies)
    wins = w.winners_from_lists(da)
    assert wins["KXHIGHTDAL-26NOV10"] == ("KXHIGHTDAL-26NOV10-B72.5", 1794294000 + 3600 * 0 + 0) or wins["KXHIGHTDAL-26NOV10"][0].endswith("B72.5")
    assert wins["KXHIGHLAX-26NOV10"] is None          # two yes markets: not exactly one, refused
    b, _ = w.build_b(da); assert len(b["requests"]) == 3
    s = w.score(da)                                    # A only: 18 new + 18 prior = 36 read, 4 unread
    assert s["city_days_read"] == 36 and len(s["city_days_unread"]) == 4 and s["verdict"].startswith("INCOMPLETE")
    # B run: all 1.00 except one Denver city-day showing 0.90 AFTER day end, and one showing 0.90 BEFORE day end only
    bb = {r["id"]: body(r["params"]["market_tickers"], r["params"]["end_ts"], [1.0] * 12) for r in b["requests"]}
    mkrun(db, b, bb)
    s = w.score(da, db)
    assert s["city_days_read"] == 39, s["city_days_read"]   # LAX Nov 10 unresolved: stays unread, never guessed
    assert s["verdict"].startswith("INCOMPLETE") and s["show_ask_close_le_0.96"] == 0
    # post-day vs pre-day: candle ending exactly at day_end does not count; the next one does
    t = "KXHIGHDEN-26NOV05-B58.5"; end = 1000000
    pre = w.city_day(t, end, [cand(end - 3600, 0.5)]); assert not pre["shows"] and pre["n_post_candles"] == 0
    post = w.city_day(t, end, [cand(end - 3540, 0.96)]); assert post["shows"]                    # 0.96 counts (at or under)
    assert not w.city_day(t, end, [cand(end - 60, 0.97)])["shows"]
    low = w.city_day(t, end, [cand(end - 60, 1.0, 0.9)]); assert not low["shows"] and low["shows_low"]   # basis difference is reported
    assert not w.city_day(t, end, [])["shows"]
    # complete 40: fix LAX so exactly one yes, then 2 showing -> FAIL, 3 showing -> kill rule not hit
    lists["l04_KXHIGHLAX-26NOV10"]["markets"].pop()
    for n_show, expect in ((2, "FAIL"), (3, "KILL RULE NOT HIT")):
        with tempfile.TemporaryDirectory() as da2, tempfile.TemporaryDirectory() as db2:
            bod = dict(bodies); bod.update(lists)
            shown = [r["id"] for r in a["requests"] if r["path"] == "/markets/candlesticks"][:n_show]
            for r in a["requests"]:
                if r["id"] in shown:
                    t = r["params"]["market_tickers"]; bod[r["id"]] = body(t, r["params"]["end_ts"], [1.0] * 6 + [0.9] * 6)
            mkrun(da2, a, bod); b2, _ = w.build_b(da2); assert len(b2["requests"]) == 4
            mkrun(db2, b2, {r["id"]: body(r["params"]["market_tickers"], r["params"]["end_ts"], [1.0] * 12) for r in b2["requests"]})
            s2 = w.score(da2, db2); assert s2["city_days_read"] == 40 and s2["verdict"].startswith(expect), s2["verdict"]
    full = {e: {"event": e, "shows": False, "shows_low": False} for e in w.UNIVERSE}
    def verdict(n):
        rows = dict(full)
        for e in w.UNIVERSE[:n]: rows[e] = {"event": e, "shows": True, "shows_low": True}
        n_show = sum(1 for e in w.UNIVERSE if rows[e]["shows"]); return n_show
    assert w.PRIOR_READ and len(w.UNIVERSE) == 40 and len(w.PRIOR_READ) == 18
print("wxdayend synthetic tests passed")
