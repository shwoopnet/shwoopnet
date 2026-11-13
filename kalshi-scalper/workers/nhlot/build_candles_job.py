#!/usr/bin/env python3
"""NHLOT price measurement, stage 2: build the candle job from the NHLOT_LISTS answers.
Committed Nov 12, 2026, before any NHL list or candle was pulled.

Uses ONLY tickers, event tickers and close times from the list answers. It never reads a
result or a price field.

Sample (pinned in the card): the 150 most recently closed games, never extended. Games that
closed within 30 minutes of each other share one batched request (at most 5 games and 100
tickers). The request count therefore depends on how the close times cluster: about 40 if
games end in slates, at most 150 (one a game). The sample is never cut to save requests.

Usage: python3 build_candles_job.py <folder of the NHLOT_LISTS run> <out dir>
Writes games.json and NHLOT_CANDLES.json.
"""
import gzip
import json
import os
import sys
from collections import Counter
from datetime import datetime
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob

MAX_GAMES, MAX_REQUESTS, GROUP_GAMES, GROUP_TICKERS, GROUP_SPAN_S = 150, 150, 5, 100, 1800
BEFORE_S, AFTER_S = 50 * 60, 120
MAX_CANDLES = 8500        # tickers times minutes in one batched request; the exchange's limit is 10,000 candles (V2's usweep2.py)


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def main():
    run, out = sys.argv[1], sys.argv[2]
    man = json.load(open(os.path.join(run, "manifest.json")))
    games = {}
    for row in man.get("rows", []):
        series = row.get("params", {}).get("series_ticker")
        if row.get("status") != 200 or series not in ("KXNHLGAME", "KXNHLTOTAL"):
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            ev, tk = m.get("event_ticker", ""), m.get("ticker", "")
            if "-" not in ev or not tk:
                continue
            g = games.setdefault(ev.split("-", 1)[1], {"ml": [], "total": [], "closes": Counter()})
            if series == "KXNHLGAME":
                g["ml"].append(tk)
                try:
                    g["closes"][ts(m["close_time"])] += 1
                except (KeyError, ValueError, TypeError):
                    pass
            else:
                g["total"].append(tk)
    rows = []
    for name, g in games.items():
        if len(set(g["ml"])) != 2 or len(set(g["total"])) < 4 or not g["closes"]:
            continue
        rows.append({"game": name, "ml": sorted(set(g["ml"])), "total": sorted(set(g["total"])), "close_ts": g["closes"].most_common(1)[0][0],
                     "ot": "KXNHLOT-%s-1" % name})   # the "game goes to overtime" market, built by name (seen in the Nov 10 census listing); a cross-check only
    rows.sort(key=lambda r: (-r["close_ts"], r["game"]))
    rows = rows[:MAX_GAMES]
    groups = []
    for r in rows:                                        # newest first; a group spans at most 30 minutes of close times
        n = len(r["ml"]) + len(r["total"]) + 1
        g = groups[-1] if groups else None
        minutes = lambda lo, hi: (hi + AFTER_S - (lo - BEFORE_S)) // 60 + 1
        if (g and len(g["games"]) < GROUP_GAMES and g["tickers"] + n <= GROUP_TICKERS and g["hi"] - r["close_ts"] <= GROUP_SPAN_S
                and (g["tickers"] + n) * minutes(r["close_ts"], g["hi"]) <= MAX_CANDLES):
            g["games"].append(r)
            g["tickers"] += n
            g["lo"] = r["close_ts"]
        else:
            groups.append({"games": [r], "tickers": n, "hi": r["close_ts"], "lo": r["close_ts"]})
    groups = groups[:MAX_REQUESTS]
    kept = [r for g in groups for r in g["games"]]
    reqs = [{"id": "n%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(t for r in g["games"] for t in r["ml"] + r["total"] + [r["ot"]]), "start_ts": g["lo"] - BEFORE_S, "end_ts": g["hi"] + AFTER_S, "period_interval": 1}}
            for k, g in enumerate(groups)]
    job = {"job_id": "NHLOT_CANDLES", "owner": "DESK_B", "registration": "kalshi-scalper/workers/IDEA_DESK_B_WAVE3.md",
           "purpose": "NHLOT price measurement (zero tries), stage 2: one minute candles of both moneyline markets, every total-goals strike and the game-goes-to-overtime market for the last 50 minutes before each game market closed. No outcome is read by the reader.",
           "heldout": "none (a price measurement; no outcome is read and no rule is scored)",
           "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": [], "ticker_allowlist": sorted({t for r in kept for t in r["ml"] + r["total"] + [r["ot"]]}),
           "max_requests": MAX_REQUESTS, "requests": reqs,
           "notes": "Built by workers/nhlot/build_candles_job.py from the NHLOT_LISTS answers: the most recently closed games (at most 150), grouped by close time, at most 5 games a request. The sample is never extended.",
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump(kept, open(os.path.join(out, "games.json"), "w"), indent=1)
    json.dump(job, open(os.path.join(out, "NHLOT_CANDLES.json"), "w"), indent=1)
    print(f"games in the lists {len(games)} | usable {len(rows)} (of at most {MAX_GAMES}) | kept {len(kept)} | requests {len(reqs)} (cap {MAX_REQUESTS})")


if __name__ == "__main__":
    main()
