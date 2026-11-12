#!/usr/bin/env python3
"""WXDAYEND (card 74) finish-the-count tool. Testing Desk, Nov 12, 2026. Research only: reads files, sends nothing. Jobs carry owner MAIN because the runner (scripts/kalshi_pull.py OWNERS) has no Testing Desk entry; Main dispatches.

Registered rule (kalshi-scalper/refine_tools/CARDS_74_84_REGISTRATION_AND_RESULT.md on claude/refine-live, unchanged here):
  40 city-days (NYC, LAX, DEN, DAL x events 2026-11-01..11-10; the only events with a window after the standard-time climate day ends).
  FAIL if fewer than 3 of the 40 show a YES ask at or under 0.96 on the winning bracket AFTER the climate day ends.
Basis fixed BEFORE any answer is read (this file is committed first):
  day_end = market close_time - 3600 s (close is one hour after the standard-time day ends for these events).
  A city-day "shows" a price if any 1 minute candle with end_period_ts > day_end has yes_ask CLOSE <= 0.96 (the basis Refinement read).
  Reported beside it, not used for the verdict: the same test on yes_ask LOW, and the count of candles with no ask at all.
  A city-day with no candle after day_end, or with no ask, does NOT show a price.
  The 20 city-days Refinement already read (NYC Nov 1-9, LAX Nov 1-9, 2 Denver) are taken from its record (0 of 20 under 1.00);
  where this pull re-reads a city-day, the new read replaces the old one.
Commands:  build-a  |  build-b <A_run_dir>  |  score <A_run_dir> <B_run_dir>   (run dirs are folders of kalshi-pull-data: manifest.json + NNNN.json.gz)
"""
import gzip, json, os, sys

TH = 0.96
PRIOR_READ = {}   # city-days read by Refinement, all 0 under 1.00: {"KXHIGHNY": 1..9, "KXHIGHLAX": 1..9}
for s in ("KXHIGHNY", "KXHIGHLAX"):
    for d in range(1, 10):
        PRIOR_READ["%s-26NOV%02d" % (s, d)] = {"shows": False, "src": "refinement"}
SERIES = ("KXHIGHNY", "KXHIGHLAX", "KXHIGHDEN", "KXHIGHTDAL")
UNIVERSE = ["%s-26NOV%02d" % (s, d) for s in SERIES for d in range(1, 11)]   # 40 event tickers
HERE = os.path.dirname(os.path.abspath(__file__))
DESK_A_JOB = os.path.join(HERE, "wxdayend_desk_a_job.json")


def price(node, key):
    """Dollars from a candle price object; accepts '<key>_dollars' strings or cent integers. None if absent."""
    if not isinstance(node, dict):
        return None
    for k in (key + "_dollars", key):
        v = node.get(k)
        if v is None or v == "":
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        return f / 100.0 if (k == key and f > 1.0) else f
    return None


def event_of(ticker):
    return ticker.rsplit("-", 1)[0]


def build_a(desk_a=DESK_A_JOB):
    j = json.load(open(desk_a))
    reqs, tk = [], []
    for i, r in enumerate(x for x in j["requests"] if x["ep"] == "candles"):
        tk.append(r["ticker"])
        reqs.append({"id": "c%02d_%s" % (i + 1, r["ticker"]), "path": "/markets/candlesticks",
                     "params": {"market_tickers": r["ticker"], "start_ts": r["start_ts"], "end_ts": r["end_ts"], "period_interval": 1}})
    for i, r in enumerate(x for x in j["requests"] if x["ep"] == "markets_list"):
        reqs.append({"id": "l%02d_%s" % (i + 1, r["event"]), "path": "/markets", "params": {"event_ticker": r["event"], "status": "settled", "limit": 100}})
    return job("WXDAYEND_A", "Card 74 finish, part A: final 2 hours of 1 minute candles of the winning bracket for 18 city-days (Dallas and Denver, Nov 1 to 9) plus the settled market lists of the 4 Nov 10 events (to find the winners).", reqs, tk, 22)


