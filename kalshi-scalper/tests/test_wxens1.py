"""WXENS1 recorder and reader on synthetic data (no network, no outcome from real markets). Research only."""
import csv
import gzip
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

import record_wxens as rec  # noqa: E402
from scalper import wxens1 as T  # noqa: E402

rec._sleep = lambda x: None
WATCH = os.path.join(HERE, "..", "workers", "WXENS1_WATCHLIST.json")


def ts(s):
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())


# 1. kernel probabilities: the three kinds sum to one for one member, and a tight cold ensemble gives a far hot tail a small mass
tot = T.member_prob("greater", 74, None, 71) + T.member_prob("less", None, 67, 71) + sum(T.member_prob("between", lo, lo + 1, 71) for lo in (67, 69, 71, 73))
assert abs(tot - 1) < 1e-9, tot
by = {"a": [70.0, 71.0, 72.0], "b": [70.5, 71.5], "c": []}
p = T.bracket_prob("greater", 80, None, by)
assert p is not None and p < 1e-6
assert T.bracket_prob("greater", 80, None, {"a": [70.0], "b": []}) is None, "fewer than two models: no probability"
# equal weight per MODEL: a model with 1 member counts as much as a model with 3
p1 = T.bracket_prob("between", 70, 71, {"a": [70.5], "b": [60.0, 60.0, 60.0]})
assert abs(p1 - 0.5 * T.member_prob("between", 70, 71, 70.5)) < 1e-9
# the bias shift moves every member
assert T.bracket_prob("greater", 70, None, by, 5.0) > T.bracket_prob("greater", 70, None, by, 0.0)

# 2. fee: 7% x C x p x (1-p) rounded UP at C = 10; the net of a win and a loss
assert T.fee_order(0.10) == 0.07 and abs(T.net(0.10, True) - (1 - 0.10 - 0.007)) < 1e-12 and abs(T.net(0.10, False) - (-0.10 - 0.007)) < 1e-12
assert T.fee_order(0.10, mult=1.2) == 0.08

# 3. trade choice: ask in 3c..30c and p at least 3x ask; at most 2 per city-day, best ratio first; 31c and 2c are cheap-excluded
br = [{"ticker": "A", "ask": 0.05, "p": 0.20}, {"ticker": "B", "ask": 0.10, "p": 0.31}, {"ticker": "C", "ask": 0.10, "p": 0.29}, {"ticker": "D", "ask": 0.02, "p": 0.50},
      {"ticker": "E", "ask": 0.31, "p": 0.99}, {"ticker": "F", "ask": 0.08, "p": 0.30}, {"ticker": "G", "ask": 0.30, "p": 0.90}, {"ticker": "H", "ask": 0.05, "p": None}]
sel = [b["ticker"] for b in T.choose_trades(br)]
assert sel == ["A", "F"], sel          # ratios A 4.0, F 3.75, B 3.1, G 3.0
assert [b["ticker"] for b in T.control_trades(br)] == ["A", "B", "C", "F", "G", "H"]
assert T.choose_trades([{"ticker": "X", "ask": 0.10, "p": 0.30}])[0]["ticker"] == "X", "exactly 3x qualifies"

# 4. bias: needs 5 settled days recorded before the look, plain mean of the latest 14, a result seen after the look is not used
look = 1_000_000
errors = {("NYC", "2026-11-%02d" % d): (float(d % 3), look - 10) for d in range(1, 11)}
b = T.bias_for("NYC", "2026-11-12", look, errors)
assert abs(b - sum(errors[("NYC", "2026-11-%02d" % d)][0] for d in range(1, 11)) / 10) < 1e-12
assert T.bias_for("NYC", "2026-11-04", look, errors) == 0.0, "3 days only: no correction"
late = dict(errors)
late[("NYC", "2026-11-10")] = (50.0, look + 1)
assert T.bias_for("NYC", "2026-11-12", look, late) != 50.0 and abs(T.bias_for("NYC", "2026-11-12", look, late) - sum(late[("NYC", "2026-11-%02d" % d)][0] for d in range(1, 10)) / 9) < 1e-12

