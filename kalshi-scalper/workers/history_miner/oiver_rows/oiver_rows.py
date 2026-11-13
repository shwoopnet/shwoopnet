"""OIVER rows builder (History Miner, Nov 13, 2026): one shared builder for the OIVER scorers. From the Head of R&D's order of 21:05Z and the 19:53Z
convention; rules and the hand case in EXPECTED_BY_HAND.md (3ec68915), committed first. Reads one results list run (CFRTI_K_LISTS) and one or more
KXBTC15M candle runs; development windows only (a close at or after 2026-12-01 stops the build). Writes one CSV and prints counts only.
Usage: python3 -I oiver_rows.py <out.csv> <CFRTI_K_LISTS run folder> <candle run folder> [<candle run folder> ...]"""
import csv, gzip, hashlib, json, math, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
HELDOUT_FIRST = 1796083200          # 2026-12-01T00:00:00Z
LIST_JOB = "CFRTI_K_LISTS"
CANDLE_JOBS = {"CFRTI_K_CANDLES", "CFRTI_K_PROBE", "CFRTI_K_R6SLICE"}
PREFIX = "KXBTC15M-"
COLS = ["ticker", "event_ticker", "close_ts", "oi_180", "oi_360", "yes_bid", "yes_ask", "no_bid", "no_ask", "result"]


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def load_run(folder, jobs):
    hm_guard.refuse_all([folder])
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise Stop("run not complete: %s" % folder)
    job = m.get("job") or {}
    if job.get("job_id") not in jobs:
        raise Stop("run %s is job %r, not one of %s" % (folder, job.get("job_id"), sorted(jobs)))
    root = os.path.realpath(folder)
    by = {}
    for r in m.get("rows", []):
        if r.get("truncated") or not r.get("file") or "sha256" not in r or "bytes" not in r:
            raise Stop("row %s is not a whole answer with sha256 and bytes" % r.get("id"))
        p = os.path.realpath(os.path.join(folder, r["file"]))
        if os.path.commonpath([root, p]) != root:
            raise Stop("file outside run: %s" % r["file"])
        hm_guard.refuse_all([p])
        raw = gzip.open(p, "rb").read()
        if hashlib.sha256(raw).hexdigest() != r["sha256"] or len(raw) != r["bytes"]:
            raise Stop("sha256 or bytes mismatch %s" % r["file"])
        by.setdefault(r["id"], []).append((r, json.loads(raw)))
    out = []
    for q in job["requests"]:
        rows = sorted(by.get(q["id"], []), key=lambda x: x[0].get("page", 1))
        if not rows or [x[0].get("page", 1) for x in rows] != list(range(1, len(rows) + 1)):
            raise Stop("request %s not answered on pages 1..k" % q["id"])
        if any(x[0].get("status") != 200 for x in rows):
            raise Stop("request %s has a non-200 page" % q["id"])
        if rows[-1][1].get("cursor"):
            raise Stop("request %s left a cursor" % q["id"])
        out.append((q, [x[1] for x in rows]))
    return out


def oi(c):
    if c is None:
        return None
    v = c.get("open_interest_fp", c.get("open_interest"))
    if isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def px(c, k):
    o = c.get(k)
    if not isinstance(o, dict) or o.get("close_dollars") in (None, ""):
        return None
    try:
        x = float(o["close_dollars"])
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def build(out_path, list_dir, candle_dirs):
    hm_guard.refuse_all([out_path])
    listed = {}
    for _, pages in load_run(list_dir, {LIST_JOB}):
        for pg in pages:
            for mk in pg.get("markets") or []:
                if mk.get("ticker", "").startswith(PREFIX):
                    listed[mk["ticker"]] = mk
    counts = {"windows": 0, "no_list_row": 0, "missing_oi": 0, "crossed_or_locked": 0, "no_bid": 0, "no_ask": 0, "no_quote_candle": 0, "duplicate_agree": 0}
    requested, cands = set(), {}
    for d in candle_dirs:
        run_c = {}
        for q, pages in load_run(d, CANDLE_JOBS):
            for t in str(q["params"].get("market_tickers", "")).split(","):
                if t.startswith(PREFIX):
                    requested.add(t)
            for pg in pages:
                for mk in pg.get("markets") or []:
                    for c in mk.get("candlesticks") or []:
                        run_c.setdefault(mk.get("market_ticker"), {})[int(c["end_period_ts"])] = c
        for t, cs in run_c.items():
            if t in cands:
                close = iso(listed[t]["close_time"]) if t in listed else None
                keys = [close - 180, close - 360] if close else []
                if any(cands[t].get(k) != cs.get(k) for k in keys):
                    raise Stop("two runs disagree on %s" % t)
                counts["duplicate_agree"] += 1
                for k, c in cs.items():
                    cands[t].setdefault(k, c)
            else:
                cands[t] = dict(cs)
    rows = []
    for t in sorted(requested):
        mk = listed.get(t)
        if mk is None:
            counts["no_list_row"] += 1
            continue
        close = iso(mk["close_time"])
        if close >= HELDOUT_FIRST:
            raise Stop("held-out window %s" % t)
        cs = cands.get(t, {})
        o180, o360 = oi(cs.get(close - 180)), oi(cs.get(close - 360))
        if o180 is None or o360 is None:
            counts["missing_oi"] += 1
        c = cs.get(close - 180)
        yb = ya = None
        if c is None:
            counts["no_quote_candle"] += 1
        else:
            yb, ya = px(c, "yes_bid"), px(c, "yes_ask")
            if yb is not None and yb <= EPS:
                yb = None
            if ya is not None and ya >= 1 - EPS:
                ya = None
            if yb is None:
                counts["no_bid"] += 1
            if ya is None:
                counts["no_ask"] += 1
            if yb is not None and ya is not None and yb >= ya - EPS:
                counts["crossed_or_locked"] += 1
                yb = ya = None
        nb = round(1 - ya, 6) if ya is not None else None
        na = round(1 - yb, 6) if yb is not None else None
        f = lambda x: "" if x is None else repr(x)
        rows.append((close, t, [t, mk["event_ticker"], close, f(o180), f(o360), f(yb), f(ya), f(nb), f(na), mk.get("result") or ""]))
        counts["windows"] += 1
    with open(out_path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(COLS)
        w.writerows(r for _, _, r in sorted(rows))
    return counts


if __name__ == "__main__":
    try:
        print(json.dumps(build(sys.argv[1], sys.argv[2], sys.argv[3:])), file=sys.stderr)
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
