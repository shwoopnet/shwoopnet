"""CFRTI-K held-out reader test on a MADE-UP fixture (synthetic candles from cfrti_k.synth, shifted). python3 -I cfrti_k_heldout_test.py"""
import sys, os, gzip, json, tempfile, calendar, time, io, contextlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import cfrti_k as K, cfrti_k_heldout as H
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def folder(d, name, body):
    p = os.path.join(d, name); os.makedirs(p); json.dump({"rows": [{"status": 200, "file": "a.json.gz"}]}, open(p + "/manifest.json", "w")); json.dump(body, gzip.open(p + "/a.json.gz", "wt")); return p
def build(days, start, edge, seed):
    M, B, P = K.synth(days=days, edge=edge, seed=seed)
    sh = calendar.timegm(time.strptime(start, "%Y-%m-%d")) - calendar.timegm(time.strptime("2026-08-01", "%Y-%m-%d"))
    d = tempfile.mkdtemp()
    lists = folder(d, "lists", {"markets": [{"ticker": tk, "close_time": iso(m["close"] + sh), "result": "yes" if m["yes"] else "no", "floor_strike": m["strike"]} for tk, m in M.items()]})
    cands = folder(d, "cands", {"markets": [{"market_ticker": tk, "candlesticks": [{"end_period_ts": ts + sh, "yes_bid": {"close": b}, "yes_ask": {"close": a}} for ts, (b, a) in cs.items()]} for tk, cs in B.items()]})
    perp = folder(d, "perp", {"candlesticks": [{"end_period_ts": ts + sh, "bid": {"close": p / 10000 - 0.00005}, "ask": {"close": p / 10000 + 0.00005}} for ts, p in P.items()]})
    return lists, cands, perp
H_MON = calendar.timegm(time.strptime("2026-11-14", "%Y-%m-%d"))
# 1. the held-out filter: a series spanning Oct 25 to Dec 24 loads only closes on or after 2026-11-14
lists, cands, perp = build(60, "2026-10-25", True, 7)
mk = H.load_markets_ho(lists); assert mk and min(m["close"] for m in mk.values()) >= H_MON, "a close before HELD_FROM was loaded"
assert max(m["close"] for m in mk.values()) > H_MON + 30 * 86400
tr = H.trades_of(mk, K.load_binary(cands), K.load_perp(perp)); assert len(tr) >= 50 and min(t["close"] for t in tr) >= H_MON, len(tr)
# 2. the label rule
def T(c): return dict(pnl=c, win=1 if c > 0 else 0, day=0, close=0)
assert H.label([T(0.5)] * 49) == "NOT_ENOUGH_DATA"
assert H.label([T(0.30)] * 30 + [T(-0.20)] * 20) == "PASS"                    # PF 1.5, mean positive, n 50
assert H.label([T(0.13)] * 20 + [T(-0.10)] * 30) == "FAIL"                   # PF 0.87
assert H.label([T(0.25)] * 20 + [T(-0.20)] * 30) == "FAIL"                   # PF 0.83 (mean negative): fails
assert H.label([T(0.30)] * 12 + [T(-0.20)] * 38) == "FAIL"                   # PF 0.47 at n 50
assert H.label([T(0.20)] * 24 + [T(-0.30)] * 26) == "FAIL"                   # PF 0.62
mid = [T(0.22)] * 30 + [T(-0.20)] * 30; assert 1.0 < K.pf([t["pnl"] for t in mid]) < 1.3 and H.label(mid) == "FAIL"   # bar missed, PF above 1.0: still FAIL at n >= 50 (the Head's ruling)
# 3. under 50 prints only the count and spends nothing
lists2, cands2, perp2 = build(2, "2026-11-14", False, 3)
mk_ = os.path.join(tempfile.mkdtemp(), "m.txt")
buf = io.StringIO()
with contextlib.redirect_stdout(buf): t2 = H.run(lists2, cands2, perp2, now=H.READ_NOT_BEFORE + 1, marker=mk_)
out = buf.getvalue(); assert len(t2) < 50 and "NOT_ENOUGH_DATA" in out and "cash PF" not in out and not os.path.exists(mk_), out
# 4. before the read date it refuses; at 50 or more it writes the marker, prints a label, and a second run refuses before reading
try:
    with contextlib.redirect_stdout(io.StringIO()): H.run(lists, cands, perp, now=H.READ_NOT_BEFORE - 1, marker=mk_)
    raise AssertionError("ran before the read date")
except SystemExit as e: assert "2026-11-20" in str(e)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): H.run(lists, cands, perp, now=H.READ_NOT_BEFORE + 5, marker=mk_)
out = buf.getvalue(); assert os.path.exists(mk_) and ("LABEL: PASS" in out or "LABEL: FAIL" in out) and "HELDOUT_PULL_RUNS.md copy read by the guard: sha256" in out, out
try:
    with contextlib.redirect_stdout(io.StringIO()): H.run(lists, cands, perp, now=H.READ_NOT_BEFORE + 9, marker=mk_)
    raise AssertionError("second read not refused")
except SystemExit as e: assert "has been made" in str(e)
print("CFRTI-K HELD-OUT TEST OK (filter from Nov 14, label rule, under 50 prints only the count and spends nothing, refuses before Nov 20, marker, second run refused)")
print(out.strip())
