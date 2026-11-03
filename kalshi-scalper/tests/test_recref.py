"""RECREF recorder and its source adapters on saved fixtures (no network, no outcome). Research only."""
import csv
import gzip
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

import record_ref as rr  # noqa: E402
import ref_adapters as ad  # noqa: E402

rr._sleep = lambda x: None
REAL_GET = rr.http_get
FX = os.path.join(HERE, "fixtures")
WATCH = os.path.join(HERE, "..", "workers", "RECREF_WATCHLIST.json")
NOW = 1_800_000_000 - 1_800_000_000 % 7200 + 300      # 5 minutes into a 2 hour slot


def fx(name):
    return open(os.path.join(FX, name), encoding="utf-8").read()


def iso(e):
    return __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(e))


# ---- adapters on fixtures ----
def t_kworb():
    rows = ad.kworb_parse({"top": 3}, [fx("ref_kworb_us_daily.html")])
    assert len(rows) == 3 and rows[0][0] == 1 and rows[0][1] == "Ray Parker Jr. - Ghostbusters" and rows[0][2] == 1260711 and rows[0][3] == 41757322, rows
    assert ad.kworb_parse({}, ["<html>changed</html>"]) == []


def t_apple():
    rows = ad.apple_parse({"top": 3}, [fx("ref_apple_top_free.json")])
    assert [r[0] for r in rows] == [1, 2, 3] and rows[0][1] and rows[0][4].isdigit(), rows
    legacy = json.dumps({"feed": {"entry": [{"im:name": {"label": "App A"}, "id": {"attributes": {"im:id": "11"}}}]}})
    assert ad.apple_parse({}, [legacy]) == [[1, "App A", None, None, "11"]]
    assert ad.apple_parse({}, ["not json"]) == []


def t_rt():
    rows = ad.rt_parse({}, [fx("ref_rt.html")])
    assert rows[0][1] == "tomatometer" and rows[0][2] == 66 and rows[0][3] == 356, rows
    assert rows[1][1] == "popcornmeter" and rows[1][2] == 92, rows
    assert ad.rt_parse({}, ["<html>no score yet</html>"]) == []


def t_mc():
    rows = ad.mc_parse({}, [fx("ref_mc.html")])
    assert rows == [[1, "metascore", 94, 141, "critic_reviews"]], rows
    assert ad.mc_parse({}, ["<html></html>"]) == []


def t_xtracker():
    u = ad.xtracker_url("realDonaldTrump", "2026-11-03T05:00:00Z", "2026-11-04T04:59:00Z")
    assert u == "https://xtracker.polymarket.com/api/users/realDonaldTrump/posts?startDate=2026-11-03T05%3A00%3A00Z&endDate=2026-11-04T04%3A59%3A00Z", u
    rows = ad.xtracker_parse({}, [fx("ref_xtracker_posts.json")])
    assert len(rows) == 1 and rows[0][2] == 4 and "last_post=2026-" in rows[0][4] and "truncated" not in rows[0][4], rows
    assert ad.xtracker_parse({}, ["junk"]) == [] and ad.xtracker_parse({}, ['{"data": 5}']) == []


def t_billboard():
    rows = ad.billboard_parse({"top": 3}, [fx("ref_billboard_hot100.html")])
    assert [r[0] for r in rows] == [1, 2, 3] and rows[0][1].endswith("Ella Langley") and rows[0][4] == "chart_date=2026-11-07", rows
    assert ad.billboard_parse({}, ["<html>layout changed</html>"]) == []


def t_steam():
    rows = ad.steam_parse({"top": 3}, [fx("ref_steam_top.json")])
    assert [r[0] for r in rows] == [1, 2, 3] and rows[1][1] == "Loftia", rows
    assert ad.steam_parse({}, ["<html>"]) == []


def t_slug():
    assert ad.slugify("Wild Horse Nine", "_") == "wild_horse_nine"
    assert ad.slugify("Phantom Blade Zero", "-") == "phantom-blade-zero"
    assert ad.slugify("Bob's Burgers: The Movie!", "_") == "bobs_burgers_the_movie"


