#!/usr/bin/env python3
"""kalshi-pull (Nov 12, 2026): a MANUAL, on-demand pull of Kalshi's PUBLIC market data for the research sessions. Research data only: nothing here trades.

The logic of the request checks (host pin, path patterns, ticker and series allowlists, denied paths, a 429 stop) follows the research runner src/scalper/pullrunner.py; this
copy is the one that runs on a GitHub runner, with a slower pace and a stricter 429 rule.

What it can do: read ONE job file from kalshi-scalper/workers/kalshi_pull_jobs/, check every request in it, then send them one at a time, GET only, to ONE of exactly two hard-coded
(host, base path) pairs in the ROUTES table (the elections API, or Kalshi's public perpetuals "margin" API for the candlesticks of KXBTCPERP and KXETHPERP only), at most ONE request a second, and write the raw answers (gzipped) plus a manifest to an output folder that the workflow pushes to its own data branch (never main).

What it cannot do: it holds no key and sends no Authorization header, cookie or body; it follows no redirect; it never changes address, never uses a proxy and never retries around a
refusal. A 429 is waited out with a doubling pause and three 429s in a row END the run (what was fetched so far is still written). It reads only the standard library.

Exit codes: 0 finished (or dry run), 2 stopped (429s, failures, cap or time), 4 refused (job file or day cap) before any request."""
import argparse
import calendar
import gzip
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HOST = "api.elections.kalshi.com"
BASE_PATH = "/trade-api/v2"
PERPS_HOST = "external-api.kalshi.com"            # the same pair scripts/record_perps_candles.py has used since Nov 6, 2026
PERPS_BASE_PATH = "/trade-api/v2/margin"
# The ONLY two places a request can go. A job names one by KEY ("route"); it can never supply a host or a base path of its own (a job that carries a "route" key may not carry "host" or "base_path" at all).
ROUTES = {"elections": (HOST, BASE_PATH), "perps": (PERPS_HOST, PERPS_BASE_PATH)}
DEFAULT_ROUTE = "elections"                       # the five older jobs have no "route" key and still pin host and base_path by value
PERPS_TICKERS = frozenset({"KXBTCPERP", "KXETHPERP"})
PERPS_PATH = re.compile(r"/markets/(?P<ticker>[A-Z0-9]{2,32})/candlesticks")
PERPS_PARAMS = frozenset({"period_interval", "start_ts", "end_ts"})
PERPS_MAX_WINDOW_S = 86400                        # one UTC day of 1 minute candles (1,440), the size the existing recorder asks for
HERE = os.path.dirname(os.path.abspath(__file__))
JOB_DIR = os.path.join(HERE, "..", "kalshi-scalper", "workers", "kalshi_pull_jobs")
END_UTC = "2027-02-28T23:59:00Z"      # nothing is pulled from here on
GAP_S = 1.0                           # at least this long between two request starts: at most 1 request a second
BACKOFF_S = 5.0                       # first wait after a 429, then doubling
BACKOFF_MAX_S = 60.0
MAX_429_IN_ROW = 3                    # three refusals in a row end the run
MAX_FAILS_IN_ROW = 3                  # three other failures (5xx, 3xx, network) in a row end the run
HARD_MAX_REQUESTS = 1200              # no job may ask for more, whatever its file says
MAX_BODY_BYTES = 5 * 1000 * 1000      # one answer
MAX_RUN_BYTES = 200 * 1000 * 1000     # one run
MAX_RUN_SECONDS = 40 * 60             # one run (the workflow's own timeout is longer)
MAX_JOB_BYTES = 2 * 1000 * 1000
MAX_RUNS_PER_DAY = 6                  # real runs per UTC day, counted from the manifests already on the data branch
MAX_PAGES = 50
UA = {"User-Agent": "shwoopnet-research-pull", "Accept": "application/json"}

TOP_KEYS = {"job_id", "status", "owner", "registration", "purpose", "heldout", "route", "host", "base_path", "allowed_endpoints", "ticker_allowlist", "series_allowlist", "pacing_seconds",
            "max_requests", "stop_rules", "requests", "notes"}
