#!/usr/bin/env python3
"""Synthetic test of engine1_nc15.py (invented tickers, prices and dates; no real run is opened). python3 -I engine1_nc15_test.py"""
import os, sys, json, gzip, tempfile, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_nc15 as X
def put(base, run, bodies):
    d = os.path.join(base, *run.split("/")); os.makedirs(d); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; json.dump(b, gzip.open(os.path.join(d, fn), "wt")); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"status": "complete", "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
def cand(e, bid, ask, last=0.5, vol=3, oi=10, full=True):
    k = {"end_period_ts": e, "yes_bid": {"close_dollars": bid}, "yes_ask": {"close_dollars": ask}}
    if full: k.update({"price": {"close_dollars": last}, "volume_fp": vol, "open_interest_fp": oi})
    return k
def main():
    b = tempfile.mkdtemp(); out = os.path.join(b, "out")
    cut = X.CUT; before = "2026-10-03T15:45:00Z"
    A = {"markets": [{"ticker": "KXSILVER15M-T1", "close_time": before, "result": "yes"},                        # kept
                     {"ticker": "KXSILVER15M-T2", "close_time": "2026-10-03T16:00:00Z", "result": "no"},        # at the cut: dropped
                     {"ticker": "KXSILVER15M-T3", "close_time": before, "result": ""},                          # no result: dropped
                     {"ticker": "KXFOO15M-T4", "close_time": before, "result": "yes"}]}                         # foreign series
    X_ = {"markets": [{"ticker": "KXWTI15M-T5", "close_time": "2026-10-02T12:00:00Z", "result": "no"}]}
    e1 = X.calendar.timegm((2026, 10, 3, 15, 45, 0)); e0 = e1 - 60
    runs = {X.LISTS[0]: [A], X.LISTS[1]: [X_]}
    for r in X.CANDLES: runs[r] = [{"markets": []}]
    runs[X.CANDLES[0]] = [{"markets": [{"market_ticker": "KXSILVER15M-T1", "candlesticks": [cand(e0, 0.4, 0.5), cand(e0, 0.4, 0.5), cand(e1, 0.5, 0.6, full=False), cand(e1 + 60, 0.5, 0.6), {"end_period_ts": e1}]},
                                       {"market_ticker": "KXSILVER15M-T2", "candlesticks": [cand(e0, 0.1, 0.2)]}, {"market_ticker": "KXWTI15M-T5", "candlesticks": [cand(1790000000, 0.7, 0.8)]}]}]
    for r, bodies in runs.items(): put(b, r, bodies)
    allow = os.path.join(b, "HELDOUT_PULL_RUNS.md")
    try: X.build(b, out, allow); raise AssertionError("must refuse with no allow file content")
    except SystemExit: pass
    open(allow, "w").write("x readable ONLY by engine1_nc15.py %s %s\n" % (X.self_sha(), " ".join(X.LISTS + X.CANDLES)))
    L = X.build(b, out, allow); c = L["counts"]
    assert L["markets"] == 2 and c["dropped by the cut"] == 1 and c["no result (dropped)"] == 1 and c["unknown series or no close"] == 1, c
    assert c["candle after close (dropped)"] == 1 and c["duplicate candle (first kept)"] == 1 and c["candle unreadable (no end, bid or ask)"] == 1, c
    assert c["candle market not kept (not parsed)"] == 1 and c["candles kept"] == 3 and c["candle without last (NULL)"] == 1 and c["candle without volume (NULL)"] == 1 and c["candle without oi (NULL)"] == 1, c
    db = sqlite3.connect(os.path.join(out, "ENGINE1_nc15_extract.sqlite"))
    assert db.execute("select count(*) from market").fetchone()[0] == 2 and db.execute("select count(*) from candle where ticker like '%T2'").fetchone()[0] == 0
    assert db.execute("select yes_bid,yes_ask,last,volume,oi from candle where end_ts=?", (e0,)).fetchone() == (0.4, 0.5, 0.5, 3.0, 10.0)
    print("engine1_nc15 test ok", c)

class Guard(dict):
    """A market object that raises on any key but ticker and close_time (a dropped market must never have another key read)."""
    def __getitem__(self, k):
        if k not in ("ticker", "close_time"): raise AssertionError("key %r of a dropped market was read" % k)
        return dict.__getitem__(self, k)
    def get(self, k, d=None): raise AssertionError("get(%r) on a dropped market" % k)
    def __contains__(self, k): raise AssertionError("contains(%r) on a dropped market" % k)
    def keys(self): raise AssertionError("keys() on a dropped market")
    def items(self): raise AssertionError("items() on a dropped market")
    def values(self): raise AssertionError("values() on a dropped market")
    def __iter__(self): raise AssertionError("iter on a dropped market")
def guard_test():
    b = tempfile.mkdtemp(); out = os.path.join(b, "out"); allow = os.path.join(b, "H.md")
    open(allow, "w").write("x engine1_nc15.py %s %s\n" % (X.self_sha(), " ".join(X.LISTS + X.CANDLES)))
    late = Guard({"ticker": "KXSILVER15M-T9", "close_time": "2026-10-03T16:00:00Z", "result": "yes", "secret": 1})
    foreign = Guard({"ticker": "KXFOO15M-T8", "close_time": "2026-10-02T00:00:00Z", "result": "yes"})
    ok = {"ticker": "KXSILVER15M-T1", "close_time": "2026-10-02T00:00:00Z", "result": "yes"}
    orig = X.run_bodies
    X.run_bodies = lambda base, run: iter([{"markets": [late, foreign, ok]}] if run in X.LISTS[:1] else ([{"markets": []}] if run in X.LISTS else [{"markets": [{"market_ticker": "KXSILVER15M-T9", "candlesticks": [object()]}, {"market_ticker": "KXSILVER15M-T1", "candlesticks": []}]}]))
    try: L = X.build(b, out, allow)
    finally: X.run_bodies = orig
    c = L["counts"]; assert c["dropped by the cut"] == 1 and c["unknown series or no close"] == 1 and L["markets"] == 1 and c["candle market not kept (not parsed)"] == len(X.CANDLES), c
    print("guard test ok (dropped markets: only ticker and close_time were read; a non-kept candle market is not parsed)")
main(); guard_test()
