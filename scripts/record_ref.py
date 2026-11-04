#!/usr/bin/env python3
"""Reference-value recorder (RECREF, Nov 3, 2026, research only).

Kalshi lists thousands of entertainment and tech markets that settle on a public number (a Spotify chart, a Rotten Tomatoes or Metacritic score, an App Store rank, a post
count). The public sources show only their CURRENT value, so there is no history to test "does the live reference already imply the outcome at the look". This records,
every 2 hours, the Kalshi quotes of the watched series together with the current reference value from the public source, each with its own timestamp, so the test can
be run later on what was on file at the look.

The watchlist (kalshi-scalper/workers/RECREF_WATCHLIST.json) decides what is polled and which source each series is paired with; this script names no ticker. Public GET
only: no key, no signing, no account, no order. One request per second per host, a descriptive User-Agent, one retry after a 429 or 5xx and then the read is skipped and
counted. A run is idempotent: its files are named for the 2 hour slot, so a re-run of a slot replaces them; settled results are written once per ticker."""
import argparse
import csv
import glob
import gzip
import json
import os
import sys
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_adapters as ad  # noqa: E402

BASE = "https://external-api.kalshi.com/trade-api/v2"
SLOT_S = 7200
HOST_GAP_S = 1.0                 # one request per second per host
MAX_PAGES = 4
QUOTE_COLS = ["slot_ts", "poll_ts", "server_date_header", "family", "refs", "series", "ticker", "event_ticker", "title", "open_time", "close_time", "mins_to_close", "status",
              "strike_type", "floor_strike", "cap_strike", "yes_bid", "yes_ask", "last", "volume", "open_interest"]
REF_COLS = ["slot_ts", "poll_ts", "ref_id", "adapter", "url", "http_status", "rank", "name", "value", "value2", "note"]
RESULT_COLS = ["ticker", "series", "event_ticker", "close_time", "result", "expiration_value", "settlement_ts", "seen_ts"]
RUN_COLS = ["slot_ts", "poll_ts", "series_polled", "refs_polled", "calls_kalshi", "calls_ref", "n429", "n_errors", "parse_failures", "quote_rows", "ref_rows", "result_rows"]

_sleep = time.sleep      # replaced in tests
_clock = time.time
_last_hit = {}           # host -> time of the last request


def http_get(url):
    """(status, body text or None, Date header). Never raises. Waits so a host sees at most one request a second."""
    host = urlparse(url).netloc
    wait = _last_hit.get(host, 0) + HOST_GAP_S - _clock()
    if wait > 0:
        _sleep(wait)
    _last_hit[host] = _clock()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ad.UA}), timeout=20) as r:
            return r.status, r.read(12_000_000).decode("utf-8", "replace"), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


def get_retry(url):
    """Up to two more tries after a pause (3 s, then 6 s) on a 429, a server error or no answer. Returns (status, body, date, n429, calls)."""
    st, body, date = http_get(url)
    n429, calls = (1 if st == 429 else 0), 1
    for pause in (3.0, 6.0):
        if not (st == 429 or st >= 500 or st == 0):
            break
        _sleep(pause)
        st, body, date = http_get(url)
        calls += 1
        n429 += 1 if st == 429 else 0
    return st, body, date, n429, calls


def first(m, *keys):
    for k in keys:
        if m.get(k) not in (None, ""):
            return m[k]
    return ""


def parse_iso(s):
    try:
        return int(time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))) - time.timezone
    except Exception:
        return None


def slot_of(now):
    return int(now - now % SLOT_S)


def load_watchlist(path):
    w = json.load(open(path))
    return w["series"], {r["id"]: r for r in w["refs"]}, w.get("default_window_hours", 168)


def wanted(market, window_hours, now):
    """Keep a market that closes within the window (never one already past its close)."""
    c = parse_iso(market.get("close_time") or "")
    return c is not None and now - 600 <= c <= now + window_hours * 3600


def quote_row(slot, ts, date, entry, m, keys=""):
    c = parse_iso(m.get("close_time") or "")
    mins = round((c - ts) / 60.0, 1) if c is not None else ""
    return [slot, ts, date, entry.get("family", ""), keys, entry["series"], m.get("ticker"), m.get("event_ticker"), (m.get("title") or "")[:120],
            m.get("open_time"), m.get("close_time"), mins, m.get("status"), m.get("strike_type"), first(m, "floor_strike"), first(m, "cap_strike"),
            first(m, "yes_bid_dollars", "yes_bid"), first(m, "yes_ask_dollars", "yes_ask"), first(m, "last_price_dollars", "last_price"),
            first(m, "volume_fp", "volume"), first(m, "open_interest_fp", "open_interest")]


def result_row(series, m, ts):
    return [m.get("ticker"), series, m.get("event_ticker"), m.get("close_time"), m.get("result"), first(m, "expiration_value"),
            first(m, "settlement_ts", "settled_time", "expiration_time"), ts]


