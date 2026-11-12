#!/usr/bin/env python3
"""INPLAYJUMP PILOT job (Head-approved Nov 12, 2026): ONE candle batch per family on its first development days, for the cost and tradeability line only. Offline: sends nothing.
  python3 -I build_inplayjump_pilot.py <INPLAYJUMP_SERIES.json> <stage 1 (lists) run folder> <outdir>
The lists run folder is the ONLY placeholder: substitute it once the lists answer lands. Clock families: window = S - 70 minutes (S = the ticker's US Eastern start) to the batch's last close, so one pull also serves PREMOVE;
tennis: the market's open time to the last close (Amendment 2). Per family the first matches by close time (development window only, Tie never) up to tickers <= 100 and minutes x tickers <= 9,000. No result is read by the pilot."""
import gzip, json, os, sys, calendar, time, re, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "desk_a_verify"))
from inplayjump import clock_start
def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def main(series_path, folder, outdir):
    import heldout_guard; heldout_guard.refuse_heldout(folder, "pilot builder")
    S = json.load(open(series_path)); man = json.load(open(os.path.join(folder, "manifest.json"))); mk = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        b = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            c = iso_ts(m.get("close_time") or "")
            if m.get("ticker") and c: mk[m["ticker"]] = (m["ticker"].split("-")[0], c, iso_ts(m.get("open_time") or ""))       # the result field is NOT read here
    reqs = []; info = {}
    for f in S["families_ranked_by_events"]:
        lo, hi = iso_ts(f["development"]["closes_from"]), iso_ts(f["development"]["closes_before"]); clock = f["in_play"] == "clock"
        items = sorted(((t, c) for t, (s, c, o) in mk.items() if s in f["series"] and lo <= c < hi and not t.endswith("-TIE")), key=lambda x: (x[1], x[0]))
        def start(t, c): return (clock_start(t) - 5 * 60) if clock and clock_start(t) else (mk[t][2] or c - 20 * 3600)       # Amendment 2: no window anchored on the close; tennis from the market open
        cur = []
        for it in items:
            trial = cur + [it]; s0 = min(start(t, c) for t, c in trial); span = (trial[-1][1] - s0) / 60
            if cur and (len(trial) > 100 or span * len(trial) > 9000): break
            cur = trial
        if not cur: info[f["family"]] = 0; continue
        s0 = min(start(t, c) for t, c in cur)
        reqs.append(dict(id="p%02d" % len(reqs), path="/markets/candlesticks", params={"market_tickers": ",".join(t for t, _ in cur), "start_ts": s0, "end_ts": cur[-1][1], "period_interval": 1})); info[f["family"]] = len(cur)
    tk = sorted({t for r in reqs for t in r["params"]["market_tickers"].split(",")})
    job = {"job_id": "INPLAYJUMP_PILOT", "owner": "DESK_A", "registration": "kalshi-scalper/workers/inplayjump/INPLAYJUMP_REGISTRATION.md", "purpose": "INPLAYJUMP pilot: one 1 minute candle batch per family on its first development days; cost and tradeability only, no result read.",
           "heldout": "none: development windows only", "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": sorted({t.split("-")[0] for t in tk}), "ticker_allowlist": tk, "max_requests": len(reqs), "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"}, "requests": reqs}
    os.makedirs(outdir, exist_ok=True); json.dump(job, open(os.path.join(outdir, "INPLAYJUMP_PILOT.json"), "w"), indent=1)
    print("pilot requests %d | contracts %d | contracts per family %s" % (len(reqs), len(tk), info))
if __name__ == "__main__": main(*sys.argv[1:4])
