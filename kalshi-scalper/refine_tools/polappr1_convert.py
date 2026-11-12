"""W-POL-APPR1 converter: pulled run folders -> cand_all.jsonl, plus the derived marker.

Usage:
  python3 -I kalshi-scalper/refine_tools/polappr1_convert.py RUNS_DIR OUT_DIR --held CAND_FIRST_PULL.jsonl
      [--jobs JOB.json JOB.json ...]   (default: the three jobs/POLAPPR1_CANDLES*.json)
      [--meta kalshi-scalper/refine_tools/POLAPPR1_MARKETS.json]

RUNS_DIR is the data branch's pull/ folder, one job's folder, or one run folder (found by manifest.json, any depth).
--held is the first W-POL-APPR1 pull (cand.jsonl, same row format). Local files only: no network, no key.

Marker rule: POLAPPR1_PULL_COMPLETE (content = total number of requests over all parts) is written ONLY when
every request id of every part has a manifest row, in some run, with status 200 (not truncated) or 404 (no candles),
every stored answer matches its manifest sha256, and the latest run of EACH part says STATUS complete. Answers merge
by request id across runs (a later answer replaces an earlier one); a run of an other job is ignored; a run of
PART_REST counts for PART. Otherwise no marker and no output file, only 'pull incomplete: N of M answered'.
The marker is never written by hand. Refuses if POLAPPR1_READ_DONE exists in OUT_DIR and on any sha256 mismatch.

Rows of HELD-OUT events (polappr1_score.is_heldout, event close = latest market close) are dropped from the
output, whether they come from --held or from a pull, so the scorer's input holds no held-out candle.
"""
import argparse
import glob
import gzip
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import polappr1_score as S  # noqa: E402

MARKER = S.MARKER
READ_DONE = S.READ_DONE
ANSWERED = (200, 404)
HIST = re.compile(r"/historical/markets/([A-Z0-9][A-Z0-9._-]{0,63})/candlesticks")


class Refuse(Exception):
    pass


def find_runs(root):
    out = []
    for d, _, files in os.walk(root):
        if "manifest.json" in files:
            out.append(d)
    return sorted(out, key=lambda p: (os.path.basename(p), p))


def read_body(path):
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return gzip.decompress(raw)
    except OSError:
        return raw


def base_job(jid):
    return jid[:-5] if jid and jid.endswith("_REST") else jid


def row_of(c):
    g = lambda k: (c.get(k) or {}).get("close_dollars") or (c.get(k) or {}).get("close")
    return [c["end_period_ts"], g("yes_ask"), g("yes_bid"), g("price"), c.get("volume_fp") or c.get("volume")]


def collect(runs, parts):
    """answers {id: (run, row)}; last_ok {part: latest run's STATUS is complete}."""
    answers = {}
    last_status = {}
    for run in runs:
        with open(os.path.join(run, "manifest.json")) as f:
            man = json.load(f)
        part = base_job((man.get("job") or {}).get("job_id"))
        if part not in parts:
            continue
        try:
            with open(os.path.join(run, "STATUS")) as f:
                last_status[part] = f.read().strip()
        except OSError:
            last_status[part] = ""
        for row in man.get("rows", []):
            rid = row.get("id")
            if rid not in parts[part]:
                continue
            if row.get("status") == 200 and row.get("truncated"):
                continue
            if row.get("status") in ANSWERED:
                answers[rid] = (run, row)
    return answers, last_status


def verify(answers):
    for rid, (run, row) in sorted(answers.items()):
        fn = row.get("file")
        if not fn or not os.path.isfile(os.path.join(run, fn)):
            if row["status"] == 200:
                raise Refuse("answer file missing for request %s" % rid)
            continue
        if hashlib.sha256(read_body(os.path.join(run, fn))).hexdigest() != row.get("sha256"):
            raise Refuse("sha256 mismatch for request %s" % rid)


def candles_of(req, body):
    """{ticker: [rows]} for one answered request (body None for a 404)."""
    if "market_tickers" in req["params"]:
        tks = req["params"]["market_tickers"].split(",")
        got = {m["market_ticker"]: m.get("candlesticks", []) for m in (body or {}).get("markets", [])}
        return {t: [row_of(c) for c in got.get(t, [])] for t in tks}
    t = HIST.fullmatch(req["path"]).group(1)
    return {t: [row_of(c) for c in (body or {}).get("candlesticks", [])]}


def convert(runs_dir, out_dir, job_paths, meta_path, held_path):
    if os.path.exists(os.path.join(out_dir, READ_DONE)):
        raise Refuse("%s exists in the output folder; refusing" % READ_DONE)
    parts, reqs = {}, {}
    for p in job_paths:
        with open(p) as f:
            job = json.load(f)
        parts[job["job_id"]] = {r["id"] for r in job["requests"]}
        for r in job["requests"]:
            if r["id"] in reqs:
                raise Refuse("request id %s is in two parts" % r["id"])
            reqs[r["id"]] = r
    n = len(reqs)
    runs = find_runs(runs_dir)
    answers, last = collect(runs, parts)
    verify(answers)
    ok_status = all(last.get(p) == "complete" for p in parts)
    if len(answers) < n or not ok_status:
        print("pull incomplete: %d of %d answered" % (len(answers), n))
        return False
    with open(meta_path) as f:
        meta = json.load(f)["markets"]
    cuts = S.load_cuts()
    new = {}
    for rid, (run, row) in answers.items():
        body = json.loads(read_body(os.path.join(run, row["file"]))) if row["status"] == 200 else None
        for t, cs in candles_of(reqs[rid], body).items():
            e, s, ct, res = meta[t]
            new[t] = {"t": t, "e": e, "s": s, "ct": ct, "res": res, "src": "live" if "market_tickers" in reqs[rid]["params"] else "hist", "c": cs}
    held, held_n = {}, 0
    with open(held_path, "rb") as f:
        held_sha = hashlib.sha256(f.read()).hexdigest()
    with open(held_path) as f:
        for l in f:
            if l.strip():
                j = json.loads(l)
                held[j["t"]] = j
                held_n += 1
    merged = dict(new)
    merged.update(held)  # the first pull wins on a repeated market (the sets do not overlap by construction)
    rows = list(merged.values())
    ec = S.event_closes(rows)
    keep = [j for j in rows if not S.is_heldout(cuts, j["s"], ec[j["e"]])]
    keep.sort(key=lambda j: (j["e"], j["t"]))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, S.CANDLES), "w") as f:
        f.write("\n".join(json.dumps(j) for j in keep) + ("\n" if keep else ""))
    with open(os.path.join(out_dir, "POLAPPR1_INPUTS.json"), "w") as f:
        json.dump({"requests": n, "parts": sorted(parts), "held_sha256": held_sha, "held_rows": held_n, "new_rows": len(new), "rows_kept": len(keep),
                   "rows_dropped_heldout": len(rows) - len(keep)}, f)
    with open(os.path.join(out_dir, MARKER), "w") as f:
        f.write(str(n))
    print("pull complete: %d of %d answered; marker %s written" % (n, n, MARKER))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--held", required=True)
    ap.add_argument("--jobs", nargs="+", default=sorted(glob.glob(os.path.join(HERE, "jobs", "POLAPPR1_CANDLES*.json"))))
    ap.add_argument("--meta", default=os.path.join(HERE, "POLAPPR1_MARKETS.json"))
    a = ap.parse_args(argv)
    try:
        convert(a.runs_dir, a.out_dir, a.jobs, a.meta, a.held)
    except Refuse as e:
        print("refused: %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
