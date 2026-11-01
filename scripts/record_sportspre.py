#!/usr/bin/env python3
"""Recorder for SPORTS-PRE (Oct 31, 2026, the owner approved; registration: kalshi-scalper/workers/SPORTSPRE_REGISTRATION.md on the research branch). Research only.

Question it feeds: is the Kalshi pre-game moneyline (KXNFLGAME, KXNCAAFGAME, KXNBAGAME, KXMLBGAME) wrong where ESPN's PRE-GAME win probability (BPI/FPI) can see it? ESPN's summary `predictor`
exists only before the start and is removed afterwards, so it cannot be downloaded later: it has to be recorded forward, with the recorder's own receive time, so that look-ahead can be audited.

What it does, on PUBLIC keyless endpoints only (Kalshi public market data; ESPN public JSON). No key, no secret, no auth header, no order, no write call:
  1. every 15 minutes reads ESPN's scoreboards (today and the next ET day) for the four leagues: the schedule, the ESPN start time and the teams.
  2. for each game that has not started and starts 120 down to 30 minutes from now, every 5 minutes: ONE bulk read of each series' open Kalshi markets (both team markets of the game: yes bid, ask,
     sizes, status, with the server Date header), and from ESPN the core `.../predictor` response RAW and the summary's `predictor` block, each with the recorder's receive time.
  3. results, later: for games that were tracked and have ended, Kalshi `result` of both team markets (public GET /markets/{ticker}), ESPN's final status and score, and the core predictor
     read again after the game (to audit whether ESPN changes it after the start).
Games that start on or after STOP_TRACK_ISO are not tracked; the script exits at STOP_ALL_ISO. Requests: every one goes through http_get (pacing, backoff on 429 and 5xx, never raises).

Requests per minute (disclosed, see also the workflow header): Kalshi at most about 1 bulk read per series per 5 minutes while games are in the window (4 series, usually 1 to 3 pages each), plus up to 12
result reads per 10 minutes: about 2 a minute at the peak. ESPN: 2 per tracked game per 5 minutes (a college football Saturday has up to about 25 games in a 90 minute window: about 10 a minute), plus
the schedule (10 reads per 15 minutes) and results (3 per game once): about 12 a minute at the peak, under 2 a minute on an ordinary evening. Hard floor between requests: 1.0 s Kalshi, 0.4 s ESPN.

Files per job (out_dir): games.csv, quotes.csv, predictor.csv, espn_raw.jsonl, results.csv, coverage.csv. Raw ESPN bodies are stored as returned (parsed JSON, re-serialised); the parsed columns in predictor.csv
are a convenience, the raw lines are the record."""
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
from zoneinfo import ZoneInfo

KALSHI = "https://external-api.kalshi.com/trade-api/v2"
ESPN_SITE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_CORE = "https://sports.core.api.espn.com/v2/sports"
UA = {"User-Agent": "shwoopnet-research-recorder"}
ET = ZoneInfo("America/New_York")

# Built-in stop dates (UTC). Games starting on or after STOP_TRACK_ISO are not tracked; nothing at all runs after STOP_ALL_ISO. Registration: stop 2026-12-31, read 2027-01-01 after 12:00 UTC.
STOP_TRACK_ISO = "2026-12-31T00:00:00Z"
STOP_ALL_ISO = "2027-01-01T06:00:00Z"

LEAGUES = {  # kalshi series -> (espn sport, espn league, extra scoreboard params)
    "KXNFLGAME": ("football", "nfl", [""]),
    "KXNCAAFGAME": ("football", "college-football", ["&groups=80", "&groups=81"]),
    "KXNBAGAME": ("basketball", "nba", [""]),
    "KXMLBGAME": ("baseball", "mlb", [""]),
}
LOOK_FAR_S = 120 * 60       # start polling a game this long before its start
LOOK_NEAR_S = 30 * 60       # stop polling this long before its start
POLL_EVERY_S = 300
SCHED_EVERY_S = 900
RESULT_EVERY_S = 600
RESULT_BATCH = 6
RESULT_MIN_AGE_S = 150 * 60     # do not even ask before the game could have ended
RESULT_GIVE_UP_S = 72 * 3600
MIN_GAP = {"kalshi": 1.0, "espn": 0.4}

