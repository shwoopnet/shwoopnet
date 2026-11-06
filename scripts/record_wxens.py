#!/usr/bin/env python3
"""Ensemble temperature recorder (WXENS1, Nov 3, 2026, research only).

For the registered forward test kalshi-scalper/workers/WXENS1_REGISTRATION.md: at the registered looks (07:00 and 10:00 local STANDARD time of each watched city) this records,
for each city's target days, (1) every member of the Open-Meteo ensemble daily maximum temperature, (2) the NWS point forecast high, (3) the Kalshi quote of every open bracket of
the target day's KXHIGH event; every few hours it also records each newly settled market's result and the IEM daily observed maximum. Nothing is scored here.
WXLOW1 (workers/WXLOW1_REGISTRATION.md) adds the same for the daily LOW: the ensemble `temperature_2m_min` members (in the SAME ensemble call), the NWS night temperature (from the same
forecast body), the quotes of the KXLOWT event, its result and the IEM `min_tmpf`, in tables named `<table>_low` beside the highs. The highs tables and columns are unchanged.

Public GET endpoints only: no key, no signing, no account, no order, no environment variable. A run is idempotent: output files are named for the UTC hour slot they fall in, so
a re-run of the same hour overwrites the same file; results, events and observations are written once per key. The server's Date header is kept on every row.
Cities and models come from kalshi-scalper/workers/WXENS1_WATCHLIST.json; this script names no ticker of its own."""
import argparse
import csv
import glob
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

KALSHI = "https://external-api.kalshi.com/trade-api/v2"
OPENMETEO = "https://ensemble-api.open-meteo.com/v1/ensemble"
NWS = "https://api.weather.gov"
IEM = "https://mesonet.agron.iastate.edu/api/1/daily.json"
UA = {"User-Agent": "shwoopnet-research-recorder", "Accept": "application/json"}
GAP_S = 0.5
MAX_PAGES = 4
ROOT = "wxens"

COLS = {
    "ens": ["slot_ts", "poll_ts", "server_date_header", "city", "look", "target_date", "model", "member_key", "tmax_f"],
    "nws": ["slot_ts", "poll_ts", "server_date_header", "city", "look", "target_date", "nws_high_f", "period_start", "period_name", "grid"],
    "quotes": ["slot_ts", "poll_ts", "server_date_header", "city", "look", "target_date", "series", "ticker", "event_ticker", "close_time", "strike_type", "floor_strike",
               "cap_strike", "yes_bid", "yes_ask", "last", "volume", "status"],
    "events": ["event_ticker", "city", "series", "target_date", "close_time", "rules_primary", "seen_ts"],
    "results": ["ticker", "event_ticker", "city", "target_date", "result", "expiration_value", "close_time", "seen_ts"],
    "obs": ["city", "target_date", "station", "iem_max_tmpf", "seen_ts"],
    "runs": ["slot_ts", "poll_ts", "server_date_header", "clock_skew_s", "cities_due", "calls", "n429", "n_errors", "ens_rows", "nws_rows", "quote_rows", "result_rows", "obs_rows"],
}

# WXLOW1: the same tables for the daily low, named with a _low suffix (the highs files are never touched)
COLS["ens_low"] = [c if c != "tmax_f" else "tmin_f" for c in COLS["ens"]]
COLS["nws_low"] = ["slot_ts", "poll_ts", "server_date_header", "city", "look", "target_date", "nws_low_f", "role", "period_start", "period_name", "grid"]
COLS["quotes_low"] = COLS["quotes"]
COLS["events_low"] = COLS["events"]
COLS["results_low"] = COLS["results"]
COLS["obs_low"] = ["city", "target_date", "station", "iem_min_tmpf", "seen_ts"]
COLS["runs"] = COLS["runs"] + ["ens_low_rows", "nws_low_rows", "quote_low_rows", "result_low_rows", "obs_low_rows"]
LOW_TABLES = ("ens_low", "nws_low", "quotes_low", "events_low", "results_low", "obs_low")

_sleep = time.sleep      # replaced in tests


def http_get(url):
    """(status, decoded json or None, Date header). Never raises."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def parse_iso(s):
    try:
        return int(time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))) - time.timezone
    except Exception:
        return None


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


def slot_of(now):
    return int(now - now % 3600)


def local_std(now, off_h):
    """The city's local STANDARD time (never daylight time) as a naive datetime."""
    return datetime.fromtimestamp(now, timezone.utc).replace(tzinfo=None) + timedelta(hours=off_h)


def look_label(hour, due_hours):
    """The registered look for a local standard hour, or None. 07..09 is the 07:00 look, 10..11 the 10:00 look (the wider window is for a manual run)."""
    if hour not in due_hours:
        return None
    return "07" if hour < 10 else "10"


