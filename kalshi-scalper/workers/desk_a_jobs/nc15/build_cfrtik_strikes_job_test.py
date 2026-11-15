"""python3 -I build_cfrtik_strikes_job_test.py (invented checks of the job's shape, then the runner's own load_job and dry_run if a runner copy is given as argv[1])."""
import sys, os, json, importlib.util
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import build_cfrtik_strikes_job as B
j = B.build(); r = j["requests"]
assert len(r) == 6 * 5 and j["max_requests"] == len(r) * 2 + 6 and len({x["id"] for x in r}) == len(r)
assert all(x["path"] == "/markets" and set(x["params"]) <= {"series_ticker", "status", "min_close_ts", "max_close_ts", "limit"} for x in r)
assert min(x["params"]["min_close_ts"] for x in r) == B.START and max(x["params"]["max_close_ts"] for x in r) == B.END - 1
for s in B.SERIES:
    rs = sorted((x for x in r if x["params"]["series_ticker"] == s), key=lambda x: x["params"]["min_close_ts"])
    assert all(a["params"]["max_close_ts"] + 1 == b["params"]["min_close_ts"] for a, b in zip(rs, rs[1:])), s   # contiguous
assert "result" not in json.dumps(j["allowed_endpoints"]) and j["pacing_seconds"] == 5.0 and set(j["series_allowlist"]) == set(B.SERIES)
if len(sys.argv) > 1:
    sp = importlib.util.spec_from_file_location("kp", sys.argv[1]); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    p = os.path.join(os.environ.get("TMPDIR", "/tmp"), "CFRTIK_STRIKES_DAILY.json"); json.dump(j, open(p, "w")); job = m.load_job(p); m.dry_run(job, out=lambda s: None); print("runner load_job and dry_run OK")
print("ALL OK")
