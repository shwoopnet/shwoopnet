"""Made-up runs of EXPECTED_BY_HAND.md; prints MISMATCHES [] when wxdayend2.py agrees with the hand figures."""
import gzip, hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wxdayend2 as W

N2 = 1793602800 - 3600   # 2026-11-02T06:00Z


def c(end, close, low=None):
    a = {"close_dollars": "%.4f" % close}
    if low is not None:
        a["low_dollars"] = "%.4f" % low
    return {"end_period_ts": end, "yes_ask": a}


def run(folder, items):
    os.makedirs(folder); rows, reqs = [], []
    for rid, params, body in items:
        raw = json.dumps(body).encode(); fn = rid + ".json.gz"
        with gzip.open(os.path.join(folder, fn), "wb") as f:
            f.write(raw)
        rows.append({"id": rid, "page": 1, "status": 200, "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        reqs.append({"id": rid, "params": params})
    json.dump({"status": "complete", "job": {"requests": reqs}, "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))


def make(base, two_yes=False, bad_end=False):
    d = tempfile.mkdtemp(dir=base)
    dal1, den1 = "KXHIGHTDAL-26NOV01-B79.5", "KXHIGHDEN-26NOV01-T65"
    e_dal = 1793602800 + (3600 if bad_end else 0)
    lst = [{"ticker": "KXHIGHTDAL-26NOV10-B78.5", "event_ticker": "KXHIGHTDAL-26NOV10", "result": "yes", "close_time": "2026-11-11T07:00:00Z"},
           {"ticker": "KXHIGHTDAL-26NOV10-B80.5", "event_ticker": "KXHIGHTDAL-26NOV10", "result": "yes" if two_yes else "no", "close_time": "2026-11-11T07:00:00Z"}]
    run(os.path.join(d, "A"), [
        ("wx_c01", {"market_tickers": dal1, "end_ts": e_dal}, {"markets": [{"market_ticker": dal1, "candlesticks": [c(N2, .50), c(N2 + 1800, .96, .96)]}]}),
        ("wx_c10", {"market_tickers": den1, "end_ts": 1793606400}, {"markets": [{"market_ticker": den1, "candlesticks": [c(N2 + 3600 + 1800, .97, .90)]}]}),
        ("wx_l01", {"event_ticker": "KXHIGHTDAL-26NOV10"}, {"markets": lst})])
    t10 = "KXHIGHTDAL-26NOV10-B78.5"
    run(os.path.join(d, "B"), [("wxb_c_" + t10, {"market_tickers": t10}, {"markets": [{"market_ticker": t10, "candlesticks": [c(1794376800 - 1800, .50)]}]})])
    return os.path.join(d, "A"), os.path.join(d, "B")


bad = []
root = tempfile.mkdtemp()
r = W.count(*make(root))
exp = {"covered": 3, "shows_close": 1, "shows_low": 2, "no_post_day_candle": 1, "winner_unconfirmed": 2, "unresolved": [], "not_recounted": 37,
       "verdict": "incomplete: 37 city-days not recounted"}
if r != exp:
    bad.append(("base", r))
r2 = W.count(*make(root, two_yes=True))
if r2["unresolved"] != ["KXHIGHTDAL-26NOV10"] or r2["covered"] != 2:
    bad.append(("two yes", r2))
try:
    W.count(*make(root, bad_end=True)); bad.append(("bad end not refused",))
except W.Stop as e:
    print("bad end ->", e)
hd = os.path.join(root, "HELDOUT_x"); os.makedirs(hd)
try:
    W.count(*make(hd)); bad.append(("HELDOUT not refused",))
except (W.Stop, SystemExit) as e:
    print("HELDOUT ->", str(e)[:60])
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
