"""SPXOI1 T derivation, BUILD 2 (History Miner, Nov 13, 2026), from the Head of R&D's spec of 18:49Z only; Desk A's code was not read. Expected figures in
EXPECTED_BY_HAND.md, committed first (9a91f648). Reads open interest only from one SPXOI1_CANDLES run (job file sha256 497042e9...); no price, volume or result.
oi_rise = OI(candle ending close - 180) - OI(candle ending close - 360); T = nearest-rank 90th percentile. Prints n, T and counts; writes nothing.
A non-200 page stops the run (a market that does not exist blocks it). Runs only after Auditor B's structure check of the landed run and the Head's go.
Usage: python3 -I spxoi1t2.py <SPXOI1_CANDLES.json job file> <candles run folder>"""
import gzip, hashlib, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

JOB_ID = "SPXOI1_CANDLES"
JOB_SHA = "497042e9188f4561a80e290ed2b2cd4dd2cc41e62fe0d2dbc457f67e7a3ca6b9"
HELDOUT_FIRST = 1796083200          # 2026-12-01T00:00:00Z
LAG = 120                           # the job's end_ts is close - 120


class Stop(Exception):
    pass


def load_run(folder, job):
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise Stop("run not complete")
    if m.get("job") != job:
        raise Stop("the run's embedded job is not the given job file")
    root = os.path.realpath(folder)
    by = {}
    for r in m.get("rows", []):
        if r.get("truncated") or not r.get("file"):
            raise Stop("row %s truncated or without a file" % r.get("id"))
        if "sha256" not in r or "bytes" not in r:
            raise Stop("row %s lacks sha256 or bytes" % r.get("id"))
        p = os.path.realpath(os.path.join(folder, r["file"]))
        if os.path.commonpath([root, p]) != root:
            raise Stop("file outside run: %s" % r["file"])
        hm_guard.refuse_all([p])
        raw = gzip.open(p, "rb").read()
        if hashlib.sha256(raw).hexdigest() != r["sha256"] or len(raw) != r["bytes"]:
            raise Stop("sha256 or bytes mismatch %s" % r["file"])
        by.setdefault(r["id"], []).append((r, json.loads(raw)))
    out = {}
    for q in job["requests"]:
        rows = sorted(by.get(q["id"], []), key=lambda x: x[0].get("page", 1))
        if not rows or [x[0].get("page", 1) for x in rows] != list(range(1, len(rows) + 1)):
            raise Stop("request %s not answered on pages 1..k" % q["id"])
        if any(x[0].get("status") != 200 for x in rows):
            raise Stop("request %s has a non-200 page" % q["id"])
        if rows[-1][1].get("cursor"):
            raise Stop("request %s left a cursor" % q["id"])
        out[q["id"]] = (q, [x[1] for x in rows])
    return out


def oi(c):
    if c is None:
        return "no_candle"
    v = c.get("open_interest_fp", c.get("open_interest"))
    if isinstance(v, bool):                                                     # finite check (Head, 18:55Z): a bool is not OI
        return "no_oi"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "no_oi"
    return x if math.isfinite(x) else "no_oi"                                   # NaN and inf are not OI


def derive(job_path, folder, job_sha=JOB_SHA):
    hm_guard.refuse_all([job_path, folder])
    raw = open(job_path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != job_sha:
        raise Stop("job file is not the audited %s" % job_sha[:8])
    job = json.loads(raw)
    if job.get("job_id") != JOB_ID:
        raise Stop("job_id %r is not %s" % (job.get("job_id"), JOB_ID))
    counts = {"windows": 0, "used": 0, "dropped_no_candle": 0, "dropped_no_oi": 0}
    rises = []
    for q, pages in load_run(folder, job).values():
        t, close = q["params"]["market_tickers"], int(q["params"]["end_ts"]) + LAG
        if close >= HELDOUT_FIRST:
            raise Stop("held-out window %s" % t)
        counts["windows"] += 1
        cs = {}
        for pg in pages:
            for mk in pg.get("markets") or []:
                if mk.get("market_ticker") == t:
                    for c in mk.get("candlesticks") or []:
                        cs[int(c["end_period_ts"])] = c
        a, b = oi(cs.get(close - 180)), oi(cs.get(close - 360))
        bad = [x for x in (a, b) if isinstance(x, str)]
        if bad:
            counts["dropped_" + ("no_candle" if "no_candle" in bad else "no_oi")] += 1
            continue
        rises.append(a - b)
        counts["used"] += 1
    rises.sort()
    n = len(rises)
    T = rises[(90 * n + 99) // 100 - 1] if n else None
    return {"n": n, "T": T, "counts": counts}


if __name__ == "__main__":
    try:
        print(json.dumps(derive(sys.argv[1], sys.argv[2])))
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