# 5. halves keep whole days together; verdict: not enough data, falsified, candidate
tr = [{"date": "2026-12-%02d" % (1 + i // 3), "net": 0.5, "net_stress": 0.4, "price": 0.1} for i in range(300)]
h1, h2 = T.split_halves(tr)
assert len(h1) + len(h2) == 300 and h1[-1]["date"] < h2[0]["date"]
assert T.verdict(tr[:149], True)[0] == "NOT_ENOUGH_DATA" and T.verdict(tr[:200], False)[0] == "NOT_ENOUGH_DATA"
assert T.verdict(tr[:200], True)[0] != "NOT_ENOUGH_DATA"
loss = [dict(t, net=-0.1, net_stress=-0.1) for t in tr]
assert T.verdict(loss, False)[0] == "FALSIFIED"
mixed = [dict(t, net=(0.9 if i % 10 == 0 else -0.05)) for i, t in enumerate(tr)]      # PF 0.9/0.45 = 2.0 but make the second half negative
for t in mixed[len(mixed) // 2:]:
    t["net"] = -0.05
assert T.verdict(mixed, False)[0] == "FALSIFIED", "one half not above zero"
assert T.verdict(tr, False)[0] == "NOT_YET_FALSIFIED" or T.verdict(tr, False)[1]["pf"] == float("inf")

# 6. recorder helpers: looks by local STANDARD hour, event date, ensemble parse
city = {"key": "NYC", "std_offset_h": -5}
assert rec.due_targets(city, ts("2026-11-04 12:12"), {7, 10}) == [("L0_07", "2026-11-04"), ("L1_07", "2026-11-05")]
assert rec.due_targets(city, ts("2026-11-04 15:12"), {7, 10}) == [("L1_10", "2026-11-05")]
assert rec.due_targets(city, ts("2026-11-04 16:12"), {7, 10}) == [] and rec.due_targets(city, ts("2026-11-04 16:12"), {7, 8, 10, 11}) == [("L1_10", "2026-11-05")]
assert rec.due_targets({"key": "LAX", "std_offset_h": -8}, ts("2026-11-04 18:12"), {7, 10}) == [("L1_10", "2026-11-05")]
assert rec.event_date("KXHIGHNY-26NOV04") == "2026-11-04" and rec.event_date("KXHIGHNY") is None
body = {"daily": {"time": ["2026-11-04", "2026-11-05"], "temperature_2m_max": [60.1, 61.0], "temperature_2m_max_member01_ncep_gefs_seamless": [59.0, None],
                  "temperature_2m_max_member02_ncep_gefs_seamless": [62.0, 63.0], "temperature_2m_max_member01_ecmwf_ifs025": [61.5, 64.0], "other": [1, 2]}}
pe = rec.parse_ensemble(body, {"2026-11-05"})
assert sorted(pe) == [("ecmwf_ifs025", "temperature_2m_max_member01_ecmwf_ifs025", "2026-11-05", 64.0),
                      ("ncep_gefs_seamless", "temperature_2m_max_member02_ncep_gefs_seamless", "2026-11-05", 63.0),
                      ], pe
assert rec.parse_ensemble({"daily": {"time": ["2026-11-05"], "temperature_2m_max": [61.0]}}, {"2026-11-05"}) == [("single", "temperature_2m_max", "2026-11-05", 61.0)]
nws = {"properties": {"periods": [{"isDaytime": False, "startTime": "2026-11-05T18:00:00-05:00", "temperature": 40, "name": "Thursday Night"},
                                  {"isDaytime": True, "startTime": "2026-11-05T06:00:00-05:00", "temperature": 66, "name": "Thursday"}]}}
assert rec.parse_nws(nws, "2026-11-05") == (66.0, "2026-11-05T06:00:00-05:00", "Thursday") and rec.parse_nws(nws, "2026-11-06") is None


# 7. a full fake run: ONE ensemble call, one NWS pair and one market listing per due city; files are slot named; a re-run overwrites; results are written once
NOW = ts("2026-11-04 15:12")          # 10:12 in New York standard time: NYC L1_10; Chicago 09:12 and the others not due
calls = []


def mk(ticker, kind, fl, cp, ask, vol="900.00", ev="KXHIGHNY-26NOV05"):
    return {"ticker": ticker, "event_ticker": ev, "close_time": "2026-11-06T06:00:00Z", "strike_type": kind, "floor_strike": fl, "cap_strike": cp,
            "yes_bid_dollars": "%.4f" % (ask - 0.01), "yes_ask_dollars": "%.4f" % ask, "last_price_dollars": "0.0500", "volume_fp": vol, "status": "active", "rules_primary": "CLINYC rule text"}


def fake(url):
    calls.append(url)
    if url.startswith(rec.OPENMETEO):
        assert url.count("latitude=") == 1 and "models=gfs_seamless,ecmwf_ifs025,icon_seamless" in url
        b = {"daily": {"time": ["2026-11-04", "2026-11-05", "2026-11-06"], "temperature_2m_max_member01_ncep_gefs_seamless": [60, 62, 63], "temperature_2m_max_member01_ecmwf_ifs025": [61, 63, 64]}}
        return 200, b, "Wed, 04 Nov 2026 15:12:30 GMT"
    if "/points/" in url:
        return 200, {"properties": {"forecast": "https://api.weather.gov/gridpoints/OKX/34,45/forecast", "gridId": "OKX", "gridX": 34, "gridY": 45}}, ""
    if "/gridpoints/" in url:
        return 200, nws, ""
    if "status=open" in url:
        return 200, {"markets": [mk("KXHIGHNY-26NOV05-T70", "greater", 70, None, 0.04), mk("KXHIGHNY-26NOV05-B64.5", "between", 64, 65, 0.20),
                                 mk("KXHIGHNY-26NOV04-T66", "greater", 66, None, 0.50, ev="KXHIGHNY-26NOV04")], "cursor": ""}, "Wed, 04 Nov 2026 15:12:31 GMT"
    if "status=settled" in url:
        m = mk("KXHIGHNY-26NOV03-T66", "greater", 66, None, 0.5, ev="KXHIGHNY-26NOV03")
        m.update(result="yes", expiration_value="68")
        return 200, {"markets": [m], "cursor": ""}, ""
    if url.startswith(rec.IEM):
        return 200, {"data": [{"max_tmpf": 68.0}]}, ""
    return 404, None, ""


rec.http_get = fake
with tempfile.TemporaryDirectory() as d:
    with tempfile.TemporaryDirectory() as d2:
        assert rec.run(WATCH, d2, now=NOW + 5, results=False)[4] == 8, "four UTC-5 cities at 10:12 and four UTC-8 cities at 07:12 are due; Chicago (09:12) is not"
        assert sum(1 for u in calls if u.startswith(rec.OPENMETEO)) == 1, "one batched ensemble call for all due cities"
    calls.clear()
    s = rec.run(WATCH, d, now=NOW + 5, results=True, only=["NYC"])
    assert s[4] == 1, "only New York selected"
    assert sum(1 for u in calls if u.startswith(rec.OPENMETEO)) == 1
    day = os.path.join(d, "wxens")
    ens = list(csv.DictReader(gzip.open(os.path.join(day, "ens", "2026-11-04", "15.csv.gz"), "rt")))
    assert {r["target_date"] for r in ens} == {"2026-11-05"} and {r["look"] for r in ens} == {"L1_10"} and len(ens) == 2, ens
    q = list(csv.DictReader(gzip.open(os.path.join(day, "quotes", "2026-11-04", "15.csv.gz"), "rt")))
    assert {r["target_date"] for r in q} == {"2026-11-05"} and len(q) == 2, "only the target day's brackets, not today's"
    assert list(csv.DictReader(gzip.open(os.path.join(day, "nws", "2026-11-04", "15.csv.gz"), "rt")))[0]["nws_high_f"] == "66.0"
    assert list(csv.DictReader(gzip.open(os.path.join(day, "events", "2026-11-04", "15.csv.gz"), "rt")))[0]["rules_primary"] == "CLINYC rule text"
    res = list(csv.DictReader(gzip.open(os.path.join(day, "results", "2026-11-04", "15.csv.gz"), "rt")))
    assert res[0]["expiration_value"] == "68" and res[0]["target_date"] == "2026-11-03"
    assert list(csv.DictReader(gzip.open(os.path.join(day, "obs", "2026-11-04", "15.csv.gz"), "rt")))[0]["iem_max_tmpf"] == "68.0"
    # same slot again: files replaced, results/events/obs not repeated (and, being new, the files are not written at all for them)
    n_before = len(glob_ := os.listdir(os.path.join(day, "quotes", "2026-11-04")))
    rec.run(WATCH, d, now=NOW + 400, results=True, only=["NYC"])
    assert len(os.listdir(os.path.join(day, "quotes", "2026-11-04"))) == n_before == 1
    assert len(list(csv.DictReader(gzip.open(os.path.join(day, "results", "2026-11-04", "15.csv.gz"), "rt")))) == 1, "known results are not rewritten"

    # 8. the reader: first primary poll at or after 10:00 local standard time, probabilities, trade list, counts without an outcome
    days, official = T.build(d, WATCH)
    assert ("NYC", "2026-11-05") in days, days.keys()
    br = {b["ticker"]: b for b in days[("NYC", "2026-11-05")]["brackets"]}
    assert br["KXHIGHNY-26NOV05-T70"]["ask"] == 0.04 and br["KXHIGHNY-26NOV05-T70"]["p"] is not None
    # the 10:00 look of 2026-11-05 is 2026-11-04 15:00Z; a poll before it would not count
    assert T.look_ts("2026-11-05", -5) == ts("2026-11-04 15:00")
    sel, ctl = T.trade_list(days, ["NYC"])
    assert all("net" not in t for t in sel), "counts need no outcome"

# 9. a network failure is counted, never a crash and never a made up row
rec.http_get = lambda url: (0, None, "")
with tempfile.TemporaryDirectory() as d:
    s = rec.run(WATCH, d, now=NOW, results=False)
    assert s[7] >= 2 and s[8] == 0 and s[10] == 0, s
    rec.http_get = lambda url: (429, None, "")
    s = rec.run(WATCH, d, now=NOW, results=False)
    assert s[6] >= 1

# 10. city choice: the 8 highest median volumes among the first 7 dates, ties alphabetical
dd = {}
for i, c in enumerate("ABCDEFGHIJ"):
    for k in range(8):
        dd[(c, "2026-11-%02d" % (1 + k))] = {"brackets": [{"volume": float(100 - i * 5 if k < 7 else 99999)}]}
assert T.choose_cities(dd) == list("ABCDEFGH")
print("ok")
