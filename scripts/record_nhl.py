#!/usr/bin/env python3
"""NHL pre-puck-drop ladder recorder (RECBUILD1, Nov 4, 2026, the owner approved collector 1; research only).

Why it exists (NHLAUDIT1): the NHL goal and assist ladders (KXNHLGOAL, KXNHLAST, and KXNHLPTS beside them) were the only cheap-side pool that came out positive on fresh data,
but the history could not say which rungs were tradable BEFORE the puck dropped: a rung entered the test universe only if its LIFETIME volume was above 0, which includes in-game
and post-goal trading, so winners (which trade a lot) were over-represented. A forward read needs the ladder as it stood at the look, with the volume at that moment. This records it.

What it does, on PUBLIC keyless endpoints only (ESPN public scoreboard and summary, Kalshi public market data). No key, no secret, no auth header, no order, no write call.
  1. Reads today's NHL schedule from ESPN's scoreboard (game id, start time, teams) every 30 minutes, matches each game to its Kalshi events (the event ticker tail is the two team
     codes), and writes the schedule row so the reader never needs ESPN for the start time.
  2. For each game that has not started, at 120, 90, 60, 30 and 5 minutes before ESPN's start time (a look is taken from its target time on, for at most LOOK_SLACK_S), takes ONE bulk
     read of each series' open markets and writes EVERY rung of the game's event: bid, ask, both sizes, volume, 24 hour volume, open interest, last price, status, with the server's
     Date header. A game with no open ladder at a look is written as a zero (looks.csv), so "no ladder yet" is told apart from "not captured".
  3. Afterwards, for games that have ended: ESPN's box score goals and assists per skater (results.csv), once per game.
Nothing is chosen or filtered here (no price band, no volume floor): the universe is fixed by the reader from the `volume` column AT THE LOOK.

Requests: at most 1 per second per host (pacing), 429 and 5xx backed off (Retry-After honoured, capped at 60 s), the User-Agent says what this is and is never changed. Kalshi: 1 to 5 pages per
series per cycle, a cycle only when a look is due (a 7 pm ET slate has about 16 games, so about 5 cycles in 2 hours). ESPN: 2 scoreboard reads per 30 minutes plus one summary per finished game.

Output, under <root> (the checked out quote-data branch's nhl/ folder): quotes/<UTC date>/<HH>.csv.gz (appended, multi-member gzip), looks/<date>.csv, games/<date>.csv, results/<date>.csv,
runs/<date>.csv. A job writes nothing outside nhl/."""
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
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KALSHI = "https://external-api.kalshi.com/trade-api/v2"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
UA = {"User-Agent": "shwoopnet-research-recorder (public data, GET only)"}
ET = ZoneInfo("America/New_York")

# Nothing runs after STOP_ALL_ISO. The frozen read is expected 2026-12-20 to 2027-01-05, so this leaves a month of margin; extending it is a one line edit.
STOP_ALL_ISO = "2027-02-01T06:00:00Z"
SERIES = ("KXNHLGOAL", "KXNHLAST", "KXNHLPTS")
LOOKS_MIN = (120, 90, 60, 30, 5)                  # minutes before ESPN's start time
LOOK_SLACK_S = {120: 720, 90: 720, 60: 720, 30: 720, 5: 240}   # a look is still taken this long after its target (a late start of a job loses the earliest looks, never invents them)
SCHED_EVERY_S = 1800
RESULT_EVERY_S = 1800
RESULT_MIN_AGE_S = 3 * 3600
RESULT_GIVE_UP_S = 72 * 3600
RESULT_BATCH = 8
LOOP_S = 15.0
MIN_GAP = {"kalshi": 1.0, "espn": 1.0}
MAX_PAGES = 5
# Job start times (UTC, HH:MM). A job runs until a few minutes past the next anchor at least an hour away (the next job queues behind it), and ends sooner when no look is due before then.
DEFAULT_ANCHORS = "14:45,21:30,01:30"
STOP_PAD_S = 300

# Kalshi writes some team codes with two letters or the older code; ESPN uses its own. Both spellings are accepted when matching an event ticker's tail.
ALIAS = [{"TB", "TBL"}, {"NJ", "NJD"}, {"SJ", "SJS"}, {"LA", "LAK"}, {"UTA", "UTAH"}, {"WSH", "WAS"}]

