#!/usr/bin/env python3
"""In-game recorder (Nov 8, 2026, research only; V2's INGAMELAG1 and SERIESLAG1 spec, owner approved the build).
Records, for every open NBA game, the moneyline (both teams) and the two spread and two total markets nearest 50c at the first poll (fixed for the game), at about 20 seconds during
play (about 2 minutes before), so a lag between related markets after a big in-play move can be measured at a resolution Kalshi's 1 minute candles cannot give.
Public data only: no key, no auth header, no order; one request stream with at least 0.5 s between calls and a doubling wait after a 429. Rows go to CSV files in the folder given
(the workflow pushes them gzipped to the `sports-data` branch, never to main). It stops by itself on 2027-01-31 and after one cycle (up to the next 4 hour boundary)."""
import calendar
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
GROUPS = {"NBA": ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL")}
GAP_S = 0.5
BACKOFF_S = 2.0
BACKOFF_MAX_S = 30.0
HOT_POLL_S = 20.0
COLD_POLL_S = 120.0
HOT_FOR_S = 3 * 3600
HOT_MOVE = 0.02
LIST_EVERY_S = 300
MAX_HOT = 8
END_UTC = "2027-01-31T23:59:00Z"
UA = {"User-Agent": "shwoopnet-research-recorder"}
COLS = ["t_recv_ms", "server_date", "event", "kind", "ticker", "strike", "yes_bid", "yes_ask", "bid_size", "ask_size", "last_price", "volume"]
COVER = ["event", "polls", "ok_polls", "n429", "first_ms", "last_ms"]


def epoch_of(s):
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mid(m):
    b, a = num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars"))
    return (b + a) / 2 if b is not None and a is not None and a >= b and a > 0 else None


def choose(kind, markets):
    """Which markets of an event to follow for the whole game: the moneyline keeps every market (both teams); a spread or total keeps the two whose YES mid is nearest 50c now
    (a market with no two-sided quote is never chosen). Deterministic: ties break on the ticker."""
    if kind == "ml":
        return sorted(m["ticker"] for m in markets if isinstance(m, dict) and m.get("ticker"))
    quoted = [(abs(mid(m) - 0.5), m["ticker"]) for m in markets if isinstance(m, dict) and m.get("ticker") and mid(m) is not None]
    return [t for _d, t in sorted(quoted)[:2]]


def next_poll(state, now_s, new_mid):
    """Cadence: 20 s while hot (a moneyline move of 2c or more since the last poll starts three hot hours), else 120 s. Returns (hot_until, seconds to the next poll)."""
    hot_until = state.get("hot_until", 0)
    last = state.get("last_mid")
    if new_mid is not None and last is not None and abs(new_mid - last) >= HOT_MOVE:
        hot_until = now_s + HOT_FOR_S
    return hot_until, (HOT_POLL_S if now_s < hot_until else COLD_POLL_S)


def http_get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


class Stream:
    """One call at a time, at least GAP_S between calls; after a 429 a wait that doubles up to BACKOFF_MAX_S."""

    def __init__(self, fetch=None, clock=time.time, sleep=time.sleep):
        self.fetch, self.clock, self.sleep = fetch or http_get, clock, sleep
        self.next_ok, self.backoff, self.n429 = 0.0, BACKOFF_S, 0

    def get(self, url):
        wait = self.next_ok - self.clock()
        if wait > 0:
            self.sleep(wait)
        st, body, date = self.fetch(url)
        t = int(self.clock() * 1000)
        if st == 429:
            self.n429 += 1
            self.next_ok = self.clock() + self.backoff
            self.backoff = min(BACKOFF_MAX_S, self.backoff * 2)
        else:
            self.next_ok = self.clock() + GAP_S
            if st == 200:
                self.backoff = BACKOFF_S
        return st, body, date, t


def suffix(event_ticker):
    return event_ticker.split("-", 1)[1] if "-" in event_ticker else ""


def list_games(stream, group):
    """{game suffix: {"ml": event, "spread": event, "total": event}} for the open events of one group's three series."""
    games = {}
    for kind, series in zip(("ml", "spread", "total"), group):
        st, body, _d, _t = stream.get("%s/events?series_ticker=%s&status=open&limit=200" % (BASE, series))
        if st != 200 or not isinstance(body, dict):
            continue
        for e in body.get("events", []):
            t = e.get("event_ticker") if isinstance(e, dict) else None
            if t and suffix(t):
                games.setdefault(suffix(t), {})[kind] = t
    return {k: v for k, v in games.items() if "ml" in v}


def row(t_ms, date, event, kind, m):
    return [t_ms, date, event, kind, m.get("ticker"), m.get("floor_strike", m.get("strike_type", "")), m.get("yes_bid_dollars"), m.get("yes_ask_dollars"),
            m.get("yes_bid_size_fp"), m.get("yes_ask_size_fp"), m.get("last_price_dollars"), m.get("volume_fp")]


def run(outdir, cycle_hours=4, stream=None, now_fn=time.time):
    stream = stream or Stream()
    end = (int(now_fn() // (cycle_hours * 3600)) + 1) * cycle_hours * 3600
    os.makedirs(outdir, exist_ok=True)
    obs_f = open(os.path.join(outdir, "obs.csv"), "a", newline="")
    cov_f = open(os.path.join(outdir, "coverage.csv"), "a", newline="")
    obs, cov = csv.writer(obs_f), csv.writer(cov_f)
    obs.writerow(COLS)
    cov.writerow(COVER)
    games, follow, due, cover = {}, {}, {}, {}
    last_list = -1e9
    try:
        while True:
            now = now_fn()
            if now >= end or past_end(now):
                break
            if now - last_list >= LIST_EVERY_S:
                last_list = now
                for group in GROUPS.values():
                    games.update(list_games(stream, group))
            ready = sorted((due.get(g, 0), g) for g in games if due.get(g, 0) <= now)
            hot = [g for _d, g in ready if follow.get(g, {}).get("hot_until", 0) > now]
            cold = [g for _d, g in ready if g not in hot]
            for g in (hot[:MAX_HOT] + cold[:4]) or []:
                ev = games[g]
                st_info = follow.setdefault(g, {"tickers": {}, "hot_until": 0, "last_mid": None})
                cv = cover.setdefault(g, [0, 0, 0, None, None])
                ml_mid = None
                for kind in ("ml", "spread", "total"):
                    if kind not in ev:
                        continue
                    cv[0] += 1
                    st, body, date, t_ms = stream.get("%s/markets?event_ticker=%s" % (BASE, ev[kind]))
                    if st == 429:
                        cv[2] += 1
                    if st != 200 or not isinstance(body, dict):
                        continue
                    cv[1] += 1
                    cv[3] = cv[3] or t_ms
                    cv[4] = t_ms
                    markets = [m for m in body.get("markets", []) if isinstance(m, dict)]
                    if kind not in st_info["tickers"]:
                        st_info["tickers"][kind] = choose(kind, markets)
                    keep = set(st_info["tickers"][kind])
                    for m in markets:
                        if m.get("ticker") in keep:
                            obs.writerow(row(t_ms, date, ev[kind], kind, m))
                            if kind == "ml" and ml_mid is None:
                                ml_mid = mid(m)
                st_info["hot_until"], wait = next_poll(st_info, now_fn(), ml_mid)
                st_info["last_mid"] = ml_mid if ml_mid is not None else st_info["last_mid"]
                due[g] = now_fn() + wait
            obs_f.flush()
            time.sleep(1.0)
    finally:
        for g, cv in sorted(cover.items()):
            cov.writerow([games.get(g, {}).get("ml", g)] + cv)
        obs_f.close()
        cov_f.close()


if __name__ == "__main__":
    if past_end(time.time()):
        print("past the end date: nothing to record")
        sys.exit(0)
    hours = 4
    if "--cycle-hours" in sys.argv:
        hours = int(sys.argv[sys.argv.index("--cycle-hours") + 1])
    run(sys.argv[1], hours)
