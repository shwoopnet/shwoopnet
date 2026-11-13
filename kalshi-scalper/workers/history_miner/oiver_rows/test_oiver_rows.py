"""Made-up runs of EXPECTED_BY_HAND.md (base, then the dated line of 21:10Z: F1 to F4); prints MISMATCHES [] when oiver_rows.py agrees with the hand file."""
import gzip, hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oiver_rows as R

C1 = 1793793600
T = ["KXBTC15M-26NOV040700-00", "KXBTC15M-26NOV040715-15", "KXBTC15M-26NOV040730-30", "KXBTC15M-26NOV040800-00"]
M5 = "KXBTC15M-26NOV040745-45"
HASHES = {}


def canon(job):
    return hashlib.sha256(json.dumps(job, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(folder, job_id, items, drop_sha=False, pre=None, extra_key=False):
    """items: ((rid, page, params), body); pre: {rid: [status, ...]} rows written BEFORE that request's page 1 answer (a status of 'last:N' replaces the 200)."""
    os.makedirs(folder); rows, reqs = [], []
    for (rid, page, params), body in items:
        for st in (pre or {}).get(rid, []):
            if page == 1:
                rows.append({"id": rid, "page": 1, "status": st, "bytes": 0})
        raw = json.dumps(body).encode(); fn = "%s_p%d.json.gz" % (rid, page)
        with gzip.open(os.path.join(folder, fn), "wb") as f:
            f.write(raw)
        row = {"id": rid, "page": page, "status": 200, "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "truncated": False}
        if drop_sha:
            del row["sha256"]; drop_sha = False
        rows.append(row)
        if page == 1:
            reqs.append({"id": rid, "params": params})
    job = {"job_id": job_id, "requests": reqs}
    HASHES[job_id] = canon(job)
    if extra_key:
        job = dict(job, note="changed")
    json.dump({"status": "complete", "job": job, "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))


def tail(folder, rid, status):
    """Append a final non-200 row for request rid (the request ends on it)."""
    p = os.path.join(folder, "manifest.json"); m = json.load(open(p))
    m["rows"].append({"id": rid, "page": 1, "status": status, "bytes": 0}); json.dump(m, open(p, "w"))


def lm(t, close, res):
    return {"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "close_time": close, "result": res}


def cd(end, oi=None, b=None, a=None):
    c = {"end_period_ts": end}
    if oi is not None:
        c["open_interest_fp"] = oi
    if b is not None:
        c["yes_bid"] = {"close_dollars": "%.4f" % b}
    if a is not None:
        c["yes_ask"] = {"close_dollars": "%.4f" % a}
    return c


def m1(alt=False):
    return [cd(C1 - 360, "500000.00"), cd(C1 - 180, "590000.00", .20, .23 if alt else .22), cd(C1 - 120, "1.00", .5, .6)]


def make(base, list_job="CFRTI_K_LISTS", cjob="CFRTI_K_CANDLES", conflict=False, drop_sha=False, m3close="2026-11-04T12:30:00Z", m1close="2026-11-04T12:00:00Z",
         list2=None, m2res="no", pre=None, last=None, extra_key=False):
    d = tempfile.mkdtemp(dir=base)
    items = [(("settled", 1, {"series_ticker": "KXBTC15M"}), {"markets": [lm(T[0], m1close, "yes"), lm(T[1], "2026-11-04T12:15:00Z", m2res)], "cursor": "x"}),
             (("settled", 2, None), {"markets": [lm(T[2], m3close, "no"), lm(M5, "2026-11-04T12:45:00Z", "yes")], "cursor": ""})]
    if list2 is not None:
        items.append((("all", 1, {"series_ticker": "KXBTC15M"}), {"markets": list2, "cursor": ""}))
    run(os.path.join(d, "L"), list_job, items)
    m3c = R.iso(m3close); m1c = R.iso(m1close)
    m1c_c = [cd(m1c - 360, "500000.00"), cd(m1c - 180, "590000.00", .20, .22)] if m1c != C1 else m1()
    body = {"markets": [
        {"market_ticker": T[0], "candlesticks": m1c_c},
        {"market_ticker": T[1], "candlesticks": [cd(C1 + 900 - 360, "400000.00"), cd(C1 + 900 - 180, "410000.00", .40, .40)]},
        {"market_ticker": T[2], "candlesticks": [cd(m3c - 180, "300000.00", 0.0, .30)]},
        {"market_ticker": T[3], "candlesticks": [cd(C1 + 3600 - 180, "1.00", .1, .2)]}]}
    run(os.path.join(d, "C1"), cjob, [(("b0", 1, {"market_tickers": ",".join(T)}), body)], drop_sha=drop_sha, pre=pre, extra_key=extra_key)
    if last:
        tail(os.path.join(d, "C1"), "b0", last)
    run(os.path.join(d, "C2"), "CFRTI_K_R6SLICE", [(("s0", 1, {"market_tickers": T[0]}), {"markets": [{"market_ticker": T[0], "candlesticks": m1(conflict)}]})])
    return os.path.join(d, "out.csv"), os.path.join(d, "L"), [os.path.join(d, "C1"), os.path.join(d, "C2")]


def build(o, l, c):
    return R.build(o, l, c, job_hashes=dict(HASHES))


bad = []
root = tempfile.mkdtemp()
EXP = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EXPECTED_BY_HAND.md")).read().split("```\n")[1].split("```")[0]
BASE = {"windows": 3, "no_list_row": 1, "missing_oi": 1, "crossed_or_locked": 1, "no_bid": 1, "no_ask": 0, "no_quote_candle": 0, "duplicate_agree": 1, "blank_result": 0}


def same(kw, what, csv_text=EXP, counts=BASE):
    o, l, c = make(root, **kw)
    got = build(o, l, c)
    if open(o).read() != csv_text:
        bad.append((what, "csv", open(o).read()))
    if got != counts:
        bad.append((what, "counts", got))


same({}, "base")
same({"pre": {"b0": [429]}}, "429 before the 200")
same({"list2": [lm(T[0], "2026-11-04T12:00:00Z", ""), lm(T[1], "2026-11-04T12:15:00Z", "no")], "m2res": ""}, "F4 merge")
blank_csv = EXP.replace("400000.0,,,,,no\n", "400000.0,,,,,\n")
same({"m2res": "", "list2": [lm(T[1], "2026-11-04T12:15:00Z", "")]}, "F4 blank", blank_csv, dict(BASE, blank_result=1))


def refused(kw, what, base=root):
    o, l, c = make(base, **kw)
    try:
        build(o, l, c)
    except (R.Stop, SystemExit) as e:
        print("refused", what, "->", str(e)[:90]); return
    bad.append(("not refused", what))


refused({"conflict": True}, "two runs disagree")
refused({"list_job": "SPREADLISTS"}, "wrong list job")
refused({"cjob": "NOSIDE1_CANDLES"}, "wrong candle job")
refused({"drop_sha": True}, "row without sha256")
refused({"m1close": "2026-09-11T23:45:00Z"}, "F1 close before WINDOW_FROM")
refused({"m3close": "2026-11-09T00:00:00Z"}, "F1 close at WINDOW_TO")
refused({"last": 429}, "F2 request ending on a 429")
refused({"last": 404}, "F2 request ending on a 404")
refused({"extra_key": True}, "F3 embedded job differs")
refused({"list2": [lm(T[0], "2026-11-04T12:05:00Z", "yes")]}, "F4 close_time disagrees")
refused({"list2": [lm(T[0], "2026-11-04T12:00:00Z", "no")]}, "F4 yes against no")
hd = os.path.join(root, "HELDOUT_x"); os.makedirs(hd)
refused({}, "HELDOUT_ path", base=hd)
o, l, c = make(root)
try:
    R.build(o, l, c); bad.append(("not refused", "F3 made-up job against the real pinned hashes"))
except R.Stop as e:
    print("refused F3 real pins ->", str(e)[:90])
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
