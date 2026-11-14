"""Test for spxoi1_threshold_run.py: INVENTED rows only (SPXOI1_THRESHOLD_HAND_CASE.md). Run: python3 -B -W ignore test_spxoi1_threshold_run.py"""
import calendar, gzip, json, math, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import spxoi1_threshold_run as t

T = lambda *a: calendar.timegm(a)
iso = lambda ts: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(ts))
def mkrun(d, bodies):
    os.makedirs(d); rows = []
    for i, (rid, body) in enumerate(bodies):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "page": 1, "status": 200, "file": f})
    json.dump({"job": {}, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))
def mrow(tk, close): return {"ticker": tk, "event_ticker": "KXINX15M-EV" + tk[-4:], "open_time": iso(close - 900), "close_time": iso(close), "result": "yes", "strike_type": "greater_or_equal", "floor_strike": 7000.0, "volume_fp": "5.00"}
def cnode(tk, close, rise=None, oi_prev=1000, a=True, b=True, raw_now=None, raw_prev=None):
    """OI at close-360 = oi_prev, at close-180 = oi_prev + rise (strings, as landed); a/b False = that candle absent; raw_* override the stored value."""
    cs = []
    if b: cs.append({"end_period_ts": close - 360, "open_interest_fp": ("%.2f" % oi_prev) if raw_prev is None else raw_prev})
    if a: cs.append({"end_period_ts": close - 180, "open_interest_fp": ("%.2f" % (oi_prev + rise)) if raw_now is None else raw_now})
    return {"market_ticker": tk, "candlesticks": cs}
def build(d, specs, series="KXINX15M"):
    """specs: list of (name, close, node kwargs or None = no answer at all)."""
    mk = [mrow("%s-%s" % (series, n), c) for n, c, _ in specs]
    nodes = [cnode("%s-%s" % (series, n), c, **kw) for n, c, kw in specs if kw is not None]
    L, C = os.path.join(d, "L"), os.path.join(d, "C")
    mkrun(L, [("l1", {"markets": mk})]); mkrun(C, [("c1", {"markets": nodes})])
    return L, C
base = T(2026, 11, 10, 15, 0, 0)
def ten(rises, start=0): return [("W%02d" % (start + i), base + 900 * i, dict(rise=r)) for i, r in enumerate(rises)]
R10 = [-5, 0, 3, 3, 7, 10, 12, 20, 25, 100]
quiet = lambda *a: None
def run(d, specs, **kw):
    L, C = build(d, specs, **kw); return t.run([L], [C], hash_check=False)
with tempfile.TemporaryDirectory() as d:
    r = run(d, ten(R10)); assert r["n"] == 10 and r["T"] == 25 and r["missing_candle"] == 0 and r["unreadable_open_interest"] == 0 and r["extra_windows_with_rise_ge_T"] == 2, r
with tempfile.TemporaryDirectory() as d:
    r = run(d, ten(sorted(R10 + [40]))); assert r["n"] == 11 and r["T"] == 40, r
with tempfile.TemporaryDirectory() as d:
    r = run(d, ten(list(range(1, 21)))); assert r["n"] == 20 and r["T"] == 18 and r["extra_windows_with_rise_ge_T"] == 3, r
with tempfile.TemporaryDirectory() as d:
    r = run(d, ten([7])); assert r["n"] == 1 and r["T"] == 7
# the rank function itself
assert t.nearest_rank_p90([5]) == 5 and t.nearest_rank_p90(list(range(1, 11))) == 9 and t.nearest_rank_p90(list(range(1, 12))) == 10 and t.nearest_rank_p90(list(range(1, 21))) == 18 and t.nearest_rank_p90(list(range(1, 101))) == 90 and t.nearest_rank_p90([3, 1, 2]) == 3 and t.nearest_rank_p90([]) is None
assert t.nearest_rank_p90([-3, -2, -1, 0, 0, 0, 0, 0, 0, 5]) == 0          # negative and zero rises kept, ties are just the value
# drops: missing candle 3, unreadable 5; none changes n or T
extra = [("D1", base + 900 * 20, dict(rise=5, a=False)), ("D2", base + 900 * 21, dict(rise=5, b=False)), ("D3", base + 900 * 22, None),
         ("U1", base + 900 * 23, dict(rise=5, raw_now="nan")), ("U2", base + 900 * 24, dict(rise=5, raw_now=None)), ("U3", base + 900 * 25, dict(rise=5, raw_now=True)),
         ("U4", base + 900 * 26, dict(rise=5, raw_now="inf")), ("U5", base + 900 * 27, dict(rise=5, raw_prev="x"))]
