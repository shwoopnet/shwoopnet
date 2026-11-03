"""RECBOOK2: plain assert tests, no network, no git. Run: python tests/test_book_series.py"""
import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "kalshi-scalper" / "src"))
from scalper import book_series as B

rec = root / "scripts" / "record_book2.py"
if rec.exists():          # the recorder lives on main (branch claude/v2-recorder-book2); its own cases are gate B7 in test/bookRecorderGates.test.js
    pass
# R1: the reader takes both layouts (Bitcoin without a series column, book2 with one) and filters by series
btc = {"poll_ts_local_ms": "1", "server_date_header": "Tue, 03 Nov 2026 21:00:00 GMT", "ticker": "KXBTCD-26NOV0317-T87249.99", "strike": "87249.99", "close_time": "2026-11-03T22:00:00Z",
       "yes_bid_px_1": "0.08", "yes_bid_sz_1": "10", "no_bid_px_1": "0.9", "no_bid_sz_1": "3"}
eth = dict(btc, series="KXETHD", ticker="KXETHD-26NOV0317-T2289.99", poll_ts_local_ms="2")
allp = list(B.rows_to_polls([btc, eth, dict(eth), dict(btc, server_date_header="")]))
assert [p.series for p in allp] == ["KXBTCD", "KXETHD"], "duplicate and no-date rows are dropped"
p = allp[1]
assert p.yes_px == [0.08] and p.yes_sz == [10.0] and p.no_px == [0.9] and p.close == 1793743200.0 and p.t == 1793739600.0
assert [x.series for x in B.rows_to_polls([btc, eth], series="KXETHD")] == ["KXETHD"]
t1 = {"ticker": "KXGOLDH-1", "trade_id": "z", "created_time": "2026-11-03T21:00:01Z", "yes_price_dollars": "0.05", "count_fp": "2.00", "taker_outcome_side": "no", "series": "KXGOLDH"}
assert [t.series for t in B.rows_to_trades([t1, t1, dict(t1, trade_id="y")])] == ["KXGOLDH", "KXGOLDH"]
assert B.DIRS == ("book/", "book2/")
print("ok")