GAMES_COLS = ["job_ts_ms", "league", "espn_id", "start_iso", "home_id", "home_abbr", "home_name", "away_id", "away_abbr", "away_name", "event_ticker", "home_ticker", "away_ticker", "match"]
QUOTE_COLS = ["poll_ts_ms", "server_date_header", "league", "espn_id", "event_ticker", "ticker", "side", "yes_sub_title", "yes_bid", "yes_ask", "yes_bid_size", "yes_ask_size", "status", "start_iso", "mins_to_start"]
PRED_COLS = ["recv_ms", "league", "espn_id", "kind", "http", "last_modified", "home_gp", "away_gp"]
RESULT_COLS = ["recv_ms", "league", "espn_id", "event_ticker", "home_ticker", "away_ticker", "home_result", "away_result", "espn_state", "espn_completed", "home_score", "away_score", "resolved"]
COVER_COLS = ["job_start_ms", "job_end_ms", "polls", "games_tracked", "games_matched", "kalshi_reqs", "espn_reqs", "n429", "n5xx", "failed", "results_written"]

_open = urllib.request.urlopen     # replaced in tests
_sleep = time.sleep                # replaced in tests
_now = time.time                   # replaced in tests
STATS = {"kalshi_reqs": 0, "espn_reqs": 0, "n429": 0, "n5xx": 0, "failed": 0}
_last_req = {}


def epoch(iso):
    return int(datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())


STOP_TRACK = epoch(STOP_TRACK_ISO)
STOP_ALL = epoch(STOP_ALL_ISO)


def iso(ep):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ep))