def due_targets(city, now, due_hours):
    """[(look, target_date iso)] for this city now. The 07:00 look records the settlement day (lead 0) and the day after (lead 1); the 10:00 look records the day after only."""
    t = local_std(now, city["std_offset_h"])
    lab = look_label(t.hour, due_hours)
    if lab is None:
        return []
    leads = [0, 1] if lab == "07" else [1]
    return [("L%d_%s" % (ld, lab), (t.date() + timedelta(days=ld)).isoformat()) for ld in leads]


def event_date(event_ticker):
    """KXHIGHNY-26NOV04 -> 2026-11-04, or None."""
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)$", event_ticker or "")
    if not m:
        return None
    try:
        return datetime.strptime("20%s%s%s" % (m.group(1), m.group(2), m.group(3)), "%Y%b%d").date().isoformat()
    except ValueError:
        return None


def parse_ensemble(obj, dates, var="temperature_2m_max"):
    """Open-Meteo ensemble body for ONE location -> [(model, member_key, target_date, tmax_f)]. Any daily key that starts with temperature_2m_max is a member or the control;
    the model is the key with its 'memberNN' part and the variable prefix removed (a bare key is kept only when it is the only one). Dates not in `dates` and null values are dropped."""
    out = []
    daily = (obj or {}).get("daily") or {}
    days = daily.get("time") or []
    for key, vals in daily.items():
        if not key.startswith(var) or not isinstance(vals, list):
            continue
        model = re.sub(r"_?member\d+", "", key)[len(var):].lstrip("_") or "single"
        for d, v in zip(days, vals):
            if d in dates and num(v) is not None:
                out.append((model, key, d, float(v)))
    if any(m != "single" for m, _, _, _ in out):
        out = [r for r in out if r[0] != "single"]      # a bare key beside suffixed models cannot be assigned to a model
    return out


def parse_nws(body, date):
    """NWS forecast body -> (high_f, period_start, period_name) of the daytime period that starts on `date`, or None."""
    for p in ((body or {}).get("properties") or {}).get("periods") or []:
        if p.get("isDaytime") and str(p.get("startTime", ""))[:10] == date and num(p.get("temperature")) is not None:
            return float(p["temperature"]), p.get("startTime"), p.get("name")
    return None


def parse_nws_low(body, date):
    """NWS forecast body -> [(low_f, role, period_start, period_name)] for the NIGHT periods (isDaytime false) that touch the calendar day `date`: role 'prior' = the night that starts the evening
    before `date` (it ends on the morning of `date`, where the day's low usually falls), role 'same' = the night that starts on `date` (it can hold a late cold front). One of each at most."""
    prev = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).date().isoformat()
    out = {}
    for p in ((body or {}).get("properties") or {}).get("periods") or []:
        if p.get("isDaytime") is not False or num(p.get("temperature")) is None:
            continue
        d0 = str(p.get("startTime", ""))[:10]
        role = "prior" if d0 == prev else "same" if d0 == date else None
        if role and role not in out:
            out[role] = (float(p["temperature"]), role, p.get("startTime"), p.get("name"))
    return [out[r] for r in ("prior", "same") if r in out]


def quote_row(slot, ts, hdr, city, look, date, series, m):
    return [slot, ts, hdr, city, look, date, series, m.get("ticker"), m.get("event_ticker"), m.get("close_time"), m.get("strike_type"), first(m, "floor_strike"),
            first(m, "cap_strike"), first(m, "yes_bid_dollars", "yes_bid"), first(m, "yes_ask_dollars", "yes_ask"), first(m, "last_price_dollars", "last_price"),
            first(m, "volume_fp", "volume"), m.get("status")]


def list_markets(series, status, extra=""):
    """All pages of a market listing: (markets, calls, n429, error, date header)."""
    out, cursor, calls, n429, date = [], "", 0, 0, ""
    for _ in range(MAX_PAGES):
        url = "%s/markets?series_ticker=%s&status=%s&limit=1000%s%s" % (KALSHI, series, status, extra, ("&cursor=" + cursor) if cursor else "")
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


def load_watchlist(path):
    return json.load(open(path))


def known(data_dir, table, col):
    seen = set()
    for p in glob.glob(os.path.join(data_dir, ROOT, table, "**", "*.csv.gz"), recursive=True):
        try:
            with gzip.open(p, "rt", newline="") as f:
                for row in csv.DictReader(f):
                    seen.add(row[col] if isinstance(col, str) else tuple(row[c] for c in col))
        except Exception:
            pass
    return seen