QUOTE_COLS = ["poll_ms", "server_date_header", "series", "espn_id", "look_min", "mins_to_start", "event_ticker", "ticker", "player", "strike", "yes_bid", "yes_ask", "yes_bid_size",
              "yes_ask_size", "volume", "volume_24h", "open_interest", "last", "status", "start_iso"]
LOOK_COLS = ["poll_ms", "server_date_header", "espn_id", "look_min", "mins_to_start", "series", "event_ticker", "n_markets", "read_ok"]
GAME_COLS = ["seen_ms", "espn_id", "start_iso", "state", "home_id", "home_abbr", "home_name", "away_id", "away_abbr", "away_name", "event_goal", "event_ast", "event_pts", "match"]
RESULT_COLS = ["recv_ms", "espn_id", "start_iso", "state", "completed", "team_abbr", "athlete_id", "player", "goals", "assists"]
RUN_COLS = ["job_start_ms", "job_end_ms", "stop_ms", "games_seen", "looks_captured", "looks_missed", "cycles", "results_games", "kalshi_reqs", "espn_reqs", "n429", "n5xx", "failed", "quote_rows"]

_open = urllib.request.urlopen     # replaced in tests
_sleep = time.sleep                # replaced in tests
_now = time.time                   # replaced in tests
STATS = {"kalshi_reqs": 0, "espn_reqs": 0, "n429": 0, "n5xx": 0, "failed": 0}
_last_req = {}


def epoch(iso_s):
    return int(datetime.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())


STOP_ALL = epoch(STOP_ALL_ISO)


def iso(ep):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ep))


def parse_iso(s):
    """ESPN writes 2026-11-05T00:30Z (no seconds); Kalshi writes full ISO. Epoch seconds or None."""
    if not s:
        return None
    try:
        return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def http_get(url, host):
    """(status, decoded json or None, Date header, receive time in ms). NEVER raises: a failed read is a status. Paced per host and retried with backoff on 429 and 5xx."""
    key = "kalshi" if host == "kalshi" else "espn"
    status, retries, recv = 0, 3, int(_now() * 1000)
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
                STATS["failed"] += 1
            return status, None, "", recv
        except Exception:
            status = 0
            if attempt < retries:
                _sleep(2.0 * (attempt + 1))
                continue
    STATS["failed"] += 1
    return status, None, "", recv


# ---------------------------------------------------------------- ESPN schedule and Kalshi matching

def parse_scoreboard(body):
    """Games of one ESPN scoreboard: dicts with id, start (epoch), state and the two teams. A game with no start, no home and away team or no id is skipped."""
    out = []
    for e in (body or {}).get("events") or []:
        try:
            comp = e["competitions"][0]
            teams = {}
            for c in comp["competitors"]:
                t = c["team"]
                teams[c.get("homeAway")] = {"id": str(t.get("id", "")), "abbr": t.get("abbreviation", ""), "name": t.get("displayName", "")}
            start = parse_iso(e.get("date"))
            if start is None or "home" not in teams or "away" not in teams:
                continue
            out.append({"id": str(e["id"]), "start": start, "state": e["status"]["type"]["state"], "home": teams["home"], "away": teams["away"]})
        except (KeyError, IndexError, TypeError):
            continue
    return out


def schedule_dates(now):
    """The ET calendar dates to ask for: today, and the date six hours from now (a late job reaches into the next ET day)."""
    return sorted({datetime.fromtimestamp(now, ET).strftime("%Y%m%d"), datetime.fromtimestamp(now + 6 * 3600, ET).strftime("%Y%m%d")})


def refresh_schedule(now):
    """({espn id: game}, ok). ok is False when no scoreboard could be read, so the job keeps its old schedule and tries again soon instead of deciding there is nothing to do."""
    sched, ok = {}, False
    for d in schedule_dates(now):
        st, body, _d, _r = http_get("%s/scoreboard?dates=%s&limit=200" % (ESPN, d), "espn")
        if st == 200 and isinstance(body, dict):
            ok = True
            for g in parse_scoreboard(body):
                sched[g["id"]] = g
    return sched, ok


def variants(abbr):
    a = (abbr or "").upper()
    for grp in ALIAS:
        if a in grp:
            return set(grp)
    return {a}


def event_tail(event):
    """(date, 'AWAYHOME') from a ticker like KXNHLGOAL-26NOV04OTTBUF, or (None, None)."""
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)([A-Z]{4,8})$", event or "")
    if not m:
        return None, None
    try:
        d = datetime.strptime(m.group(1) + m.group(2) + m.group(3), "%y%b%d").date()
    except ValueError:
        return None, None
    return d, m.group(4)


