"""Generic runner for the queued Kalshi pull jobs (workers/pulljobs/*.json). PULLJOBS1.

Public GETs on api.elections.kalshi.com only. No key, no account endpoint, no POST.

  python3 -I src/scalper/pullrunner.py JOB.json --dry-run [--limit N]
  python3 -I src/scalper/pullrunner.py JOB.json --approved JOB_ID [--max N] [--pacing S]

Rules enforced here (not left to the job file):
* a real run needs `--approved <job_id>` equal to the job's id, and a job with status "active";
* the only host ever called is api.elections.kalshi.com over https (HOST_ALLOWLIST); a job naming any
  other host is refused, and every URL is checked again right before it is sent;
* only GET; only paths that match one of the job's allowed_endpoints; every `ticker` / `series` in a path
  must be in the job's allowlists; only the params the endpoint lists; account, portfolio, order and key
  paths are refused by DENY_PATH whatever the job says; no Authorization header or key is ever sent;
* pacing (seconds between two requests), max_requests (a --max may only LOWER it);
* a 429 pauses pause_seconds (300) and retries the same request once; a second 429 in a row stops the
  run (exit 2) with the cursor saved; 3 other failures in a row also stop it;
* a checkpoint (job "checkpoints": cumulative read counts) stops the run (exit 3) so a person can look at
  the counts; running the same command again acknowledges it and goes on;
* the read log (workers/pulljobs/<job>_READLOG.json) holds status only: counts, timestamps, status
  codes, the request id. Never a payload. Response bodies go to the job's scratch output_dir, which must
  be outside the repository (raw data is never committed).
Exit codes: 0 finished, 2 stopped by a 429 or failures, 3 checkpoint, 4 refused."""
import os, sys, json, re, time, datetime, argparse, urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))          # kalshi-scalper
HOST_ALLOWLIST = ("api.elections.kalshi.com",)
DENY_PATH = re.compile(r"portfolio|account|/orders|order_group|/fills|/positions|api_key|api-key|subaccount|communications|login|logout|/rfq|/quotes", re.I)
DENY_PARAM = re.compile(r"key|token|secret|signature|auth", re.I)
LOGDIR = os.path.join(REPO, "workers", "pulljobs")
INF = 10 ** 9


class Refused(Exception):
    pass


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class UrllibHttp:
    """The only real network code. Sends GET with no credentials."""
    def get(self, url, timeout=30):
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "scalper-pullrunner/1"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception:
            return -1, b""


def load_job(path):
    job = json.load(open(path))
    for k in ("job_id", "status", "host", "base_path", "allowed_endpoints", "requests", "max_requests", "pacing_seconds", "stop_rules", "output_dir"):
        if k not in job:
            raise Refused("job file lacks '%s'" % k)
    return job


def check_job(job):
    """Static checks of the whole plan. Raises Refused on the first problem."""
    if job["host"] not in HOST_ALLOWLIST:
        raise Refused("host %r is not allowlisted" % job["host"])
    eps = []
    for e in job["allowed_endpoints"]:
        if e.get("method", "GET") != "GET":
            raise Refused("only GET is allowed")
        eps.append((re.compile(e["path_pattern"]), set(e.get("params_allowed", [])), e["name"]))
    tk = set(job.get("ticker_allowlist", [])); sr = set(job.get("series_allowlist", []))
    seen = set()
    for r in job["requests"]:
        if r["id"] in seen:
            raise Refused("duplicate request id %s" % r["id"])
        seen.add(r["id"])
        check_request(job, r, eps, tk, sr)
    return len(job["requests"])


def check_request(job, r, eps=None, tk=None, sr=None):
    if eps is None:
        eps = [(re.compile(e["path_pattern"]), set(e.get("params_allowed", [])), e["name"]) for e in job["allowed_endpoints"]]
        tk = set(job.get("ticker_allowlist", [])); sr = set(job.get("series_allowlist", []))
    path = r["path"]
    if DENY_PATH.search(path):
        raise Refused("denied path %s" % path)
    for k in r.get("params", {}):
        if DENY_PARAM.search(k):
            raise Refused("denied param %s" % k)
    for rx, allowed, name in eps:
        m = rx.fullmatch(path)
        if not m:
            continue
        for p in r.get("params", {}):
            if p not in allowed:
                raise Refused("param %s not allowed for %s" % (p, name))
        g = m.groupdict()
        if "ticker" in g and g["ticker"] not in tk:
            raise Refused("ticker %s not in the allowlist" % g["ticker"])
        if "series" in g and g["series"] not in sr:
            raise Refused("series %s not in the allowlist" % g["series"])
        # a series or ticker given as a query param must be allowlisted too
        sp = r.get("params", {}).get("series_ticker")
        if sp is not None and sp not in sr:
            raise Refused("series_ticker %s not in the allowlist" % sp)
        return name
    raise Refused("path %s matches no allowed endpoint" % path)


def build_url(job, path, params):
    if job["host"] not in HOST_ALLOWLIST:
        raise Refused("host not allowlisted")
    q = urllib.parse.urlencode(params, safe=",") if params else ""
    url = "https://%s%s%s%s" % (job["host"], job["base_path"], path, ("?" + q) if q else "")
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.hostname not in HOST_ALLOWLIST or u.username or u.port not in (None, 443):
        raise Refused("url failed the host check")
    return url


