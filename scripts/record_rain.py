#!/usr/bin/env python3
"""Recorder RAINCAL (Oct 31, 2026, the owner approved the research session's RAINCAL proposal; the registration is kalshi-scalper/workers/RAINCAL_REGISTRATION.md on the research
branch). Research data only: nothing here trades, signs or sends an order.

What it records. Kalshi's daily rain series KXRAIN has one binary market per US city per day ("Will it rain in <city> on <date>?", total precipitation at the NWS climate
station strictly above 0 inches, a trace counts as 0). The market day is midnight to midnight local STANDARD time, so a market closes at 05:00Z (Eastern), 06:00Z (Central),
07:00Z (Mountain, Phoenix) or 08:00Z (Pacific) and its day is [close_time - 24 h, close_time). For every open market whose local standard time is between 6:00 and 8:00 AM
(close_time - 18 h to close_time - 16 h) each pass writes:
  - quotes.csv:   the market's yes bid / ask / sizes, status, last price, volume and open interest, from ONE public list read of the whole series;
  - pop.csv:      the NWS gridpoint probability of precipitation, EVERY period that overlaps the market day, with the forecast's updateTime and generatedAt so a reader can
                  prove no look-ahead (the registered PoP_day = the max of the periods that end after the 7:00 AM look is computed in the analysis, not here);
  - obs.csv:      the station's latest observation (information only, never used by the rule);
  - coverage.csv: one row per pass (requests, 429s and 503s, failures, markets in window), so a missed city or day is counted, not silent.
A separate results pass (--results) copies the last few days of settled KXRAIN markets (result, close time, expiration value) into results.csv. The analysis also reads Kalshi's
public settled markets itself; the public API is the record, this copy is a convenience.

It reads PUBLIC endpoints only: Kalshi's public market data and api.weather.gov. No key, no secret, no signing, no POST, no order, no account path. api.weather.gov requires a
descriptive User-Agent header: that identifies the program, it is NOT an authentication header and carries no credential.

Politeness. Two request streams, each one call at a time (Kalshi at least 1.0 s apart, the NWS at least 1.5 s apart). Every request goes through Stream.get: a 429 or 503 (or a
dropped connection) waits 2 s, doubling up to 30 s, tried at most 4 times, then the read is marked failed and the job goes on. A failed request never fails the job.

It stops by itself: nothing is recorded from END_UTC (2026-12-31 23:59 UTC); the results pass runs until RESULTS_END_UTC (2027-01-03 23:59 UTC) so the last days settle. Stop it
sooner by deleting the workflow.

Rows are written as the exchange returns them (prices as numbers, a missing value empty, never zero)."""
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

KALSHI = "https://external-api.kalshi.com/trade-api/v2"
NWS = "https://api.weather.gov"
SERIES = "KXRAIN"
END_UTC = "2026-12-31T23:59:00Z"            # nothing is recorded from here on
RESULTS_END_UTC = "2027-01-03T23:59:00Z"    # the results pass runs a little longer so the last market days settle
LOOK_BEFORE_CLOSE_S = 17 * 3600             # 7:00 AM local standard time
WINDOW_FROM_CLOSE_S = 18 * 3600             # polls from 6:00 AM ...
WINDOW_TO_CLOSE_S = 16 * 3600               # ... to 8:00 AM local standard time
DAY_S = 24 * 3600
KALSHI_GAP_S = 1.0
NWS_GAP_S = 1.5
BACKOFF_S = 2.0
BACKOFF_MAX_S = 30.0
MAX_TRIES = 4
RESULTS_DAYS = 4
JOB_BUDGET_S = 20 * 60                      # a pass that is still running after this long stops asking for more cities