def match_event(game, events):
    """The event ticker of `events` (a dict of event_ticker -> markets of one series) that is this game: tail = away code + home code (either spelling), date within a day of the ET date.
    Ambiguity (two events fit) returns '' so a wrong game is never recorded."""
    day0 = datetime.fromtimestamp(game["start"], ET).date()
    want = {a + h for a in variants(game["away"]["abbr"]) for h in variants(game["home"]["abbr"])}
    hits = []
    for ev in events:
        d, tail = event_tail(ev)
        if d is not None and tail in want and abs((d - day0).days) <= 1:
            hits.append(ev)
    return hits[0] if len(hits) == 1 else ""


def fetch_series_markets(series):
    """All open markets of one series (at most MAX_PAGES pages of 1000): ({event_ticker: [markets]}, Date header of the last page, receive ms of the first page, ok). ok is False if no page was read;
    a series cut short by a failed later page is returned with what was read and ok True (the caller records n_markets, so a short read shows)."""
    markets, cursor, date, recv0, ok = [], "", "", 0, False
    for _ in range(MAX_PAGES):
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


def first(m, *keys):
    for k in keys:
        if m.get(k) not in (None, ""):
            return m[k]
    return ""


def quote_rows(series, game, look, poll_ms, date, event, markets):
    """One row per rung of the event, as the listing shows it at this moment (nothing filtered)."""
    mins = round((game["start"] - poll_ms / 1000.0) / 60.0, 2)
    rows = []
    for m in sorted(markets, key=lambda x: x.get("ticker") or ""):
        rows.append([poll_ms, date, series, game["id"], look, mins, event, m.get("ticker"), (m.get("yes_sub_title") or "").split(":")[0].strip(), first(m, "floor_strike"),
                     first(m, "yes_bid_dollars", "yes_bid"), first(m, "yes_ask_dollars", "yes_ask"), first(m, "yes_bid_size_fp"), first(m, "yes_ask_size_fp"),
                     first(m, "volume_fp", "volume"), first(m, "volume_24h_fp"), first(m, "open_interest_fp", "open_interest"), first(m, "last_price_dollars", "last_price"),
                     m.get("status"), iso(game["start"])])
    return rows


# ---------------------------------------------------------------- output

def append_csv(path, cols, rows, gz=False):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with (gzip.open(path, "at", newline="") if gz else open(path, "a", newline="")) as f:
        w = csv.writer(f)
        if new:
            w.writerow(cols)
        w.writerows(rows)


def day_of(ep):
    return time.strftime("%Y-%m-%d", time.gmtime(ep))


def read_csv_any(path):
    op = gzip.open if path.endswith(".gz") else open
    try:
        with op(path, "rt", newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, EOFError):
        return []


def known_games(root):
    """Games written by earlier jobs and this one: {espn_id: latest row}; and the ids already given a result."""
    games, done = {}, set()
    for p in sorted(glob.glob(os.path.join(root, "games", "*.csv"))):
        for r in read_csv_any(p):
            games[r["espn_id"]] = r
    for p in glob.glob(os.path.join(root, "results", "*.csv")):
        for r in read_csv_any(p):
            done.add(r["espn_id"])
    return games, done


# ---------------------------------------------------------------- looks

def due_looks(sched, taken, now):
    """(game, look) pairs to take now: the game has not started, now is from the target (start - look) to LOOK_SLACK_S after it, and the look has not been taken."""
    out = []
    for g in sched.values():
        if g["state"] != "pre":
            continue
        for lk in LOOKS_MIN:
            tgt = g["start"] - lk * 60
            if (g["id"], lk) not in taken and tgt <= now < min(tgt + LOOK_SLACK_S[lk], g["start"]):
                out.append((g, lk))
    return out


def next_target(sched, taken, now):
    """The earliest look target that is still ahead (or still inside its slack) and not taken, or None."""
    best = None
    for g in sched.values():
        if g["state"] != "pre":
            continue
        for lk in LOOKS_MIN:
            tgt = g["start"] - lk * 60
            if (g["id"], lk) not in taken and now < min(tgt + LOOK_SLACK_S[lk], g["start"]):
                best = tgt if best is None else min(best, tgt)
    return best


