"""python3 -I hourbridge_load_test.py : the loader's wall on invented files; late rows raise on any column but close_time."""
import os, sys, gzip, csv, io, tempfile, collections, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hourbridge_load as L
class Late(dict):
    """a row at or after the cut: only close_time may be read"""
    def __getitem__(s, k):
        if k != "close_time": raise AssertionError("touched column %r of a row outside the window" % k)
        return super().__getitem__(k)
cnt = collections.Counter()
rows = [Late({"close_time": "2026-11-02T00:00:00Z", "ticker": "X", "strike": "1"}), Late({"close_time": "2026-10-27T23:00:00Z", "ticker": "X"})]
assert L.ladder_rows(rows, cnt) == [] and cnt["ladder row outside the window (dropped)"] == 2
rr = [Late({"close_time": "2026-11-05T00:00:00Z", "ticker": "KXBTC15M-A", "result": "yes"})]
assert L.result_rows(rr, cnt) == {} and cnt["result row outside the window (dropped)"] == 1             # the result column is never touched
ok = [{"close_time": "2026-10-28T18:00:00Z", "ticker": "KXBTCD-26OCT2814-T1", "strike": "80900", "status": "active", "t_recv_ms": "5", "yes_bid": "0.5", "yes_ask": "0.52"}, {"close_time": "2026-10-28T18:00:00Z", "ticker": "KXETHD-1", "strike": "1", "status": "active", "t_recv_ms": "5", "yes_bid": "0.5", "yes_ask": "0.52"}]
got = L.ladder_rows(ok, cnt); assert got == [(1793210400, "KXBTCD-26OCT2814-T1", 80900.0, 5, 0.5, 0.52)] and cnt["ladder ticker outside the wall (dropped)"] == 1, got
assert L.in_window("2026-10-28T00:00:00Z") == 1793145600 and L.in_window("2026-11-01T23:59:59Z") is not None and L.in_window("2026-11-02T00:00:00Z") is None and L.CUT == calendar.timegm((2026, 11, 2, 0, 0, 0)) and L.START == calendar.timegm((2026, 10, 28, 0, 0, 0))
# a 15 minute quote of a ticker not in the kept results is dropped
assert L.quote_rows([{"ticker": "KXBTC15M-Z", "strike": "1", "t_recv_ms": "1", "yes_bid": "0.5", "yes_ask": "0.6"}], {}, cnt) == []
# files: end to end on an invented checkout; directories dated 2026-11-02 and later are never opened
base = tempfile.mkdtemp()
def put(date, run, name, header, rows_):
    d = os.path.join(base, "quotes", date, run); os.makedirs(d, exist_ok=True)
    b = io.StringIO(); w = csv.writer(b); w.writerow(header); w.writerows(rows_)
    gzip.open(os.path.join(d, name), "wt").write(b.getvalue())
H = 1793210400                                                       # 2026-10-28T18:00:00Z
put("2026-10-28", "1700", "results.csv.gz", ["ticker", "result", "close_time", "seen_ms"], [["KXBTC15M-A", "yes", "2026-10-28T18:00:00Z", "1"], ["KXBTC15M-B", "no", "2026-11-02T00:15:00Z", "1"]])
put("2026-10-28", "1700", "quotes.csv.gz", ["t_send_ms", "t_recv_ms", "ticker", "yes_bid", "yes_ask", "bid_size", "ask_size", "strike", "status"], [[1, (H - 100) * 1000 - 500, "KXBTC15M-A", 0.6, 0.64, 1, 1, 100050, "active"], [1, 5, "KXBTC15M-B", 0.6, 0.64, 1, 1, 1, "active"]])
put("2026-10-28", "1700", "ladder.csv.gz", ["t_send_ms", "t_recv_ms", "ticker", "yes_bid", "yes_ask", "bid_size", "ask_size", "strike", "status", "close_time"], [[1, (H - 100) * 1000 - 500, "KXBTCD-X-T1", 0.79, 0.81, 1, 1, 100000, "active", "2026-10-28T18:00:00Z"], [1, (H - 100) * 1000 - 500, "KXBTCD-X-T2", 0.59, 0.61, 1, 1, 100100, "active", "2026-10-28T18:00:00Z"]])
bad = os.path.join(base, "quotes", "2026-11-02", "0100"); os.makedirs(bad)                # an unreadable file in a late directory: never opened
open(os.path.join(bad, "results.csv.gz"), "wb").write(b"not gzip")
allow = os.path.join(base, "H.md"); L.ALLOW_FILE = allow; open(allow, "w").write("x\n")
try: L.load(base); assert False
except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write("y %s hourbridge_load.py %s\n" % (L.ALLOW_MARK, L.self_sha()))
ev, c = L.load(base)
assert len(ev) == 1 and ev[0]["H"] == H and ev[0]["result"] == "yes" and ev[0]["q15"]["strike"] == 100050.0 and sorted(ev[0]["ladder"]) == [100000.0, 100100.0] and c["result row outside the window (dropped)"] == 1, (ev, c)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import hourbridge as HB
assert HB.decide(ev[0])[0] == "ok"                                                           # the loader's event feeds the core
print("ALL OK")