def parse_iso(s):
    """ESPN writes 2026-10-31T22:00Z (no seconds); Kalshi writes full ISO. Epoch seconds or None."""
    if not s:
        return None
    try:
        return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def http_get(url, host):
    """(status, decoded json or None, Date header, receive time in ms). NEVER raises: a failed read is a status, so one bad request cannot fail the job.
    Paced (MIN_GAP per host) and retried with backoff on 429 and 5xx (honouring Retry-After, capped at 60 s)."""
    key = "kalshi" if host == "kalshi" else "espn"
    status, retries = 0, 3
    for attempt in range(retries + 1):
        wait = MIN_GAP[key] - (_now() - _last_req.get(key, 0.0))
        if wait > 0:
            _sleep(wait)
        _last_req[key] = _now()
        STATS[key + "_reqs"] += 1
        recv = int(_now() * 1000)
        try:
            with _open(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return r.status, json.load(r), r.headers.get("Date", ""), recv
        except urllib.error.HTTPError as e:
            status = e.code
            if e.code == 429 or e.code >= 500:
                STATS["n429" if e.code == 429 else "n5xx"] += 1
                if attempt < retries:
                    try:
                        ra = float(e.headers.get("Retry-After", ""))
                    except (TypeError, ValueError):
                        ra = 0.0
                    _sleep(min(60.0, max(ra, 2.0 * (2 ** attempt))))
                    continue
            return status, None, "", recv
        except Exception:
            status = 0
            if attempt < retries:
                _sleep(2.0 * (attempt + 1))
                continue
    STATS["failed"] += 1
    return status, None, "", recv


# ---------------------------------------------------------------- ESPN

def parse_scoreboard(body, series):
    """Games of one scoreboard response: dicts with id, start (epoch), state, and the two teams. Games with no start, no two competitors or no home/away are skipped."""
    out = []
    for e in (body or {}).get("events") or []:
        try:
            comp = e["competitions"][0]
            teams = {}
            for c in comp["competitors"]:
                t = c["team"]
                teams[c.get("homeAway")] = {"id": str(t.get("id", "")), "abbr": t.get("abbreviation", ""), "loc": t.get("location", ""), "name": t.get("name", ""),
                                            "disp": t.get("displayName", ""), "short": t.get("shortDisplayName", "")}
            start = parse_iso(e.get("date"))
            if start is None or "home" not in teams or "away" not in teams:
                continue
            out.append({"id": str(e["id"]), "series": series, "start": start, "state": e["status"]["type"]["state"], "home": teams["home"], "away": teams["away"]})
        except (KeyError, IndexError, TypeError):
            continue
    return out


def schedule_dates(now):
    """The ET calendar dates to ask for: today and the day of now + 3 hours (a late game can be listed under the next ET date)."""
    d = {datetime.fromtimestamp(now, ET).strftime("%Y%m%d"), datetime.fromtimestamp(now + 3 * 3600, ET).strftime("%Y%m%d")}
    return sorted(d)


def refresh_schedule(now):
    sched = {}
    for series, (sport, league, extras) in LEAGUES.items():
        for d in schedule_dates(now):
            for ex in extras:
                st, body, _d, _r = http_get("%s/%s/%s/scoreboard?dates=%s&limit=500%s" % (ESPN_SITE, sport, league, d, ex), "espn")
                if st == 200:
                    for g in parse_scoreboard(body, series):
                        sched[g["id"] + series] = g
    return sched


def core_predictor_url(series, gid):
    sport, league, _ex = LEAGUES[series]
    return "%s/%s/leagues/%s/events/%s/competitions/%s/predictor" % (ESPN_CORE, sport, league, gid, gid)


def summary_url(series, gid):
    sport, league, _ex = LEAGUES[series]
    return "%s/%s/%s/summary?event=%s" % (ESPN_SITE, sport, league, gid)


def team_gp(side):
    """A team's gameProjection (percent) from a core predictor side, or None."""
    for s in (side or {}).get("statistics") or []:
        if s.get("name") == "gameProjection":
            return num(s.get("value"))
    return None


def team_loss(side):
    for s in (side or {}).get("statistics") or []:
        if s.get("name") == "teamChanceLoss":
            return num(s.get("value"))
    return None


def predictor_probs(body):
    """(home %, away %) from a core predictor body. NBA fills only the away team's statistics, so a missing side is the other side's teamChanceLoss. (None, None) if unreadable."""
    if not isinstance(body, dict):
        return None, None
    h, a = body.get("homeTeam"), body.get("awayTeam")
    hg, ag = team_gp(h), team_gp(a)
    if hg is None:
        hg = team_loss(a)
    if ag is None:
        ag = team_loss(h)
    return hg, ag


# ---------------------------------------------------------------- Kalshi matching (the ESPN1 logic: ticker code, names, date)

MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower().replace("&", "and").replace("state", "st")).strip()


def ticker_date(event):
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)(\d{4})?", event or "")
    if not m or m.group(2) not in MON:
        return None
    try:
        return datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3))).date()
    except ValueError:
        return None


def team_score(code, sub, t):
    """0 means no match. t is {abbr, loc, name, disp, short}."""
    s = 0
    if code and code.upper() == (t["abbr"] or "").upper():
        s += 2
    ns = norm(sub)
    cands = {norm(t["loc"]), norm(t["disp"]), norm(t["short"]), norm(t["name"])}
    if ns and ns in cands:
        s += 2
    elif ns and len(ns.split()) >= 2 and len(ns.split()[-1]) == 1 and ns[:-2] == norm(t["loc"]) and norm(t["name"]).startswith(ns[-1]):
        s += 2     # "Los Angeles L"
    elif ns and norm(t["loc"]) and (norm(t["loc"]).startswith(ns) or ns.startswith(norm(t["loc"]))):
        s += 1
    return s


