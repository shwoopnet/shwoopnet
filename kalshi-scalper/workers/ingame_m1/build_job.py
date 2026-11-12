#!/usr/bin/env python3
"""Build the kalshi-pull job for the in-game lag MEASUREMENT (step 1 of the card
workers/IDEA_DESK_B_INGAME_CARD.md; zero tries; no trade is scored). Rebuilt ONCE on Nov 12, 2026
at the Head of R&D's direction, from a longer FIXED list, before any candle was pulled.

Source of the list, for tickers and close times ONLY (no price, no result is read from it):
Refinement's committed files on branch claude/refine-live, kalshi-scalper/refine_tools/
  SPREAD_CELL1_EVENTS.json   [series, event ticker, close time] of every listed spread event
  jobs/SPREADCELL1.json      its ticker_allowlist: the market tickers of those events

Pinned sample: every NBA, NHL and NFL event in that list whose close time is from
2026-10-20 00:00:00 UTC to 2026-11-11 23:59:59 UTC.

Markets asked for, chosen WITHOUT any price: both moneyline markets, and for each team its two
lowest spread strikes in the list (the strikes that are live when a game is close).

Usage: python3 build_job.py SPREAD_CELL1_EVENTS.json SPREADCELL1.json <out dir>
Writes games.json and two job files, INGAMELAG_M1A.json and INGAMELAG_M1B.json (one measurement, two pulls).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

START_UTC = "2026-10-20T00:00:00Z"
END_UTC = "2026-11-11T23:59:59Z"
SERIES = {"KXNBASPREAD": ("NBA", "KXNBAGAME"), "KXNHLSPREAD": ("NHL", "KXNHLGAME"), "KXNFLSPREAD": ("NFL", "KXNFLGAME")}
PLAY_MIN = {"NBA": 150, "NHL": 165, "NFL": 195}     # a generous game length, minutes
LATE_CLOSE_MIN = 100                                 # the market can close this long after the game is decided
TAIL_S = 120


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def split(t):
    m = re.match(r"^(.*?)(\d+)$", t.rsplit("-", 1)[1])
    return (m.group(1), int(m.group(2))) if m else (None, None)


def main():
    events = json.load(open(sys.argv[1]))["events"]
    allow = json.load(open(sys.argv[2]))["ticker_allowlist"]
    out = sys.argv[3]
    by_event = {}
    for t in allow:
        by_event.setdefault(t.rsplit("-", 1)[0], []).append(t)
    lo, hi = ts(START_UTC), ts(END_UTC)
    rows, skipped = [], 0
    for series, ev, close in sorted(events, key=lambda e: (e[2], e[1])):
        if series not in SERIES or not (lo <= close <= hi):
            continue
        sport, game_series = SERIES[series]
        name = ev.split("-", 1)[1]
        strikes = {}
        for t in by_event.get(ev, []):
            code, n = split(t)
            if code:
                strikes.setdefault(code, []).append((n, t))
        codes = sorted(strikes)
        teams = name[7:]                              # after the date, e.g. 26NOV10 + BOSPHI
        if len(codes) == 1:                           # only one team has spread strikes: the other code is what is left of the name
            c = codes[0]
            other = teams[len(c):] if teams.startswith(c) else (teams[:-len(c)] if teams.endswith(c) else None)
            codes = sorted([c, other]) if other else codes
        if len(codes) != 2 or teams not in (codes[0] + codes[1], codes[1] + codes[0]):
            skipped += 1
            continue
        spread = [t for c in sorted(strikes) for _n, t in sorted(strikes[c])[:2]]
        if not spread:
            skipped += 1
            continue
        rows.append({"sport": sport, "game": name, "event": ev, "ml": ["%s-%s-%s" % (game_series, name, c) for c in codes], "spread": spread,
                     "list_close_ts": close, "start_ts": close - 60 * (PLAY_MIN[sport] + LATE_CLOSE_MIN), "end_ts": close + TAIL_S})
    # One moneyline ticker is enough for the reader (the other side is its mirror), so only the first is asked for: smaller answers.
    asked = lambda r: [r["ml"][0]] + r["spread"]
    half = (len(rows) + 1) // 2
    jobs = []
    for part, chunk, base in (("A", rows[:half], 0), ("B", rows[half:], half)):
        reqs = [{"id": "g%03d_%s_%s" % (base + k + 1, r["sport"], r["game"]), "path": "/markets/candlesticks",
                 "params": {"market_tickers": ",".join(asked(r)), "start_ts": r["start_ts"], "end_ts": r["end_ts"], "period_interval": 1}}
                for k, r in enumerate(chunk)]
        jobs.append({
            "job_id": "INGAMELAG_M1" + part, "owner": "DESK_B",
            "registration": "kalshi-scalper/workers/IDEA_DESK_B_INGAME_CARD.md",
            "purpose": "In-game lag card, step 1, part %s of 2: a MEASUREMENT with zero tries. One minute candles of one moneyline market and four low spread strikes for each NBA, NHL and NFL game of a fixed list (closes 2026-10-20 to 2026-11-11). No trade is scored." % part,
            "heldout": "none (a measurement of quote timing; no settlement result is read and no rule is scored). The spread markets are also the unread sample of W-SPREAD-CELL1: the reader uses in-play candles only and prints no pre-game price and no outcome.",
            "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks",
                                   "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
            "series_allowlist": [], "ticker_allowlist": sorted({t for r in chunk for t in asked(r)}),
            "max_requests": len(reqs) + 15, "requests": reqs,
            "notes": "One batched request per game, 3 to 5 tickers, about 4 to 5 hours of 1 minute candles ending at the market's close. The fixed list of 215 games is split into two jobs (A then B) only to stay under the 200 MB a run size cap; the two answers are ONE measurement, read once, and the list is never extended.",
            "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                           "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}})
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "games.json"), "w"), indent=1)
    for j in jobs:
        json.dump(j, open(os.path.join(out, j["job_id"] + ".json"), "w"), indent=1)
    print("games", len(rows), {s: sum(1 for r in rows if r["sport"] == s) for s in PLAY_MIN}, "| skipped", skipped, "| requests", [len(j["requests"]) for j in jobs])


if __name__ == "__main__":
    main()
