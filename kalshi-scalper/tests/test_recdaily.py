"""RECDAILY recorder and reader on synthetic data (no network, no outcome). Research only."""
import csv
import gzip
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

import record_daily as rd  # noqa: E402
from scalper import recdaily as r  # noqa: E402

rd._sleep = lambda x: None
WATCH = os.path.join(HERE, "..", "workers", "RECDAILY_WATCHLIST.json")
NOW = 1_800_000_000 - 1_800_000_000 % 1800 + 120      # 2 minutes into a slot
CLOSE_ISO = rd.iso(NOW + 6 * 3600)


def mk(ticker, close, yb="0.90", ya="0.92", **kw):
    m = {"ticker": ticker, "event_ticker": ticker.rsplit("-", 1)[0], "close_time": close, "open_time": rd.iso(NOW - 3600), "status": "active", "strike_type": "greater",
         "floor_strike": 100, "yes_bid_dollars": yb, "yes_ask_dollars": ya, "last_price_dollars": "0.91", "volume_fp": "12.00", "open_interest_fp": "5.00"}
    m.update(kw)
    return m


def fake_get(url):
    if "series_ticker=KXGOLDD&status=open" in url:
        return 200, {"markets": [mk("KXGOLDD-A-T1", CLOSE_ISO), mk("KXGOLDD-A-T2", rd.iso(NOW + 90 * 3600))], "cursor": ""}, "Tue, 03 Nov 2026 12:00:00 GMT"
    if "series_ticker=KXBTCMAXMON&status=open" in url:
        return 200, {"markets": [mk("KXBTCMAXMON-X-1", rd.iso(NOW + 20 * 86400))], "cursor": ""}, ""
    if "series_ticker=KXGOLDD&status=settled" in url:
        return 200, {"markets": [mk("KXGOLDD-OLD-T1", rd.iso(NOW - 3600), result="yes"), mk("KXGOLDD-OLD-T2", rd.iso(NOW - 3600), result="")], "cursor": ""}, ""
    if "status=open" in url:
        return 429, None, ""
    return 200, {"markets": [], "cursor": ""}, ""


def t_run_is_watchlist_driven_and_idempotent():
    with tempfile.TemporaryDirectory() as d:
        s1 = rd.run(WATCH, d, now=NOW, getter=fake_get)
        s2 = rd.run(WATCH, d, now=NOW + 60, getter=fake_get)         # same slot: overwrites, no second result file
        q = glob_one(d, "quotes")
        assert len(q) == 1, q
        rows = list(csv.DictReader(gzip.open(q[0], "rt")))
        tick = sorted(x["ticker"] for x in rows)
        assert tick == ["KXBTCMAXMON-X-1", "KXGOLDD-A-T1"], tick       # the 90 hour gold market is outside the 30 hour window; the monthly one is kept
        assert s1[7] > 0 and s1[6] > 0                                 # other series answered 429: counted, run still finished
        res = glob_one(d, "results")
        assert len(res) == 1
        assert [x["ticker"] for x in csv.DictReader(gzip.open(res[0], "rt"))] == ["KXGOLDD-OLD-T1"]   # unsettled (no result) is skipped; second run adds nothing
        assert s2[9] == 0


def glob_one(d, kind):
    import glob
    return glob.glob(os.path.join(d, "daily", kind, "**", "*.csv.gz"), recursive=True)


def t_reader_nearest_look():
    close = NOW + 6 * 3600
    rows = []
    for k in range(0, 13):
        ts = NOW + k * 1800 + 40
        m = mk("KXGOLDD-A-T1", CLOSE_ISO, yb=str(0.80 + k / 100), ya=str(0.82 + k / 100))
        raw = dict(zip(rd.QUOTE_COLS, rd.quote_row(ts - ts % 1800, ts, "", "KXGOLDD", {"tests": ["USWEEP1"]}, m)))
        rows.append(r._clean(raw))
    q = r.nearest_to_look(rows, "KXGOLDD-A-T1", minutes_before_close=360)
    assert q is not None and q["look_gap_s"] <= 25 * 60 and abs(q["poll_ts"] - (close - 360 * 60)) <= 60
    assert r.nearest_to_look(rows, "KXGOLDD-A-T1", minutes_before_close=1440) is None        # no poll near a look before the recording began
    assert r.nearest_to_look(rows, "NOPE", minutes_before_close=60) is None
    w = r.usweep1_window(rows, {"KXGOLDD-A-T1": "yes"}, "KXGOLDD-A-T1", 360)
    assert w["result"] == "yes" and list(w["candles"].values())[0][1] > 0.8
    w2 = r.usweep1_window(rows, {}, "KXGOLDD-A-T1", 1440)
    assert w2["candles"] == {}
    try:
        r.nearest_to_look(rows, "KXGOLDD-A-T1")
        assert False
    except ValueError:
        pass


def t_reader_roundtrip_from_disk():
    with tempfile.TemporaryDirectory() as d:
        rd.run(WATCH, d, now=NOW, getter=fake_get)
        dd = os.path.join(d, "daily")
        rows = r.load_quotes(dd, series="KXGOLDD")
        assert [x["ticker"] for x in rows] == ["KXGOLDD-A-T1"]
        assert r.load_results(dd) == {"KXGOLDD-OLD-T1": "yes"}
        assert r.tickers(rows, "KXGOLDD") == ["KXGOLDD-A-T1"]
        open(os.path.join(dd, "quotes", "bad.csv.gz"), "wb").write(b"junk")
        assert len(r.load_quotes(dd, series="KXGOLDD")) == len(rows)        # a corrupt file is skipped, not fatal


def t_watchlist_covers_registered_series():
    w = json.load(open(WATCH))
    ser = {e["series"] for e in w["watch"]}
    for s in ("KXGOLDD", "KXSILVERD", "KXNATGASD", "KXBRENTD", "KXHIGHTSATX", "KXCPI", "KXCPICORE", "KXPCECORE", "KXGDP", "KXFEDDECISION", "KXFED", "KXBTCMAXMON", "KXETHMINMON"):
        assert s in ser, s
    sys.path.insert(0, os.path.join(HERE, "..", "src"))
    from scalper import usweep1
    for e in w["watch"]:
        if e["test"] == "USWEEP1":
            assert usweep1.FWD[e["series"]] in e["looks_minutes_before_close"], e["series"]


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("t_"):
            f()
            print("ok  ", n)
