#!/usr/bin/env python3
"""WHEEL0 coverage check for one landed candle run. COUNTS ONLY: no result is read (the lists are read with the result field untouched) and nothing is scored.
usage: python3 -I wheel0_coverage.py <candle run folder> <lists run folder> [<lists run folder> ...]
Prints one line: requests answered, bytes, markets asked for, markets with any candle, markets with a candle at all three looks (600, 360 and 180 s before the close)
and at every minute from 600 to 180 s, the first and last close, and SPLIT if the run is much over the size guide."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wheel0 as Z
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from listed_runs_guard import refuse_listed      # standing rule (h): runs named in HELDOUT_PULL_RUNS.md are refused (Nov 13)

GUIDE_MB_PER_REQUEST, SPLIT_FACTOR = 0.172, 1.5      # CFRTI_K_CANDLES: 37 MB for 215 requests; "much over" = half as much again


def main(candle_run, list_runs):
    Z.refuse_heldout(candle_run)
    refuse_listed(candle_run)
    for _lr in list_runs: refuse_listed(_lr)
    man = json.load(open(os.path.join(candle_run, "manifest.json"))); rows = man["rows"]; job = man.get("job", {})
    ok = sum(1 for r in rows if r.get("status") == 200 and r.get("file") and not r.get("truncated")); trunc = sum(1 for r in rows if r.get("truncated"))
    mb = sum(r.get("bytes", 0) for r in rows) / 1e6; planned = len(job.get("requests", [])) or len(rows)
    asked = set(job.get("ticker_allowlist") or [])
    mk, cnt = Z.read_markets(list_runs, with_result=False)
    series = sorted({t.split("-")[0] for t in asked}) or sorted({m["series"] for m in mk.values()})
    mk = {t: m for t, m in mk.items() if (t in asked if asked else m["series"] in series)}
    cd = Z.read_candles([candle_run], mk)
    anyc = sum(1 for t in mk if cd.get(t)); looks3 = full = two3 = 0
    for t, m in mk.items():
        c = cd.get(t) or {}
        if all((m["close"] - L) in c for L in Z.LOOKS): looks3 += 1
        if all((m["close"] - s) in c for s in range(180, 601, 60)): full += 1
        if all(((c.get(m["close"] - L) or (None, None))[0] is not None and (c.get(m["close"] - L) or (None, None))[1] is not None and 0 < c[m["close"] - L][0] < c[m["close"] - L][1] < 1) for L in Z.LOOKS): two3 += 1
    closes = sorted(m["close"] for t, m in mk.items() if cd.get(t)); iso = lambda x: time.strftime("%Y-%m-%d %H:%MZ", time.gmtime(x))
    guide = planned * GUIDE_MB_PER_REQUEST; split = mb > SPLIT_FACTOR * guide
    out = {"job": job.get("job_id"), "run_status": man.get("status"), "requests_answered": "%d of %d" % (ok, planned), "truncated_answers": trunc, "megabytes": round(mb, 1), "size_guide_megabytes": round(guide, 1),
           "series": series, "markets_asked_for": len(asked) or None, "markets_usable_after_rule_h_and_dates": len(mk), "markets_with_any_candle": anyc, "markets_with_a_candle_at_all_three_looks": looks3,
           "markets_two_sided_at_all_three_looks": two3, "markets_with_every_minute_600_to_180": full, "first_close": iso(closes[0]) if closes else None, "last_close": iso(closes[-1]) if closes else None,
           "list_reader_counts": cnt, "note": "counts only; no result read; nothing scored"}
    print(json.dumps(out, indent=1))
    print("ONE LINE: %s: %s requests answered, %.1f MB (guide %.1f)%s; %d markets, %d with any candle, %d with a candle at all three looks (%d two-sided at all three, %d with every minute); closes %s to %s." % (
        out["job"], out["requests_answered"], mb, guide, " SPLIT: much over the guide" if split else "", len(mk), anyc, looks3, two3, full, out["first_close"], out["last_close"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
