#!/usr/bin/env python3
"""NC15 hourly candle job builder (Idea Desk A, Nov 14, 2026, step 3 of the NC15 history pull; the Head's order after the probe). Offline, sends nothing.
  python3 -I build_nc15_candles.py <landed NC15_LISTS run folder> <out dir>
Reads ONLY the fields `ticker` and `close_time` of the landed lists run (after the whole-run proof of spxoi1_threshold.check_run); it reads nothing else from a market. Tickers are never typed: every ticker in a job comes from the lists answer.
One request per HOUR BLOCK: the kept closes in (H, H + 3600] for all 11 series, up to 44 tickers (the probe showed a batched hour returns each ticker's own window, 15 one minute candles, plus one candle ending at close + 60 s), start_ts = the earliest close in the block - 900, end_ts = the latest close, period_interval 1. EVENT830's eight series are CUT +-5 minutes around the 13:30Z closes on its calendar dates up to the end date (Auditor B). End date 2026-11-13T23:59Z.
STANDING READER RULE (the Head): a reader of these files drops any candle ending after its market's close."""
import sys, os, json, math, calendar, time, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, "..", "..", "desk_a_verify"))
from build_nc15_jobs import SERIES, REGISTRATION, HELDOUT, STOP, base, ts
END = ts("2026-11-13T23:59:00Z")
EVENT830_SERIES = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"]
EVENT830_DATES = ["2026-11-05", "2026-11-06", "2026-11-10", "2026-11-12", "2026-11-13"]      # SLOT_CALENDARS.EVENT830 rows up to the end date (functions/kalshiSlotLib.js on main); each is a 13:30Z close
CUT_S = 300
RETRY_SLACK = 12                                                                             # the runner counts every request SENT against the cap, retries included
READER_RULE = "STANDING READER RULE: drop any candle ending after its market's close (a batched hour returns one extra candle ending at close + 60 s for the closes before the block's last close)."
def parse_lists(folder):
    import spxoi1_threshold as S
    man = S.check_run(folder)
    job = man.get("job"); reqs = job.get("requests") if isinstance(job, dict) else None
    if not isinstance(reqs, list) or not reqs: sys.exit("REFUSED: %s carries no embedded job request list" % folder)
    if {r.get("id") for r in reqs if isinstance(r, dict)} - {r.get("id") for r in man["rows"]}: sys.exit("REFUSED: %s has request ids of its job with no rows" % folder)
    for b in S.bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []): yield m.get("ticker"), m.get("close_time")
def plan(lists):
    closes, c = {}, collections.Counter()
    for tk, ct in parse_lists(lists):
        if not isinstance(tk, str) or not isinstance(ct, str): c["no_close"] += 1; continue
        s = tk.split("-")[0]
        if s not in SERIES: c["unknown_series"] += 1; continue
        try: cl = ts(ct)
        except ValueError: c["no_close"] += 1; continue
        if cl > END: c["after_end"] += 1; continue
        if s in EVENT830_SERIES and any(abs(cl - ts(d + "T13:30:00Z")) <= CUT_S for d in EVENT830_DATES): c["event830"] += 1; continue
        closes[tk] = cl
    return {"closes": closes, "dropped_event830": c["event830"], "ignored_after_end": c["after_end"], "ignored_unknown_series": c["unknown_series"], "ignored_no_close": c["no_close"]}
def build_jobs(pl, max_per_file=1188):
    blocks = collections.defaultdict(list)
    for tk, cl in pl["closes"].items(): blocks[(cl - 1) // 3600].append(tk)
    reqs = []
    for i, h in enumerate(sorted(blocks), 1):
        tk = sorted(blocks[h]); cl = [pl["closes"][t] for t in tk]
        reqs.append({"id": "h%05d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(tk), "start_ts": min(cl) - 900, "end_ts": max(cl), "period_interval": 1}})
    ep = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    jobs = []
    for f in range(math.ceil(len(reqs) / max_per_file)):
        part = reqs[f * max_per_file:(f + 1) * max_per_file]; tks = sorted({t for r in part for t in r["params"]["market_tickers"].split(",")})
        jid = "NC15_CANDLES_%d" % (f + 1)
        jobs.append(base(jid, "1 minute candles of each NC15 market's whole 15 minute window, batched one hour block per request (up to 44 tickers), built from the landed NC15_LISTS run; development history to 2026-11-13T23:59Z.", ep, tks, len(part) + RETRY_SLACK, part,
                         "%s EVENT830's eight series are cut +-5 minutes around the 13:30Z closes on %s (its forward windows). Part %d of %d, %d requests, cap %d (requests + %d for retries). Pacing 5.0 s. Tickers and closes from the landed lists run only." % (READER_RULE, ", ".join(EVENT830_DATES), f + 1, math.ceil(len(reqs) / max_per_file), len(part), len(part) + RETRY_SLACK, RETRY_SLACK)))
    return jobs
def totals(jobs):
    n = sum(len(j["requests"]) for j in jobs)
    return {"requests": n, "files": len(jobs), "hours_at_5s": 5 * n / 3600}
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    pl = plan(os.path.abspath(sys.argv[1])); jobs = build_jobs(pl); os.makedirs(sys.argv[2], exist_ok=True)
    for j in jobs:
        with open(os.path.join(sys.argv[2], j["job_id"] + ".json"), "w") as f: json.dump(j, f, indent=1); f.write("\n")
    t = totals(jobs); print("kept tickers %d | dropped for EVENT830 %d | after the end date %d | unknown series %d | no close_time %d" % (len(pl["closes"]), pl["dropped_event830"], pl["ignored_after_end"], pl["ignored_unknown_series"], pl["ignored_no_close"]))
    print("requests %d in %d file(s) | %.2f hours at 5 s" % (t["requests"], t["files"], t["hours_at_5s"]))
