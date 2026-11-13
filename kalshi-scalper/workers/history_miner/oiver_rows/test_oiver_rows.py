"""Made-up runs of EXPECTED_BY_HAND.md; prints MISMATCHES [] when oiver_rows.py agrees with the hand file."""
import gzip, hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oiver_rows as R

C1 = 1793793600
T = ["KXBTC15M-26NOV040700-00", "KXBTC15M-26NOV040715-15", "KXBTC15M-26NOV040730-30", "KXBTC15M-26NOV040800-00"]
M5 = "KXBTC15M-26NOV040745-45"


def run(folder, job_id, items, drop_sha=False):
    os.makedirs(folder); rows, reqs = [], []
    for (rid, page, params), body in items:
        raw = json.dumps(body).encode(); fn = "%s_p%d.json.gz" % (rid, page)
        with gzip.open(os.path.join(folder, fn), "wb") as f:
            f.write(raw)
        row = {"id": rid, "page": page, "status": 200, "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        if drop_sha:
            del row["sha256"]; drop_sha = False
        rows.append(row)
        if page == 1:
            reqs.append({"id": rid, "params": params})
    json.dump({"status": "complete", "job": {"job_id": job_id, "requests": reqs}, "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))


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


def make(base, list_job="CFRTI_K_LISTS", cjob="CFRTI_K_CANDLES", conflict=False, drop_sha=False, held=False):
    d = tempfile.mkdtemp(dir=base)
    m3close = "2026-12-02T16:15:00Z" if held else "2026-11-04T12:30:00Z"
    run(os.path.join(d, "L"), list_job, [
        (("settled", 1, {"series_ticker": "KXBTC15M"}), {"markets": [lm(T[0], "2026-11-04T12:00:00Z", "yes"), lm(T[1], "2026-11-04T12:15:00Z", "no")], "cursor": "x"}),
        (("settled", 2, None), {"markets": [lm(T[2], m3close, "no"), lm(M5, "2026-11-04T12:45:00Z", "yes")], "cursor": ""})])
    m3c = (1796228100 if held else C1 + 1800)
    body = {"markets": [
        {"market_ticker": T[0], "candlesticks": m1()},
        {"market_ticker": T[1], "candlesticks": [cd(C1 + 900 - 360, "400000.00"), cd(C1 + 900 - 180, "410000.00", .40, .40)]},
        {"market_ticker": T[2], "candlesticks": [cd(m3c - 180, "300000.00", 0.0, .30)]},
        {"market_ticker": T[3], "candlesticks": [cd(C1 + 3600 - 180, "1.00", .1, .2)]}]}
    run(os.path.join(d, "C1"), cjob, [(("b0", 1, {"market_tickers": ",".join(T)}), body)], drop_sha=drop_sha)
    run(os.path.join(d, "C2"), "CFRTI_K_R6SLICE", [(("s0", 1, {"market_tickers": T[0]}), {"markets": [{"market_ticker": T[0], "candlesticks": m1(conflict)}]})])
    return os.path.join(d, "out.csv"), os.path.join(d, "L"), [os.path.join(d, "C1"), os.path.join(d, "C2")]


bad = []
root = tempfile.mkdtemp()
out, L, Cs = make(root)
counts = R.build(out, L, Cs)
exp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EXPECTED_BY_HAND.md")).read().split("```\n")[1].split("```")[0]
if open(out).read() != exp:
    bad.append(("csv", open(out).read()))
if counts != {"windows": 3, "no_list_row": 1, "missing_oi": 1, "crossed_or_locked": 1, "no_bid": 1, "no_ask": 0, "no_quote_candle": 0, "duplicate_agree": 1}:
    bad.append(("counts", counts))


def refused(kw, what, base=root):
    o, l, c = make(base, **kw)
    try:
        R.build(o, l, c)
    except (R.Stop, SystemExit) as e:
        print("refused", what, "->", str(e)[:80]); return
    bad.append(("not refused", what))


refused({"conflict": True}, "two runs disagree")
refused({"list_job": "SPREADLISTS"}, "wrong list job")
refused({"cjob": "NOSIDE1_CANDLES"}, "wrong candle job")
refused({"drop_sha": True}, "row without sha256")
refused({"held": True}, "held-out close")
hd = os.path.join(root, "HELDOUT_x"); os.makedirs(hd)
refused({}, "HELDOUT_ path", base=hd)
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
