"""WXLOW1: the daily-low extension of the WXENS1 recorder and reader, on synthetic data (no network). Research only."""
import csv
import gzip
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

import record_wxens as rec  # noqa: E402
from scalper import wxens1 as W  # noqa: E402
from scalper import wxlow1 as L  # noqa: E402

rec._sleep = lambda x: None
WATCH = os.path.join(HERE, "..", "workers", "WXENS1_WATCHLIST.json")


def ts(s):
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())


def rows(d, table, day, hh):
    return list(csv.DictReader(gzip.open(os.path.join(d, "wxens", table, day, hh + ".csv.gz"), "rt")))


# 1. the watchlist: every city has the KXLOWT series, named in the watchlist and not in the script
w = json.load(open(WATCH))
assert len(w["cities"]) == 14 and all(c["low_series"].startswith("KXLOWT") for c in w["cities"])
assert [c["low_series"] for c in w["cities"] if c["key"] == "NYC"] == ["KXLOWTNYC"]
assert len({c["low_series"] for c in w["cities"]}) == 14

# 2. parse_ensemble on the LIVE response shape seen 2026-11-03 (model names ncep_gefs_seamless, ecmwf_ifs025_ensemble, icon_seamless_eps); max and min keys never mix
live = {"daily": {"time": ["2026-11-03", "2026-11-04", "2026-11-05"],
                  "temperature_2m_min_ncep_gefs_seamless": [53.4, 56.9, 62.3], "temperature_2m_min_member01_ncep_gefs_seamless": [53.6, 57.1, 60.4],
                  "temperature_2m_min_member01_ecmwf_ifs025_ensemble": [52.0, 55.0, 59.0], "temperature_2m_min_member02_icon_seamless_eps": [54.0, 58.0, None],
                  "temperature_2m_max_member01_ncep_gefs_seamless": [70.0, 71.0, 72.0], "temperature_2m_max_ncep_gefs_seamless": [69.0, 70.0, 71.0]}}
lo = rec.parse_ensemble(live, {"2026-11-04", "2026-11-05"}, "temperature_2m_min")
assert sorted({m for m, _, _, _ in lo}) == ["ecmwf_ifs025_ensemble", "icon_seamless_eps", "ncep_gefs_seamless"], lo
assert all(k.startswith("temperature_2m_min") for _, k, _, _ in lo) and len(lo) == 7        # the icon None on 11-05 is dropped
hi = rec.parse_ensemble(live, {"2026-11-04"})
assert all(k.startswith("temperature_2m_max") for _, k, _, _ in hi) and {m for m, _, _, _ in hi} == {"ncep_gefs_seamless"} and len(hi) == 2

# 3. NWS night temperature: the night that starts the evening before the date ('prior') and the night that starts on it ('same'); daytime periods never count
body = {"properties": {"periods": [
    {"name": "Tonight", "isDaytime": False, "startTime": "2026-11-03T18:00:00-05:00", "temperature": 54},
    {"name": "Wednesday", "isDaytime": True, "startTime": "2026-11-04T06:00:00-05:00", "temperature": 73},
    {"name": "Wednesday Night", "isDaytime": False, "startTime": "2026-11-04T18:00:00-05:00", "temperature": 59},
    {"name": "Thursday Night", "isDaytime": False, "startTime": "2026-11-05T18:00:00-05:00", "temperature": 49}]}}
assert rec.parse_nws_low(body, "2026-11-04") == [(54.0, "prior", "2026-11-03T18:00:00-05:00", "Tonight"), (59.0, "same", "2026-11-04T18:00:00-05:00", "Wednesday Night")]
assert rec.parse_nws_low(body, "2026-11-08") == [] and rec.parse_nws_low(None, "2026-11-04") == []
assert rec.parse_nws(body, "2026-11-04")[0] == 73.0, "the highs parser is unchanged"

# 4. a full fake run: still ONE ensemble call asking for both variables; the lows add one listing per due city; low tables are separate files; the highs files hold only highs
NOW = ts("2026-11-04 15:12")      # 10:12 New York standard time
calls = []


def mk(ticker, kind, fl, cp, ask, ev, vol="300.00"):
    return {"ticker": ticker, "event_ticker": ev, "close_time": "2026-11-06T06:00:00Z", "strike_type": kind, "floor_strike": fl, "cap_strike": cp,
            "yes_bid_dollars": "%.4f" % (ask - 0.01), "yes_ask_dollars": "%.4f" % ask, "last_price_dollars": "0.0500", "volume_fp": vol, "status": "active", "rules_primary": "low rule text CLINYC"}


