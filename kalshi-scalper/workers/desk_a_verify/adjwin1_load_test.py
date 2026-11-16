"""python3 -I adjwin1_load_test.py : the loader on invented runs; late-close markets must raise on every key but ticker and close_time."""
import os, sys, json, gzip, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adjwin1_load as L
class Guarded(dict):                                           # raises on any key other than the allowed ones
    def __init__(s, d, allowed): super().__init__(d); s.allowed = allowed
    def __getitem__(s, k):
        if k not in s.allowed: raise AssertionError("touched key %r of a late market" % k)
        return super().__getitem__(k)
    def __contains__(s, k): raise AssertionError("touched a late market's keys")
    def get(s, k, d=None): raise AssertionError("get on a late market")
    def keys(s): raise AssertionError("keys")
    def items(s): raise AssertionError("items")
    def __iter__(s): raise AssertionError("iter")
base = tempfile.mkdtemp()
def put(run, bodies):
    d = os.path.join(base, *run.split("/")); os.makedirs(d); rows = []
    for i, b in enumerate(bodies):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b, default=dict)); rows.append({"id": "h%d" % i, "status": 200, "file": fn})
    json.dump({"status": "complete", "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
# lists: one early market (kept), one at the cut (dropped), one far late
early = {"ticker": "KXWTI15M-26AUG011200-00", "close_time": "2026-08-01T12:00:00Z", "result": "yes"}
cutm = {"ticker": "KXWTI15M-26OCT031600-00", "close_time": "2026-10-03T16:00:00Z", "result": "no"}
late = {"ticker": "KXWTI15M-26NOV101200-00", "close_time": "2026-11-10T12:00:00Z", "result": "no"}
cl = L.iso("2026-08-01T12:00:00Z")
class LateBody(dict): pass
# a late market object that raises on every key but ticker and close_time: serialized as plain dict for the file, so test the guard class on the in-memory path separately
put(L.LISTS[0], [{"markets": [early, cutm, late]}]); put(L.LISTS[1], [{"markets": []}])
cndl = lambda e, b, a: {"end_period_ts": e, "yes_bid": {"close_dollars": b}, "yes_ask": {"close_dollars": a}}
put(L.CANDLES[0], [{"markets": [{"market_ticker": early["ticker"], "candlesticks": [cndl(cl - 840, "0.49", "0.51"), cndl(cl, "0.98", "1.00"), cndl(cl + 60, "0.99", "1.00"), {"end_period_ts": cl - 60}]},
                                {"market_ticker": late["ticker"], "candlesticks": "SHOULD NOT BE PARSED"}]}])
for r in L.CANDLES[1:]: put(r, [{"markets": []}])
allow = os.path.join(base, "HELDOUT_PULL_RUNS.md")
# 1: refuses without the allow-list line
L.ALLOW_FILE = allow; open(allow, "w").write("| `X/1` | nothing |\n")
try: L.load(base); assert False
except SystemExit as e: assert "REFUSED" in str(e)
# 2: a line without the file's hash still refuses
open(allow, "w").write("NC15 runs " + " ".join(L.LISTS + L.CANDLES) + " " + L.ALLOW_MARK + " (adjwin1_load.py, sha256 deadbeef)\n")
try: L.load(base); assert False
except SystemExit as e: assert "REFUSED" in str(e)
# 3: the full line loads; counts and content
open(allow, "w").write("NC15 runs " + " ".join(L.LISTS + L.CANDLES) + " " + L.ALLOW_MARK + " (adjwin1_load.py, sha256 " + L.self_sha() + ")\n")
w, c = L.load(base)
assert list(w) == ["KXWTI15M"] and len(w["KXWTI15M"]) == 1, w
win = w["KXWTI15M"][0]; assert win["close"] == cl and win["result"] == "yes" and win["candles"] == [(cl - 840, .49, .51), (cl, .98, 1.0)], win
assert c.get("dropped by the cut") == 2 or c.get("dropped by the cut") == 1, c
assert c["dropped by the cut"] == 2 and c["candle after close (dropped)"] == 1 and c["candle unreadable"] == 1 and c["candle market not kept (not parsed)"] == 1, c
# 4: through load() itself, markets at or after the cut raise on every key but ticker and close_time
orig = L.run_bodies
def fake(base_, run):
    if run in L.LISTS[:1]: yield {"markets": [Guarded(cutm, {"ticker", "close_time"}), Guarded(late, {"ticker", "close_time"}), dict(early)]}
    else: yield from orig(base_, run)
L.run_bodies = fake
w2, c2 = L.load(base)
assert c2["dropped by the cut"] == 2 and len(w2["KXWTI15M"]) == 1, c2
g = Guarded(cutm, {"ticker", "close_time"})
for bad in ("result", "volume"):
    try: g[bad]; assert False
    except AssertionError as e: assert "touched key" in str(e)
# no-result rows are counted in total and per series
put2 = {"ticker": "KXWTI15M-26AUG011215-00", "close_time": "2026-08-01T12:15:00Z", "result": "void"}
def fake2(base_, run):
    if run in L.LISTS[:1]: yield {"markets": [dict(early), dict(put2)]}
    else: yield from orig(base_, run)
L.run_bodies = fake2
w3, c3 = L.load(base)
assert c3["no result (dropped)"] == 1 and c3["no result (dropped): KXWTI15M"] == 1, c3
print("ALL OK")
