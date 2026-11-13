"""OIVER rows builder (History Miner, Nov 13, 2026): one shared builder for the OIVER scorers. From the Head of R&D's order of 21:05Z and the 19:53Z
convention; rules and the hand case in EXPECTED_BY_HAND.md (3ec68915), committed first. Reads one results list run (CFRTI_K_LISTS) and one or more
KXBTC15M candle runs. Writes one CSV and prints counts only. Auditor B's F1 to F4 and the Head's range ruling (21:10Z) are in the dated line of
EXPECTED_BY_HAND.md (tests cb323557, written first).
Blinding: windows must close in [2026-09-12T00:00Z, 2026-11-09T00:00Z), or the build stops. Every unread or unfrozen KXBTC15M held-out starts on or after
Nov 9 (DEPTH1, CFRTI1-BTC and CFRTI-B from Nov 9; W-SPOTLEAD1's block from Nov 11; CFRTI-K from Nov 14). The landed runs that feed it are CFRTI_K_CANDLES
2026-11-12T1840Z_43279857619 (closes Sep 12 to Nov 4), with CFRTI_K_R6SLICE 2026-11-12T1643Z_43261752453 only as an exact cross-check, and
CFRTI_K_LISTS 2026-11-12T1645Z_43262026759 for results. They end Nov 4, so there is no blinding issue. CFRTI_K_PROBE (Aug 20) is before WINDOW_FROM,
so passing it stops the build. The OIVER cards' own held-out (from Dec 1) is unaffected.
Usage: python3 -I oiver_rows.py <out.csv> <CFRTI_K_LISTS run folder> <candle run folder> [<candle run folder> ...]"""
import csv, gzip, hashlib, json, math, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
WINDOW_FROM = 1789171200            # 2026-09-12T00:00:00Z (F1, the Head's ruling)
WINDOW_TO = 1794182400              # 2026-11-09T00:00:00Z, exclusive
JOB_HASHES = {                      # F3: sha256 of json.dumps(job, sort_keys=True, separators=(",", ":")) of each audited job as run (= the file before PR 888)
    "CFRTI_K_LISTS": "c8f9e7392cff51315e8f409a97b61461b94ab93cf6b865370c6ea12c2d9f2d9d",
    "CFRTI_K_CANDLES": "9ee226200875dfd8bf049ae69b7302da25bc17d8d9c0c8fc30697eb9cdbf4c77",
    "CFRTI_K_PROBE": "af06ad9a667b5feaee72369fa842fe6307a0335ce65852ca713cfe8565f9ec50",
    "CFRTI_K_R6SLICE": "65217aba9ea7916c7402ee3c8dd0fa24bab8e8fdc4546cc0e3528cc7f2719547",
}
LIST_JOB = "CFRTI_K_LISTS"
CANDLE_JOBS = {"CFRTI_K_CANDLES", "CFRTI_K_PROBE", "CFRTI_K_R6SLICE"}
PREFIX = "KXBTC15M-"
COLS = ["ticker", "event_ticker", "close_ts", "oi_180", "oi_360", "yes_bid", "yes_ask", "no_bid", "no_ask", "result"]


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def canon(job):
    return hashlib.sha256(json.dumps(job, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_run(folder, jobs, job_hashes):
    hm_guard.refuse_all([folder])
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise Stop("run not complete: %s" % folder)
    job = m.get("job") or {}
    if job.get("job_id") not in jobs:
        raise Stop("run %s is job %r, not one of %s" % (folder, job.get("job_id"), sorted(jobs)))
    if canon(job) != job_hashes.get(job["job_id"]):                            # F3
        raise Stop("run %s: the embedded job is not the audited %s" % (folder, job["job_id"]))
    root = os.path.realpath(folder)
    pages = {}
    for r in m.get("rows", []):                                                 # F2: manifest order, grouped by request and page
        pages.setdefault(r.get("id"), {}).setdefault(r.get("page", 1), []).append(r)
    out = []
    for q in job["requests"]:
        got = pages.get(q["id"], {})
        if not got or sorted(got) != list(range(1, len(got) + 1)):
            raise Stop("request %s not answered on pages 1..k" % q["id"])
        bodies = []
        for pg in sorted(got):
            rows = got[pg]
            if rows[-1].get("status") != 200 or sum(1 for r in rows if r.get("status") == 200) != 1:
                raise Stop("request %s page %d does not end on its one 200 row" % (q["id"], pg))
            r = rows[-1]
            if r.get("truncated") is not False or not r.get("file") or "sha256" not in r or "bytes" not in r:
                raise Stop("row %s page %d is not a whole answer with sha256 and bytes" % (q["id"], pg))
            p = os.path.realpath(os.path.join(folder, r["file"]))
            if os.path.commonpath([root, p]) != root:
                raise Stop("file outside run: %s" % r["file"])
            hm_guard.refuse_all([p])
            raw = gzip.open(p, "rb").read()
            if hashlib.sha256(raw).hexdigest() != r["sha256"] or len(raw) != r["bytes"]:
                raise Stop("sha256 or bytes mismatch %s" % r["file"])
            bodies.append(json.loads(raw))
        if bodies[-1].get("cursor"):
            raise Stop("request %s left a cursor" % q["id"])
        out.append((q, bodies))
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


def build(out_path, list_dir, candle_dirs, job_hashes=None):
    hm_guard.refuse_all([out_path])
    job_hashes = JOB_HASHES if job_hashes is None else job_hashes
    listed = {}
    for _, pages in load_run(list_dir, {LIST_JOB}, job_hashes):
        for pg in pages:
            for mk in pg.get("markets") or []:
                t = mk.get("ticker", "")
                if not t.startswith(PREFIX):
                    continue
                old = listed.get(t)
                if old is None:
                    listed[t] = mk
                    continue
                if old.get("close_time") != mk.get("close_time") or old.get("event_ticker") != mk.get("event_ticker"):   # F4
                    raise Stop("list rows of %s disagree on close_time or event_ticker" % t)
                a, b = old.get("result") or "", mk.get("result") or ""
                if a and b and a != b:
                    raise Stop("list rows of %s disagree on the result (%s, %s)" % (t, a, b))
                if b and not a:
                    listed[t] = mk
    counts = {"windows": 0, "no_list_row": 0, "missing_oi": 0, "crossed_or_locked": 0, "no_bid": 0, "no_ask": 0, "no_quote_candle": 0, "duplicate_agree": 0,
              "blank_result": 0}
    requested, cands = set(), {}
    for d in candle_dirs:
        run_c = {}
        for q, pages in load_run(d, CANDLE_JOBS, job_hashes):
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
        if not (WINDOW_FROM <= close < WINDOW_TO):                             # F1, both ends
            raise Stop("window %s closes outside [2026-09-12, 2026-11-09)" % t)
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
        if not (mk.get("result") or ""):
            counts["blank_result"] += 1
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
