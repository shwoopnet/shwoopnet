#!/usr/bin/env python3
"""External-signal shadow logger (Nov 11, 2026; the owner: "EXTERNAL-SIGNAL SHADOW LOGGER: APPROVED"). Research data only: nothing here trades, signs, reads a key or writes to Firebase.

What it does. It reads kalshi-scalper/signals/REGISTRY.json. For each registered, enabled, due entry it makes ONE public read of the signal (a number or a short string, extracted by a
declarative spec: a JSON path or a CSV column, no eval, no regex) and ONE public read of the Kalshi market it is meant to be tested against (best bid, ask, sizes, close time), and appends
a row to a CSV. The point is that a new non-price candidate (weather, scores, options, onchain) can be tested forward without writing a new recorder each time.

Safety, all from constants in this file:
  - HOST ALLOWLIST: a signal url must be https and its host must be in ALLOWLIST. A registry edit cannot add a host; that is a code edit. The Kalshi quote host is fixed here.
  - GET only, no auth header, no key, no environment variable except the repository name for the User-Agent.
  - At least GAP_S between requests, MAX_REQUESTS per run, MAX_BYTES per response, a TIME budget per run; a 429 or 5xx backs off and is tried MAX_TRIES times; one failing source never stops the others.
  - It always exits 0. It stops by itself: from END_UTC nothing is recorded, and each entry has its own stopDate.
  - An entry that fails validation is skipped and named; the registry file is data, never code."""
import argparse
import calendar
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit, quote