def note_game(root, g, matched, written):
    """Writes the schedule row of a game when it, or the events matched to it, changed since the last row written by this job (the reader takes the latest row per espn_id)."""
    key = (g["id"], matched.get((g["id"], SERIES[0]), ""), matched.get((g["id"], SERIES[1]), ""), matched.get((g["id"], SERIES[2]), ""))
    if key in written:
        return
    written.add(key)
    h, a = g["home"], g["away"]
    append_csv(os.path.join(root, "games", day_of(g["start"]) + ".csv"), GAME_COLS, [[int(_now() * 1000), g["id"], iso(g["start"]), g["state"], h["id"], h["abbr"], h["name"], a["id"], a["abbr"], a["name"],
                                                                                   key[1], key[2], key[3], "ok" if any(key[1:]) else "no_event_yet"]])


def take_looks(root, due, taken, matched, written):
    """One cycle: one bulk read per series, then every due (game, look) is written. Returns (looks captured, quote rows)."""
    reads = {s: fetch_series_markets(s) for s in SERIES}
    captured, nrows = 0, 0
    for g, lk in due:
        if not any(reads[s][3] for s in SERIES):
            continue                       # nothing could be read: the look stays due until its slack ends
        if not all(reads[s][3] for s in SERIES) and _now() < min(g["start"] - lk * 60 + LOOK_SLACK_S[lk], g["start"]) - 90:
            continue                       # one series failed: try the whole look again while time is left; near the end of its slack it is written with read_ok 0 for the failed series
        ev = {s: (match_event(g, reads[s][0]) if reads[s][3] else matched.get((g["id"], s), "")) for s in SERIES}
        for s in SERIES:
            matched[(g["id"], s)] = ev[s] or matched.get((g["id"], s), "")
        row_ms = max(reads[s][2] for s in SERIES)
        for s in SERIES:
            events, date, poll_ms, ok = reads[s]
            event = ev[s]
            mk = events.get(event, []) if (ok and event) else []
            day = day_of(poll_ms // 1000 if poll_ms else row_ms // 1000)
            hour = time.strftime("%H", time.gmtime((poll_ms or row_ms) // 1000))
            rows = quote_rows(s, g, lk, poll_ms or row_ms, date, event, mk)
            append_csv(os.path.join(root, "quotes", day, hour + ".csv.gz"), QUOTE_COLS, rows, gz=True)
            nrows += len(rows)
            append_csv(os.path.join(root, "looks", day + ".csv"), LOOK_COLS, [[poll_ms or row_ms, date, g["id"], lk, round((g["start"] - (poll_ms or row_ms) / 1000.0) / 60.0, 2), s, event, len(mk), 1 if ok else 0]])
        taken.add((g["id"], lk))
        captured += 1
        note_game(root, g, matched, written)
    return captured, nrows


# ---------------------------------------------------------------- results

def box_goals_assists(body):
    """[(team abbr, athlete id, name, goals, assists)] from an ESPN hockey summary. Position groups hold the same skaters once ('forwards', 'defenses'); the empty 'skaters' group and goalies are skipped by
    needing both a goals and an assists key."""
    out, seen = [], set()
    try:
        for tp in body["boxscore"]["players"]:
            abbr = (tp.get("team") or {}).get("abbreviation", "")
            for grp in tp.get("statistics") or []:
                keys = grp.get("keys") or []
                if "goals" not in keys or "assists" not in keys:
                    continue
                gi, ai = keys.index("goals"), keys.index("assists")
                for a in grp.get("athletes") or []:
                    ath = a.get("athlete") or {}
                    aid = str(ath.get("id", ""))
                    if not aid or aid in seen:
                        continue
                    seen.add(aid)
                    st = a.get("stats") or []
                    out.append((abbr, aid, ath.get("displayName", ""), st[gi] if gi < len(st) else "", st[ai] if ai < len(st) else ""))
    except (KeyError, TypeError, AttributeError):
        return []
    return out


def results_pass(root, now, tried):
    """Box scores for tracked games that have ended: at most RESULT_BATCH per pass, a game is asked again no sooner than 30 minutes after a try. Returns games written."""
    games, done = known_games(root)
    written = 0
    for gid, r in sorted(games.items(), key=lambda kv: kv[1].get("start_iso", "")):
        if written >= RESULT_BATCH:
            break
        start = parse_iso(r.get("start_iso"))
        if gid in done or tried.get(gid, 0) > now or start is None or now - start < RESULT_MIN_AGE_S or now - start > RESULT_GIVE_UP_S:
            continue
        tried[gid] = now + 1800
        st, body, _d, recv = http_get("%s/summary?event=%s" % (ESPN, gid), "espn")
        if st != 200 or not isinstance(body, dict):
            continue
        stype = ((((body.get("header") or {}).get("competitions") or [{}])[0].get("status") or {}).get("type")) or {}
        if stype.get("completed") is not True:
            continue
        rows = [[recv, gid, r.get("start_iso", ""), stype.get("state", ""), stype.get("completed", ""), abbr, aid, name, g, a] for abbr, aid, name, g, a in box_goals_assists(body)]
        if rows:
            append_csv(os.path.join(root, "results", day_of(start) + ".csv"), RESULT_COLS, rows)
            written += 1
    return written


# ---------------------------------------------------------------- the job

def anchors_of(spec):
    out = []
    for part in spec.split(","):
        hh, mm = part.strip().split(":")
        out.append(int(hh) * 3600 + int(mm) * 60)
    return sorted(out)


def stop_time(now, anchors):
    """A few minutes past the first anchor (a UTC time of day) at least an hour away. The next scheduled job starts at that anchor and queues behind this one."""
    base = now - now % 86400
    cands = sorted(base + a + k * 86400 for k in (0, 1, 2) for a in anchors)
    return next(c for c in cands if c - now >= 3600) + STOP_PAD_S


def run(root, stop_at):
    job_ms = int(_now() * 1000)
    sched, sched_at, sched_ok, taken, matched, written = {}, -1e18, False, set(), {}, set()
    tried, next_results = {}, 0.0
    cycles = results_games = captured = quote_rows_n = 0
    seen = set()
    while _now() < stop_at and _now() < STOP_ALL:
        now = _now()
        if now - sched_at >= (SCHED_EVERY_S if sched_ok else 120):
            new, sched_ok = refresh_schedule(now)
            sched, sched_at = (new if sched_ok else sched), now
            seen |= set(sched)
            for g in sched.values():
                if g["state"] == "pre":
                    note_game(root, g, matched, written)
        if now >= next_results:
            next_results = now + RESULT_EVERY_S
            results_games += results_pass(root, now, tried)
        due = due_looks(sched, taken, now)
        if due:
            cycles += 1
            c, n = take_looks(root, due, taken, matched, written)
            captured += c
            quote_rows_n += n
        nt = next_target(sched, taken, _now())
        if sched_ok and (nt is None or nt > stop_at):
            break                          # nothing left to take before the next job starts: end now instead of idling on billed minutes
        _sleep(LOOP_S)
    results_games += results_pass(root, _now(), tried)
    # a look whose window passed during this job without being taken is a miss (looks whose target was before the job began are not counted: they belong to the previous job)
    missed = 0
    for g in sched.values():
        for lk in LOOKS_MIN:
            tgt = g["start"] - lk * 60
            if tgt >= job_ms / 1000.0 and (g["id"], lk) not in taken and _now() >= min(tgt + LOOK_SLACK_S[lk], g["start"]):
                missed += 1
    end_ms = int(_now() * 1000)
    append_csv(os.path.join(root, "runs", day_of(job_ms / 1000.0) + ".csv"), RUN_COLS, [[job_ms, end_ms, int(stop_at * 1000), len(seen), captured, missed, cycles, results_games, STATS["kalshi_reqs"],
                                                                                             STATS["espn_reqs"], STATS["n429"], STATS["n5xx"], STATS["failed"], quote_rows_n]])


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="the nhl/ folder of the checked out quote-data branch")
    ap.add_argument("--anchors", default=DEFAULT_ANCHORS, help="UTC job start times, HH:MM comma separated; this job stops a few minutes past the next one at least an hour away")
    ap.add_argument("--max-minutes", type=float, default=0, help="for a test: stop after this many minutes")
    a = ap.parse_args(argv)
    now = _now()
    if now >= STOP_ALL:
        print("past the stop date %s: nothing to record" % STOP_ALL_ISO)
        return 0
    stop_at = now + a.max_minutes * 60 if a.max_minutes else stop_time(now, anchors_of(a.anchors))
    try:
        run(a.root, stop_at)
    except Exception as e:      # a bug must not lose what was recorded or fail the push step
        print("recorder error: %r" % (e,), file=sys.stderr)
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
