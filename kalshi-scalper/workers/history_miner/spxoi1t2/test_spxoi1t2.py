"""Builds the made-up runs of EXPECTED_BY_HAND.md and checks spxoi1t2.py against the hand figures. Prints MISMATCHES [] when all agree."""
import gzip, hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxoi1t2 as S

C0 = 1793901600
RISE = [500, -200, 0, 1200, 300, 800, 50, 2000, 700, 100, None, None, None, 1500]
ODD = {14: "nan", 15: "inf", 16: True}                                         # run C: close - 180 OI of W15 to W17


def tick(close):
    et = close - 5 * 3600
    h, m = (et % 86400) // 3600, (et % 3600) // 60
    return "KXINX15M-26NOV05%02d%02d-%02d" % (h, m, m)


def make(base, n=14, job_id="SPXOI1_CANDLES", status="complete", drop_sha=False, held=False):
    d = tempfile.mkdtemp(dir=base)
    reqs, ans = [], []
    for i in range(n):
        close = C0 + 900 * i
        if held and i == 0:
            close = 1796228100                       # 2026-12-02T16:15Z
        t = tick(close)
        reqs.append({"id": "c%03d" % (i + 1), "path": "/markets/candlesticks", "params": {"market_tickers": t, "start_ts": close - 1800, "end_ts": close - 120, "period_interval": 1}})
        cs = []
        if i != 10:
            cs.append({"end_period_ts": close - 360, "open_interest_fp": "10000.00"})
        if i == 12:
            cs.append({"end_period_ts": close - 180, "open_interest_fp": None})
        elif i in ODD:
            cs.append({"end_period_ts": close - 180, "open_interest_fp": ODD[i]})
        elif i != 11:
            cs.append({"end_period_ts": close - 180, "open_interest_fp": "%.2f" % (10000 + (RISE[i] or 0))})
        cs.append({"end_period_ts": close - 120, "open_interest_fp": "99999.00"})
        ans.append(("c%03d" % (i + 1), {"markets": [{"market_ticker": t, "candlesticks": cs}]}))
    job = {"job_id": job_id, "requests": reqs}
    jp = os.path.join(d, "job.json"); open(jp, "w").write(json.dumps(job))
    run = os.path.join(d, "run"); os.makedirs(run); rows = []
    for rid, body in ans:
        raw = json.dumps(body).encode(); fn = rid + "_p1.json.gz"
        with gzip.open(os.path.join(run, fn), "wb") as f:
            f.write(raw)
        row = {"id": rid, "page": 1, "status": 200, "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        if drop_sha and rid == "c002":
            del row["sha256"]
        rows.append(row)
    json.dump({"status": status, "job": job, "rows": rows}, open(os.path.join(run, "manifest.json"), "w"))
    return jp, run, hashlib.sha256(open(jp, "rb").read()).hexdigest()


bad = []
root = tempfile.mkdtemp()
jp, run, sha = make(root)
a = S.derive(jp, run, sha)
if a != {"n": 11, "T": 1500.0, "counts": {"windows": 14, "used": 11, "dropped_no_candle": 2, "dropped_no_oi": 1}}:
    bad.append(("A", a))
jp, run, sha = make(root, n=13)
b = S.derive(jp, run, sha)
if (b["n"], b["T"]) != (10, 1200.0):
    bad.append(("B", b))


jp, run, sha = make(root, n=17)
c = S.derive(jp, run, sha)
if c != {"n": 11, "T": 1500.0, "counts": {"windows": 17, "used": 11, "dropped_no_candle": 2, "dropped_no_oi": 4}}:
    bad.append(("C", c))


def refused(kw, what, base=root):
    jp, run, sha = make(base, **kw)
    try:
        S.derive(jp, run, sha)
    except (S.Stop, SystemExit) as e:
        print("refused", what, "->", e); return
    bad.append(("not refused", what))


refused({"job_id": "SPXOI1_LISTS"}, "wrong job_id")
refused({"drop_sha": True}, "row without sha256")
refused({"held": True}, "window closing 2026-12-02")
refused({"status": "partial"}, "partial run")
hd = os.path.join(root, "HELDOUT_x"); os.makedirs(hd)
refused({}, "HELDOUT_ path", base=hd)
jp, run, sha = make(root)
try:
    S.derive(jp, run); bad.append(("not refused", "job sha not 497042e9"))
except S.Stop as e:
    print("refused job sha ->", e)
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
