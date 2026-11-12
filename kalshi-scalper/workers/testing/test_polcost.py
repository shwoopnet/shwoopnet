"""Synthetic test for polcost.py (made-up open markets; no Kalshi). Run: python3 -W ignore test_polcost.py"""
import gzip, json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import polcost as pc, kalshi_pull as kp

def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]])); rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))
def mk(t, b, a, bs="100", as_="80"): return {"ticker": t, "yes_bid_dollars": b, "yes_ask_dollars": a, "yes_bid_size_fp": bs, "yes_ask_size_fp": as_, "status": "active"}
with tempfile.TemporaryDirectory() as dc, tempfile.TemporaryDirectory() as d:
    json.dump({"rows": [{"id": "x", "status": 200, "file": "1.json.gz"}]}, open(os.path.join(dc, "manifest.json"), "w"))
    gzip.open(os.path.join(dc, "1.json.gz"), "wt").write(json.dumps({"series": [{"ticker": "KXAAA", "category": "Politics", "frequency": "weekly"}, {"ticker": "KXBBB", "category": "Politics", "frequency": "daily"}, {"ticker": "KXONE", "category": "Politics", "frequency": "one_off"}]}))
    j = pc.build_job(dc); kp.check_job(j)
    assert [r["id"] for r in j["requests"]] == ["open_KXAAA", "open_KXBBB"] and all(r["params"]["status"] == "open" and r["max_pages"] == 3 for r in j["requests"]) and j["max_requests"] == 6 + 14
    # cost: KXAAA liquid (1c spread at mid .50: round trip 0.01 + 0.035 = 4.5c), KXBBB wide (6c spread: 9.5c); one-sided, out-of-band and duplicate markets are ignored
    bodies = {"open_KXAAA": {"markets": [mk("KXAAA-1", "0.4950", "0.5050"), mk("KXAAA-2", "0.4950", "0.5050"), mk("KXAAA-3", "0.0000", "0.5000"), mk("KXAAA-4", "0.9000", "0.9300"), mk("KXAAA-1", "0.4950", "0.5050")]},
              "open_KXBBB": {"markets": [mk("KXBBB-1", "0.4700", "0.5300", "40", "10"), mk("KXBBB-2", "0.4700", "0.5300", "40", "10")]}}
    mkrun(d, j, bodies); t = pc.table(d)
    assert t["open_markets_listed"] == 7 - 1 and t["overall"]["markets_quoted_20c_to_80c"] == 4 and t["overall"]["series"] == 2
    assert abs(t["per_series"]["KXAAA"]["median_round_trip"] - 0.045) < 1e-4 and abs(t["per_series"]["KXBBB"]["median_round_trip"] - 0.095) < 1e-4 and t["per_series"]["KXBBB"]["median_size_at_touch"] == 10.0
    assert abs(t["overall"]["median_round_trip"] - 0.07) < 1e-4 and t["verdict"].startswith("POL-i2 CLOSED on cost"), t["verdict"]
    assert t["tries_added"] == 0 and t["rule_scored"] is False and "00:00Z" in t["limit"]
    ok = {"open_KXAAA": {"markets": [mk("KXAAA-1", "0.4950", "0.5050"), mk("KXAAA-2", "0.4950", "0.5050")]}, "open_KXBBB": {"markets": []}}
    d2 = os.path.join(d, "ok"); os.mkdir(d2); mkrun(d2, j, ok); t2 = pc.table(d2); assert t2["verdict"].startswith("at or under the 5c line") and "WITHIN 1c" in t2["verdict"], t2["verdict"]     # 4.5c is within 1c of the line
print("polcost synthetic tests passed")
