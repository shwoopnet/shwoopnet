#!/usr/bin/env python3
"""Low-frequency quote recorder (RECDAILY, Nov 3, 2026, research only).

Several registered forward tests (USWEEP1, BARRIER1, NOWCAST1, FEDIMPL1) watch daily, weekly or monthly Kalshi markets at looks hours or days apart. The forward
ledger and a research sandbox are ephemeral and the shared API limit makes ad-hoc pulls fail, so this records the public quote of every watched market every 30 minutes and
the result when it settles. The watchlist (kalshi-scalper/workers/RECDAILY_WATCHLIST.json) decides what is polled; this script holds no ticker of its own.

Public GET endpoints only: no key, no signing, no account, no order. A run is idempotent: its output file is named for the 30 minute slot it falls in, so a re-run of the
same slot overwrites the same file, and settled results are written once per ticker. The server's Date header is kept on every row so clock skew can be measured."""
import argparse
import csv
import glob
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
UA = {"User-Agent": "shwoopnet-research-recorder"}
SLOT_S = 1800
GAP_S = 0.5                      # pause between reads, the shared public limit is low
MAX_PAGES = 6
QUOTE_COLS = ["slot_ts", "poll_ts", "server_date_header", "tests", "series", "ticker", "event_ticker", "open_time", "close_time", "mins_to_close", "status",
              "strike_type", "floor_strike", "cap_strike", "yes_bid", "yes_ask", "last", "volume", "open_interest"]
RESULT_COLS = ["ticker", "series", "event_ticker", "close_time", "result", "expiration_value", "settlement_ts", "seen_ts"]
REF_COLS = ["ref_id", "type", "effective_date", "percent_rate", "p1", "p25", "p75", "p99", "volume_billions", "revision", "seen_ts"]
RUN_COLS = ["slot_ts", "poll_ts", "server_date_header", "clock_skew_s", "series_polled", "calls", "n429", "n_errors", "quote_rows", "result_rows"]


_sleep = time.sleep      # replaced in tests


def http_get(url):
    """(status, decoded json or None, Date header). Never raises."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


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


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def load_watchlist(path):
    w = json.load(open(path))
    by_series = {}
    for e in w["watch"]:
        s = by_series.setdefault(e["series"], {"tests": [], "window_hours": w.get("default_window_hours", 30), "keep_all_open": False, "utc_hours": None,
                                               "weekdays_only": False, "stop_date": None})
        # Optional per entry limits (SOFR1, Nov 6, 2026): poll only inside [h0, h1) UTC, only Monday to Friday, and never after stop_date. No limit means every slot, as before.
        if e.get("utc_hours"):
            s["utc_hours"] = e["utc_hours"]
        if e.get("weekdays_only"):
            s["weekdays_only"] = True
        if e.get("stop_date"):
            s["stop_date"] = e["stop_date"]
        s["tests"].append(e["test"])
        if e.get("keep_all_open"):
            s["keep_all_open"] = True
        s["window_hours"] = max(s["window_hours"], e.get("window_hours") or 0)
    return by_series


def active(cfg, now):
    """False when this series' own limits say not to poll at this moment (outside its UTC hours, a weekend, or past its stop date)."""
    g = time.gmtime(now)
    if cfg.get("stop_date") and time.strftime("%Y-%m-%d", g) > cfg["stop_date"]:
        return False
    if cfg.get("weekdays_only") and g.tm_wday >= 5:
        return False
    h = cfg.get("utc_hours")
    return not h or h[0] <= g.tm_hour < h[1]


def fetch_refs(refs, data_dir, now):
    """Daily reference rows (the NY Fed's SOFR): one public GET per reference, written once per effective date. Returns (calls, errors)."""
    calls = errs = 0
    for r in refs:
        if not active(r, now):
            continue
        st, body, _ = http_get(r["url"])
        calls += 1
        rows = []
        if st == 200 and isinstance(body, dict):
            for x in body.get("refRates") or []:
                if x.get("effectiveDate") and x.get("percentRate") is not None:
                    rows.append([r["id"], x.get("type", ""), x["effectiveDate"], x["percentRate"], x.get("percentPercentile1", ""), x.get("percentPercentile25", ""),
                                 x.get("percentPercentile75", ""), x.get("percentPercentile99", ""), x.get("volumeInBillions", ""), x.get("revisionIndicator", ""), int(now)])
        if not rows:
            errs += 1
            continue
        path = os.path.join(data_dir, "daily", "ref", rows[0][2] + ".csv.gz")
        if not os.path.exists(path):
            write_gz(path, REF_COLS, rows)
        _sleep(GAP_S)
    return calls, errs


def wanted(market, cfg, now):
    """Keep a market when the series keeps all open markets, or when it closes within the window (never one already past its close)."""
    if cfg["keep_all_open"]:
        return True
    c = parse_iso(market.get("close_time") or "")
    return c is not None and now - 600 <= c <= now + cfg["window_hours"] * 3600


