#!/usr/bin/env python3
"""Synthetic test of engine1_econhist.py (invented tickers and dates; the real run is not opened). python3 -I engine1_econhist_test.py"""
import os, sys, json, gzip, tempfile, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_econhist as X
class Guard(dict):
    def __getitem__(self, k):
        if k not in ("ticker", "close_time"): raise AssertionError("key %r of a dropped market was read" % k)
        return dict.__getitem__(self, k)
    def get(self, k, d=None): raise AssertionError("get on a dropped market")
    def __contains__(self, k): raise AssertionError("contains on a dropped market")
    def keys(self): raise AssertionError("keys on a dropped market")
    def items(self): raise AssertionError("items on a dropped market")
def main():
    b = tempfile.mkdtemp(); out = os.path.join(b, "out"); allow = os.path.join(b, "H.md"); d = os.path.join(b, *X.RUN.split("/")); os.makedirs(d)
    body = {"markets": [{"ticker": "KXCPI-25AUG-T1", "close_time": "2025-09-25T12:30:00Z", "event_ticker": "KXCPI-25AUG", "result": "yes"},                 # kept
                        Guard({"ticker": "KXCPI-25SEP-T2", "close_time": "2025-09-26T00:00:00Z", "event_ticker": "x", "result": "no"}),                 # at the cut: dropped
                        {"ticker": "KXPAYROLLS-26AUG-T3", "close_time": "2026-09-04T12:30:00Z", "event_ticker": "KXPAYROLLS-26AUG", "result": "no"},     # no cut: kept
                        {"ticker": "KXUE-26AUG-T4", "close_time": "2026-09-04T12:30:00Z", "event_ticker": "KXUE-26AUG", "result": ""},                   # kept, result NULL
                        Guard({"ticker": "KXFOO-T5", "close_time": "2026-01-01T00:00:00Z", "result": "yes"}),                                           # unknown series
                        {"ticker": "KXPAYROLLS-26AUG-T3", "close_time": "2026-09-04T12:30:00Z", "event_ticker": "KXPAYROLLS-26AUG", "result": "no"}]}    # duplicate
    json.dump({"markets": []}, gzip.open(os.path.join(d, "0001.json.gz"), "wt")); json.dump({"status": "complete", "rows": [{"id": "r", "status": 200, "file": "0001.json.gz"}]}, open(os.path.join(d, "manifest.json"), "w"))
    try: X.build(b, out, allow); raise AssertionError("must refuse without an allow file")
    except SystemExit: pass
    open(allow, "w").write("x readable ONLY by engine1_econhist.py %s %s\n" % (X.self_sha(), X.RUN))
    orig = X.run_bodies
    X.run_bodies = lambda base, run: iter([body])
    try: L = X.build(b, out, allow)
    finally: X.run_bodies = orig
    c = L["counts"]
    assert L["markets"] == 3 and c["dropped by the cut KXCPI"] == 1 and c["unknown series or no close"] == 1 and c["duplicate ticker (first kept)"] == 1 and c["result not yes or no (kept, NULL) KXUE"] == 1, c
    db = sqlite3.connect(os.path.join(out, "ENGINE1_econhist_extract.sqlite"))
    assert db.execute("select count(*) from market where ticker like 'KXCPI-25SEP%'").fetchone()[0] == 0 and db.execute("select result from market where ticker='KXUE-26AUG-T4'").fetchone()[0] is None
    print("engine1_econhist test ok", c)
main()