OWNERS = {"V2", "REFINEMENT", "DESK_A", "DESK_B", "MAIN"}
DENY_PATH = re.compile(r"portfolio|account|/orders|order_group|/fills|/positions|api_key|api-key|subaccount|communications|login|logout|/rfq|/quotes|/margin|/exchange", re.I)
DENY_PARAM = re.compile(r"key|token|secret|signature|auth", re.I)
ID_RE = re.compile(r"[A-Z0-9_]{2,32}")
REQ_ID_RE = re.compile(r"[A-Za-z0-9_.-]{1,80}")
TICKER_RE = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,63}")
SERIES_RE = re.compile(r"[A-Z0-9]{2,32}")
CURSOR_RE = re.compile(r"[A-Za-z0-9_=.-]{1,512}")
REG_RE = re.compile(r"kalshi-scalper/[A-Za-z0-9_./-]{1,120}\.md")
BAD_CHARS = re.compile(r"[\\/?&#%=@:\s]|\.\.|[^\x21-\x7e]")     # applied to every value except a comma list of tickers (commas are checked per ticker)
STATUS_VALUES = {"open", "closed", "settled", "unopened"}


class Refused(Exception):
    pass


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


# ---------------------------------------------------------------- the job file
def load_job(path):
    if os.path.getsize(path) > MAX_JOB_BYTES:
        raise Refused("job file is over %d bytes" % MAX_JOB_BYTES)
    with open(path, "rb") as f:
        raw = f.read()
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        raise Refused("job file must be ASCII")
    job = json.loads(raw)
    if not isinstance(job, dict):
        raise Refused("job file is not an object")
    return job


def check_job(job):
    """Static checks of the whole plan before ANY request. Returns the list of compiled endpoints. Raises Refused on the first problem."""
    unknown = set(job) - TOP_KEYS
    if unknown:
        raise Refused("unknown keys %s" % sorted(unknown))
    for k in ("job_id", "status", "owner", "registration", "purpose", "heldout", "allowed_endpoints", "pacing_seconds", "max_requests", "stop_rules", "requests"):
        if k not in job:
            raise Refused("job file lacks '%s'" % k)
    if not isinstance(job["job_id"], str) or not ID_RE.fullmatch(job["job_id"]):
        raise Refused("bad job_id")
    if job["status"] != "active":
        raise Refused("job %s is '%s', not active" % (job["job_id"], job["status"]))
    if job["owner"] not in OWNERS:
        raise Refused("bad owner")
    if not isinstance(job["registration"], str) or not REG_RE.fullmatch(job["registration"]):
        raise Refused("registration must be a kalshi-scalper/*.md path")
    if not isinstance(job["purpose"], str) or not 1 <= len(job["purpose"]) <= 400:
        raise Refused("purpose must be one short line")
    if not isinstance(job["heldout"], str) or not job["heldout"].strip():
        raise Refused("heldout must say 'none' or name the registration whose one read this is")
    route = route_of(job)
    if not isinstance(job["pacing_seconds"], (int, float)) or job["pacing_seconds"] < GAP_S:
        raise Refused("pacing_seconds can only be slower than %s" % GAP_S)
    cap = job["max_requests"]
    if not isinstance(cap, int) or isinstance(cap, bool) or not 1 <= cap <= HARD_MAX_REQUESTS:
        raise Refused("max_requests must be 1 to %d" % HARD_MAX_REQUESTS)
    sr = job["stop_rules"]
    if not isinstance(sr, dict) or sr.get("stop_after_consecutive_429", MAX_429_IN_ROW) > MAX_429_IN_ROW:
        raise Refused("a job may only lower the 429 stop (%d)" % MAX_429_IN_ROW)
    eps = []
    for e in job["allowed_endpoints"]:
        if not isinstance(e, dict) or e.get("method", "GET") != "GET":
            raise Refused("only GET is allowed")
        eps.append((re.compile(e["path_pattern"]), set(e.get("params_allowed", [])), e["name"]))
    if not eps:
        raise Refused("no allowed endpoint")
    tk = set(job.get("ticker_allowlist", []))
    sr_ = set(job.get("series_allowlist", []))
    if not all(isinstance(t, str) and TICKER_RE.fullmatch(t) for t in tk) or not all(isinstance(s, str) and SERIES_RE.fullmatch(s) for s in sr_):
        raise Refused("bad ticker or series in an allowlist")
    reqs = job["requests"]
    if not isinstance(reqs, list) or not reqs:
        raise Refused("no requests")
    if len(reqs) > cap:
        raise Refused("%d requests but max_requests is %d" % (len(reqs), cap))
    seen = set()
    for r in reqs:
        if not isinstance(r, dict) or not set(r) <= {"id", "path", "params", "max_pages"}:
            raise Refused("a request has unknown keys")
        if not isinstance(r.get("id"), str) or not REQ_ID_RE.fullmatch(r["id"]) or r["id"] in seen:
            raise Refused("bad or repeated request id")
        seen.add(r["id"])
        check_request(r, eps, tk, sr_)
        if route == "perps":
            check_perps_request(r, tk)
    if route == "perps":
        check_perps_job(job, tk, sr_)
    return eps


