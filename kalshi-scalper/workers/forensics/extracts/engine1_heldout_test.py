#!/usr/bin/env python3
"""Synthetic test of engine1_heldout.py (invented tickers and dates; no pull run is opened). python3 -I engine1_heldout_test.py"""
import os, sys, json, gzip, tempfile, sqlite3, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_heldout as X
class Guard(dict):
    def __getitem__(self, k):
        if k not in ("ticker", "close_time"): raise AssertionError("key %r of a dropped market was read" % k)
        return dict.__getitem__(self, k)
    def get(self, k, d=None): raise AssertionError("get on a dropped market")
    def __contains__(self, k): raise AssertionError("contains on a dropped market")
    def keys(self): raise AssertionError("keys")
    def items(self): raise AssertionError("items")
def put(base, run, body):
    d = os.path.join(base, *run.split("/")); os.makedirs(d); json.dump(body, gzip.open(os.path.join(d, "0001.json.gz"), "wt")); json.dump({"status": "complete", "rows": [{"id": "r", "status": 200, "file": "0001.json.gz"}]}, open(os.path.join(d, "manifest.json"), "w"))
def cand(e, bid, ask, full=True):
    k = {"end_period_ts": e, "yes_bid": {"close_dollars": bid}, "yes_ask": {"close_dollars": ask}}
    if full: k.update({"price": {"close_dollars": 0.5}, "volume_fp": "3", "open_interest_fp": "10"})
    return k
def main():
    assert X.FROM == 1791043200 and X.TO["KXBTC15M"] == 1793145600 and X.TO["KXSILVER15M"] == 1793721600 and X.TO["KXZEC15M"] == 1793721600 and len(X.TO) == 12 and "KXNATGAS15M" not in X.TO and "KXCOPPER15M" not in X.TO
    b = tempfile.mkdtemp(); out = os.path.join(b, "out"); allow = os.path.join(b, "H.md"); LS, CS = ("L/x_1",), ("C/x_2",)
    ok = {"ticker": "KXBTC15M-T1", "close_time": "2026-10-10T12:00:00Z", "result": "yes"}; okz = {"ticker": "KXZEC15M-T6", "close_time": "2026-11-03T15:45:00Z", "result": "no"}
    early = Guard({"ticker": "KXBTC15M-T2", "close_time": "2026-10-03T15:45:00Z", "result": "yes"}); late = Guard({"ticker": "KXBTC15M-T3", "close_time": "2026-10-28T00:00:00Z", "result": "yes"})
    e830 = Guard({"ticker": "KXWTI15M-T7", "close_time": "2026-10-12T13:30:00Z", "result": "yes"}); foreign = Guard({"ticker": "KXFOO15M-T4", "close_time": "2026-10-10T00:00:00Z", "result": "yes"}); nores = {"ticker": "KXBTC15M-T5", "close_time": "2026-10-10T13:00:00Z", "result": ""}
    put(b, LS[0], {"markets": []}); put(b, CS[0], {"markets": []})
    e1 = calendar.timegm((2026, 10, 10, 11, 45, 0)); X_bodies = {LS[0]: [{"markets": [ok, early, late, foreign, nores, okz, e830]}], CS[0]: [{"markets": [{"market_ticker": "KXBTC15M-T1", "candlesticks": [cand(e1, 0.4, 0.5), cand(e1, 0.4, 0.5), cand(e1 + 900, 0.5, 0.6), cand(e1 + 960, 0.5, 0.6), cand(e1 + 60, 0.5, 0.6, full=False)]}, {"market_ticker": "KXBTC15M-T2", "candlesticks": [object()]}]}]}
    try: X.build(b, out, allow, LS, CS); raise AssertionError("must refuse without an allow file")
    except SystemExit: pass
    try: X.build(b, out, allow, (), ()); raise AssertionError("must refuse with no run names")
    except SystemExit: pass
    open(allow, "w").write("x engine1_heldout.py %s %s %s\n" % (X.self_sha(), LS[0], CS[0]))
    orig = X.run_bodies; X.run_bodies = lambda base, run: iter(X_bodies[run])
    try: L = X.build(b, out, allow, LS, CS)
    finally: X.run_bodies = orig
    c = L["counts"]; assert L["markets"] == 3 and c["dropped before 2026-10-03T16:00Z"] == 1 and c["dropped at or after the series' end"] == 1 and c["unknown series or no close"] == 1 and c["result not yes or no (kept as void)"] == 1 and c["dropped: EVENT830 13:30Z close (KXWTI15M)"] == 1, c
    assert c["candles kept"] == 3 and c["duplicate candle (first kept)"] == 1 and c["candle after close (dropped)"] == 1 and c["candle without last (NULL)"] == 1 and c["candle market not kept (not parsed)"] == 1, c
    db = sqlite3.connect(os.path.join(out, "ENGINE1_heldout_extract.sqlite")); assert db.execute("select count(*) from market").fetchone()[0] == 3 and db.execute("select count(*) from market where result='void'").fetchone()[0] == 1
    print("engine1_heldout test ok", c)
main()