def match_game(game, events):
    """events: {event_ticker: [market, market]} of one series. Returns (event_ticker, home market, away market, status). Ambiguous or missing: no event."""
    day0 = datetime.fromtimestamp(game["start"], ET).date()
    best = []
    for ev, mk in events.items():
        if len(mk) != 2:
            continue
        d = ticker_date(ev)
        if d is None or abs((d - day0).days) > 1:
            continue
        m1, m2 = mk
        c1, c2 = (m1.get("ticker") or "").rsplit("-", 1)[-1], (m2.get("ticker") or "").rsplit("-", 1)[-1]
        s1, s2 = m1.get("yes_sub_title") or "", m2.get("yes_sub_title") or ""
        h, a = game["home"], game["away"]
        ah, aa = team_score(c1, s1, h), team_score(c2, s2, a)
        bh, ba = team_score(c2, s2, h), team_score(c1, s1, a)
        if ah > 0 and aa > 0 and ah + aa >= bh + ba:
            best.append((ah + aa - abs((d - day0).days) * 10, ev, m1, m2))
        elif bh > 0 and ba > 0:
            best.append((bh + ba - abs((d - day0).days) * 10, ev, m2, m1))
    if not best:
        return "", None, None, "none"
    best.sort(key=lambda b: -b[0])
    if len(best) > 1 and best[1][0] == best[0][0]:
        return "", None, None, "ambiguous"
    return best[0][1], best[0][2], best[0][3], "ok"


def fetch_series_markets(series):
    """All open markets of the series in one go (at most 5 pages). (events {ticker: [markets]}, Date header of the last page, receive ms of the first page, ok)."""
    markets, cursor, date, recv0, ok = [], "", "", 0, False
    for _ in range(5):
        url = "%s/markets?series_ticker=%s&status=open&limit=1000%s" % (KALSHI, series, ("&cursor=" + cursor) if cursor else "")
        st, body, d, recv = http_get(url, "kalshi")
        if st != 200 or not isinstance(body, dict):
            break
        ok = True
        recv0 = recv0 or recv
        date = d or date
        markets += body.get("markets") or []
        cursor = body.get("cursor") or ""
        if not cursor:
            break
    events = {}
    for m in markets:
        events.setdefault(m.get("event_ticker"), []).append(m)
    return events, date, recv0, ok


def quote_rows(poll_ms, date, game, event, home_m, away_m):
    rows = []
    for side, m in (("home", home_m), ("away", away_m)):
        rows.append([poll_ms, date, game["series"], game["id"], event, m.get("ticker"), side, m.get("yes_sub_title"), m.get("yes_bid_dollars"), m.get("yes_ask_dollars"),
                     m.get("yes_bid_size_fp"), m.get("yes_ask_size_fp"), m.get("status"), iso(game["start"]), round((game["start"] - poll_ms / 1000.0) / 60.0, 2)])
    return rows


# ---------------------------------------------------------------- output

class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        for name, cols in (("games", GAMES_COLS), ("quotes", QUOTE_COLS), ("predictor", PRED_COLS), ("results", RESULT_COLS), ("coverage", COVER_COLS)):
            f = open(os.path.join(d, name + ".csv"), "a", newline="")
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(cols)
            self.files.append(f)
            self.w[name] = w
        self.raw = open(os.path.join(d, "espn_raw.jsonl"), "a")
        self.files.append(self.raw)

    def write(self, name, rows):
        self.w[name].writerows(rows)

    def write_raw(self, recv_ms, kind, series, gid, status, date, body):
        self.raw.write(json.dumps({"recv_ms": recv_ms, "kind": kind, "league": series, "espn_id": gid, "http": status, "date_header": date, "body": body}, separators=(",", ":")) + "\n")

    def flush(self):
        for f in self.files:
            f.flush()

    def close(self):
        self.flush()
        for f in self.files:
            f.close()


def read_csv_any(path):
    op = gzip.open if path.endswith(".gz") else open
    try:
        with op(path, "rt", newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, EOFError):
        return []


def known_games(root):
    """Matched games recorded by earlier jobs and this one: {(league, espn_id): row}, and the keys already given a final result."""
    games, done = {}, set()
    for p in glob.glob(os.path.join(root, "*", "*", "games.csv*")):
        for r in read_csv_any(p):
            if r.get("event_ticker"):
                games[(r["league"], r["espn_id"])] = r
    for p in glob.glob(os.path.join(root, "*", "*", "results.csv*")):
        for r in read_csv_any(p):
            done.add((r["league"], r["espn_id"]))
    return games, done


