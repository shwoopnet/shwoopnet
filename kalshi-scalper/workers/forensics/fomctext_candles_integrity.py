#!/usr/bin/env python3
"""FOMCTEXT_CANDLES input integrity (Forensics desk, Nov 14, 2026; the Head's overnight item 1). Counts, times and hashes only: it reads the manifest, the job file, and from each answer ONLY the candle end times
(end_period_ts) and the number of candles; no price, bid, ask, volume or open interest field is touched.
Checks: (1) the run's request tickers equal the job's ticker allowlist exactly (set equality, no repeat); (2) every request window is 13:55 to 14:45 US Eastern on one date (start_ts and end_ts converted with the New York zone);
(3) the latest window end and the latest candle end are not after LIMIT_END (2026-04-29T18:45Z) and no candle is before its request's start; (4) HTTP status counts (200, 404, others), truncated rows, rows without a file;
(5) for every file, its sha256 on disk (the .gz bytes) and whether the manifest's own sha256 of the decompressed body equals the sha256 of the decompressed file; writes the "sha256  file" list to <out list>.
usage: python3 -I fomctext_candles_integrity.py <run folder> <job json> <out sha256 list>"""
import sys, os, json, gzip, hashlib, collections, re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from listed_runs_guard import refuse_listed

ET = ZoneInfo("America/New_York"); LIMIT_END = int(datetime(2026, 4, 29, 18, 45, tzinfo=timezone.utc).timestamp()); HELD_FROM = datetime(2026, 6, 17, tzinfo=timezone.utc).timestamp()
folder, jobp, outp = sys.argv[1:4]
for p in (os.path.abspath(folder), os.path.realpath(folder)):
    if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)): raise SystemExit("REFUSED: HELDOUT_ path")
refuse_listed(folder)
man = json.load(open(os.path.join(folder, "manifest.json"))); job = json.load(open(jobp)); rows = man["rows"]
allow = list(job["ticker_allowlist"]); tk = lambda r: re.match(r"^/historical/markets/([^/]+)/candlesticks$", r.get("path") or "").group(1)
req = [tk(r) for r in rows]
out = {"manifest_status": man.get("status"), "requests_sent": man.get("requests_sent"), "rows": len(rows), "job_id_in_manifest": (man.get("job") or {}).get("job_id")}
out["allowlist_tickers"] = len(allow); out["request_tickers"] = len(req); out["request_tickers_distinct"] = len(set(req))
out["tickers_equal_allowlist_as_sets"] = set(req) == set(allow); out["in_allowlist_not_requested"] = len(set(allow) - set(req)); out["requested_not_in_allowlist"] = len(set(req) - set(allow))
bad_window = 0; max_end = 0; held = 0; windows = collections.Counter()
for r in rows:
    p = r.get("params") or {}; a, b = int(p["start_ts"]), int(p["end_ts"])
    da, db = datetime.fromtimestamp(a, ET), datetime.fromtimestamp(b, ET)
    if not (da.date() == db.date() and (da.hour, da.minute) == (13, 55) and (db.hour, db.minute) == (14, 45)): bad_window += 1
    windows[da.strftime("%Y-%m-%d")] += 1; max_end = max(max_end, b)
    if b >= HELD_FROM: held += 1
out["request_windows_not_13_55_to_14_45_ET"] = bad_window; out["latest_request_end_utc"] = datetime.fromtimestamp(max_end, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
out["request_end_after_limit_2026-04-29T18:45Z"] = sum(1 for r in rows if int(r["params"]["end_ts"]) > LIMIT_END); out["requests_on_or_after_2026-06-17_held_out"] = held
out["request_dates"] = len(windows)
st = collections.Counter(r.get("status") for r in rows); out["http_status_counts"] = {str(k): v for k, v in sorted(st.items(), key=lambda t: str(t[0]))}
out["truncated_rows"] = sum(1 for r in rows if r.get("truncated")); out["rows_without_a_file"] = sum(1 for r in rows if not r.get("file"))
named = [r["file"] for r in rows if r.get("file")]; out["files_named_but_missing"] = sum(1 for f in named if not os.path.isfile(os.path.join(folder, f)))
out["stray_files"] = len([f for f in os.listdir(folder) if f not in ("manifest.json", "STATUS") and f not in set(named)])
lines = []; body_hash_ok = body_hash_bad = 0; latest_candle = 0; before_start = 0; after_limit = 0; empty200 = 0; with_candles = 0; ncandles = 0
for r in rows:
    f = r.get("file")
    if not f or not os.path.isfile(os.path.join(folder, f)): continue
    raw = open(os.path.join(folder, f), "rb").read(); lines.append("%s  %s" % (hashlib.sha256(raw).hexdigest(), f))
    body = gzip.decompress(raw)
    if r.get("sha256") and hashlib.sha256(body).hexdigest() == r["sha256"]: body_hash_ok += 1
    else: body_hash_bad += 1
    if r.get("status") == 200:
        d = json.loads(body); cs = d.get("candlesticks") if isinstance(d, dict) else None
        if not cs: empty200 += 1; continue
        with_candles += 1
        for c in cs:
            t = c.get("end_period_ts")
            if isinstance(t, int):
                ncandles += 1; latest_candle = max(latest_candle, t)
                if t < int(r["params"]["start_ts"]): before_start += 1
                if t > LIMIT_END: after_limit += 1
out["manifest_body_sha256_equal"] = body_hash_ok; out["manifest_body_sha256_not_equal"] = body_hash_bad
out["answers_200_with_candles"] = with_candles; out["answers_200_empty"] = empty200; out["candles_counted"] = ncandles
out["latest_candle_end_utc"] = datetime.fromtimestamp(latest_candle, timezone.utc).strftime("%Y-%m-%dT%H:%MZ") if latest_candle else None
out["candles_before_their_request_start"] = before_start; out["candles_after_2026-04-29T18:45Z"] = after_limit
open(outp, "w").write("\n".join(sorted(lines, key=lambda l: l.split("  ")[1])) + "\n")
out["sha256_list_lines"] = len(lines)
print(json.dumps(out, indent=1))
