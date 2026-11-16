"""python3 -I build_ladder_census_job_test.py [runner copy path]"""
import sys, os, json, importlib.util
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import build_ladder_census_job as B
j = B.build(); r = j["requests"]
assert len({x["id"] for x in r}) == len(r) and j["max_requests"] <= 432 and len(r) < 470, (len(r), j["max_requests"])
assert all(x["path"] == "/markets" and set(x["params"]) <= {"series_ticker", "status", "min_close_ts", "max_close_ts", "limit"} for x in r)
assert {x["params"]["series_ticker"] for x in r} == set(j["series_allowlist"])
for s in j["series_allowlist"]:
    rs = sorted((x for x in r if x["params"]["series_ticker"] == s), key=lambda x: x["params"]["min_close_ts"])
    assert all(a["params"]["max_close_ts"] + 1 == b["params"]["min_close_ts"] for a, b in zip(rs, rs[1:])), s
assert min(x["params"]["min_close_ts"] for x in r if x["params"]["series_ticker"] in B.HOURLY_ARCHIVED) == B.ARCH_END
assert max(x["params"]["max_close_ts"] for x in r) == B.END - 1 and j["pacing_seconds"] == 5.0
if len(sys.argv) > 1:
    sp = importlib.util.spec_from_file_location("kp", sys.argv[1]); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    p = os.path.join(os.environ.get("TMPDIR", "/tmp"), "LADDER_CENSUS_LISTS.json"); json.dump(j, open(p, "w")); m.dry_run(m.load_job(p), out=lambda s: None); print("runner load_job and dry_run OK")
print("ALL OK", len(r), "requests, cap", j["max_requests"])