# ---------------------------------------------------------------- the polls

def window_games(sched, now):
    """Games that have not started, start before STOP_TRACK and are 30 to 120 minutes away."""
    return [g for g in sched.values() if g["state"] == "pre" and g["start"] < STOP_TRACK and LOOK_NEAR_S <= g["start"] - now <= LOOK_FAR_S]


def poll_cycle(out, due, matched, written_games, job_ms, nopred):
    """One poll of every due game. Kalshi first (one bulk read per series), then ESPN game by game."""
    by_series = {}
    for g in due:
        by_series.setdefault(g["series"], []).append(g)
    for series, games in by_series.items():
        events, date, poll_ms, ok = fetch_series_markets(series)
        if not ok:
            continue
        for g in games:
            key = g["series"] + g["id"]
            if key in nopred:
                continue
            if key not in matched or matched[key][3] != "ok":
                matched[key] = match_game(g, events)
            event, hm, am, status = matched[key]
            if key not in written_games:
                written_games.add(key)
                h, a = g["home"], g["away"]
                out.write("games", [[job_ms, series, g["id"], iso(g["start"]), h["id"], h["abbr"], h["name"], a["id"], a["abbr"], a["name"], event,
                                     (hm or {}).get("ticker", ""), (am or {}).get("ticker", ""), status]])
            if status != "ok":
                continue
            fresh = events.get(event) or []
            cur = {m.get("ticker"): m for m in fresh}
            hm, am = cur.get(hm.get("ticker"), hm), cur.get(am.get("ticker"), am)
            out.write("quotes", quote_rows(poll_ms, date, g, event, hm, am))
            st, body, d, recv = http_get(core_predictor_url(series, g["id"]), "espn")
            core_status = st
            out.write_raw(recv, "core_predictor", series, g["id"], st, d, body)
            hg, ag = predictor_probs(body)
            out.write("predictor", [[recv, series, g["id"], "core_predictor", st, (body or {}).get("lastModified", "") if isinstance(body, dict) else "", hg, ag]])
            st, body, d, recv = http_get(summary_url(series, g["id"]), "espn")
            pred = (body or {}).get("predictor") if isinstance(body, dict) else None
            state = ((((body or {}).get("header") or {}).get("competitions") or [{}])[0].get("status") or {}).get("type", {}).get("state") if isinstance(body, dict) else None
            out.write_raw(recv, "summary_predictor", series, g["id"], st, d, {"predictor": pred, "state": state})
            sh = sa = None
            if isinstance(pred, dict):
                sh, sa = num((pred.get("homeTeam") or {}).get("gameProjection")), num((pred.get("awayTeam") or {}).get("gameProjection"))
            out.write("predictor", [[recv, series, g["id"], "summary_predictor", st, "", sh, sa]])
            if core_status == 400 and pred is None:
                nopred.add(key)     # ESPN publishes no pre-game probability for this game (for example a lower division college game): probed once, then left alone for this job
        out.flush()
    return len(due)