KALSHI = "https://external-api.kalshi.com/trade-api/v2"
# Hosts of the feeds the repo's other recorders already read, plus a few named public ones. Sports league and broadcaster score sites are NOT on it (test/noSportsScoreSitesGates.test.js): their terms forbid automated collection (V2's INGAMELAG1 source probe, Nov 11, 2026). Adding a host is a code edit and a review.
ALLOWLIST = frozenset({
    "api.weather.gov", "mesonet.agron.iastate.edu",
    "www.okx.com", "www.deribit.com", "api.coinbase.com", "api.kraken.com",
})
END_UTC = "2027-02-28T23:59:00Z"          # nothing is recorded from here on (the workflow checks the same date)
MAX_STOP_DATE = "2027-02-28"
GAP_S = 1.0
BACKOFF_S = 2.0
BACKOFF_MAX_S = 16.0
MAX_TRIES = 3
MAX_REQUESTS = 24                          # per run, retries included
MAX_ENTRIES = 8                            # enabled entries per run (2 requests each)
MAX_BYTES = 262144                         # per response
MAX_VALUE_LEN = 40                         # a signal value is a number or a string this short
TIME_BUDGET_S = 40                         # after this no new entry is started, so a run stays near one billed minute
CADENCES = ("run", "day")
ID_RE = re.compile(r"^[A-Z0-9]{2,12}$")
TICKER_RE = re.compile(r"^[A-Z0-9-]{3,40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COLS = ["id", "signal_value", "signal_t_ms", "signal_status", "signal_date_hdr", "kalshi_ticker", "yes_bid", "yes_ask", "bid_size", "ask_size", "close_time", "quote_t_ms",
        "quote_date_hdr", "flags"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


def user_agent():
    # An identification header, not a credential; no personal details.
    return "shwoopnet-research-recorder (research only, no key; https://github.com/%s)" % os.environ.get("GITHUB_REPOSITORY", "shwoopnet")


def day_of(now):
    return time.strftime("%Y-%m-%d", time.gmtime(now))


def validate_entry(e):
    """Returns '' if the entry is acceptable, else the reason. Pure. The registry is untrusted data."""
    if not isinstance(e, dict):
        return "not an object"
    if not isinstance(e.get("id"), str) or not ID_RE.match(e["id"]):
        return "bad id"
    r = e.get("readme")
    if not isinstance(r, str) or not 5 <= len(r) <= 120:
        return "bad readme pointer"
    u = e.get("url")
    if not isinstance(u, str) or len(u) > 300 or not u.isascii() or any(c in u for c in " \r\n\t\\"):
        return "bad url"
    try:
        p = urlsplit(u)
        port = p.port
    except ValueError:
        return "bad url"
    if p.scheme != "https" or p.username or p.password or port not in (None, 443) or p.hostname not in ALLOWLIST or p.fragment:
        return "url host not on the allowlist or not plain https"
    ps = e.get("parse")
    if not isinstance(ps, dict):
        return "bad parse spec"
    if ps.get("type") == "json":
        path = ps.get("path")
        if set(ps) != {"type", "path"} or not isinstance(path, list) or not 1 <= len(path) <= 8:
            return "bad json path"
        for k in path:
            if isinstance(k, bool) or not (isinstance(k, int) and 0 <= k < 1000 or isinstance(k, str) and 1 <= len(k) <= 40):
                return "bad json path element"
    elif ps.get("type") == "csv":
        col, row = ps.get("column"), ps.get("row")
        if set(ps) != {"type", "column", "row"} or isinstance(col, bool) or not isinstance(col, int) or not 0 <= col <= 50:
            return "bad csv column"
        if not (row in ("first", "last") or (isinstance(row, int) and not isinstance(row, bool) and 0 <= row < 10000)):
            return "bad csv row"
    else:
        return "parse type must be json or csv"
    k = e.get("kalshi")
    if not isinstance(k, dict) or len(k) != 1 or list(k)[0] not in ("ticker", "series") or not isinstance(list(k.values())[0], str) or not TICKER_RE.match(list(k.values())[0]):
        return "bad kalshi ticker or series"
    if e.get("cadence") not in CADENCES:
        return "bad cadence"
    sd = e.get("stopDate")
    if not isinstance(sd, str) or not DATE_RE.match(sd) or sd > MAX_STOP_DATE:
        return "missing or too late stopDate"
    if not isinstance(e.get("enabled"), bool):
        return "enabled must be true or false"
    return ""


def load_registry(path):
    """(entries that validate, list of 'ID: reason' problems). Never raises."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("entries")
        if not isinstance(raw, list):
            return [], ["registry has no entries list"]
    except Exception:
        return [], ["registry unreadable"]
    ok, bad, seen = [], [], set()
    for e in raw:
        why = validate_entry(e)
        if not why and e["id"] in seen:
            why = "duplicate id"
        if why:
            bad.append("%s: %s" % (e.get("id") if isinstance(e, dict) else "?", why))
        else:
            seen.add(e["id"])
            ok.append(e)
    return ok, bad


def is_due(e, now, hour_utc=None):
    """Enabled, not stopped, not past the end; 'day' entries only at the first start of the UTC day (hour below 4)."""
    if past_end(now) or not e.get("enabled") or day_of(now) > e["stopDate"]:
        return False
    h = time.gmtime(now).tm_hour if hour_utc is None else hour_utc
    return e["cadence"] == "run" or h < 4


def pick_json(body, path):
    cur = body
    for k in path:
        if isinstance(k, int):
            if not isinstance(cur, list) or k >= len(cur):
                return None
            cur = cur[k]
        else:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
    return cur


def pick_csv(text, column, row):
    rows = [r for r in csv.reader(text.splitlines()) if r]
    if not rows:
        return None
    try:
        r = rows[0] if row == "first" else rows[-1] if row == "last" else rows[row]
        return r[column]
    except IndexError:
        return None


def clean_value(v):
    """A number or a short string, else None. Control characters are dropped and a leading formula character is neutralised so a CSV opened in a sheet cannot run it."""
    if isinstance(v, bool) or v is None or isinstance(v, (dict, list)):
        return None
    s = str(v)
    s = "".join(c for c in s if c.isprintable()).strip()
    if not s or len(s) > MAX_VALUE_LEN:
        return None
    try:
        float(s)
    except ValueError:
        if s[0] in "=+-@":
            s = "'" + s
    return s


def extract(spec, body_bytes):
    """The signal value from a response body, by the declarative spec. None if it cannot be read."""
    try:
        if spec["type"] == "json":
            return clean_value(pick_json(json.loads(body_bytes.decode("utf-8")), spec["path"]))
        return clean_value(pick_csv(body_bytes.decode("utf-8"), spec["column"], spec["row"]))
    except Exception:
        return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the host allowlist is checked on the registry URL only, so a redirect could leave it (an open redirect or a compromised endpoint on an allowlisted host). A 3xx answer is a failed read."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(url, headers):
    """(status, body bytes or None, Date header). Never raises. A body over MAX_BYTES is a failure (status -1). Redirects are refused."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=headers), timeout=15) as r:
            b = r.read(MAX_BYTES + 1)
            if len(b) > MAX_BYTES:
                return -1, None, ""
            return r.status, b, r.headers.get("Date", "") or ""
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


class Stream:
    """One request stream. EVERY request goes through `get`: at least gap_s apart, at most MAX_REQUESTS in all, a 429, 5xx or dropped connection backs off and is tried MAX_TRIES times.
    `fetch` is the transport ((url) -> (status, bytes, date)); tests pass a fake one with a fake clock and sleep."""

    def __init__(self, gap_s, headers, fetch=None, clock=time.time, sleep=time.sleep, max_requests=MAX_REQUESTS):
        assert gap_s >= 1.0
        self.gap_s, self.clock, self.sleep, self.max_requests = gap_s, clock, sleep, max_requests
        self.fetch = fetch or (lambda url: http_get(url, headers))
        self.next_ok = 0.0
        self.requests = 0
        self.capped = False

    def get(self, url):
        wait = BACKOFF_S
        st, body, date = 0, None, ""
        for attempt in range(MAX_TRIES):
            if self.requests >= self.max_requests:
                self.capped = True
                return 0, None, ""
            gap = self.next_ok - self.clock()
            if gap > 0:
                self.sleep(gap)
            st, body, date = self.fetch(url)
            self.requests += 1
            self.next_ok = self.clock() + self.gap_s
            if st == 429 or st >= 500 or st == 0:
                if attempt + 1 < MAX_TRIES:
                    self.sleep(wait)
                    self.next_ok = max(self.next_ok, self.clock())
                    wait = min(BACKOFF_MAX_S, wait * 2)
                continue
            return st, body, date
        return st, None, date


def num(x):
    try:
        return "" if x is None or x == "" else str(float(x))
    except (TypeError, ValueError):
        return ""


def read_quote(stream, kalshi):
    """(market dict or None, date header). `kalshi` is {'ticker': T} or {'series': S}; public GET /markets only."""
    if "ticker" in kalshi:
        st, body, date = stream.get("%s/markets/%s" % (KALSHI, quote(kalshi["ticker"])))
        try:
            m = json.loads(body.decode("utf-8")).get("market") if st == 200 and body else None
        except Exception:
            m = None
        return (m if isinstance(m, dict) else None), date
    st, body, date = stream.get("%s/markets?series_ticker=%s&status=open&limit=50" % (KALSHI, quote(kalshi["series"])))
    try:
        ms = [m for m in (json.loads(body.decode("utf-8")).get("markets") or []) if isinstance(m, dict) and m.get("close_time")] if st == 200 and body else []
    except Exception:
        ms = []
    return (min(ms, key=lambda m: m["close_time"]) if ms else None), date


def record_entry(stream, e, clock=time.time):
    """One output row for one entry. Failures of either read are flags, never exceptions."""
    flags = []
    t0 = int(clock() * 1000)
    st, body, sdate = stream.get(e["url"])
    value = extract(e["parse"], body) if st == 200 and body is not None else None
    if value is None:
        flags.append("signal_missing" if st == 200 else "signal_http_%s" % st)
    t1 = int(clock() * 1000)
    m, qdate = read_quote(stream, e["kalshi"])
    if m is None:
        flags.append("quote_missing")
    if stream.capped:
        flags.append("request_cap")
    t2 = int(clock() * 1000)
    m = m or {}
    return [e["id"], "" if value is None else value, t0, st, sdate, m.get("ticker", ""), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars")),
            num(m.get("yes_bid_size_fp")), num(m.get("yes_ask_size_fp")), m.get("close_time", ""), t2, qdate, ";".join(flags)]


def run(entries, stream, now, clock=time.time, budget_s=TIME_BUDGET_S):
    """Rows for every due entry. A failure on one entry never stops the next; no new entry starts after the time budget or the request cap."""
    rows, started = [], clock()
    due = [e for e in entries if is_due(e, now)][:MAX_ENTRIES]
    for e in due:
        if clock() - started > budget_s or stream.capped:
            break
        try:
            rows.append(record_entry(stream, e, clock))
        except Exception:
            rows.append([e["id"], "", int(clock() * 1000), "", "", "", "", "", "", "", "", "", "", "entry_error"])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="CSV file to append to (written only when there are rows)")
    ap.add_argument("--registry", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kalshi-scalper", "signals", "REGISTRY.json"))
    args = ap.parse_args(argv)
    now = time.time()
    if past_end(now):
        print("past the end date (%s): nothing to record" % END_UTC)
        return 0
    try:
        entries, bad = load_registry(args.registry)
        for b in bad:
            print("skipped: %s" % b)
        stream = Stream(GAP_S, {"User-Agent": user_agent()})
        rows = run(entries, stream, now)
        if rows:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "a", newline="") as f:
                w = csv.writer(f)
                if f.tell() == 0:
                    w.writerow(COLS)
                w.writerows(rows)
        print("entries due: %d, rows: %d, requests: %d" % (len([e for e in entries if is_due(e, now)]), len(rows), stream.requests))
    except Exception as ex:      # a recorder that fails loudly loses a day; this one exits 0
        print("recorder error (ignored): %s" % type(ex).__name__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
