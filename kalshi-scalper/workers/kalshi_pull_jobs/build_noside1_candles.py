#!/usr/bin/env python3
"""Builds the request list of NOSIDE1_CANDLES (stage 2 of the approval NO-side pull, W-NO-ARM1) from the stage 1 answers. Offline: it sends no request.

  python3 -I build_noside1_candles.py <stage 1 run folder from the data branch> > NOSIDE1_CANDLES.json

Rules (from the registration and its amendments): development events only (third 0 and 1 of NOSIDE1_CUTS.json; the held-out third is never requested), series taken round robin one
event at a time in name order, events of a series in close-time order, every market of an event, hourly candles from 2 days before the close to the close, one request per market:
the live series endpoint for a market that closes after 2026-09-12 and the historical endpoint before it. Settled markets only. The total of stage 1 and stage 2 never passes 1,200."""
import gzip
import json
import os
import re
import sys
import calendar
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOTAL_CAP = 1200
CUTOVER = calendar.timegm(time.strptime("2026-09-12", "%Y-%m-%d"))


def iso_ts(s):
    if not isinstance(s, str):
        return None
    try:
        return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        return None


def read_markets(folder):
    """{event_ticker: [market objects]} from the stage 1 manifest and its answers."""
    man = json.load(open(os.path.join(folder, "manifest.json")))
    out = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row:
            continue
        body = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            if isinstance(m, dict) and m.get("ticker") and m.get("event_ticker") and m.get("result") in ("yes", "no"):
                out.setdefault(m["event_ticker"], {})[m["ticker"]] = m
    return man["requests_sent"], {e: list(v.values()) for e, v in out.items()}


def build(cuts, events, stage1_requests, total_cap=TOTAL_CAP):
    cap = total_cap - stage1_requests
    queues = []
    for series in sorted(cuts["series"]):
        dev = [e for e, third in cuts["series"][series]["events"] if third in (0, 1) and e in events]
        dev.sort(key=lambda e: (min(iso_ts(m.get("close_time")) or 0 for m in events[e]), e))
        queues.append((series, dev))
    reqs, tickers = [], set()
    while any(q for _, q in queues) and len(reqs) < cap:
        for series, q in queues:
            if not q:
                continue
            ev = q.pop(0)
            for m in sorted(events[ev], key=lambda x: x["ticker"]):
                close = iso_ts(m.get("close_time"))
                if close is None or len(reqs) >= cap:
                    continue
                live = close > CUTOVER
                path = ("/series/%s/markets/%s/candlesticks" % (series, m["ticker"])) if live else ("/historical/markets/%s/candlesticks" % m["ticker"])
                reqs.append({"id": m["ticker"], "path": path, "params": {"start_ts": close - 2 * 86400, "end_ts": close, "period_interval": 60}})
                tickers.add(m["ticker"])
    return reqs, sorted(tickers), cap


def main(folder):
    cuts = json.load(open(os.path.join(HERE, "NOSIDE1_CUTS.json")))
    n1, events = read_markets(folder)
    reqs, tickers, cap = build(cuts, events, n1)
    job = json.load(open(os.path.join(HERE, "NOSIDE1_CANDLES.json")))
    job.update({"status": "active", "max_requests": cap, "requests": reqs, "ticker_allowlist": tickers, "series_allowlist": sorted(cuts["series"]),
                "allowed_endpoints": [
                    {"name": "series_market_candlesticks", "method": "GET", "path_pattern": "/series/(?P<series>[A-Z0-9]{2,32})/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]},
                    {"name": "historical_market_candlesticks", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}]})
    json.dump(job, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
