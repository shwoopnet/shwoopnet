"""SPREADLISTS converter: pulled run folders -> SPREAD_CELL1_EXPECTED.json, plus the derived marker.

Usage:
  python3 -I kalshi-scalper/refine_tools/spread_cell1_times_convert.py RUNS_DIR OUT_DIR
      [--job kalshi-scalper/refine_tools/jobs/SPREADLISTS.json]
      [--events kalshi-scalper/refine_tools/SPREAD_CELL1_EVENTS.json]

Same raw layout as spread_cell1_convert.py (0001.json.gz ..., manifest.json, STATUS). Local files
only; no network, no key. Only three time fields are kept per event: close_time,
expected_expiration_time, occurrence_datetime (null when absent). No price, result or volume is
read. Event = ticker prefix before the last '-'.

SPREADLISTS_COMPLETE is written ONLY when every request has a manifest row (status 200 or 404) in
some run, every stored answer matches its sha256, and the STATUS of the latest run says complete.
Otherwise nothing is written and only 'lists incomplete: N of M answered' is printed.
Refuses if SPREADCELL1_READ_DONE exists in OUT_DIR (the times must not change after the read).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # python -I does not add the script folder
from spread_cell1_convert import Refuse, find_runs, collect, verify, read_body  # noqa: E402

JOB_ID = "SPREADLISTS"
MARKER = "SPREADLISTS_COMPLETE"
READ_DONE = "SPREADCELL1_READ_DONE"
FIELDS = ("close_time", "expected_expiration_time", "occurrence_datetime")


def convert(runs_dir, out_dir, job_path, events_path):
    if os.path.exists(os.path.join(out_dir, READ_DONE)):
        raise Refuse("%s exists in the output folder; refusing" % READ_DONE)
    with open(job_path) as f:
        job = json.load(f)
    reqs = job["requests"]
    n = len(reqs)
    ids = {r["id"] for r in reqs}
    runs = find_runs(runs_dir)
    answers, used = collect(runs, job.get("job_id", JOB_ID), ids)
    verify(answers)
    latest_ok = False
    if used:
        try:
            with open(os.path.join(used[-1], "STATUS")) as f:
                latest_ok = f.read().strip() == "complete"
        except OSError:
            latest_ok = False
    if len(answers) < n or not latest_ok:
        print("lists incomplete: %d of %d answered" % (len(answers), n))
        return False
    with open(events_path) as f:
        events = json.load(f)["events"]
    times = {}
    for rid, (run, row) in answers.items():
        if row["status"] != 200:
            continue
        body = json.loads(read_body(os.path.join(run, row["file"])))
        for m in body.get("markets", []):
            t = m.get("ticker")
            if t:
                times[t.rsplit("-", 1)[0]] = {k: (m.get(k) or None) for k in FIELDS}
    out = {}
    for s, e, c in events:
        out[e] = times.get(e) or {k: None for k in FIELDS}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "SPREAD_CELL1_EXPECTED.json"), "w") as f:
        json.dump(out, f, sort_keys=True)
    with open(os.path.join(out_dir, MARKER), "w") as f:
        f.write(str(n))
    print("lists complete: %d of %d answered; marker %s written" % (n, n, MARKER))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--job", default=os.path.join(HERE, "jobs", "SPREADLISTS.json"))
    ap.add_argument("--events", default=os.path.join(HERE, "SPREAD_CELL1_EVENTS.json"))
    a = ap.parse_args(argv)
    try:
        convert(a.runs_dir, a.out_dir, a.job, a.events)
    except Refuse as e:
        print("refused: %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
