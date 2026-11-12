"""NOSIDE1 converter (W-NO-ARM1): pulled run folders -> cand_no.jsonl, plus the derived marker.

Usage:
  python3 -I kalshi-scalper/refine_tools/noside1_convert.py RUNS_DIR OUT_DIR
      --markets MARKETS.jsonl [MARKETS2.jsonl ...] --existing HELD_cand_no.jsonl
      [--job kalshi-scalper/refine_tools/jobs/NOSIDE1_CANDLES.json]

RUNS_DIR holds run folders (0001.json.gz ..., manifest.json, STATUS), or is one. Runs whose
manifest job_id starts with 'NOSIDE1' are merged by request id (the pull is split in parts:
NOSIDE1_CANDLES, NOSIDE1_CANDLES_P2, _P3, same request ids and params). A later answer
replaces an earlier one. Local files only. No network, no Kalshi key, no trading code.

--markets: market records (jsonl, one object per line: ticker, event_ticker, series,
  close_time 'YYYY-MM-DDTHH:MM:SS...', result 'yes'/'no') from the merged market lists. The
  answers carry candles only, so the close time and the settled result come from here.
--existing: the already-held cand_no.jsonl (302 markets from the earlier pull). The master job
  skipped those markets, so they are merged in here; a market in both is taken from the new pull.

Marker rule: NOSIDE1_PULL_COMPLETE (content 1034 = requests in the master job) is written ONLY
when every master request id is answered (status 200 or 404) in some run, every stored answer
matches its manifest sha256, and the STATUS of the latest run (last folder by name) is
'complete'. Otherwise only 'pull incomplete: N of M answered' is printed and nothing is written.
Refuses if NOSIDE1_READ_DONE exists in OUT_DIR, and on any sha256 mismatch.
Output cand_no.jsonl line: {"t","e","s","ct" (close epoch),"res","c": [[end_period_ts, yes_ask,
  yes_bid, price, volume], ...]}  (candle values as dollar strings or null).
"""
import argparse, calendar, gzip, hashlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "NOSIDE1"
MARKER = "NOSIDE1_PULL_COMPLETE"
READ_DONE = "NOSIDE1_READ_DONE"
ANSWERED = (200, 404)


class Refuse(Exception):
    pass


def ts(s):
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))


def find_runs(root):
    if os.path.isfile(os.path.join(root, "manifest.json")):
        return [root]
    return sorted(os.path.join(root, d) for d in os.listdir(root)
                  if os.path.isfile(os.path.join(root, d, "manifest.json")))


def read_body(path):
    raw = open(path, "rb").read()
    try:
        return gzip.decompress(raw)
    except OSError:
        return raw


def collect(runs, valid_ids):
    answers, used = {}, []
    for run in runs:
        man = json.load(open(os.path.join(run, "manifest.json")))
        jid = (man.get("job") or {}).get("job_id")
        if not (jid or "").startswith(PREFIX):
            continue
        used.append(run)
        for row in man.get("rows", []):
            if row.get("id") in valid_ids and row.get("status") in ANSWERED:
                answers[row["id"]] = (run, row)
    return answers, used


def verify(answers):
    for rid, (run, row) in sorted(answers.items()):
        fn = row.get("file")
        if not fn or not os.path.isfile(os.path.join(run, fn)):
            if row["status"] == 200:
                raise Refuse("answer file missing for request %s" % rid)
            continue
        if hashlib.sha256(read_body(os.path.join(run, fn))).hexdigest() != row.get("sha256"):
            raise Refuse("sha256 mismatch for request %s" % rid)


def row_of(c):
    g = lambda k: (c.get(k) or {}).get("close_dollars") or (c.get(k) or {}).get("close")
    return [c["end_period_ts"], g("yes_ask"), g("yes_bid"), g("price"),
            c.get("volume_fp") or c.get("volume")]


def candles_of(req, body):
    """{ticker: [rows]} from one answer: a live batch (markets[]) or a historical one (candlesticks[])."""
    body = body or {}
    if req["id"].startswith("hist_"):
        tk = req["path"].split("/")[3]
        return {tk: [row_of(c) for c in body.get("candlesticks", [])]}
    return {m["market_ticker"]: [row_of(c) for c in m.get("candlesticks", [])]
            for m in body.get("markets", [])}


def req_tickers(req):
    if req["id"].startswith("hist_"):
        return [req["path"].split("/")[3]]
    return req["params"]["market_tickers"].split(",")


def load_markets(paths):
    mk = {}
    for p in paths:
        for l in open(p):
            l = l.strip()
            if not l:
                continue
            r = json.loads(l)
            if r.get("result") in ("yes", "no") and r.get("ticker"):
                mk[r["ticker"]] = r
    return mk


def convert(runs_dir, out_dir, job_path, markets_paths, existing):
    if os.path.exists(os.path.join(out_dir, READ_DONE)):
        raise Refuse("%s exists in the output folder; refusing" % READ_DONE)
    job = json.load(open(job_path))
    reqs = job["requests"]
    n = len(reqs)
    byid = {r["id"]: r for r in reqs}
    answers, used = collect(find_runs(runs_dir), set(byid))
    verify(answers)
    latest_ok = False
    if used:
        try:
            latest_ok = open(os.path.join(used[-1], "STATUS")).read().strip() == "complete"
        except OSError:
            pass
    if len(answers) < n or not latest_ok:
        print("pull incomplete: %d of %d answered" % (len(answers), n))
        return False
    mk = load_markets(markets_paths)
    cand = {}
    for rid, (run, row) in answers.items():
        body = json.loads(read_body(os.path.join(run, row["file"]))) if row["status"] == 200 else None
        got = candles_of(byid[rid], body)
        for t in req_tickers(byid[rid]):
            if t not in mk:
                raise Refuse("market record missing for %s" % t)
            cand[t] = got.get(t, [])
    os.makedirs(out_dir, exist_ok=True)
    lines = []
    if existing:
        for l in open(existing):
            if l.strip():
                j = json.loads(l)
                if j["t"] not in cand:
                    lines.append(json.dumps(j))
    for t in sorted(cand):
        m = mk[t]
        lines.append(json.dumps({"t": t, "e": m["event_ticker"], "s": m["series"],
                                 "ct": ts(m["close_time"]), "res": m["result"], "c": cand[t]}))
    with open(os.path.join(out_dir, "cand_no.jsonl"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, MARKER), "w") as f:
        f.write(str(n))
    print("pull complete: %d of %d answered; marker %s written" % (n, n, MARKER))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--markets", nargs="+", required=True)
    ap.add_argument("--existing", default=None)
    ap.add_argument("--job", default=os.path.join(HERE, "jobs", "NOSIDE1_CANDLES.json"))
    a = ap.parse_args(argv)
    try:
        convert(a.runs_dir, a.out_dir, a.job, a.markets, a.existing)
    except Refuse as e:
        print("refused: %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