with tempfile.TemporaryDirectory() as d:
    specs = ten(R10) + extra
    # U2: the field is ABSENT: drop the key from the stored candle
    L, C = build(d, specs)
    man = json.load(open(os.path.join(C, "manifest.json"))); f = os.path.join(C, man["rows"][0]["file"]); body = json.load(gzip.open(f))
    for n in body["markets"]:
        if n["market_ticker"].endswith("-U2"):
            for c in n["candlesticks"]: c.pop("open_interest_fp", None) if c["end_period_ts"] == base + 900 * 24 - 180 else None
    gzip.open(f, "wt").write(json.dumps(body))
    r = t.run([L], [C], hash_check=False)
    assert r["n"] == 10 and r["T"] == 25 and r["missing_candle"] == 3 and r["unreadable_open_interest"] == 5, r
# the date range: [2026-11-05, 2026-11-14); an out-of-range window is not read
with tempfile.TemporaryDirectory() as d:
    sp = [("A", T(2026, 11, 5, 0, 0, 0), dict(rise=1)), ("B", T(2026, 11, 4, 23, 59, 59), dict(rise=2)), ("C", T(2026, 11, 13, 23, 59, 59), dict(rise=3)), ("E", T(2026, 11, 14, 0, 0, 0), dict(rise=4)), ("F", T(2026, 12, 1, 0, 0, 0), dict(rise=5))]
    L, C = build(d, sp)
    class Poison(dict):
        def get(self, key, default=None):
            if key.endswith(("-B", "-E", "-F")): raise AssertionError("read an outside window: " + key)
            return super().get(key, default)
    r = t.compute(k.markets([L]), Poison(k.candles([C])), set())
    assert r["n"] == 2 and r["windows_listed"] == 5 and r["outside_range_not_read"] == 3 and r["T"] == 3, r          # rises 1 and 3: rank ceil(1.8) = 2 -> 3
# another series is not a window
with tempfile.TemporaryDirectory() as d:
    L, C = build(d, ten(R10), series="KXBTC15M"); r = t.run([L], [C], hash_check=False); assert r["n"] == 0 and r["T"] is None and r["windows_listed"] == 0
# a market with no close time is listed and not read; the hash check is called by default and skipped only when asked
with tempfile.TemporaryDirectory() as d:
    L, C = build(d, ten(R10))
    mk = k.markets([L]); some = sorted(mk)[0]; mk[some] = dict(mk[some], close=None)
    r = t.compute(mk, k.candles([C]), set()); assert r["n"] == 9 and r["outside_range_not_read"] == 1 and r["windows_listed"] == 10, r
    calls = []; saved = t.check_hashes; t.check_hashes = lambda want=None: calls.append(1)
    try:
        t.run([L], [C]); assert calls == [1]
        t.run([L], [C], hash_check=False); assert calls == [1]
    finally: t.check_hashes = saved
# no per-window text; the hash refusal
with tempfile.TemporaryDirectory() as d:
    L, C = build(d, ten(R10)); out = t.render(t.run([L], [C], hash_check=False)); assert "KXINX15M-" not in out and "W0" not in out and "T = 25" in out and "extra" in out
try: t.check_hashes({"spxoi1.py": "0" * 16, "scorekit.py": "f219b43c755b4b87"}); assert 0
except SystemExit as e: assert "audited" in str(e)
try: t.check_hashes({"spxoi1.py": "be22330d6d8d9f03", "scorekit.py": "0" * 16}); assert 0
except SystemExit as e: assert "audited" in str(e)
t.check_hashes()          # the real files are the audited builds
print("test_spxoi1_threshold_run: all checks passed")