def paths(job):
    out = os.path.realpath(job["output_dir"])
    top = os.path.realpath(os.path.join(REPO, ".."))          # the git checkout
    if out == top or out.startswith(top + os.sep):
        raise Refused("output_dir must be scratch outside the repository: %s" % out)
    jid = job["job_id"]
    return dict(out=out, log=os.path.join(LOGDIR, jid + "_READLOG.json"),
                cur=os.path.join(REPO, job.get("resume_cursor_file", "workers/pulljobs/%s_CURSOR.json" % jid)))


def dry_run(job, limit, out=print):
    n = check_job(job)
    cap = min(job["max_requests"], n)
    out("job %s  status=%s  host=%s" % (job["job_id"], job["status"], job["host"]))
    out("plan: %d requests (max_requests %d, expected %s), pacing %ss" % (n, job["max_requests"], job.get("expected_requests"), job["pacing_seconds"]))
    out("at 25 reads an hour: %.1f hours for %d reads" % (cap / 25.0, cap))
    for i, r in enumerate(job["requests"][: (limit if limit else 10)]):
        out("  %4d  GET %s" % (i + 1, build_url(job, r["path"], r.get("params"))))
    if n > (limit if limit else 10):
        out("  ... %d more (use --limit N to print more)" % (n - (limit if limit else 10)))
    out("dry run: no request was made")
    return n


def run(job, http=None, sleep=time.sleep, clock=time.time, max_override=None, pacing_override=None, out=print, approved=None):
    if approved != job["job_id"]:
        raise Refused("refused: pass --approved %s (explicit approval of this job id)" % job["job_id"])
    if job["status"] != "active":
        raise Refused("job %s is %s, not active" % (job["job_id"], job["status"]))
    check_job(job)
    P = paths(job)
    os.makedirs(P["out"], exist_ok=True); os.makedirs(os.path.dirname(P["log"]), exist_ok=True)
    http = http or UrllibHttp()
    sr = job["stop_rules"]; pause = sr.get("pause_seconds_on_429", 300); max429 = sr.get("stop_after_consecutive_429", 2); maxfail = sr.get("stop_after_consecutive_other_failures", 3)
    cap = job["max_requests"]                               # answered requests (200, 404, other); a 429 is not a read
    max_attempts = job.get("max_attempts", int(cap * 1.25) + 2)   # every request sent, 429s included: the real load
    if max_override is not None:
        cap = min(cap, max_override); max_attempts = min(max_attempts, int(max_override * 1.25) + 2)
    pacing = job["pacing_seconds"] if pacing_override is None else max(pacing_override, 0)
    cps = sorted(job.get("checkpoints", []))
    st = json.load(open(P["cur"])) if os.path.exists(P["cur"]) else {"next_index": 0, "reads": 0, "attempts": 0, "at_checkpoint": None}
    log = json.load(open(P["log"])) if os.path.exists(P["log"]) else {"job_id": job["job_id"], "counts": {}, "requests": [], "stops": []}
    st["at_checkpoint"] = None                              # running again acknowledges a checkpoint
    last = [-INF]
    consec429 = fails = 0
    reqs = job["requests"]

    def save():
        json.dump(st, open(P["cur"], "w"), indent=1); json.dump(log, open(P["log"], "w"), indent=1)

    while st["next_index"] < len(reqs) and st["reads"] < cap and st["attempts"] < max_attempts:
        r = reqs[st["next_index"]]
        check_request(job, r)
        url = build_url(job, r["path"], r.get("params"))
        w = pacing - (clock() - last[0])
        if w > 0:
            sleep(w)
        last[0] = clock()
        code, body = http.get(url)
        st["attempts"] += 1
        if code != 429:
            st["reads"] += 1
        c = log["counts"]; c[str(code)] = c.get(str(code), 0) + 1
        log["requests"].append({"i": st["next_index"] + 1, "id": r["id"], "status": code, "at": utc_now()})
        if code == 429:
            consec429 += 1
            log["stops"].append({"at": utc_now(), "event": "429", "consecutive": consec429})
            if consec429 >= max429:
                log["stops"].append({"at": utc_now(), "event": "stopped: %d consecutive 429" % consec429}); save()
                out("stopped: second 429 in a row; cursor saved at request %d" % (st["next_index"] + 1)); return 2
            save(); out("429: pausing %ds" % pause); sleep(pause); last[0] = clock() - pacing
            continue                                       # same request again, once
        consec429 = 0
        if code == 200 or code == 404:
            fails = 0
            if code == 200:
                with open(os.path.join(P["out"], re.sub(r"[^A-Za-z0-9_.-]", "_", r["id"]) + ".json"), "wb") as f:
                    f.write(body)
            st["next_index"] += 1
        else:
            fails += 1
            if fails >= maxfail:
                log["stops"].append({"at": utc_now(), "event": "stopped: %d failures (%s)" % (fails, code)}); save()
                out("stopped after %d failures" % fails); return 2
            save(); continue
        save()
        if st["reads"] in cps:
            st["at_checkpoint"] = st["reads"]; save()
            out("checkpoint at %d reads: look at the counts, run the same command to go on" % st["reads"]); return 3
    out("done: %d reads, %d attempts, next_index %d of %d" % (st["reads"], st["attempts"], st["next_index"], len(reqs)))
    save(); return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("job"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--approved")
    ap.add_argument("--limit", type=int); ap.add_argument("--max", type=int); ap.add_argument("--pacing", type=float)
    a = ap.parse_args(argv)
    try:
        job = load_job(a.job)
        if a.dry_run:
            dry_run(job, a.limit); return 0
        return run(job, max_override=a.max, pacing_override=a.pacing, approved=a.approved)
    except Refused as e:
        print("REFUSED:", e); return 4


if __name__ == "__main__":
    sys.exit(main())
