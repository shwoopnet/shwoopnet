"""SPXOI1 threshold script test on INVENTED candles (hand-computed). python3 -I spxoi1_threshold_test.py"""
import sys, os, gzip, json, tempfile, calendar, time, io, contextlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import spxoi1_threshold as S
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
import hashlib
def folder(d, name, body, pages=None, status="complete", mutate=None):
    """a kalshi-pull run folder: pages = a list of bodies (one request id r1, pages 1..k); default one page. mutate(rows) edits the manifest rows before writing"""
    p = os.path.join(d, name); os.makedirs(p); bodies = pages or [body]; rows = []
    for i, b in enumerate(bodies, 1):
        raw = json.dumps(b).encode(); fn = "%04d.json.gz" % i
        with gzip.open(os.path.join(p, fn), "wb") as f: f.write(raw)
        rows.append({"index": i, "id": "r1", "page": i, "status": 200, "bytes": len(raw), "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False, "body_kind": "object"})
    if mutate: mutate(rows)
    json.dump({"status": status, "rows": rows}, open(p + "/manifest.json", "w")); return p
base = calendar.timegm(time.strptime("2026-11-06", "%Y-%m-%d")) + 15 * 3600
# hand-built: windows 1..10 with oi_rise = 1..10 (oi at close-360 is 1000, at close-180 is 1000 + k): nearest-rank P90 of 10 values = ceil(9) = 9th = 9
markets, cands = [], []
def candles(c, rise, decoys=True):
    out = [{"end_period_ts": c - 360, "open_interest": 1000, "price": {"close": 0.5}, "volume": 999999}, {"end_period_ts": c - 180, "open_interest": 1000 + rise, "price": {"close": 0.99}, "volume": 7}]
    out.append({"end_period_ts": c - 270, "open_interest": 5000000})     # a decoy candle at the wrong minute: must not be read
    return out
for k in range(1, 11):
    c = base + 900 * k; tk = "KXINX15M-W%d" % k
    markets.append({"ticker": tk, "close_time": iso(c), "result": "yes", "yes_bid": 0.9, "floor_strike": 1.0})
    cands.append({"market_ticker": tk, "candlesticks": candles(c, k)})
# dropped: a window with the close-360 candle missing, one with a non-number open interest, one with no candles at all
c = base + 900 * 20; markets.append({"ticker": "KXINX15M-D1", "close_time": iso(c)}); cands.append({"market_ticker": "KXINX15M-D1", "candlesticks": [{"end_period_ts": c - 180, "open_interest": 2000}]})
c = base + 900 * 21; markets.append({"ticker": "KXINX15M-D2", "close_time": iso(c)}); cands.append({"market_ticker": "KXINX15M-D2", "candlesticks": [{"end_period_ts": c - 360, "open_interest": "n/a"}, {"end_period_ts": c - 180, "open_interest": 2000}]})
c = base + 900 * 22; markets.append({"ticker": "KXINX15M-D3", "close_time": iso(c)})
# excluded by the date range: closes before Nov 5, on Nov 14, and on Dec 1; and another series
for name, ct in (("E1", calendar.timegm(time.strptime("2026-11-04", "%Y-%m-%d")) + 15 * 3600), ("E2", S.WINDOW_TO), ("E3", S.HELDOUT_FIRST + 3600)):
    markets.append({"ticker": "KXINX15M-" + name, "close_time": iso(ct)}); cands.append({"market_ticker": "KXINX15M-" + name, "candlesticks": candles(ct, 10 ** 6)})
markets.append({"ticker": "KXBTC15M-X", "close_time": iso(base + 900 * 30)}); cands.append({"market_ticker": "KXBTC15M-X", "candlesticks": candles(base + 900 * 30, 10 ** 6)})
d = tempfile.mkdtemp(); lists = folder(d, "lists", {"markets": markets}); cd = folder(d, "cands", {"markets": cands})
rises, miss, unread = S.derive(S.closes(lists), S.oi_by_end(cd))
assert sorted(rises) == list(range(1, 11)) and miss == 2 and unread == 1, (sorted(rises), miss, unread)      # D1 and D3 missing a candle, D2 unreadable OI
assert S.nearest_rank(rises) == 9
buf = io.StringIO()
with contextlib.redirect_stdout(buf): S.main(lists, cd)
out = buf.getvalue().strip().split("\n")
assert out[0].startswith("HELDOUT_PULL_RUNS.md copy read by the guard: sha256 ") and out[1] == "n = 10, T = 9" and out[2] == "dropped, missing candle = 2" and out[3] == "dropped, unreadable open interest = 1" and len(out) == 4, out
# nearest-rank edges: n 1, n 5 (ceil(4.5) = 5th), n 11 (ceil(9.9) = 10th), n 20 (ceil(18) = 18th), ties
assert S.nearest_rank([7]) == 7 and S.nearest_rank([1, 2, 3, 4, 5]) == 5 and S.nearest_rank(list(range(1, 12))) == 10 and S.nearest_rank(list(range(1, 21))) == 18 and S.nearest_rank([5, 5, 5, 9, 9, 9, 9, 9, 9, 9]) == 9
# negative rises are kept (open interest can fall)
assert S.derive({"KXINX15M-N": base}, {"KXINX15M-N": {base - 360: 100.0, base - 180: 60.0}}) == ([-40.0], 0, 0)
# only the two named fields are read from each source: the script text names no price, result or volume key
src = open(os.path.join(here, "spxoi1_threshold.py")).read().split('import sys, os, gzip', 1)[1]
for bad in ("yes_bid", "yes_ask", '"result"', "volume", "price", "floor_strike"): assert bad not in src, bad
# the guard: a HELDOUT_ folder is refused
h = os.path.join(d, "HELDOUT_X"); os.makedirs(h); json.dump({"rows": []}, open(h + "/manifest.json", "w"))
try: list(S.bodies(h)); raise AssertionError("HELDOUT_ folder not refused")
except SystemExit: pass
# F1: the real candles carry open_interest_fp as a STRING: it is read first, open_interest is the fallback
assert S.oi_of({"open_interest_fp": "1050.00", "open_interest": 7}) == 1050.0           # fp wins over the plain field
assert S.oi_of({"open_interest_fp": "1050"}) == 1050.0 and S.oi_of({"open_interest": 12}) == 12.0     # string fp alone; plain field alone
assert S.oi_of({"open_interest_fp": None, "open_interest": 12}) == 12.0 and S.oi_of({"open_interest_fp": "", "open_interest": 12}) == 12.0    # an empty fp falls back
for bad in ({"open_interest_fp": "n/a", "open_interest": 7}, {"open_interest_fp": "nan"}, {"open_interest_fp": "inf"}, {"open_interest": float("nan")}, {"open_interest": float("inf")}, {"open_interest": True}, {"open_interest_fp": True}, {}, {"open_interest": None}): assert S.oi_of(bad) is None, bad
# a string-fp candle set is read end to end (every real window would have dropped before)
c0 = base + 900 * 40; fpm = [{"ticker": "KXINX15M-F", "close_time": iso(c0)}]
fpc = [{"market_ticker": "KXINX15M-F", "candlesticks": [{"end_period_ts": c0 - 360, "open_interest_fp": "2000.50"}, {"end_period_ts": c0 - 180, "open_interest_fp": "2010.75"}]}]
d2 = tempfile.mkdtemp(); r2, m2, u2 = S.derive(S.closes(folder(d2, "l", {"markets": fpm})), S.oi_by_end(folder(d2, "c", {"markets": fpc}))); assert r2 == [10.25] and (m2, u2) == (0, 0), (r2, m2, u2)
# F2: run-integrity refusals (each must raise SystemExit before anything is read)
def refused(**kw):
    dd = tempfile.mkdtemp()
    try:
        S.check_run(folder(dd, "x", {"markets": fpm}, **kw)); return False
    except SystemExit: return True
assert not refused()                                                                       # a clean run passes
assert refused(status="stopped_429") and refused(status="stopped_size") and refused(status="")
def m_sha(rows): rows[0]["sha256"] = "0" * 64
def m_bytes(rows): rows[0]["bytes"] += 1
def m_trunc(rows): rows[0]["truncated"] = True
def m_404(rows): rows[0]["status"] = 404
def m_nofile(rows): os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nonexistent")) if False else rows[0].pop("file")
for fn in (m_sha, m_bytes, m_trunc, m_404, m_nofile): assert refused(mutate=fn), fn.__name__
# pages: 1 to k contiguous, all 200, the last without a cursor
pg = [{"markets": [], "cursor": "abc"}, {"markets": []}]; dd = tempfile.mkdtemp(); S.check_run(folder(dd, "p", None, pages=pg))      # two pages, the last has no cursor: fine
dd = tempfile.mkdtemp()
try: S.check_run(folder(dd, "p", None, pages=[{"markets": [], "cursor": "abc"}])); raise AssertionError("a last page with a cursor was accepted")
except SystemExit: pass
dd = tempfile.mkdtemp()
def m_gap(rows): rows[1]["page"] = 3                                                      # pages 1 and 3: page 2 missing
try: S.check_run(folder(dd, "p", None, pages=[{"markets": [], "cursor": "abc"}, {"markets": []}], mutate=m_gap)); raise AssertionError("a page gap was accepted")
except SystemExit: pass
dd = tempfile.mkdtemp()
def m_retry(rows): rows.insert(0, {"index": 0, "id": "r1", "page": 1, "status": 429, "bytes": 0})        # a 429 retry row before the 200 answer is fine
S.check_run(folder(dd, "p", {"markets": fpm}, mutate=m_retry))
# PATCH folders (the Head's order, Nov 14): extra candle run folders merged by (ticker, end_period_ts); each passes the same run-integrity check; a conflicting value for the same ticker and end STOPS; an identical duplicate is fine
dp = tempfile.mkdtemp(); cp = base + 900 * 50; pm = [{"ticker": "KXINX15M-P1", "close_time": iso(cp)}]
c_main = [{"market_ticker": "KXINX15M-P1", "candlesticks": [{"end_period_ts": cp - 180, "open_interest_fp": "3010"}]}]       # the close-360 candle is missing in the main run
c_patch = [{"market_ticker": "KXINX15M-P1", "candlesticks": [{"end_period_ts": cp - 360, "open_interest_fp": "3000"}]}]
lp, cm, cpt = folder(dp, "l", {"markets": pm}), folder(dp, "cm", {"markets": c_main}), folder(dp, "cp", {"markets": c_patch})
assert S.derive(S.closes(lp), S.oi_by_end(cm)) == ([], 1, 0)                                                                 # main alone: dropped for a missing candle
assert S.derive(S.closes(lp), S.oi_by_end([cm, cpt])) == ([10.0], 0, 0), "the patch must fill the missing candle"            # merged: kept, rise 10
c_dup = [{"market_ticker": "KXINX15M-P1", "candlesticks": [{"end_period_ts": cp - 180, "open_interest_fp": "3010.0"}]}]
assert S.derive(S.closes(lp), S.oi_by_end([cm, cpt, folder(dp, "cd", {"markets": c_dup})])) == ([10.0], 0, 0)                  # an identical value (same number) is not a conflict
c_bad = [{"market_ticker": "KXINX15M-P1", "candlesticks": [{"end_period_ts": cp - 180, "open_interest_fp": "9999"}]}]
try: S.oi_by_end([cm, cpt, folder(dp, "cb", {"markets": c_bad})]); raise AssertionError("a conflicting patch value was accepted")
except SystemExit as e: assert "conflict" in str(e).lower(), str(e)
try: S.oi_by_end([cm, folder(dp, "cx", {"markets": c_patch}, status="stopped_429")]); raise AssertionError("an incomplete patch run was accepted")
except SystemExit: pass
buf = io.StringIO()
with contextlib.redirect_stdout(buf): S.main(lp, cm, cpt)
assert buf.getvalue().strip().split("\n")[1:] == ["n = 1, T = 10", "dropped, missing candle = 0", "dropped, unreadable open interest = 0"], buf.getvalue()
print("SPXOI1 THRESHOLD TEST OK (rise = candle at -180 s minus candle at -360 s, dropped windows counted, date range, nearest-rank P90, only two fields per source, guard)")
