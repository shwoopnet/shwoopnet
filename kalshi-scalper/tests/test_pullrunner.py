"""Unit test for src/scalper/pullrunner.py with a fake HTTP layer. python3 -I tests/test_pullrunner.py"""
import os, sys, json, copy, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "scalper"))
import pullrunner as pr

class Fake:
    def __init__(self, script): self.script = list(script); self.urls = []
    def get(self, url, timeout=30):
        self.urls.append(url); c = self.script.pop(0) if self.script else 200
        return c, (b'{"candlesticks": []}' if c == 200 else b"")

def job(tmp, n=6, **kw):
    reqs = [{"id": "T%d" % i, "path": "/historical/markets/T%d/candlesticks" % i, "params": {"start_ts": 1, "end_ts": 2, "period_interval": 60}} for i in range(n)]
    j = dict(job_id="TESTJOB%d" % os.getpid(), status="active", host="api.elections.kalshi.com", base_path="/trade-api/v2",
             allowed_endpoints=[{"name": "c", "method": "GET", "path_pattern": r"/historical/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}],
             ticker_allowlist=[r["id"] for r in reqs], series_allowlist=[], requests=reqs, max_requests=n, pacing_seconds=10,
             stop_rules={"pause_seconds_on_429": 300, "stop_after_consecutive_429": 2, "stop_after_consecutive_other_failures": 3},
             output_dir=os.path.join(tmp, "out"), checkpoints=[])
    j.update(kw); return j

class Clock:
    def __init__(self): self.t = 1000.0; self.sleeps = []
    def now(self): return self.t
    def sleep(self, s): self.sleeps.append(s); self.t += s

def cleanup(j):
    for suf in ("_READLOG.json", "_CURSOR.json"):
        p = os.path.join(pr.LOGDIR, j["job_id"] + suf)
        if os.path.exists(p): os.remove(p)

def go(j, script, **kw):
    h = Fake(script); c = Clock(); lines = []
    code = pr.run(j, http=h, sleep=c.sleep, clock=c.now, out=lines.append, **kw); return code, h, c, lines

def st_reads(j):
    return json.load(open(os.path.join(pr.REPO, 'workers/pulljobs/%s_CURSOR.json' % j['job_id'])))['reads']

def refused(f):
    try: f()
    except pr.Refused as e: return str(e)
    return None

tmp = tempfile.mkdtemp(); fails = 0
def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name); fails += 0 if ok else 1

try:
    # 1 no approval, wrong approval, inactive
    j = job(tmp); check("refuses without --approved", refused(lambda: pr.run(j, http=Fake([]), approved=None)) is not None)
    check("refuses a wrong --approved id", refused(lambda: pr.run(j, http=Fake([]), approved="OTHER")) is not None)
    ji = job(tmp, status="inactive"); check("refuses an inactive job", refused(lambda: pr.run(ji, http=Fake([]), approved=ji["job_id"])) is not None)
    # 2 host
    jb = job(tmp, host="example.com"); check("refuses another host", refused(lambda: pr.check_job(jb)) is not None)
    check("build_url refuses a host outside the allowlist", refused(lambda: pr.build_url(jb, "/x", {})) is not None)
    # 3 allowlist and denied paths and params
    jt = job(tmp); jt["requests"][0]["path"] = "/historical/markets/EVIL/candlesticks"
    check("refuses a ticker not in the allowlist", "allowlist" in (refused(lambda: pr.check_job(jt)) or ""))
    jp = job(tmp); jp["requests"][0] = {"id": "P", "path": "/portfolio/balance", "params": {}}
    check("refuses a portfolio path", "denied" in (refused(lambda: pr.check_job(jp)) or ""))
    jq = job(tmp); jq["requests"][0]["params"]["api_key"] = "x"
    check("refuses a key-like param", "denied" in (refused(lambda: pr.check_job(jq)) or ""))
    jr = job(tmp); jr["requests"][0]["params"]["foo"] = 1
    check("refuses a param not listed", "not allowed" in (refused(lambda: pr.check_job(jr)) or ""))
    jo = job(tmp); jo["requests"][0] = {"id": "O", "path": "/exchange/status", "params": {}}
    check("refuses a path matching no endpoint", refused(lambda: pr.check_job(jo)) is not None)
    jd = job(tmp, output_dir=os.path.join(pr.REPO, "scratch_bad"))
    check("refuses an output_dir inside the repository", "scratch" in (refused(lambda: pr.paths(jd)) or ""))
    # 4 normal run: pacing, cap, only the host, log has no payload
    j = job(tmp, n=4); code, h, c, _ = go(j, [], approved=j["job_id"])
    check("finishes with exit 0", code == 0)
    check("sent 4 requests, all to the one host", len(h.urls) == 4 and all(u.startswith("https://api.elections.kalshi.com/trade-api/v2/") for u in h.urls))
    check("pacing: 3 sleeps of 10s between 4 requests", c.sleeps == [10.0, 10.0, 10.0] or sum(c.sleeps) >= 30 - 1e-6)
    lg = json.load(open(os.path.join(pr.LOGDIR, j["job_id"] + "_READLOG.json")))
    check("read log has counts and statuses and no payload", lg["counts"] == {"200": 4} and "candlesticks" not in json.dumps(lg))
    check("raw bodies go to scratch", os.path.exists(os.path.join(tmp, "out", "T0.json")))
    cleanup(j)
    # 5 cap lowering only
    j = job(tmp, n=6); code, h, c, _ = go(j, [], approved=j["job_id"], max_override=2)
    check("--max lowers the cap (2 reads)", len(h.urls) == 2); cleanup(j)
    j = job(tmp, n=3); code, h, c, _ = go(j, [], approved=j["job_id"], max_override=99)
    check("--max cannot raise the cap", len(h.urls) == 3); cleanup(j)
    # 6 single 429: pause 300, retry same request, continue
    j = job(tmp, n=3); code, h, c, _ = go(j, [200, 429, 200, 200], approved=j["job_id"])
    check("one 429 pauses 300s and the run goes on", code == 0 and 300 in c.sleeps and len(h.urls) == 4 and h.urls[1] == h.urls[2])
    lg = json.load(open(os.path.join(pr.LOGDIR, j["job_id"] + "_READLOG.json")))
    check("429 not counted as a read", st_reads(j) == 3); cleanup(j)
    # 7 two 429 in a row: stop, cursor saved
    j = job(tmp, n=5); code, h, c, _ = go(j, [200, 429, 429], approved=j["job_id"])
    st = json.load(open(os.path.join(pr.REPO, "workers/pulljobs/%s_CURSOR.json" % j["job_id"])))
    check("second consecutive 429 stops (exit 2), cursor at request 2", code == 2 and st["next_index"] == 1 and len(h.urls) == 3)
    # 8 resume from the cursor
    code, h2, c2, _ = go(j, [], approved=j["job_id"])
    check("resume continues from the cursor, not from the start", code == 0 and len(h2.urls) == 4 and h2.urls[0].endswith("T1/candlesticks?start_ts=1&end_ts=2&period_interval=60")); cleanup(j)
    # 9 429 then success then 429 is not "consecutive"
    j = job(tmp, n=4); code, h, c, _ = go(j, [429, 200, 429, 200, 200], approved=j["job_id"])
    check("non-consecutive 429s do not stop the run", code == 0); cleanup(j)
    # 10 404 skipped, 3 other failures stop
    j = job(tmp, n=3); code, h, c, _ = go(j, [404, 200, 200], approved=j["job_id"])
    check("404 is logged and skipped", code == 0 and len(h.urls) == 3); cleanup(j)
    j = job(tmp, n=3); code, h, c, _ = go(j, [500, 500, 500], approved=j["job_id"])
    check("three failures in a row stop (exit 2)", code == 2); cleanup(j)
    # 11 checkpoint
    j = job(tmp, n=5, checkpoints=[2]); code, h, c, _ = go(j, [], approved=j["job_id"])
    check("checkpoint stops with exit 3 after 2 reads", code == 3 and len(h.urls) == 2)
    code, h, c, _ = go(j, [], approved=j["job_id"]); check("running again acknowledges it and finishes", code == 0 and len(h.urls) == 3); cleanup(j)
    # 12 dry run makes no request
    j = job(tmp, n=3); lines = []; n = pr.dry_run(j, 2, out=lines.append)
    check("dry run prints the plan and calls nothing", n == 3 and any("no request was made" in l for l in lines))
    # 13 the real job files in the repo pass the static check (no network)
    d = pr.LOGDIR
    for f in sorted(os.listdir(d)):
        if f.endswith(".json") and "_READLOG" not in f and "_CURSOR" not in f:
            jj = pr.load_job(os.path.join(d, f)); n = pr.check_job(jj)
            check("repo job %s passes the allowlist check (%d requests, host %s)" % (jj["job_id"], n, jj["host"]), jj["host"] in pr.HOST_ALLOWLIST and n <= jj["max_requests"] or jj["max_requests"] == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("FAILED %d" % fails if fails else "ALL PASSED"); sys.exit(1 if fails else 0)