def t_targets_for():
    ms = [{"event_ticker": "E-WILD", "title": "Wild Horse Nine Rotten Tomatoes score?", "close_time": "2026-11-09T15:00:00Z"},
          {"event_ticker": "E-WILD", "title": "Wild Horse Nine Rotten Tomatoes score?", "close_time": "2026-11-09T15:00:00Z"},
          {"event_ticker": "E-X", "title": "something else", "close_time": "2026-11-09T15:00:00Z"}]
    rt = {"id": "rt", "adapter": "rt", "per_event": {"title_regex": "^(.*?) Rotten Tomatoes score", "sep": "_", "url": "https://www.rottentomatoes.com/m/{slug}"}}
    assert rr.targets_for(rt, ms) == {"E-WILD": ("wild_horse_nine", "https://www.rottentomatoes.com/m/wild_horse_nine")}
    xt = {"id": "xt", "adapter": "xtracker", "params": {"handle": "h"}, "per_close": {"hours": 24}}
    (key, url), = rr.targets_for(xt, ms[:1]).values()
    assert key == "close2026-11-09T15" and "startDate=2026-11-08T15%3A00%3A00Z&endDate=2026-11-09T15%3A00%3A00Z" in url, (key, url)
    fixed = {"id": "k", "adapter": "kworb", "params": {"url": "https://kworb.net/x.html"}}
    assert rr.targets_for(fixed, ms) == {"": ("", "https://kworb.net/x.html")}


# ---- the recorder on faked reads ----
def mk(ticker, close, **kw):
    m = {"ticker": ticker, "event_ticker": ticker.rsplit("-", 1)[0], "title": "T " + ticker, "close_time": close, "open_time": iso(NOW - 3600), "status": "active",
         "strike_type": "greater", "floor_strike": 90, "yes_bid_dollars": "0.40", "yes_ask_dollars": "0.45", "last_price_dollars": "0.42", "volume_fp": "9.00",
         "open_interest_fp": "3.00"}
    m.update(kw)
    return m


FAKE_WL = {"default_window_hours": 168,
           "refs": [{"id": "mc_page", "adapter": "mc", "per_event": {"title_regex": "^(.*?) Metacritic score", "sep": "-", "url": "https://www.metacritic.com/game/{slug}/"}},
                    {"id": "kw_us", "adapter": "kworb", "params": {"url": "https://kworb.net/spotify/country/us_daily.html", "top": 3}}],
           "series": [{"series": "SER_A", "family": "fam", "refs": ["mc_page"]}, {"series": "SER_B", "family": "fam2", "refs": ["kw_us"], "window_hours": 24}]}


def fake_http(calls):
    def get(url):
        calls.append(url)
        if "series_ticker=SER_A&status=open" in url:
            return 200, json.dumps({"markets": [mk("SER_A-1-T1", iso(NOW + 2 * 86400), title="Astro Bot Metacritic score?"), mk("SER_A-1-T2", iso(NOW + 20 * 86400))], "cursor": ""}), "Tue, 03 Nov 2026 12:00:00 GMT"
        if "series_ticker=SER_B&status=open" in url:
            return 200, json.dumps({"markets": [mk("SER_B-1-T1", iso(NOW + 2 * 3600)), mk("SER_B-1-T2", iso(NOW + 3 * 86400))], "cursor": ""}), ""
        if "status=settled" in url and "SER_A" in url:
            return 200, json.dumps({"markets": [mk("SER_A-0-T1", iso(NOW - 3600), result="yes", expiration_value="94"), mk("SER_A-0-T2", iso(NOW - 3600), result="")], "cursor": ""}), ""
        if "status=settled" in url:
            return 200, json.dumps({"markets": [], "cursor": ""}), ""
        if "metacritic.com" in url:
            return 200, fx("ref_mc.html"), ""
        if "kworb.net" in url:
            return 429, None, ""
        return 404, None, ""
    return get


def read(path):
    with gzip.open(path, "rt", newline="") as f:
        return list(csv.DictReader(f))


