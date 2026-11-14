"""Invented rows only. Tests for oicore_extract.py (canonical extract) and the extract mode of oicore_proven.py. Written before the code."""
import os, sys, tempfile, unittest, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oicore_extract as X
import oicore_proven as P
def row(ts, side="yes", result="yes", fill=0.1, fee=0.004, count=10, status="filled", strategy="OICORE", ticker="KXBTC15M-T"):
    return {"strategy": strategy, "status": status, "ts": ts, "side": side, "result": result, "avgFill": fill, "avgFee": fee, "count": count, "ticker": ticker}
def ts(i): return "2026-11-%02dT%02d:00:00.000Z" % (1 + i // 24, i % 24)
class T(unittest.TestCase):
    def test_canonical_bytes_by_hand(self):
        rep = {"generatedAt": "X", "slotOrders": [row(ts(2), side="no", result="no", fill=0.938, fee=0.0035, count=10, ticker="B"),
                                                 row(ts(1), fill=0.1, fee=0.004, count=12, ticker="A")]}
        text, c = X.extract(rep, 2)
        want = ("ts,ticker,side,count,avgFill,avgFee,result\n"
                "2026-11-01T01:00:00.000Z,A,yes,12,0.100000,0.004000,yes\n"
                "2026-11-01T02:00:00.000Z,B,no,10,0.938000,0.003500,no\n")
        self.assertEqual(text, want)
        self.assertEqual((c["excluded_exit"], c["excluded_unreadable"], c["open_unsettled"]), (0, 0, 0))
    def test_filters_counts_and_first_n_by_ts(self):
        rows = [row(ts(i)) for i in range(10, 0, -1)]                     # out of order, 10 rows
        rows += [row(ts(11), result="exit"), row(ts(12), fee=None), row(ts(13), result=None), row(ts(14), strategy="EVENT830"), row(ts(15), status="open")]
        text, c = X.extract({"slotOrders": rows}, 5)
        lines = text.strip().split(chr(10))[1:]
        self.assertEqual([l.split(",")[0] for l in lines], [ts(i) for i in range(1, 6)])   # the first 5 by ts
        self.assertEqual((c["rows_available"], c["excluded_exit"], c["excluded_unreadable"], c["open_unsettled"]), (10, 1, 1, 1))
    def test_fewer_rows_than_n_refuses(self):
        with self.assertRaises(ValueError): X.extract({"slotOrders": [row(ts(i)) for i in range(4)]}, 5)
    def test_no_generatedAt_and_stable_hash(self):
        a = X.extract({"generatedAt": "A", "slotOrders": [row(ts(i)) for i in range(5)]}, 5)[0]
        b = X.extract({"generatedAt": "B", "extra": 1, "slotOrders": [row(ts(i)) for i in range(5)] + [row(ts(9))]}, 5)[0]
        self.assertEqual(hashlib.sha256(a.encode()).hexdigest(), hashlib.sha256(b.encode()).hexdigest())
    def test_scorer_reads_only_the_extract(self):
        rows = [row(ts(i)) for i in range(66)] + [row(ts(i), result="no") for i in range(66, 100)]
        text, _ = X.extract({"slotOrders": rows}, 100)
        m = os.path.join(tempfile.mkdtemp(), "mk")
        r = P.run_extract(text, 100, m)
        self.assertEqual((r["read_point"], r["rows_used"], r["verdict"]), (100, 100, "PROVEN"))
        self.assertEqual((r["first_ts"], r["last_ts"]), (ts(0), ts(99)))
        self.assertEqual([w["rows"] for w in r["windows"]], [33, 33, 34])
        self.assertTrue(P.run_extract(text, 100, m)["verdict"].startswith("REFUSED"))   # read once
    def test_scorer_refuses_a_wrong_row_count_or_header(self):
        text, _ = X.extract({"slotOrders": [row(ts(i)) for i in range(100)]}, 100)
        m = os.path.join(tempfile.mkdtemp(), "mk")
        self.assertTrue(P.run_extract(text, 150, m)["verdict"].startswith("REFUSED"))      # extract has 100 rows, point 150
        self.assertTrue(P.run_extract(text.replace("ts,ticker", "xx,ticker"), 100, m)["verdict"].startswith("REFUSED"))
        self.assertEqual(os.listdir(m) if os.path.exists(m) else [], [])
if __name__ == "__main__": unittest.main()
