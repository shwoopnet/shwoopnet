#!/usr/bin/env python3
"""MADE-UP DATA for livedata_fields.py. Invented answers in the shape of a pull run (manifest.json with the job, rows
with sha256, numbered .json.gz files). Nothing came from Kalshi. Every value that must never be printed is a SENTINEL:
the number 77.77 or 66.61, a word starting SENTINEL (in either case), or the id pattern ZZ9 (in either case). Usage: make_fixtures_MADE_UP_DATA.py <out>

  normal      four answered requests: an events list with milestones, an index series, an old index window, calibrations.
  refused     as normal, one request answered 429 and one never sent.
  bad_sha     as normal, one file altered after the manifest was written: the reader must refuse.
  no_job      as normal, the manifest carries no job: the reader must refuse.
  not_json    as normal, one stored answer is not JSON.
"""
import gzip
import hashlib
import json
import os
import sys

T0 = 1794536000


def answers():
    series = {"city": "SENTINELCITY", "config_version": "SENTINEL-v1.0", "units": "SENTINELUNIT",
              "timeseries": [{"t": (T0 + 60 * i) * 1000, "v": 77.77, "status": "SENTINELSTATUS", "contributors": 3,
                              "stations": {"ZZ9A%02d" % k: {"reading": 66.61, "code": "SENTINELCODE"} for k in range(15)}} for i in range(5)]}
    events = {"events": [{"event_ticker": "KXTEMPMIAH-ZZ9", "title": "SENTINEL title", "strike_date": "2026-11-13T05:00:00Z"}],
              "milestones": [{"id": "ZZ9-milestone", "type": "SENTINELTYPE", "start_date": "2026-11-13T04:00:00Z", "end_date": "2026-11-13T05:00:00Z",
                              "details": {"status": "SENTINELSTATUS", "home_score": 7777, "away_score": 6661}, "primary_event_tickers": ["KXTEMPMIAH-ZZ9"],
                              "last_updated_ts": "2026-11-13T04:30:00Z"}], "cursor": "SENTINELCURSOR"}
    cal = {"city": "SENTINELCITY", "calibrations": [{"effective_ts": (T0 - 86400 * 7 * k) * 1000, "version": "SENTINEL-v1.%d" % k,
                                                     "weights": {"ZZ9A01": 0.7777, "zz9a02": 0.6661}, "offsets_c": {"ZZ9A01": 77.77},
                                                     "by_city": {"sentinelone": {"w": 1}, "sentineltwo": {"w": 2}, "sentinelthree": {"w": 3}}} for k in range(3)]}
    return [("ev_temp_miami", events), ("wx_recent", series), ("wx_old", dict(series, timeseries=[])), ("wx_calibrations", cal)]


def build(out, name, kind="normal"):
    folder = os.path.join(out, name)
    os.makedirs(folder)
    reqs, rows = [], []
    for n, (rid, body) in enumerate(answers(), 1):
        reqs.append({"id": rid, "path": "/made/up", "params": {}})
        if kind == "refused" and rid == "wx_old":
            rows.append({"index": n, "id": rid, "page": 1, "status": 429, "file": None})
            continue
        if kind == "refused" and rid == "wx_calibrations":
            continue
        fn = "%04d.json.gz" % n
        raw = gzip.compress(json.dumps(body).encode() if not (kind == "not_json" and rid == "wx_recent") else b"SENTINEL not json 77.77")
        open(os.path.join(folder, fn), "wb").write(raw)
        rows.append({"index": n, "id": rid, "page": 1, "status": 200, "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False})
    man = {"status": "complete", "rows": rows}
    if kind != "no_job":
        man["job"] = {"job_id": "MADE_UP", "requests": reqs}
    json.dump(man, open(os.path.join(folder, "manifest.json"), "w"))
    if kind == "bad_sha":
        open(os.path.join(folder, "0002.json.gz"), "wb").write(gzip.compress(b'{"timeseries": [{"t": 1, "v": 66.61}]}'))


def main():
    for k in ("normal", "refused", "bad_sha", "no_job", "not_json"):
        build(sys.argv[1], k, k)


if __name__ == "__main__":
    main()