def write_gz(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def run(watchlist, data_dir, now=None, due_hours=None, results=None, only=None, kinds=("high", "low"), redo=False):
    """One snapshot. Returns the run summary row. `due_hours` defaults to the watchlist's (7, 10); `results` True/False forces the results step, None = UTC hours 01, 07, 13, 19.
    `kinds` ("high", "low"): the WXLOW1 lows ride in the same ensemble call and the same NWS forecast body as the highs, so they add one Kalshi listing per due city and no other request."""
    now = time.time() if now is None else now
    w = load_watchlist(watchlist)
    due_hours = set(due_hours or w.get("due_local_hours") or (7, 10))
    models = w["ensemble_models"]
    want_low = "low" in kinds
    slot = slot_of(now)
    day, hh = time.strftime("%Y-%m-%d", time.gmtime(slot)), time.strftime("%H", time.gmtime(slot))
    ts = int(now)
    cities = [c for c in w["cities"] if only is None or c["key"] in only]
    plan = [(c, due_targets(c, now, due_hours)) for c in cities]
    plan = [(c, t) for c, t in plan if t]
    # Already-done guard (RECPATCH1): the workflow has a second start 30 minutes after the first. One run records every due city of the UTC hour, so if this hour's
    # snapshot files are already on the branch a second run must not overwrite them (the reader wants the FIRST poll at or after the look). It logs a row with no due city.
    if plan and not redo and any(os.path.exists(os.path.join(data_dir, ROOT, n, day, hh + ".csv.gz")) for n in ("ens", "quotes")):
        plan = []
    t = {k: [] for k in COLS}
    calls = n429 = errs = 0
    hdr0 = ""

    # 1. ensemble: one batched call for every due city (daily maximum and, for WXLOW1, daily minimum)
    if plan:
        url = "%s?latitude=%s&longitude=%s&daily=%s&models=%s&temperature_unit=fahrenheit&timezone=auto&forecast_days=3" % (
            OPENMETEO, ",".join(str(c["lat"]) for c, _ in plan), ",".join(str(c["lon"]) for c, _ in plan),
            "temperature_2m_max,temperature_2m_min" if want_low else "temperature_2m_max", ",".join(models))
        st, body, hdr = http_get(url)
        calls += 1
        hdr0 = hdr or hdr0
        if st == 429:
            n429 += 1
        if st != 200 or body is None:
            errs += 1
        else:
            locs = body if isinstance(body, list) else [body]
            for (c, tg), loc in zip(plan, locs):
                dates = {d for _, d in tg}
                rows = parse_ensemble(loc, dates)
                lrows = parse_ensemble(loc, dates, "temperature_2m_min") if want_low and c.get("low_series") else []
                for look, d in tg:
                    for model, key, dd, v in rows:
                        if dd == d:
                            t["ens"].append([slot, ts, hdr, c["key"], look, d, model, key, v])
                    for model, key, dd, v in lrows:
                        if dd == d:
                            t["ens_low"].append([slot, ts, hdr, c["key"], look, d, model, key, v])

    # 2. NWS point forecast and 3. Kalshi quotes, per due city
    seen_events = known(data_dir, "events", "event_ticker")
    seen_events_low = known(data_dir, "events_low", "event_ticker")
    for c, tg in plan:
        dates = {d for _, d in tg}
        st, pts, hdr = http_get("%s/points/%s,%s" % (NWS, c["lat"], c["lon"]))
        calls += 1
        hdr0 = hdr or hdr0
        furl = ((pts or {}).get("properties") or {}).get("forecast") if st == 200 else None
        if furl and furl.startswith(NWS + "/"):
            st2, fb, hdr = http_get(furl)
            calls += 1
            if st2 == 200:
                grid = "%s/%s,%s" % (pts["properties"].get("gridId"), pts["properties"].get("gridX"), pts["properties"].get("gridY"))
                for look, d in tg:
                    r = parse_nws(fb, d)
                    if r:
                        t["nws"].append([slot, ts, hdr, c["key"], look, d, r[0], r[1], r[2], grid])
                    if want_low and c.get("low_series"):
                        for lf, role, ps, pn in parse_nws_low(fb, d):
                            t["nws_low"].append([slot, ts, hdr, c["key"], look, d, lf, role, ps, pn, grid])
            else:
                errs += 1
                n429 += 1 if st2 == 429 else 0
        else:
            errs += 1
            n429 += 1 if st == 429 else 0
        _sleep(GAP_S)
        jobs = [(c["series"], "quotes", "events", seen_events)]
        if want_low and c.get("low_series"):
            jobs.append((c["low_series"], "quotes_low", "events_low", seen_events_low))
        for series, qtab, etab, seen in jobs:
            ms, n, x, bad, hdr = list_markets(series, "open")
            calls, n429, errs, hdr0 = calls + n, n429 + x, errs + (1 if bad else 0), hdr or hdr0
            for m in ms:
                d = event_date(m.get("event_ticker"))
                if d not in dates:
                    continue
                for look, dd in tg:
                    if dd == d:
                        t[qtab].append(quote_row(slot, ts, hdr, c["key"], look, d, series, m))
                if m.get("event_ticker") not in seen:
                    seen.add(m["event_ticker"])
                    t[etab].append([m["event_ticker"], c["key"], series, d, m.get("close_time"), (m.get("rules_primary") or "")[:500], ts])
            _sleep(GAP_S)

    # 4. results and observed extremes, every 6 hours, for every city (not only the due ones)
    do_results = results if results is not None else (time.gmtime(slot).tm_hour % 6 == 1)
    if do_results:
        lo = int(now - 4 * 86400)
        kind_specs = [("results", "obs", "series", "max_tmpf")]
        if want_low:
            kind_specs.append(("results_low", "obs_low", "low_series", "min_tmpf"))
        for rtab, otab, skey, field in kind_specs:
            seen_res = known(data_dir, rtab, "ticker")
            seen_obs = known(data_dir, otab, ("city", "target_date"))
            for c in cities:
                if not c.get(skey):
                    continue
                sm, n, x, bad, hdr = list_markets(c[skey], "settled", "&min_close_ts=%d" % lo)
                calls, n429, errs = calls + n, n429 + x, errs + (1 if bad else 0)
                days = set()
                for m in sm:
                    if m.get("ticker") in seen_res or m.get("result") not in ("yes", "no"):
                        continue
                    seen_res.add(m["ticker"])
                    d = event_date(m.get("event_ticker"))
                    days.add(d)
                    t[rtab].append([m["ticker"], m.get("event_ticker"), c["key"], d, m.get("result"), first(m, "expiration_value"), m.get("close_time"), ts])
                for d in sorted(x for x in days if x):
                    if (c["key"], d) in seen_obs:
                        continue
                    st, body, hdr = http_get("%s?station=%s&network=%s&date=%s" % (IEM, c["iem_station"], c["iem_network"], d))
                    calls += 1
                    v = None
                    if st == 200 and isinstance(body, dict):
                        rows = body.get("data") or []
                        v = num(rows[0].get(field)) if rows else None
                    if v is None:
                        errs += 1
                    else:
                        seen_obs.add((c["key"], d))
                        t[otab].append([c["key"], d, c["station"], v, ts])

    for name in ("ens", "nws", "quotes", "events", "results", "obs") + LOW_TABLES:
        if t[name]:
            write_gz(os.path.join(data_dir, ROOT, name, day, hh + ".csv.gz"), COLS[name], t[name])
    skew = ""
    if hdr0:
        try:
            from email.utils import parsedate_to_datetime
            skew = round(now - parsedate_to_datetime(hdr0).timestamp(), 1)
        except Exception:
            skew = ""
    summary = [slot, ts, hdr0, skew, len(plan), calls, n429, errs, len(t["ens"]), len(t["nws"]), len(t["quotes"]), len(t["results"]), len(t["obs"]),
               len(t["ens_low"]), len(t["nws_low"]), len(t["quotes_low"]), len(t["results_low"]), len(t["obs_low"])]
    runs = os.path.join(data_dir, ROOT, "runs", day + ".csv")
    os.makedirs(os.path.dirname(runs), exist_ok=True)
    new = not os.path.exists(runs)
    with open(runs, "a", newline="") as f:
        wr = csv.writer(f)
        if new:
            wr.writerow(COLS["runs"])
        wr.writerow(summary)
    return summary


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", help="the checked out quote-data branch; files go under wxens/")
    ap.add_argument("--watchlist", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kalshi-scalper", "workers", "WXENS1_WATCHLIST.json"))
    ap.add_argument("--wide", action="store_true", help="manual run: accept local hours 7,8,10,11 as the 07:00 and 10:00 looks")
    ap.add_argument("--results", action="store_true", help="force the results step")
    ap.add_argument("--redo", action="store_true", help="record the hour again even if its files already exist (overwrites them)")
    ap.add_argument("--highs-only", action="store_true", help="skip the WXLOW1 daily low tables")
    a = ap.parse_args(argv)
    print(run(a.watchlist, a.data_dir, due_hours=(7, 8, 10, 11) if a.wide else None, results=True if a.results else None, kinds=("high",) if a.highs_only else ("high", "low"), redo=a.redo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