def quote_row(slot, ts, date, series, cfg, m):
    c = parse_iso(m.get("close_time") or "")
    mins = round((c - ts) / 60.0, 1) if c is not None else ""
    return [slot, ts, date, "|".join(sorted(set(cfg["tests"]))), series, m.get("ticker"), m.get("event_ticker"), m.get("open_time"), m.get("close_time"), mins,
            m.get("status"), m.get("strike_type"), first(m, "floor_strike"), first(m, "cap_strike"),
            first(m, "yes_bid_dollars", "yes_bid"), first(m, "yes_ask_dollars", "yes_ask"), first(m, "last_price_dollars", "last_price"),
            first(m, "volume_fp", "volume"), first(m, "open_interest_fp", "open_interest")]


def result_row(series, m, ts):
    return [m.get("ticker"), series, m.get("event_ticker"), m.get("close_time"), m.get("result"), first(m, "expiration_value"),
            first(m, "settlement_ts", "settled_time", "expiration_time"), ts]


def list_markets(series, status, extra=""):
    """All pages of a market listing: (markets, calls, n429, error). A refused page ends the listing for this run and is counted, never retried hard."""
    out, cursor, calls, n429 = [], "", 0, 0
    for _ in range(MAX_PAGES):
        url = "%s/markets?series_ticker=%s&status=%s&limit=1000%s%s" % (BASE, series, status, extra, ("&cursor=" + cursor) if cursor else "")
        st, body, date = http_get(url)
        calls += 1
        if st == 429:
            n429 += 1
            _sleep(3.0)
            st, body, date = http_get(url)
            calls += 1
            if st == 429:
                n429 += 1
        if st != 200 or not isinstance(body, dict):
            return out, calls, n429, True, date
        out += body.get("markets") or []
        cursor = body.get("cursor") or ""
        _sleep(GAP_S)
        if not cursor:
            break
    return out, calls, n429, False, date


def known_results(data_dir):
    seen = set()
    for p in glob.glob(os.path.join(data_dir, "daily", "results", "**", "*.csv.gz"), recursive=True):
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


def run(watchlist, data_dir, now=None, getter=None):
    """One poll of the watchlist. Returns the run summary row."""
    global http_get
    real = http_get
    if getter:
        http_get = getter
    try:
        now = time.time() if now is None else now
        slot = slot_of(now)
        day = time.strftime("%Y-%m-%d", time.gmtime(slot))
        hhmm = time.strftime("%H%M", time.gmtime(slot))
        cfgs = load_watchlist(watchlist)
        seen = known_results(data_dir)
        qrows, rrows, calls, n429, errs, date0 = [], [], 0, 0, 0, ""
        for series, cfg in cfgs.items():
            if not active(cfg, now):
                continue
            ms, c, n, bad, date = list_markets(series, "open")
            calls, n429, errs, date0 = calls + c, n429 + n, errs + (1 if bad else 0), date or date0
            ts = int(time.time()) if getter is None else int(now)
            qrows += [quote_row(slot, ts, date, series, cfg, m) for m in ms if wanted(m, cfg, ts)]
            lo = int(now - 3 * 86400)
            sm, c, n, bad, date = list_markets(series, "settled", "&min_close_ts=%d" % lo)
            calls, n429, errs = calls + c, n429 + n, errs + (1 if bad else 0)
            for m in sm:
                if m.get("ticker") not in seen and m.get("result") in ("yes", "no"):
                    seen.add(m["ticker"])
                    rrows.append(result_row(series, m, int(now)))
        rc, re_ = fetch_refs(json.load(open(watchlist)).get("refs") or [], data_dir, now)
        calls, errs = calls + rc, errs + re_
        write_gz(os.path.join(data_dir, "daily", "quotes", day, hhmm + ".csv.gz"), QUOTE_COLS, qrows)
        if rrows:
            write_gz(os.path.join(data_dir, "daily", "results", day, hhmm + ".csv.gz"), RESULT_COLS, rrows)
        skew = ""
        if date0:
            try:
                from email.utils import parsedate_to_datetime
                skew = round(now - parsedate_to_datetime(date0).timestamp(), 1)
            except Exception:
                skew = ""
        summary = [slot, int(now), date0, skew, len(cfgs), calls, n429, errs, len(qrows), len(rrows)]
        runs = os.path.join(data_dir, "daily", "runs", day + ".csv")
        os.makedirs(os.path.dirname(runs), exist_ok=True)
        new = not os.path.exists(runs)
        with open(runs, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(RUN_COLS)
            w.writerow(summary)
        return summary
    finally:
        http_get = real


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", help="the checked out quote-data branch; files go under daily/")
    ap.add_argument("--watchlist", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kalshi-scalper", "workers", "RECDAILY_WATCHLIST.json"))
    a = ap.parse_args(argv)
    print(run(a.watchlist, a.data_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