def job(job_id, purpose, reqs, tickers, cap):
    return {"job_id": job_id, "owner": "MAIN", "registration": "kalshi-scalper/workers/testing/WXDAYEND_REGISTRATION.md", "purpose": purpose,
            "heldout": "none (a development existence count; no held-out data exists or is read)",
            "allowed_endpoints": [
                {"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]},
                {"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["event_ticker", "status", "limit", "cursor"]}],
            "series_allowlist": list(SERIES), "ticker_allowlist": sorted(set(tickers)), "max_requests": cap,
            "notes": "One request each, no paging. Candle windows are the 2 hours ending at the market close; the last hour is after the standard-time climate day ends.",
            "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                           "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": reqs}


def answers(run_dir):
    """{request id: parsed body} for the answers a run stored."""
    m = json.load(open(os.path.join(run_dir, "manifest.json")))
    out = {}
    for row in m["rows"]:
        if row.get("status") == 200 and row.get("file"):
            out[row["id"]] = json.load(gzip.open(os.path.join(run_dir, row["file"])))
    return m, out


def winners_from_lists(a_run):
    """For each Nov 10 event list in run A: the one settled market whose result is yes -> (ticker, close_ts). None if not exactly one."""
    from datetime import datetime
    _, ans = answers(a_run)
    res = {}
    for rid, body in ans.items():
        if not rid.startswith("l"):
            continue
        ev = rid.split("_", 1)[1]
        yes = [m for m in body.get("markets", []) if m.get("result") == "yes"]
        if len(yes) != 1:
            res[ev] = None
            continue
        ct = datetime.fromisoformat(yes[0]["close_time"].replace("Z", "+00:00")).timestamp()
        res[ev] = (yes[0]["ticker"], int(ct))
    return res


def build_b(a_run):
    w = winners_from_lists(a_run)
    reqs, tk = [], []
    for ev, v in sorted(w.items()):
        if v is None:
            continue
        t, ct = v
        tk.append(t)
        reqs.append({"id": "c_%s" % t, "path": "/markets/candlesticks", "params": {"market_tickers": t, "start_ts": ct - 7200, "end_ts": ct, "period_interval": 1}})
    return job("WXDAYEND_B", "Card 74 finish, part B: final 2 hours of 1 minute candles of the winning bracket of the 4 Nov 10 events found by part A.", reqs, tk, max(len(reqs), 1)), w


def read_candles(body, ticker):
    nodes = body.get("markets") or [body]
    for n in nodes:
        t = n.get("market_ticker") or n.get("ticker") or ticker
        if t == ticker and isinstance(n.get("candlesticks"), list):
            return n["candlesticks"]
    return []


def city_day(ticker, end_ts, candles):
    """Verdict inputs for one city-day. end_ts = the request's end_ts = the market close; day_end = close - 3600."""
    day_end = end_ts - 3600
    post = [c for c in candles if int(c["end_period_ts"]) > day_end]
    closes = [price(c.get("yes_ask"), "close") for c in post]
    lows = [price(c.get("yes_ask"), "low") for c in post]
    cl = [x for x in closes if x is not None]
    lw = [x for x in lows if x is not None]
    return {"ticker": ticker, "event": event_of(ticker), "n_post_candles": len(post), "n_no_ask": len(post) - len(cl),
            "min_ask_close": min(cl) if cl else None, "min_ask_low": min(lw) if lw else None,
            "shows": bool(cl) and min(cl) <= TH, "shows_low": bool(lw) and min(lw) <= TH}


def score(a_run, b_run=None):
    rows = {}
    for run in (a_run, b_run):
        if not run:
            continue
        m, ans = answers(run)
        for r in m["job"]["requests"]:
            if r["path"] != "/markets/candlesticks" or r["id"] not in ans:
                continue
            t = r["params"]["market_tickers"]
            rows[event_of(t)] = city_day(t, r["params"]["end_ts"], read_candles(ans[r["id"]], t))
    for ev, v in PRIOR_READ.items():
        rows.setdefault(ev, dict(v, event=ev))
    read = [e for e in UNIVERSE if e in rows]
    n_show = sum(1 for e in read if rows[e]["shows"])
    n_low = sum(1 for e in read if rows[e].get("shows_low", rows[e]["shows"]))
    unread = [e for e in UNIVERSE if e not in rows]
    if unread:
        verdict = "INCOMPLETE: %d of 40 city-days unread" % len(unread)
        if n_show >= 3:
            verdict += " (the kill rule can no longer fire: %d already show an ask at or under %.2f)" % (n_show, TH)
    else:
        verdict = "FAIL (registered kill rule: %d of 40 under 3)" % n_show if n_show < 3 else "KILL RULE NOT HIT: %d of 40 show an ask at or under %.2f after the day ends" % (n_show, TH)
    return {"city_days_read": len(read), "city_days_unread": unread, "show_ask_close_le_%.2f" % TH: n_show, "show_ask_low_le_%.2f" % TH: n_low,
            "verdict": verdict, "label": "no evidence at n = %d city-days for any profit claim (existence count only)" % len(read),
            "book_replay_line": "NOT AVAILABLE: no order book exists for these brackets; candle asks only. Any city-day that shows <= %.2f would still need a book or haircut line before it is read as tradable." % TH,
            "differs_by_basis": n_show != n_low, "rows": {e: rows[e] for e in read}}


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "build-a":
        print(json.dumps(build_a(), indent=1))
    elif c == "build-b":
        j, w = build_b(sys.argv[2])
        print(json.dumps(j, indent=1))
        print("winners:", json.dumps(w), file=sys.stderr)
    elif c == "score":
        print(json.dumps(score(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), indent=1))
    else:
        print(__doc__)
