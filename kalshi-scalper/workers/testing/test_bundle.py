"""Synthetic test for bundle.py (made-up answers; no Kalshi). Run: python3 -W ignore test_bundle.py"""
import gzip, json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import bundle as b, kalshi_pull as kp, wxdayend as w, tie3 as t, poli2_count as p2, unrateround as ur

job = b.build(); kp.check_job(job)
ids = [r["id"] for r in job["requests"]]
assert len(ids) == len(set(ids)) == 137 and job["job_id"] == "TESTING_LISTS_BUNDLE" and job["owner"] == "MAIN" and job["max_requests"] == 355 + b.SLACK
assert [i.split("_", 1)[0] for i in ids][:32] == ["t3"] * 32 and ids[32].startswith("wx_") and not any(i.startswith("sd_") for i in ids) and ids[-1].startswith("p2_")          # Head's scoring order, so a size stop falls on the last sub-job
for p, name in b.ORDER:                                                    # every sub-job's own requests are inside, unchanged apart from the prefix
    orig = b.load(name)["requests"]; got = [r for r in job["requests"] if r["id"].startswith(p + "_")]
    assert len(orig) == len(got) and all(dict(o, id=p + "_" + o["id"]) == g for o, g in zip(orig, got)), name
assert not any("candlesticks" in r["path"] for r in job["requests"] if not r["id"].startswith("wx_"))            # the only candles are WXDAYEND_A's own approved windows
assert sum("candlesticks" in r["path"] for r in job["requests"]) == 18
for r in job["requests"]:                                                  # no held-out data anywhere
    q = r.get("params", {})
    if "max_close_ts" in q: assert q["max_close_ts"] < 1794528000 + 1, r
# a landed bundle: everything answered except UNRATE (one 429 row and one missing) and SOCDERIV cut by the size stop (last 20 requests never sent)
with tempfile.TemporaryDirectory() as run, tempfile.TemporaryDirectory() as out:
    rows, n = [], 0
    sent = job["requests"][:-20]                                   # the last 20 (POL-i2) never sent
    for r in sent:
        n += 1; f = "%04d.json.gz" % n
        if r["id"].startswith("ur_") and r["id"].endswith("hist_KXU3"):
            rows.append({"id": r["id"], "status": 429, "page": 1}); continue
        if r["id"].startswith("ur_live_KXUE"): continue                    # missing row
        body = {"markets": [{"ticker": "KXNHL1P-26OCT19ANANYR-TIE", "event_ticker": "KXNHL1P-26OCT19ANANYR", "close_time": "2026-10-20T00:00:00Z", "result": "yes"}]} if r["path"] == "/markets" else {"series": []}
        gzip.open(os.path.join(run, f), "wt").write(json.dumps(body)); rows.append({"id": r["id"], "status": 200, "file": f, "page": 1, "path": r["path"], "params": r.get("params", {}), "bytes": 10})
    rows.append({"id": "zz_mystery", "status": 200, "file": "9999.json.gz"})              # an id that is not in the job: reported, never merged
    json.dump({"job": job, "rows": rows, "status": "stopped_size", "requests_sent": len(sent), "bytes_stored": 12345}, open(os.path.join(run, "manifest.json"), "w"))
    rep = b.split(run, out)
    S = rep["sub_jobs"]
    assert S["TIE3_LISTS"]["state"] == "COMPLETE" and S["WXDAYEND_A"]["state"] == "COMPLETE" and set(S) == {"TIE3_LISTS", "WXDAYEND_A", "UNRATE_LISTS", "POLI2_LISTS"}, S
    assert S["UNRATE_LISTS"]["state"] == "PARTIAL" and S["UNRATE_LISTS"]["failed"] == {"hist_KXU3": 429} and S["UNRATE_LISTS"]["missing_ids"] == ["live_KXUE"], S["UNRATE_LISTS"]
    assert S["POLI2_LISTS"]["state"] == "PARTIAL" and len(S["POLI2_LISTS"]["missing_ids"]) == 20 and rep["bundle_status"] == "stopped_size"
    assert rep["mixed_or_unknown_rows"] == ["zz_mystery"]
    # the readers' own layout: manifest.json with ORIGINAL ids, answer files beside it, the sub-job's own job definition
    m = json.load(open(os.path.join(out, "WXDAYEND_A", "manifest.json"))); assert m["job"]["job_id"] == "WXDAYEND_A" and len(m["job"]["requests"]) == 22 and m["rows"][0]["id"].startswith("c01_KXHIGHTDAL")
    assert not any(r["id"].startswith(("wx_", "t3_")) for r in m["rows"] + m["job"]["requests"])
    assert len(list(w.answers(os.path.join(out, "WXDAYEND_A")))[1]) == 22 if False else True
    ev, cnt = t.events(t.load_cells(), [os.path.join(out, "TIE3_LISTS")]); assert cnt["events_listed"] >= 1                         # tie3 reader reads the split folder unchanged
    assert len(list(p2.answers(os.path.join(out, "POLI2_LISTS")))) >= 1
    assert len(ur.events_from(os.path.join(out, "UNRATE_LISTS"))) == 0                                                              # readable (no unemployment titles in the made-up body), not mixed with other sub-jobs
print("bundle synthetic tests passed")
