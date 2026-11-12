#!/usr/bin/env python3
"""Build the kalshi-pull job for the in-game lag MEASUREMENT (step 1 of the card
workers/IDEA_DESK_B_INGAME_CARD.md; zero tries; no trade is scored).

Reads a checkout of branch sports-data (the in-game recorder's files), finds the games that
finished inside the recording, and writes:
  games.json            one row per game: the six tickers the recorder followed and the window
  INGAMELAG_M1.json     the job file, one batched 1 minute candle request per game

Only the recorder's own files are read. No network, no key.
Usage: python3 build_job.py <checkout of sports-data> <out dir>
"""
import csv
import glob
import gzip
import json
import os
import re
import sys

PLAY_S = {"NBA": int(2.5 * 3600), "NHL": int(2.75 * 3600), "NFL": int(3.25 * 3600)}   # length of the window before the decided minute
LEAD_S, TAIL_S = 900, 720
MAX_GAMES = 58                                                                        # the job cap is 60


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def mid(b, a):
    return (a + b) / 2.0 if (a is not None and b is not None and b > 0 and 0 < a <= 1) else None


def main():
    root, out = sys.argv[1], sys.argv[2]
    games = {}
    for p in sorted(glob.glob(os.path.join(root, "ingame", "*", "*", "obs.csv.gz"))):
        for r in csv.DictReader(gzip.open(p, "rt", newline="")):
            m = re.match(r"KX(NBA|NHL|NFL)(GAME|SPREAD|TOTAL)-(.+)$", r.get("event", ""))
            if not m:
                continue
            g = games.setdefault((m.group(1), m.group(3)), {"GAME": {}, "SPREAD": {}, "TOTAL": {}})
            g[m.group(2)].setdefault(r["ticker"], []).append((int(r["t_recv_ms"]) / 1000.0, num(r["yes_bid"]), num(r["yes_ask"])))
    rows = []
    for (sport, name), g in sorted(games.items()):
        if len(g["GAME"]) != 2 or not g["SPREAD"]:
            continue
        ml = sorted(g["GAME"])
        path = [(t, mid(b, a)) for t, b, a in sorted(g["GAME"][ml[0]])]
        path = [(t, x) for t, x in path if x is not None]
        if len(path) < 5 or not (path[-1][1] >= 0.97 or path[-1][1] <= 0.03):
            continue                                   # not finished inside the recording
        i = len(path) - 1
        while i > 0 and (path[i - 1][1] >= 0.97 or path[i - 1][1] <= 0.03):
            i -= 1
        end = int(path[i][0])
        rows.append({"sport": sport, "game": name, "ml": ml, "spread": sorted(g["SPREAD"])[:2], "total": sorted(g["TOTAL"])[:2],
                     "decided_ts": end, "start_ts": end - PLAY_S[sport] - LEAD_S, "end_ts": end + TAIL_S})
    rows.sort(key=lambda r: (r["decided_ts"], r["game"]))
    rows = rows[:MAX_GAMES]
    tickers = sorted({t for r in rows for t in r["ml"] + r["spread"] + r["total"]})
    reqs = [{"id": "g%03d_%s_%s" % (k + 1, r["sport"], r["game"]), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(r["ml"] + r["spread"] + r["total"]), "start_ts": r["start_ts"], "end_ts": r["end_ts"], "period_interval": 1}}
            for k, r in enumerate(rows)]
    job = {
        "job_id": "INGAMELAG_M1", "owner": "DESK_B",
        "registration": "kalshi-scalper/workers/IDEA_DESK_B_INGAME_CARD.md",
        "purpose": "In-game lag card, step 1: a MEASUREMENT with zero tries. One minute candles of the six markets the in-game recorder followed in each game that finished inside the recording. No trade is scored.",
        "heldout": "none (a measurement of quote timing; no outcome is read and no rule is scored)",
        "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks",
                               "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
        "series_allowlist": [], "ticker_allowlist": tickers,
        "max_requests": 60, "requests": reqs,
        "notes": "One batched request per game (2 moneyline, 2 spread, up to 2 total tickers; about 3 to 4 hours of 1 minute candles). The batched candle endpoint has not been seen to answer for sports markets: if the first three requests fail the run stops by the script's own rule and nothing more is spent; the fallback is one request per market for the moneyline and spread tickers only, as a new reviewed job.",
        "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
        "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                       "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "games.json"), "w"), indent=1)
    json.dump(job, open(os.path.join(out, "INGAMELAG_M1.json"), "w"), indent=1)
    print("games", len(rows), {s: sum(1 for r in rows if r["sport"] == s) for s in PLAY_S}, "| tickers", len(tickers), "| requests", len(reqs))


if __name__ == "__main__":
    main()