# City suffix -> (station identifier used for the NWS lookup, latitude, longitude, NWS office, grid x, grid y). The station behind each market's CLI code (CLIORD is O'Hare, CLIDFW
# is Dallas/Fort Worth, ...). The grid cell is what api.weather.gov/points returned for the station on 2026-10-31; a gridpoint that stops answering is logged, not guessed.
# WPB: the rule's code CLIDJT is not an airport identifier; Palm Beach International is ASSUMED and its coordinates are fixed by hand (flagged in the registration).
CITIES = {
    "ABQ": ("KABQ", 35.04167, -106.61472, "ABQ", 99, 119),
    "ATL": ("KATL", 33.64028, -84.42694, "FFC", 50, 82),
    "AUS": ("KAUS", 30.18304, -97.67987, "EWX", 158, 87),
    "BOS": ("KBOS", 42.36056, -71.01056, "BOX", 73, 101),
    "CHI": ("KORD", 41.97972, -87.90444, "LOT", 66, 77),
    "CLL": ("KCLL", 30.58222, -96.36167, "HGX", 25, 131),
    "CMH": ("KCMH", 39.9907, -82.87691, "ILN", 89, 83),
    "DAL": ("KDFW", 32.89743, -97.02196, "FWD", 81, 109),
    "DC": ("KDCA", 38.84833, -77.03417, "LWX", 97, 69),
    "DEN": ("KDEN", 39.84658, -104.65622, "BOU", 75, 66),
    "DTW": ("KDTW", 42.23139, -83.33083, "DTX", 57, 28),
    "EWR": ("KEWR", 40.6825, -74.16944, "OKX", 28, 40),
    "HOU": ("KHOU", 29.6375, -95.2825, "HGX", 66, 89),
    "IND": ("KIND", 39.72518, -86.2816, "IND", 54, 67),
    "LAX": ("KLAX", 33.93806, -118.38889, "LOX", 149, 41),
    "LEX": ("KLEX", 38.0339, -84.61146, "LMK", 91, 71),
    "LV": ("KLAS", 36.07188, -115.1634, "VEF", 121, 94),
    "MIA": ("KMIA", 25.79056, -80.31639, "MFL", 105, 51),
    "MIN": ("KMSP", 44.88306, -93.22889, "MPX", 110, 68),
    "MKE": ("KMKE", 42.955, -87.90444, "MKX", 89, 61),
    "NOLA": ("KMSY", 29.99278, -90.25083, "LIX", 61, 90),
    "NYC": ("KNYC", 40.78333, -73.96667, "OKX", 34, 45),
    "OKC": ("KOKC", 35.38861, -97.60028, "OUN", 94, 90),
    "PHIL": ("KPHL", 39.87327, -75.22678, "PHI", 48, 75),
    "PHX": ("KPHX", 33.427799, -112.003465, "PSR", 161, 57),
    "PIT": ("KPIT", 40.4846, -80.21447, "PBZ", 70, 67),
    "PVD": ("KPVD", 41.72233, -71.42772, "BOX", 64, 70),
    "SATX": ("KSAT", 29.53278, -98.46361, "EWX", 128, 59),
    "SEA": ("KSEA", 47.44472, -122.31361, "SEW", 124, 60),
    "SFO": ("KSFO", 37.61961, -122.36558, "MTR", 85, 98),
    "SGF": ("KSGF", 37.23972, -93.38972, "SGF", 63, 36),
    "STL": ("KSTL", 38.7525, -90.37361, "LSX", 89, 80),
    "TPA": ("KTPA", 27.96139, -82.54028, "TBW", 68, 98),
    "TTN": ("KTTN", 40.27639, -74.81639, "PHI", 60, 95),
    "WPB": ("KPBI", 26.6832, -80.0956, "MFL", 109, 91),
}

QUOTE_COLS = ["t_recv_ms", "server_date_header", "ticker", "city", "event_ticker", "close_time", "min_from_look", "status", "yes_bid", "yes_ask", "yes_bid_size", "yes_ask_size",
              "last_price", "volume", "open_interest"]
POP_COLS = ["t_fetch_ms", "ticker", "city", "station", "grid", "nws_update_time", "nws_generated_at", "nws_valid_times", "valid_start", "valid_end", "pop_percent"]
OBS_COLS = ["t_fetch_ms", "ticker", "city", "station", "obs_time", "precip_last_hour_mm", "text", "http"]
COVER_COLS = ["t_start_ms", "t_end_ms", "markets_listed", "markets_in_window", "cities_in_window", "kalshi_requests", "nws_requests", "n429", "n503", "n_other_fail",
              "quote_rows", "pop_rows", "obs_rows", "nws_gridpoint_fail", "note"]
