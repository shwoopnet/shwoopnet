"""Synthetic test for tie3.py (made-up data; no Kalshi, no real file). Run: python3 -W ignore test_tie3.py"""
import calendar, gzip, hashlib, json, os, random, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import tie3 as t
import kalshi_pull as kp
from datetime import datetime, timezone

random.seed(7)
def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]])); rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

cells = [{"league": "NHL", "period": "P1", "series": "KXNHLP1", "tie_suffix": "TIE", "start_rule": {"kind": "ticker_local", "tz": "America/New_York", "offset_s": 3600}},
         {"league": "NFL", "period": "Q1", "series": "KXNFLQ1", "tie_suffix": "TIE", "start_rule": {"kind": "field", "name": "open_time", "offset_s": -7200}},
         {"league": "XX", "period": "P1", "series": "KXXXP1", "tie_suffix": "TIE", "start_rule": None}]
# refusal without a frozen hash
try: t.load_cells("x.json"); raise SystemExit("unfrozen cells passed")
except SystemExit as e: assert "not frozen" in str(e)
with tempfile.TemporaryDirectory() as d:
    cp = os.path.join(d, "cells.json"); json.dump(cells, open(cp, "w")); t.CELLS_SHA256 = hashlib.sha256(open(cp, "rb").read()).hexdigest(); assert t.load_cells(cp) == cells
    t.CELLS_SHA256 = "0" * 64
    try: t.load_cells(cp); raise SystemExit("wrong hash passed")
    except SystemExit as e: assert "does not match" in str(e)
    t.CELLS_SHA256 = hashlib.sha256(open(cp, "rb").read()).hexdigest()
jl = t.build_lists(cells); kp.check_job(jl); assert len(jl["requests"]) == 6 and all(r["params"].get("max_close_ts", t.HELD_OUT_FROM - 1) < t.HELD_OUT_FROM for r in jl["requests"])

def event(series, tag, close, tie_yes, three=True, first="A", extra=None):
    ev = "%s-%s" % (series, tag); ms = []
    names = ["A", "B", "TIE"] if three else ["A", "TIE"]
    # exactly one of the three settles yes
    for nm in names:
        yes = (nm == "TIE") if tie_yes else (nm == first)
        ms.append({"ticker": "%s-%s" % (ev, nm), "event_ticker": ev, "close_time": F(close), "open_time": F(close - 20000), "result": "yes" if yes else "no", "volume_fp": "900", "title": "x"})
    return ms
ms_nhl, ms_nfl = [], []
base_close = calendar.timegm((2026, 10, 1, 4, 0, 0)); price_close = calendar.timegm((2026, 10, 25, 4, 0, 0))
nb = 200
for i in range(nb):       # NHL base: 40 percent level
    ms_nhl += event("KXNHLP1", "26OCT01%04d" % (1900 + i % 10) + "X%d" % i, base_close + 3600 * i, tie_yes=(i % 5 < 2))
# a malformed event (only two markets) and a held-out event (closes on 2026-11-13)
ms_nhl += event("KXNHLP1", "26OCT011900BAD", base_close, True, three=False)
ms_nhl += event("KXNHLP1", "26NOV131900HELD", t.HELD_OUT_FROM + 3600, True)
npr = 60
inst = {}
for i in range(npr):
    tag = "26OCT25%04d" % 1900 + "P%d" % i                      # ticker has 19:00 local
    tag = "26OCT251900P%d" % i
    e = event("KXNHLP1", tag, price_close + 60 * i, tie_yes=(i % 2 == 0))
    ms_nhl += e
for i in range(npr):
    ms_nfl += event("KXNFLQ1", "26OCT26P%d" % i, price_close + 86400 + 60 * i, tie_yes=(i % 5 == 0))