def results_pass(out, root, now, tried):
    """Results for tracked games that have ended: at most RESULT_BATCH per pass, a game is asked again no sooner than 30 minutes after a try. Returns rows written."""
    games, done = known_games(root)
    written = 0
    for (league, gid), r in sorted(games.items(), key=lambda kv: kv[1].get("start_iso", "")):
        if written >= RESULT_BATCH:
            break
        if (league, gid) in done or tried.get((league, gid), 0) > now:
            continue
        start = parse_iso(r.get("start_iso"))
        if start is None or now - start < RESULT_MIN_AGE_S:
            continue
        tried[(league, gid)] = now + 1800
        giveup = now - start > RESULT_GIVE_UP_S
        st, sbody, _d, recv = http_get(summary_url(league, gid), "espn")
        comp = ((((sbody or {}).get("header") or {}).get("competitions") or [{}])[0]) if isinstance(sbody, dict) else {}
        stype = (comp.get("status") or {}).get("type") or {}
        scores = {c.get("homeAway"): c.get("score") for c in comp.get("competitors") or []}
        res = {}
        for side in ("home", "away"):
            tk = r.get(side + "_ticker")
            s2, b2, _d2, _r2 = http_get("%s/markets/%s" % (KALSHI, tk), "kalshi")
            res[side] = ((b2 or {}).get("market") or {}).get("result", "") if s2 == 200 and isinstance(b2, dict) else ""
        final = bool(res["home"]) and bool(res["away"])
        if not final and not giveup:
            continue
        if final:
            st3, b3, d3, rv3 = http_get(core_predictor_url(league, gid), "espn")
            out.write_raw(rv3, "core_predictor_post", league, gid, st3, d3, b3)
            hg, ag = predictor_probs(b3)
            out.write("predictor", [[rv3, league, gid, "core_predictor_post", st3, (b3 or {}).get("lastModified", "") if isinstance(b3, dict) else "", hg, ag]])
        out.write("results", [[recv, league, gid, r.get("event_ticker"), r.get("home_ticker"), r.get("away_ticker"), res["home"], res["away"], stype.get("state", ""),
                               stype.get("completed", ""), scores.get("home", ""), scores.get("away", ""), 1 if final else 0]])
        written += 1
        out.flush()
    return written


def cycle_stop_time(now, cycle_s):
    """Same rule as record_quotes.py and record_book.py: stop a minute after the first cycle boundary that leaves this job a full cycle, so the next job (which starts early) queues behind it."""
    into = now % cycle_s
    first_boundary = now - into + cycle_s
    if cycle_s - into < 1800:
        return first_boundary + cycle_s + 60
    return first_boundary + 60


def run(out, root, stop_at):
    job_ms = int(_now() * 1000)
    sched, sched_at, matched, written_games, tried, nopred = {}, 0.0, {}, set(), {}, set()
    last_poll, next_results, polls, tracked, results_written = 0.0, 0.0, 0, set(), 0
    while _now() < stop_at and _now() < STOP_ALL:
        now = _now()
        if now - sched_at >= SCHED_EVERY_S:
            sched, sched_at = refresh_schedule(now) or sched, now
        due = window_games(sched, now)
        if due and now - last_poll >= POLL_EVERY_S - 5:
            last_poll = now
            polls += poll_cycle(out, due, matched, written_games, job_ms, nopred) and 1
            tracked |= {g["series"] + g["id"] for g in due}
        elif now >= next_results:
            next_results = now + RESULT_EVERY_S
            results_written += results_pass(out, root, now, tried)
        out.flush()
        _sleep(20.0)
    n_ok = sum(1 for v in matched.values() if v[3] == "ok")
    out.write("coverage", [[job_ms, int(_now() * 1000), polls, len(tracked), n_ok, STATS["kalshi_reqs"], STATS["espn_reqs"], STATS["n429"], STATS["n5xx"], STATS["failed"], results_written]])
    out.flush()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--root", default=None, help="the folder holding every job's output (to find games awaiting a result); default: two levels above out_dir")
    ap.add_argument("--cycle-hours", type=float, default=4, help="back to back jobs: stop a minute after the cycle boundary that leaves one full cycle")
    ap.add_argument("--max-minutes", type=float, default=0, help="for a test: stop after this many minutes")
    a = ap.parse_args(argv)
    now = _now()
    if now >= STOP_ALL:
        print("past the stop date %s: nothing to record" % STOP_ALL_ISO)
        return 0
    stop_at = now + a.max_minutes * 60 if a.max_minutes else cycle_stop_time(now, a.cycle_hours * 3600)
    root = a.root or os.path.dirname(os.path.dirname(os.path.abspath(a.out_dir)))
    out = Out(a.out_dir)
    try:
        run(out, root, stop_at)
    except Exception as e:      # a bug must not lose what was recorded or fail the push step
        print("recorder error: %r" % (e,), file=sys.stderr)
    finally:
        out.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