def fake(url):
    calls.append(url)
    if url.startswith(rec.OPENMETEO):
        assert url.count("latitude=") == 1 and "daily=temperature_2m_max,temperature_2m_min" in url
        b = {"daily": {"time": ["2026-11-04", "2026-11-05", "2026-11-06"],
                       "temperature_2m_max_member01_ncep_gefs_seamless": [60, 62, 63], "temperature_2m_min_member01_ncep_gefs_seamless": [40, 41, 42],
                       "temperature_2m_min_member01_ecmwf_ifs025_ensemble": [39, 43, 44]}}
        return 200, b, "Wed, 04 Nov 2026 15:12:30 GMT"
    if "/points/" in url:
        return 200, {"properties": {"forecast": "https://api.weather.gov/gridpoints/OKX/34,45/forecast", "gridId": "OKX", "gridX": 34, "gridY": 45}}, ""
    if "/gridpoints/" in url:
        return 200, {"properties": {"periods": [{"isDaytime": True, "startTime": "2026-11-05T06:00:00-05:00", "temperature": 66, "name": "Thursday"},
                                                {"isDaytime": False, "startTime": "2026-11-04T18:00:00-05:00", "temperature": 41, "name": "Wednesday Night"}]}}, ""
    if "series_ticker=KXLOWTNYC" in url and "status=open" in url:
        return 200, {"markets": [mk("KXLOWTNYC-26NOV05-T50", "greater", 50, None, 0.04, "KXLOWTNYC-26NOV05"), mk("KXLOWTNYC-26NOV05-B41.5", "between", 41, 42, 0.30, "KXLOWTNYC-26NOV05"),
                                 mk("KXLOWTNYC-26NOV04-T40", "less", None, 40, 0.50, "KXLOWTNYC-26NOV04")], "cursor": ""}, ""
    if "series_ticker=KXHIGHNY" in url and "status=open" in url:
        return 200, {"markets": [mk("KXHIGHNY-26NOV05-T70", "greater", 70, None, 0.04, "KXHIGHNY-26NOV05")], "cursor": ""}, ""
    if "series_ticker=KXLOWTNYC" in url and "status=settled" in url:
        m = mk("KXLOWTNYC-26NOV03-T45", "greater", 45, None, 0.5, "KXLOWTNYC-26NOV03")
        m.update(result="no", expiration_value="43")
        return 200, {"markets": [m], "cursor": ""}, ""
    if "series_ticker=KXHIGHNY" in url and "status=settled" in url:
        m = mk("KXHIGHNY-26NOV03-T66", "greater", 66, None, 0.5, "KXHIGHNY-26NOV03")
        m.update(result="yes", expiration_value="68")
        return 200, {"markets": [m], "cursor": ""}, ""
    if url.startswith(rec.IEM):
        return 200, {"data": [{"max_tmpf": 68.0, "min_tmpf": 43.0}]}, ""
    return 404, None, ""


rec.http_get = fake
with tempfile.TemporaryDirectory() as d:
    s = rec.run(WATCH, d, now=NOW + 5, results=True, only=["NYC"])
    assert sum(1 for u in calls if u.startswith(rec.OPENMETEO)) == 1, "lows add no ensemble request"
    assert sum(1 for u in calls if "/markets?" in u and "status=open" in u) == 2, "one extra Kalshi listing for the lows"
    assert len(s) == len(rec.COLS["runs"]) == 18
    e = rows(d, "ens", "2026-11-04", "15")
    el = rows(d, "ens_low", "2026-11-04", "15")
    assert {r["tmax_f"] for r in e} == {"62.0"} and len(e) == 1, e
    assert sorted((r["model"], r["tmin_f"]) for r in el) == [("ecmwf_ifs025_ensemble", "43.0"), ("ncep_gefs_seamless", "41.0")] and {r["look"] for r in el} == {"L1_10"}, el
    assert [r["nws_high_f"] for r in rows(d, "nws", "2026-11-04", "15")] == ["66.0"]
    nl = rows(d, "nws_low", "2026-11-04", "15")
    assert [(r["nws_low_f"], r["role"], r["target_date"]) for r in nl] == [("41.0", "prior", "2026-11-05")], nl
    ql = rows(d, "quotes_low", "2026-11-04", "15")
    assert {r["ticker"] for r in ql} == {"KXLOWTNYC-26NOV05-T50", "KXLOWTNYC-26NOV05-B41.5"} and {r["series"] for r in ql} == {"KXLOWTNYC"}, "only the target day's low brackets"
    qh = rows(d, "quotes", "2026-11-04", "15")
    assert {r["ticker"] for r in qh} == {"KXHIGHNY-26NOV05-T70"}, "the highs file holds no low bracket"
    assert rows(d, "events_low", "2026-11-04", "15")[0]["event_ticker"] == "KXLOWTNYC-26NOV05"
    rl = rows(d, "results_low", "2026-11-04", "15")
    assert rl[0]["expiration_value"] == "43" and rl[0]["ticker"].startswith("KXLOWTNYC")
    assert rows(d, "obs_low", "2026-11-04", "15")[0]["iem_min_tmpf"] == "43.0" and rows(d, "obs", "2026-11-04", "15")[0]["iem_max_tmpf"] == "68.0"
    # a re-run of the same slot overwrites the same files and does not repeat known results/events
    rec.run(WATCH, d, now=NOW + 400, results=True, only=["NYC"])
    assert len(os.listdir(os.path.join(d, "wxens", "quotes_low", "2026-11-04"))) == 1 and len(rows(d, "results_low", "2026-11-04", "15")) == 1

    # 5. the reader on the recorded low tables: the same code, the low columns
    days, official = L.build_low(d, WATCH)
    assert ("NYC", "2026-11-05") in days and official[("NYC", "2026-11-03")] == 43.0
    br = {b["ticker"]: b for b in days[("NYC", "2026-11-05")]["brackets"]}
    assert br["KXLOWTNYC-26NOV05-T50"]["ask"] == 0.04 and br["KXLOWTNYC-26NOV05-T50"]["p"] is not None and br["KXLOWTNYC-26NOV05-B41.5"]["p"] > 0.2
    dh, oh = W.build(d, WATCH)
    assert {b["ticker"] for b in dh[("NYC", "2026-11-05")]["brackets"]} == {"KXHIGHNY-26NOV05-T70"} and oh[("NYC", "2026-11-03")] == 68.0, "the WXENS1 reader still sees only highs"
    buf = io.StringIO()
    with redirect_stdout(buf):
        L.cmd_count(d, WATCH)
    out = buf.getvalue()
    assert "lows:" in out and "highs:" in out and "pooled:" in out and "no outcome read" in out
    # the lows-alone and pooled reads are refused before 300 trades, and the pooled read needs both frozen city sets
    with redirect_stdout(io.StringIO()):
        assert L.cmd_run(d, WATCH) == 1 and L.cmd_pooled(d, WATCH) == 1 and L.cmd_cities(d, WATCH) == 1