def route_of(job):
    """The route KEY of a job, after checking how it names its destination. A job with a "route" key carries no host or base_path (it names a pair, never supplies one); an older job has no
    "route" key and must carry the elections host and base path by value. Anything else is refused."""
    if "route" in job:
        if "host" in job or "base_path" in job:
            raise Refused("a job that names a route may not carry host or base_path")
        if not isinstance(job["route"], str) or job["route"] not in ROUTES:
            raise Refused("route must be one of %s" % sorted(ROUTES))
        return job["route"]
    if job.get("host") != HOST:
        raise Refused("host %r is not %s" % (job.get("host"), HOST))
    if job.get("base_path") != BASE_PATH:
        raise Refused("base_path must be %s" % BASE_PATH)
    return DEFAULT_ROUTE


def check_perps_job(job, tk, sr):
    """The perps route reads ONE kind of thing: the 1 minute candles of two named perpetuals. No list, no funding, no cursor, no series."""
    if not tk or not tk <= PERPS_TICKERS or sr:
        raise Refused("a perps job may name only KXBTCPERP and KXETHPERP, and no series")
    for e in job["allowed_endpoints"]:
        if e["path_pattern"] != r"/markets/(?P<ticker>KXBTCPERP|KXETHPERP)/candlesticks" or not set(e.get("params_allowed", [])) <= PERPS_PARAMS:
            raise Refused("a perps job may allow only the candlesticks endpoint of KXBTCPERP and KXETHPERP")


def check_perps_request(r, tk):
    m = PERPS_PATH.fullmatch(r["path"])
    if not m or m.group("ticker") not in PERPS_TICKERS or m.group("ticker") not in tk:
        raise Refused("a perps request may only read /markets/<KXBTCPERP or KXETHPERP>/candlesticks")
    p = r.get("params", {})
    if set(p) != PERPS_PARAMS or p["period_interval"] != 1 or r.get("max_pages", 1) != 1:
        raise Refused("a perps request is one page of 1 minute candles with period_interval, start_ts and end_ts")
    if not 0 < p["end_ts"] - p["start_ts"] <= PERPS_MAX_WINDOW_S:
        raise Refused("a perps request covers at most %d seconds" % PERPS_MAX_WINDOW_S)


def check_request(r, eps, tk, sr):
    path = r["path"]
    if not isinstance(path, str) or DENY_PATH.search(path) or re.search(r"%|\.\.|\\|\?|#", path):
        raise Refused("denied or malformed path %r" % path)
    params = r.get("params", {})
    if not isinstance(params, dict):
        raise Refused("params must be an object")
    mp = r.get("max_pages", 1)
    if not isinstance(mp, int) or isinstance(mp, bool) or not 1 <= mp <= MAX_PAGES:
        raise Refused("max_pages must be 1 to %d" % MAX_PAGES)
    for k, v in params.items():
        if DENY_PARAM.search(k) or k == "cursor":
            raise Refused("denied param %s" % k)
        if isinstance(v, bool) or not isinstance(v, (str, int)):
            raise Refused("param %s must be a string or an integer" % k)
        s = str(v)
        if k == "market_tickers":
            parts = s.split(",")
            if not 1 <= len(parts) <= 100 or not all(TICKER_RE.fullmatch(p) and p in tk for p in parts):
                raise Refused("market_tickers must be 1 to 100 allowlisted tickers")
        elif BAD_CHARS.search(s) or not s:
            raise Refused("param %s has a forbidden character" % k)
        if k == "status" and s not in STATUS_VALUES:
            raise Refused("bad status")
        if k in ("series_ticker",) and s not in sr:
            raise Refused("series_ticker %s not in the allowlist" % s)
        if k in ("start_ts", "end_ts", "min_close_ts", "max_close_ts") and not (isinstance(v, int) and 1500000000 <= v <= 2100000000):
            raise Refused("%s must be an integer timestamp" % k)
        if k in ("limit", "period_interval") and not (isinstance(v, int) and 1 <= v <= 1440 * 1000):
            raise Refused("%s must be an integer" % k)
    for rx, allowed, name in eps:
        m = rx.fullmatch(path)
        if not m:
            continue
        for p in params:
            if p not in allowed:
                raise Refused("param %s not allowed for %s" % (p, name))
        g = m.groupdict()
        if "ticker" in g and (g["ticker"] not in tk or not TICKER_RE.fullmatch(g["ticker"])):
            raise Refused("ticker %s not in the allowlist" % g["ticker"])
        if "series" in g and (g["series"] not in sr or not SERIES_RE.fullmatch(g["series"])):
            raise Refused("series %s not in the allowlist" % g["series"])
        if mp > 1 and "cursor" not in allowed:
            raise Refused("max_pages above 1 needs the cursor param in params_allowed")
        return name
    raise Refused("path %s matches no allowed endpoint" % path)