def list_markets(series, status, extra=""):
    """All pages of a market listing: (markets, calls, n429, error, date)."""
    out, cursor, calls, n429, date = [], "", 0, 0, ""
    for _ in range(MAX_PAGES):
        url = "%s/markets?series_ticker=%s&status=%s&limit=1000%s%s" % (BASE, series, status, extra, ("&cursor=" + cursor) if cursor else "")
        st, body, d, n, c = get_retry(url)
        calls += c
        n429 += n
        date = d or date
        try:
            doc = json.loads(body) if st == 200 and body else None
        except ValueError:
            doc = None
        if not isinstance(doc, dict):
            return out, calls, n429, True, date
        out += doc.get("markets") or []
        cursor = doc.get("cursor") or ""
        if not cursor:
            break
    return out, calls, n429, False, date


def targets_for(ref, markets):
    """The reads one reference needs. A fixed reference is one read. A per-event one is derived from the OPEN markets themselves:
    per_event: the event's title gives a page slug (a Rotten Tomatoes film, a Metacritic game);
    per_close: the account's posts in the hours before the market's close (a post-count market).
    Returns {event_ticker: (key, url)} for per-event references and {"": (key, url)} for a fixed one. At most `max_targets` events."""
    p = ref.get("params") or {}
    if ref.get("per_event"):
        pe, out = ref["per_event"], {}
        rx = re.compile(pe["title_regex"])
        for m in markets:
            ev = m.get("event_ticker") or ""
            mt = rx.search(m.get("title") or "")
            if ev and ev not in out and mt and ad.slugify(mt.group(1), pe.get("sep", "_")):
                slug = ad.slugify(mt.group(1), pe.get("sep", "_"))
                out[ev] = (slug, pe["url"].replace("{slug}", slug))
        return dict(list(out.items())[: ref.get("max_targets", 8)])
    if ref.get("per_close"):
        hours, out = ref["per_close"]["hours"], {}
        for m in markets:
            ev, c = m.get("event_ticker") or "", parse_iso(m.get("close_time") or "")
            if ev and ev not in out and c is not None:
                out[ev] = ("close" + (m.get("close_time") or "")[:13], ad.xtracker_url(p["handle"], iso(c - hours * 3600), iso(c)))
        return dict(list(out.items())[: ref.get("max_targets", 4)])
    urls_fn = ad.ADAPTERS[ref["adapter"]][0]
    return {"": ("", urls_fn(p)[0])}


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def poll_target(ref, key, url, slot, ts):
    """One read of one reference page: (rows, calls, n429, failed). A page that cannot be read or parsed is a failure, never a made-up value."""
    name = ref["adapter"]
    if name not in ad.ADAPTERS:
        return [], 0, 0, True
    st, body, _d, n429, calls = get_retry(url)
    if st != 200 or not body:
        return [], calls, n429, True
    rows = ad.ADAPTERS[name][1](ref.get("params") or {}, [body])
    rid = ref["id"] + (":" + key if key else "")
    out = [[slot, ts, rid, name, url, st, r[0], r[1], r[2] if r[2] is not None else "", r[3] if r[3] is not None else "", r[4]] for r in rows]
    return out, calls, n429, not out


def load_standalone(path):
    """References polled on their own, with no Kalshi series attached (the Yahoo 1 minute reference bars). [] when the watchlist has none."""
    return json.load(open(path)).get("standalone_refs") or []


def state_path(data_dir):
    return os.path.join(data_dir, "ref", "yahoo1m_state.json")