lists = {"live_KXNHLP1": {"markets": ms_nhl}, "hist_KXNHLP1": {"markets": []}, "live_KXNFLQ1": {"markets": ms_nfl}, "hist_KXNFLQ1": {"markets": []}, "live_KXXXP1": {"markets": []}, "hist_KXXXP1": {"markets": []}}
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    evs, counts = t.events(cells, [dl])
    assert len(evs["NHL|P1"]["base"]) == nb and counts["held_out_dropped"] == 1 and counts["dropped_not_three_settled"] == 1, counts
    assert all("result" not in e and "level" not in e for e in evs["NHL|P1"]["price"] + evs["NFL|Q1"]["price"])     # the price block carries no outcome
    assert evs["NHL|P1"]["base"][0]["level"] in (True, False)
    assert len(evs["NFL|Q1"]["price"]) == npr and evs["NFL|Q1"]["price"][0]["instant"] == price_close + 86400 - 20000 + 7200       # field rule: open_time minus (-7200 s)
    assert counts["no_start"] == 0, counts
    # start rules: ticker local 19:00 ET on Oct 25 (EDT, UTC-4) minus 3600 s = 22:00Z
    exp = calendar.timegm((2026, 10, 25, 23, 0, 0)) - 3600
    assert evs["NHL|P1"]["price"][0]["instant"] == exp, (evs["NHL|P1"]["price"][0]["instant"], exp)
    assert t.start_ts("E", [{"close": 10000}, {"close": 10600}], {"kind": "close_offset", "offset_s": 3600}) == 6400 and t.start_ts("E", [], {"kind": "close_offset", "offset_s": 1}) is None
    assert t.start_ts("KXNHLP1-26OCT25", [], cells[0]["start_rule"]) is None and t.start_ts("x", [], None) is None             # date-only ticker or no rule: skipped
    jc, _ = t.build_candles(cells, [dl]); kp.check_job(jc)
    assert all(r["params"]["end_ts"] <= t.HELD_OUT_FROM + 86400 * 5 for r in jc["requests"]) and 1 <= len(jc["requests"]) <= 10 and not any(r["path"].startswith("/historical") for r in jc["requests"])
    assert sorted(jc["ticker_allowlist"]) == sorted({e["tie_ticker"] for v in evs.values() for e in v["price"]})
    # candles: NHL Tie asks at 0.28 (base rate about 0.40: gap +12c, spread 3c), NFL Tie asks at 0.30 (base about 0.2: gap negative)
    def cs(items, ask, half):
        out = {}
        for e in items:
            out[e["tie_ticker"]] = [{"end_period_ts": e["instant"] - 60, "yes_bid": {"close_dollars": str(ask - 2 * half)}, "yes_ask": {"close_dollars": str(ask)}, "volume_fp": "1"}]
        return out
    body = {}
    cmap = cs(evs["NHL|P1"]["price"], 0.28, 0.015); cmap.update(cs(evs["NFL|Q1"]["price"], 0.30, 0.01))
    for r in jc["requests"]:
        tk = r["params"]["market_tickers"].split(",")
        body[r["id"]] = {"markets": [{"market_ticker": x, "candlesticks": cmap[x]} for x in tk if x in cmap]}
    mkrun(dc, jc, body)
    out = t.measure(cells, [dl], [dc])
    n = out["cells"]["NHL|P1"]
    assert out["tries_added"] == 0 and out["rule_scored"] is False and n["n_base_events"] == nb and abs(n["base_rate"] - 0.40) < 0.001 and n["n_priced_games"] == npr and n["share_two_sided"] == 1.0
    assert abs(n["gap_q1_median_q3"][1] - 0.12) < 1e-9 and abs(n["median_spread"] - 0.03) < 1e-9 and n["cell_status"] == "measured"
    assert out["cells"]["NFL|Q1"]["cell_status"] == "no evidence" and out["cells"]["XX|P1"]["n_priced_games"] == 0       # NFL has no base block here; XX has nothing
    assert out["verdict"].startswith("SURVIVES the measurement in 1"), out["verdict"]
    # a thin/one-sided minute is counted, not filled: make NHL bids zero -> not two-sided -> closed
    cmap2 = cs(evs["NHL|P1"]["price"], 0.28, 0.14); body2 = {r["id"]: {"markets": [{"market_ticker": x, "candlesticks": cmap2[x]} for x in r["params"]["market_tickers"].split(",") if x in cmap2]} for r in jc["requests"]}
    dc2 = os.path.join(dc, "x"); os.mkdir(dc2); mkrun(dc2, jc, body2); out2 = t.measure(cells, [dl], [dc2]); assert out2["cells"]["NHL|P1"]["share_two_sided"] == 0.0 and out2["verdict"].startswith("CLOSED")
    # a stale candle (older than 2 minutes before the instant) is not used
    cmap3 = {k_: [dict(c, end_period_ts=c["end_period_ts"] - 600) for c in v] for k_, v in cmap.items()}
    body3 = {r["id"]: {"markets": [{"market_ticker": x, "candlesticks": cmap3[x]} for x in r["params"]["market_tickers"].split(",") if x in cmap3]} for r in jc["requests"]}
    dc3 = os.path.join(dc, "y"); os.mkdir(dc3); mkrun(dc3, jc, body3); o3 = t.measure(cells, [dl], [dc3])["cells"]["NHL|P1"]; assert o3["no_candle_in_window"] == npr and o3["n_two_sided"] == 0
print("tie3 synthetic tests passed")