def t_run_rows_and_idempotence():
    wl = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(FAKE_WL, wl)
    wl.close()
    calls = []
    rr.http_get = fake_http(calls)
    rr._clock = lambda: NOW
    with tempfile.TemporaryDirectory() as d:
        s1 = rr.run(wl.name, d, now=NOW)
        qf = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(d, "ref", "quotes")) for f in fs]
        assert len(qf) == 1 and qf[0].endswith("0000.csv.gz") or qf[0].endswith(".csv.gz")
        q = read(qf[0])
        assert {r["ticker"] for r in q} == {"SER_A-1-T1", "SER_B-1-T1"}, "the 20 day and the 3 day (window 24h) markets are left out"
        assert all(len(r) == len(rr.QUOTE_COLS) for r in q)
        assert {r["ticker"]: r["refs"] for r in q} == {"SER_A-1-T1": "mc_page:astro-bot", "SER_B-1-T1": "kw_us"}
        vf = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(d, "ref", "refvals")) for f in fs]
        v = read(vf[0])
        assert [(r["ref_id"], r["name"], r["value"]) for r in v] == [("mc_page:astro-bot", "metascore", "94.0")], "a refused kworb read adds no row"
        res = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(d, "ref", "results")) for f in fs]
        assert [r["ticker"] for r in read(res[0])] == ["SER_A-0-T1"]
        # summary: 2 series, 2 refs, kalshi calls 4, ref calls 1 + 2 (kworb tried three times), 429s 2, 1 parse failure
        assert s1[2] == 2 and s1[3] == 2 and s1[4] == 4 and s1[5] == 4 and s1[6] == 3 and s1[8] == 1 and s1[9] == 2 and s1[10] == 1 and s1[11] == 1, s1
        rr.run(wl.name, d, now=NOW + 60)           # same slot again
        qf2 = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(d, "ref", "quotes")) for f in fs]
        assert qf2 == qf, "a re-run of the slot replaces the file"
        res2 = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(d, "ref", "results")) for f in fs]
        assert res2 == res and len(read(res2[0])) == 1, "a settled result is written once"
        runs = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(d, "ref", "runs")) for f in fs]
        assert len(open(runs[0]).read().strip().split("\n")) == 3
    assert all(c.startswith(("https://external-api.kalshi.com/", "https://www.metacritic.com/", "https://kworb.net/")) for c in calls)


def t_slot_and_rate_limit():
    assert rr.slot_of(NOW) == rr.slot_of(NOW - 299) and rr.slot_of(NOW + 7200) - rr.slot_of(NOW) == 7200
    # one request a second per host: two reads of the same host wait, a different host does not
    waited = []
    rr._sleep = lambda x: waited.append(round(x, 2))
    t = [1000.0]
    rr._clock = lambda: t[0]
    rr._last_hit.clear()
    rr.http_get = REAL_GET
    import urllib.request
    real = urllib.request.urlopen

    class R:
        status = 200
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n): return b"{}"
    urllib.request.urlopen = lambda *a, **k: R()
    try:
        rr.http_get("https://a.example/x")
        rr.http_get("https://a.example/y")
        rr.http_get("https://b.example/z")
    finally:
        urllib.request.urlopen = real
        rr._sleep = lambda x: None
    assert waited == [1.0], waited


def t_unknown_adapter_is_a_failure_not_a_value():
    rows, c, n, failed = rr.poll_target({"id": "z", "adapter": "nope"}, "", "https://x.example/", 1, 1)
    assert rows == [] and failed


def t_watchlist():
    w = json.load(open(WATCH))
    ids = {r["id"] for r in w["refs"]}
    assert 8 <= len(w["series"]) <= 12, len(w["series"])
    used = set()
    for e in w["series"]:
        assert set(e["refs"]) <= ids and e.get("rule_source") and e["series"].startswith("KX"), e
        used |= set(e["refs"])
    assert used == ids, "every reference is used and every series names real references"
    for r in w["refs"]:
        assert r["adapter"] in ad.ADAPTERS, r
        if r.get("per_event"):
            assert "{slug}" in r["per_event"]["url"] and r["per_event"]["url"].startswith("https://"), r
        elif r.get("per_close"):
            assert r["adapter"] == "xtracker" and r["params"]["handle"], r
        else:
            assert r["params"]["url"].startswith("https://"), r
    hosts = {r["params"]["url"].split("/")[2] for r in w["refs"] if r.get("params", {}).get("url")}
    assert hosts <= {"kworb.net", "www.billboard.com", "store.steampowered.com"}, hosts


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("t_"):
            f()
            print("ok  ", n)
