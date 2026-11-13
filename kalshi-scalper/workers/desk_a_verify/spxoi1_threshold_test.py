"""SPXOI1 threshold script test on INVENTED candles (hand-computed). python3 -I spxoi1_threshold_test.py"""
import sys, os, gzip, json, tempfile, calendar, time, io, contextlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import spxoi1_threshold as S
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def folder(d, name, body):
    p = os.path.join(d, name); os.makedirs(p); json.dump({"rows": [{"status": 200, "file": "a.json.gz"}]}, open(p + "/manifest.json", "w")); json.dump(body, gzip.open(p + "/a.json.gz", "wt")); return p
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
rises, dropped = S.derive(S.closes(lists), S.oi_by_end(cd))
assert sorted(rises) == list(range(1, 11)) and dropped == 3, (sorted(rises), dropped)
assert S.nearest_rank(rises) == 9
buf = io.StringIO()
with contextlib.redirect_stdout(buf): S.main(lists, cd)
out = buf.getvalue().strip().split("\n")
assert out[0].startswith("HELDOUT_PULL_RUNS.md copy read by the guard: sha256 ") and out[1] == "n = 10, T = 9" and out[2] == "dropped (a needed candle missing) = 3" and len(out) == 3, out
# nearest-rank edges: n 1, n 5 (ceil(4.5) = 5th), n 11 (ceil(9.9) = 10th), n 20 (ceil(18) = 18th), ties
assert S.nearest_rank([7]) == 7 and S.nearest_rank([1, 2, 3, 4, 5]) == 5 and S.nearest_rank(list(range(1, 12))) == 10 and S.nearest_rank(list(range(1, 21))) == 18 and S.nearest_rank([5, 5, 5, 9, 9, 9, 9, 9, 9, 9]) == 9
# negative rises are kept (open interest can fall)
assert S.derive({"KXINX15M-N": base}, {"KXINX15M-N": {base - 360: 100.0, base - 180: 60.0}}) == ([-40.0], 0)
# only the two named fields are read from each source: the script text names no price, result or volume key
src = open(os.path.join(here, "spxoi1_threshold.py")).read().split('import sys, os, gzip', 1)[1]
for bad in ("yes_bid", "yes_ask", '"result"', "volume", "price", "floor_strike"): assert bad not in src, bad
# the guard: a HELDOUT_ folder is refused
h = os.path.join(d, "HELDOUT_X"); os.makedirs(h); json.dump({"rows": []}, open(h + "/manifest.json", "w"))
try: list(S.bodies(h)); raise AssertionError("HELDOUT_ folder not refused")
except SystemExit: pass
print("SPXOI1 THRESHOLD TEST OK (rise = candle at -180 s minus candle at -360 s, dropped windows counted, date range, nearest-rank P90, only two fields per source, guard)")