def build_url(job, path, params, cursor=None):
    """The one place a URL is made. Re-parsed and compared to the pinned host before it is returned."""
    q = dict(params or {})
    if cursor:
        if not CURSOR_RE.fullmatch(cursor):
            raise Refused("bad cursor")
        q["cursor"] = cursor
    qs = urllib.parse.urlencode(q, safe=",") if q else ""
    host, base = ROUTES[route_of(job)] if job else ROUTES[DEFAULT_ROUTE]
    url = "https://%s%s%s%s" % (host, base, path, ("?" + qs) if qs else "")
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.hostname != host or u.username or u.password or u.port not in (None, 443) or u.fragment or not u.path.startswith(base + "/"):
        raise Refused("url failed the host check")
    return url


# ---------------------------------------------------------------- the network
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: a 3xx answer is a failed read."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _make_opener():
    """build_opener() adds the environment-proxy handler by default (it reads HTTPS_PROXY), so the opener is assembled by hand with only the handlers a plain direct HTTPS GET needs."""
    o = urllib.request.OpenerDirector()
    for h in (urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(), urllib.request.HTTPDefaultErrorHandler(), urllib.request.HTTPErrorProcessor(), _NoRedirect()):
        o.add_handler(h)
    return o


_OPENER = _make_opener()    # a hand-built opener on purpose: see the gates