# 6. pooled and lows reads on crafted data (small thresholds patched in memory): pooled prints no split, a second run is refused, both reads are one shot
def fake_days(prefix, n_days, n_win_every):
    dd, res = {}, {}
    for i in range(n_days):
        date = "2026-12-%02d" % (1 + i)
        tk = "%s-%02d-T" % (prefix, i)
        dd[("NYC", date)] = {"poll_ts": 0, "shift": 0.0, "brackets": [{"ticker": tk, "ask": 0.10, "bid": 0.09, "volume": 100.0, "p": 0.40}]}
        res[tk] = "yes" if i % n_win_every == 0 else "no"
    return dd, res


dl, rl = fake_days("KXLOWTNYC", 12, 3)
dh, rh = fake_days("KXHIGHNY", 12, 3)
save = (W.MIN_TRADES, W.FULL_TRADES, W.build, W.results_by_ticker, L.build_low)
W.MIN_TRADES, W.FULL_TRADES = 4, 20
W.build = lambda data_dir, watchlist, *a, **k: (dh, {})
L.build_low = lambda data_dir, watchlist: (dl, {})
W.results_by_ticker = lambda data_dir, sfx="": rl if sfx else rh
with tempfile.TemporaryDirectory() as d:
    json.dump({"cities": ["NYC"]}, open(os.path.join(d, "wxens1_cities.json"), "w"))
    with redirect_stdout(io.StringIO()):
        assert L.cmd_pooled(d, WATCH) == 1, "refused: the low cities are not frozen"
    json.dump({"cities": ["NYC"]}, open(os.path.join(d, "wxlow1_cities.json"), "w"))
    with redirect_stdout(io.StringIO()):
        W.FULL_TRADES = 30
        assert L.cmd_pooled(d, WATCH) == 1, "refused: 24 pooled trades is under 30 and before the stop date"
    # 12 + 12 = 24 pooled trades >= 20: the read runs
    buf = io.StringIO()
    with redirect_stdout(buf):
        W.FULL_TRADES = 24
        assert L.cmd_pooled(d, WATCH) == 0
    out = buf.getvalue()
    assert out.startswith("WXLOW1-P") and "highs" in out.splitlines()[0] and '"n": 24' in out, out
    assert "KXHIGH" not in out and "KXLOW" not in out, "no ticker, so no split by kind"
    with redirect_stdout(io.StringIO()):
        assert L.cmd_pooled(d, WATCH) == 1, "a second pooled run is refused"
        W.FULL_TRADES = 12
        assert L.cmd_run(d, WATCH) == 0 and L.cmd_run(d, WATCH) == 1, "the lows-alone read runs once"
    assert open(os.path.join(d, "wxlow1_result.txt")).read().startswith("WXLOW1-L") and '"n": 12' in open(os.path.join(d, "wxlow1_result.txt")).read()
W.MIN_TRADES, W.FULL_TRADES, W.build, W.results_by_ticker, L.build_low = save

# 7. the WXENS1 constants are what WXLOW1 uses (it imports them, it cannot drift)
assert (W.SD_F, W.MIN_RATIO, W.ASK_LO, W.ASK_HI, W.MAX_PER_DAY) == (1.5, 3.0, 0.03, 0.30, 2) and (W.MIN_TRADES, W.FULL_TRADES, W.STOP_DATE) == (150, 300, "2027-02-28")
print("ok")