RESULT_COLS = ["t_fetch_ms", "ticker", "city", "event_ticker", "close_time", "status", "result", "expiration_value", "volume"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)
RESULTS_END_EPOCH = epoch_of(RESULTS_END_UTC)


def past_end(now):
    return now >= END_EPOCH


def results_past_end(now):
    return now >= RESULTS_END_EPOCH


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def user_agent():
    repo = os.environ.get("GITHUB_REPOSITORY", "shwoopnet")
    # api.weather.gov asks for a descriptive User-Agent. It identifies this program; it is not a credential.
    return "shwoopnet-research-recorder (research only, no key; https://github.com/%s)" % repo


def rate_budget():
    """Requests a minute from the constants: the Kalshi stream is one list read per pass (plus a results read); the NWS stream is a gridpoint read and an observation read per
    city in its window. A pass handles the cities whose 2 hour window is open, at most 35 at once (they are spread over four time zones, so about 10)."""
    return {"streams": 2, "kalshi_peak_per_min": 60.0 / KALSHI_GAP_S, "nws_peak_per_min": 60.0 / NWS_GAP_S, "kalshi_per_pass": 1, "nws_per_city_per_pass": 2}


def http_get(url, headers):
    """(status, decoded json or None, Date header or ''). Never raises: a failed read is a status, so one bad second cannot end the run."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


class Stream:
    """One request stream: one call at a time, at least `gap_s` between calls. EVERY request in this file goes through `get`. A 429, a 503 or a failed connection (status 0) waits
    BACKOFF_S, doubling up to BACKOFF_MAX_S, and is asked again up to MAX_TRIES times in all; then the status is returned and the caller marks the read failed. `fetch` is the
    transport (url -> (status, body, date)); tests pass a fake one with a fake clock and sleep."""

    def __init__(self, gap_s, headers, fetch=None, clock=time.time, sleep=time.sleep):
        assert gap_s >= 1.0
        self.gap_s, self.headers, self.clock, self.sleep = gap_s, headers, clock, sleep
        self.fetch = fetch or (lambda url: http_get(url, headers))
        self.next_ok = 0.0
        self.requests = self.n429 = self.n503 = self.n_other = 0

    def get(self, url):
        wait = BACKOFF_S
        st, body, date = 0, None, ""
        for attempt in range(MAX_TRIES):
            gap = self.next_ok - self.clock()
            if gap > 0:
                self.sleep(gap)
            st, body, date = self.fetch(url)
            self.requests += 1
            self.next_ok = self.clock() + self.gap_s
            if st in (429, 503) or st == 0:
                if st == 429:
                    self.n429 += 1
                elif st == 503:
                    self.n503 += 1
                else:
                    self.n_other += 1
                if attempt + 1 < MAX_TRIES:
                    self.sleep(wait)
                    self.next_ok = max(self.next_ok, self.clock())
                    wait = min(BACKOFF_MAX_S, wait * 2)
                continue
            if st != 200:
                self.n_other += 1
            return st, body, date
        return st, None, date


def city_of(ticker):
    """The city suffix of a KXRAIN ticker (KXRAIN-26NOV01-WPB -> WPB), or None."""
    parts = (ticker or "").split("-")
    return parts[2] if len(parts) == 3 and parts[0] == SERIES else None


def in_window(close_epoch, now):
    """True while local standard time is 6:00 to 8:00 AM of the market day that closes at close_epoch."""
    return close_epoch - WINDOW_FROM_CLOSE_S <= now <= close_epoch - WINDOW_TO_CLOSE_S


def min_from_look(close_epoch, now):
    """Minutes since the 7:00 AM look (negative before it)."""
    return round((now - (close_epoch - LOOK_BEFORE_CLOSE_S)) / 60.0, 1)


_DUR = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$")


def duration_s(text):
    """Seconds in an ISO 8601 duration such as PT6H, P3DT23H or P7DT12H. None if it is not one of those shapes."""
    m = _DUR.match(text or "")
    if not m or not any(m.groups()):
        return None
    d, h, mi = (int(g) if g else 0 for g in m.groups())
    return d * 86400 + h * 3600 + mi * 60


def parse_valid_time(vt):
    """'2026-11-04T12:00:00+00:00/PT6H' -> (start epoch, end epoch), or None."""
    try:
        start_s, dur_s = vt.split("/")
        start = calendar.timegm(time.strptime(start_s[:19], "%Y-%m-%dT%H:%M:%S"))
        off = start_s[19:]
        if off and off not in ("Z", "+00:00"):
            return None                      # NWS gridpoint times are UTC; anything else is not guessed at
        d = duration_s(dur_s)
        return (start, start + d) if d else None
    except Exception:
        return None


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def pop_rows(t_fetch_ms, ticker, city, station, grid, props, close_epoch):
    """One row per PoP period that overlaps the market day [close - 24 h, close). The forecast's updateTime, generatedAt and validTimes ride on every row. Nothing is computed
    (the registered PoP_day is the max over the periods that end after the look, taken in the analysis). Returns [] when the answer has no PoP series."""
    pp = (props or {}).get("probabilityOfPrecipitation") or {}
    rows = []
    day_start = close_epoch - DAY_S
    for v in pp.get("values") or []:
        if not isinstance(v, dict):
            continue
        span = parse_valid_time(v.get("validTime"))
        if not span or span[1] <= day_start or span[0] >= close_epoch:
            continue
        val = v.get("value")
        rows.append([t_fetch_ms, ticker, city, station, grid, props.get("updateTime", ""), props.get("generatedAt", ""), props.get("validTimes", ""), iso(span[0]), iso(span[1]),
                     "" if val is None else val])
    return rows


def quote_row(t_recv_ms, date_header, market, now):
    """One CSV row from one KXRAIN market object. Missing numbers are empty, never zero."""
    close = epoch_of(market["close_time"]) if market.get("close_time") else None
    return [t_recv_ms, date_header, market.get("ticker"), city_of(market.get("ticker")), market.get("event_ticker"), market.get("close_time"),
            "" if close is None else min_from_look(close, now), market.get("status"), num(market.get("yes_bid_dollars")), num(market.get("yes_ask_dollars")),
            num(market.get("yes_bid_size_fp")), num(market.get("yes_ask_size_fp")), num(market.get("last_price_dollars")), num(market.get("volume_fp")),
            num(market.get("open_interest_fp"))]


def obs_row(t_fetch_ms, ticker, city, station, status, body):
    props = (body or {}).get("properties") or {}
    pl = props.get("precipitationLastHour") or {}
    return [t_fetch_ms, ticker, city, station, props.get("timestamp", ""), "" if pl.get("value") is None else pl.get("value"), props.get("textDescription", ""), status]


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        for name, cols in (("quotes", QUOTE_COLS), ("pop", POP_COLS), ("obs", OBS_COLS), ("coverage", COVER_COLS), ("results", RESULT_COLS)):
            f = open(os.path.join(d, name + ".csv"), "a", newline="")
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(cols)
            self.files.append(f)
            self.w[name] = w

    def write(self, name, rows):
        self.w[name].writerows(rows)

    def close(self):
        for f in self.files:
            f.flush()
            f.close()


def list_markets(kalshi, status, extra=""):
    """All markets of the series with the given status, following the cursor until it is empty. Returns (markets, date_header, ok)."""
    out, cursor, date = [], "", ""
    for _ in range(20):
        url = "%s/markets?series_ticker=%s&status=%s&limit=1000%s%s" % (KALSHI, SERIES, status, extra, ("&cursor=" + cursor) if cursor else "")
        st, body, d = kalshi.get(url)
        if st != 200 or not isinstance(body, dict):
            return out, date, False
        date = d or date
        out.extend(m for m in body.get("markets") or [] if isinstance(m, dict) and m.get("ticker"))
        cursor = body.get("cursor") or ""
        if not cursor:
            return out, date, True
    return out, date, False


def run_pass(kalshi, nws, out, now=None, deadline=None):
    """One pass: list the open markets once, then for every city whose 6:00 to 8:00 AM window is open read its forecast and observation. Never raises."""
    t0 = int(time.time() * 1000)
    now = time.time() if now is None else now
    cov = {"listed": 0, "in_win": 0, "cities": 0, "quotes": 0, "pops": 0, "obs": 0, "gridfail": 0, "note": []}
    k0, n0 = kalshi.requests, nws.requests
    markets, date, ok = list_markets(kalshi, "open")
    t_recv = int(time.time() * 1000)
    if not ok:
        cov["note"].append("market list incomplete")
    cov["listed"] = len(markets)
    wanted = []
    for m in markets:
        try:
            close = epoch_of(m["close_time"])
        except Exception:
            continue
        if city_of(m.get("ticker")) in CITIES and in_window(close, now):
            wanted.append((m, close))
    cov["in_win"] = len(wanted)
    out.write("quotes", [quote_row(t_recv, date, m, now) for m, _c in wanted])
    cov["quotes"] = len(wanted)
    cov["cities"] = len({city_of(m["ticker"]) for m, _c in wanted})
    for m, close in sorted(wanted, key=lambda x: x[0]["ticker"]):
        if deadline is not None and time.time() > deadline:
            cov["note"].append("out of time")
            break
        ticker, city = m["ticker"], city_of(m["ticker"])
        station, lat, lon, wfo, gx, gy = CITIES[city]
        grid = "%s/%d,%d" % (wfo, gx, gy)
        st, body, _d = nws.get("%s/gridpoints/%s" % (NWS, grid))
        t_fetch = int(time.time() * 1000)
        props = body.get("properties") if st == 200 and isinstance(body, dict) else None
        rows = pop_rows(t_fetch, ticker, city, station, grid, props, close) if props else []
        if not rows:
            cov["gridfail"] += 1
        out.write("pop", rows)
        cov["pops"] += len(rows)
        st2, body2, _d2 = nws.get("%s/stations/%s/observations/latest" % (NWS, station))
        out.write("obs", [obs_row(int(time.time() * 1000), ticker, city, station, st2, body2 if st2 == 200 else None)])
        cov["obs"] += 1
    out.write("coverage", [[t0, int(time.time() * 1000), cov["listed"], cov["in_win"], cov["cities"], kalshi.requests - k0, nws.requests - n0, kalshi.n429 + nws.n429,
                            kalshi.n503 + nws.n503, kalshi.n_other + nws.n_other, cov["quotes"], cov["pops"], cov["obs"], cov["gridfail"], ";".join(cov["note"])]])
    return cov


def run_results(kalshi, out, now=None):
    """Copy the settled KXRAIN markets of the last RESULTS_DAYS days into results.csv (duplicates across days are for the analysis to drop). Never raises."""
    now = time.time() if now is None else now
    markets, _d, ok = list_markets(kalshi, "settled", "&min_close_ts=%d" % int(now - RESULTS_DAYS * DAY_S))
    t = int(time.time() * 1000)
    out.write("results", [[t, m.get("ticker"), city_of(m.get("ticker")), m.get("event_ticker"), m.get("close_time"), m.get("status"), m.get("result"), m.get("expiration_value"),
                           num(m.get("volume_fp"))] for m in markets])
    return len(markets), ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--results", action="store_true", help="also copy the last days' settled markets")
    args = ap.parse_args(argv)
    now = time.time()
    if results_past_end(now):
        print("past the results end date (%s): nothing to do" % RESULTS_END_UTC)
        return 0
    out = Out(args.outdir)
    try:
        kalshi = Stream(KALSHI_GAP_S, {"User-Agent": user_agent()})
        nws = Stream(NWS_GAP_S, {"User-Agent": user_agent(), "Accept": "application/geo+json"})
        if past_end(now):
            print("past the end date (%s): no quotes recorded" % END_UTC)
        else:
            cov = run_pass(kalshi, nws, out, now, deadline=time.time() + JOB_BUDGET_S)
            print("pass: %s" % json.dumps({k: v for k, v in cov.items() if k != "note"}), cov["note"])
        if args.results:
            print("results: %s" % (run_results(kalshi, out, now),))
        print("requests: kalshi %d nws %d (429: %d, 503: %d, other: %d)" % (kalshi.requests, nws.requests, kalshi.n429 + nws.n429, kalshi.n503 + nws.n503, kalshi.n_other + nws.n_other))
    except Exception as e:          # a recorder that fails loudly loses a day; this one writes what it has and exits 0
        print("recorder error (ignored): %s" % type(e).__name__)
    finally:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