def load_state(data_dir):
    """{symbol: unix second of the last 1 minute bar on file}. A missing or unreadable file means 'nothing on file', which makes the next run a 7 day backfill."""
    try:
        d = json.load(open(state_path(data_dir)))
        return {k: int(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def range_for(last_ts, now, p):
    """Backfill (7d, the most Yahoo keeps at 1 minute) when nothing is on file or the gap is over 20 hours; otherwise today's bars."""
    return p.get("range", "1d") if last_ts and now - last_ts <= 20 * 3600 else p.get("backfill_range", "7d")


def run_standalone(ref, data_dir, slot, now, state):
    """Poll each symbol of one standalone reference. Returns (rows, calls, n429, failures); updates `state` with the newest bar kept per symbol.
    A symbol that cannot be read is a counted failure and keeps its old high-water mark, so the next run backfills the gap (inside Yahoo's 7 days)."""
    p = ref.get("params") or {}
    rows, calls, n429, fails = [], 0, 0, 0
    for sym in p.get("symbols") or []:
        last = state.get(sym, 0)
        rng = range_for(last, now, p)
        url = ad.yahoo1m_url(sym, rng)
        st, body, _d, n, c = get_retry(url)
        if st != 200 or not body:                      # the other host of the same service, one plain try (never a different User-Agent)
            url = ad.yahoo1m_url(sym, rng, ad.YH_HOSTS[1])
            st, body, _d = http_get(url)
            c += 1
            n += 1 if st == 429 else 0
        calls, n429 = calls + c, n429 + n
        parsed = ad.yahoo1m_parse({"after_ts": last}, [body]) if st == 200 and body else []
        if st != 200 or not body or (not parsed and ad.yahoo1m_parse({}, [body]) == []):
            fails += 1
            continue
        rows += [[slot, int(now), ref["id"] + ":" + sym, ref["adapter"], url, st, r[0], r[1], r[2], r[3], r[4]] for r in parsed]
        if parsed:
            state[sym] = max(last, max(r[0] for r in parsed))
    return rows, calls, n429, fails


def known_results(data_dir):
    seen = set()
    for p in glob.glob(os.path.join(data_dir, "ref", "results", "**", "*.csv.gz"), recursive=True):
        try:
            with gzip.open(p, "rt", newline="") as f:
                for row in csv.DictReader(f):
                    seen.add(row["ticker"])
        except Exception:
            pass
    return seen


def write_gz(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def run(watchlist, data_dir, now=None):
    """One poll of the watchlist. Returns the run summary row."""
    now = _clock() if now is None else now
    slot = slot_of(now)
    day = time.strftime("%Y-%m-%d", time.gmtime(slot))
    hhmm = time.strftime("%H%M", time.gmtime(slot))
    entries, refs, default_window = load_watchlist(watchlist)
    seen = known_results(data_dir)
    qrows, rrows, vrows = [], [], []
    ck = cr = n429 = errs = fails = vrows_n = 0
    date0 = ""
    done, used = set(), set()
    for e in entries:
        ms, c, n, bad, date = list_markets(e["series"], "open")
        ck, n429, errs, date0 = ck + c, n429 + n, errs + (1 if bad else 0), date or date0
        ts = int(_clock())
        win = e.get("window_hours") or default_window
        kept = [m for m in ms if wanted(m, win, ts)]
        keysby = {}                                  # event -> the reference ids that apply to its markets
        for rid in e.get("refs") or []:
            used.add(rid)
            ref = refs[rid]
            for ev, (key, url) in targets_for(ref, kept).items():
                rkey = rid + (":" + key if key else "")
                keysby.setdefault(ev, []).append(rkey)
                if (rkey, url) in done:
                    continue
                done.add((rkey, url))
                rows, c2, n2, failed = poll_target(ref, key, url, slot, int(_clock()))
                cr, n429, fails = cr + c2, n429 + n2, fails + (1 if failed else 0)
                vrows += rows
        fixed = [r for r in (e.get("refs") or []) if not (refs[r].get("per_event") or refs[r].get("per_close"))]
        qrows += [quote_row(slot, ts, date, e, m, "|".join(fixed + keysby.get(m.get("event_ticker") or "", []))) for m in kept]
        sm, c, n, bad, _d = list_markets(e["series"], "settled", "&min_close_ts=%d" % int(now - 3 * 86400))
        ck, n429, errs = ck + c, n429 + n, errs + (1 if bad else 0)
        for m in sm:
            if m.get("ticker") not in seen and m.get("result") in ("yes", "no"):
                seen.add(m["ticker"])
                rrows.append(result_row(e["series"], m, int(now)))
    state = load_state(data_dir)
    for sref in load_standalone(watchlist):
        rows, c2, n2, f2 = run_standalone(sref, data_dir, slot, int(now), state)
        if rows:       # its own file named for the poll second (never the slot): the high-water mark moves on, so a re-run in the same slot must not overwrite bars an earlier run already kept
            write_gz(os.path.join(data_dir, "ref", "bars", day, "%s.csv.gz" % int(now)), REF_COLS, rows)
        vrows_n += len(rows)
        cr, n429, fails = cr + c2, n429 + n2, fails + f2
        used.add(sref["id"])
    if state:
        os.makedirs(os.path.dirname(state_path(data_dir)), exist_ok=True)
        json.dump(state, open(state_path(data_dir), "w"), sort_keys=True)
    write_gz(os.path.join(data_dir, "ref", "quotes", day, hhmm + ".csv.gz"), QUOTE_COLS, qrows)
    write_gz(os.path.join(data_dir, "ref", "refvals", day, hhmm + ".csv.gz"), REF_COLS, vrows)
    if rrows:
        write_gz(os.path.join(data_dir, "ref", "results", day, hhmm + ".csv.gz"), RESULT_COLS, rrows)
    summary = [slot, int(now), len(entries), len(used), ck, cr, n429, errs, fails, len(qrows), len(vrows) + vrows_n, len(rrows)]
    runs = os.path.join(data_dir, "ref", "runs", day + ".csv")
    os.makedirs(os.path.dirname(runs), exist_ok=True)
    new = not os.path.exists(runs)
    with open(runs, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(RUN_COLS)
        w.writerow(summary)
    return summary


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", help="the checked out quote-data branch; files go under ref/")
    ap.add_argument("--watchlist", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kalshi-scalper", "workers", "RECREF_WATCHLIST.json"))
    a = ap.parse_args(argv)
    print(run(a.watchlist, a.data_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
