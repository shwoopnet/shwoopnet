"""SPREADCELL1 converter: pulled run folders -> candles_sp.jsonl, plus the derived marker.

Usage:
  python3 -I kalshi-scalper/refine_tools/spread_cell1_convert.py RUNS_DIR OUT_DIR
      [--job kalshi-scalper/refine_tools/jobs/SPREADCELL1.json]
      [--events kalshi-scalper/refine_tools/SPREAD_CELL1_EVENTS.json]

RUNS_DIR holds one or more run folders (0001.json.gz ..., manifest.json, STATUS), or is one.
Reads local files only. No network, no Kalshi key, no trading code.

Marker rule (committed in the registration): SPREADCELL1_PULL_COMPLETE (content = number of
requests, 274) is written ONLY when every request in the job file has a manifest row, in some
run, with status 200 or 404 (404 = no candles), every stored answer matches its manifest sha256,
and the STATUS of the latest run (last folder by name) says complete. The marker is never
written by hand. Otherwise no marker and no output file; only the line
'pull incomplete: N of M answered' is printed (no observation counts, no candle values).
Refuses to run if SPREADCELL1_READ_DONE exists in OUT_DIR, and refuses on any sha256 mismatch.
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOB_ID = "SPREADCELL1"
MARKER = "SPREADCELL1_PULL_COMPLETE"
READ_DONE = "SPREADCELL1_READ_DONE"
ANSWERED = (200, 404)


class Refuse(Exception):
    pass


def find_runs(root):
    if os.path.isfile(os.path.join(root, "manifest.json")):
        return [root]
    return sorted(os.path.join(root, d) for d in os.listdir(root)
                  if os.path.isfile(os.path.join(root, d, "manifest.json")))


def read_body(path):
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return gzip.decompress(raw)
    except OSError:
        return raw  # tolerate an un-gzipped file; the sha256 check still applies


def collect(runs, job_id, valid_ids):
    """Merge rows over runs. Returns (answers {id: (run, row)}, runs_used)."""
    answers = {}
    used = []
    for run in runs:
        with open(os.path.join(run, "manifest.json")) as f:
            man = json.load(f)
        jid = (man.get("job") or {}).get("job_id")
        if jid is not None and jid != job_id:
            continue
        used.append(run)
        for row in man.get("rows", []):
            rid = row.get("id")
            if rid not in valid_ids or row.get("status") not in ANSWERED:
                continue
            answers[rid] = (run, row)  # a later answer replaces an earlier one
    return answers, used


def verify(answers):
    for rid, (run, row) in sorted(answers.items()):
        fn = row.get("file")
        if not fn or not os.path.isfile(os.path.join(run, fn)):
            if row["status"] == 200:
                raise Refuse("answer file missing for request %s" % rid)
            continue
        got = hashlib.sha256(read_body(os.path.join(run, fn))).hexdigest()
        if got != row.get("sha256"):
            raise Refuse("sha256 mismatch for request %s" % rid)


def candle_lists(body):
    out = {}
    for m in (body or {}).get("markets", []):
        out[m["market_ticker"]] = [
            [c["end_period_ts"],
             (c.get("yes_ask") or {}).get("close_dollars"),
             (c.get("yes_bid") or {}).get("close_dollars"),
             (c.get("price") or {}).get("close_dollars"),
             c.get("volume_fp")]
            for c in m.get("candlesticks", [])]
    return out


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
        print("pull incomplete: %d of %d answered" % (len(answers), n))
        return False
    with open(events_path) as f:
        events = json.load(f)["events"]
    by_event = {}
    for r in reqs:
        for t in r["params"]["market_tickers"].split(","):
            by_event.setdefault(t.rsplit("-", 1)[0], []).append(t)
    cand = {}
    for rid, (run, row) in answers.items():
        if row["status"] == 200:
            cand.update(candle_lists(json.loads(read_body(os.path.join(run, row["file"])))))
    os.makedirs(out_dir, exist_ok=True)
    lines = []
    for s, e, c in events:
        tk = by_event.get(e)
        if not tk:
            continue  # an event with no ticker in this job (small test jobs)
        lines.append(json.dumps({"_e": e, "s": s, "c": c, "h": {t: cand.get(t, []) for t in tk}}))
    with open(os.path.join(out_dir, "candles_sp.jsonl"), "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    with open(os.path.join(out_dir, MARKER), "w") as f:
        f.write(str(n))
    print("pull complete: %d of %d answered; marker %s written" % (n, n, MARKER))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--job", default=os.path.join(HERE, "jobs", "SPREADCELL1.json"))
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