def http_get(url):
    """(status, body bytes, Date header, truncated). Never raises: a failed read is a status (0 = no answer). At most MAX_BODY_BYTES are read."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=UA), timeout=20) as r:
            body = r.read(MAX_BODY_BYTES + 1)
            return r.status, body[:MAX_BODY_BYTES], r.headers.get("Date", ""), len(body) > MAX_BODY_BYTES
    except urllib.error.HTTPError as e:
        return e.code, b"", "", False
    except Exception:
        return 0, b"", "", False


def parse_object(body):
    """The decoded body if it is a JSON object, else None. A non-object body is stored but never read for a cursor and is never an error."""
    try:
        d = json.loads(body)
    except Exception:
        return None
    return d if isinstance(d, dict) else None


# ---------------------------------------------------------------- the run
def utc_stamp(now):
    return time.strftime("%Y-%m-%dT%H%MZ", time.gmtime(now))


def runs_today(data_dir, job_id, now):
    """Real runs already on the data branch today (UTC), over all jobs. A dry run writes nothing, so it is not counted."""
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    base = os.path.join(data_dir, "pull")
    n = 0
    if os.path.isdir(base):
        for j in os.listdir(base):
            p = os.path.join(base, j)
            if os.path.isdir(p):
                n += sum(1 for d in os.listdir(p) if d.startswith(day + "T"))
    return n


def dry_run(job, out=print):
    check_job(job)
    n = len(job["requests"])
    pages = sum(r.get("max_pages", 1) for r in job["requests"])
    out("job %s  owner=%s  registration=%s" % (job["job_id"], job["owner"], job["registration"]))
    out("heldout: %s" % job["heldout"])
    out("plan: %d requests (%d pages at most), cap %d, pace one every %ss" % (n, pages, job["max_requests"], max(GAP_S, job["pacing_seconds"])))
    for i, r in enumerate(job["requests"][:10]):
        out("  %4d  GET %s" % (i + 1, build_url(job, r["path"], r.get("params"))))
    if n > 10:
        out("  ... %d more" % (n - 10))
    out("dry run: no request was sent and nothing is written")
    return n


def run(job, out_dir, fetch=None, clock=time.time, sleep=time.sleep, out=print):
    """Send the job's requests. Returns (status word, exit code). Everything fetched is written even when the run stops early."""
    check_job(job)
    fetch = fetch or http_get
    pacing = max(GAP_S, float(job["pacing_seconds"]))
    cap = job["max_requests"]
    stop429 = min(MAX_429_IN_ROW, job["stop_rules"].get("stop_after_consecutive_429", MAX_429_IN_ROW))
    os.makedirs(out_dir, exist_ok=True)
    rows, sent, total_bytes, n429_row, fails_row, backoff = [], 0, 0, 0, 0, BACKOFF_S
    last_start = [-1e18]
    t0 = clock()
    status = "complete"
    stop = False
    for r in job["requests"]:
        cursor, page = None, 0
        max_pages = r.get("max_pages", 1)
        while page < max_pages and not stop:
            if sent >= cap:
                status, stop = "stopped_at_cap", True
                break
            if clock() - t0 > MAX_RUN_SECONDS:
                status, stop = "stopped_time", True
                break
            url = build_url(job, r["path"], r.get("params"), cursor)
            wait = pacing - (clock() - last_start[0])
            if wait > 0:
                sleep(wait)
            last_start[0] = clock()
            t_send = int(clock() * 1000)
            st, body, date, truncated = fetch(url)
            t_recv = int(clock() * 1000)
            sent += 1
            row = {"index": sent, "id": r["id"], "path": r["path"], "params": r.get("params", {}), "page": page + 1, "status": st, "bytes": len(body), "t_send_ms": t_send,
                   "t_recv_ms": t_recv, "server_date": date}
            if st == 429:
                rows.append(row)
                n429_row += 1
                if n429_row >= stop429:
                    status, stop = "stopped_429", True
                    break
                sleep(backoff)                       # doubling pause; the SAME request is asked again, nothing else changes
                backoff = min(BACKOFF_MAX_S, backoff * 2)
                last_start[0] = clock()
                continue
            n429_row, backoff = 0, BACKOFF_S
            if st != 200:
                rows.append(row)
                if st == 404:
                    fails_row = 0
                    break                            # a 404 is an answer (no such market): next request
                fails_row += 1
                if fails_row >= MAX_FAILS_IN_ROW:
                    status, stop = "stopped_failures", True
                    break
                continue                             # the same request again, at most MAX_FAILS_IN_ROW in a row
            fails_row = 0
            if total_bytes + len(body) > MAX_RUN_BYTES:
                status, stop = "stopped_size", True
                break
            total_bytes += len(body)
            fname = "%04d.json.gz" % sent
            with gzip.open(os.path.join(out_dir, fname), "wb", 9) as f:
                f.write(body)
            row.update({"file": fname, "sha256": hashlib.sha256(body).hexdigest(), "truncated": bool(truncated)})
            d = None if truncated else parse_object(body)
            row["body_kind"] = "object" if d is not None else "not_object"
            rows.append(row)
            page += 1
            cursor = d.get("cursor") if d is not None else None
            if not (isinstance(cursor, str) and CURSOR_RE.fullmatch(cursor)):
                break
        if stop:
            break
    manifest = {"job": job, "script": "scripts/kalshi_pull.py", "started": utc_stamp(t0), "finished": utc_stamp(clock()), "status": status, "requests_sent": sent, "bytes_stored": total_bytes,
                "rows": rows}
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    with open(os.path.join(out_dir, "STATUS"), "w") as f:
        f.write(status + "\n")
    out("%s: %d requests sent, %d bytes stored" % (status, sent, total_bytes))
    return status, (0 if status == "complete" else 2)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--data-dir", help="the checked-out data branch (a real run writes pull/<job>/<stamp>/ under it)")
    a = ap.parse_args(argv)
    try:
        if past_end(time.time()):
            print("past the end date: nothing to pull")
            return 0
        if not ID_RE.fullmatch(a.job_id):
            raise Refused("bad job id")
        job = load_job(os.path.join(JOB_DIR, a.job_id + ".json"))
        if job.get("job_id") != a.job_id:
            raise Refused("job_id does not match the file name")
        if a.dry_run:
            dry_run(job)
            return 0
        if not a.data_dir:
            raise Refused("a real run needs --data-dir")
        now = time.time()
        if runs_today(a.data_dir, a.job_id, now) >= MAX_RUNS_PER_DAY:
            raise Refused("%d real runs already today" % MAX_RUNS_PER_DAY)
        out_dir = os.path.join(a.data_dir, "pull", a.job_id, utc_stamp(now) + "_" + re.sub(r"[^0-9]", "", os.environ.get("GITHUB_RUN_ID", "0"))[:20])
        return run(job, out_dir)[1]
    except Refused as e:
        print("REFUSED:", e)
        return 4


if __name__ == "__main__":
    sys.exit(main())
