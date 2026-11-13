"""Invented rows only. Run: python3 -I kalshi-scalper/refine_tools/test_oicore_proven.py"""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oicore_proven as P
def row(i, side="yes", result="yes", fill=0.10, fee=0.004, count=10, status="filled", strategy="OICORE"):
    return {"strategy": strategy, "status": status, "ts": "2026-11-%02dT%02d:00:00Z" % (1 + i // 24, i % 24), "side": side, "result": result, "avgFill": fill, "avgFee": fee, "count": count}
class T(unittest.TestCase):
    def setUp(self): self.m = os.path.join(tempfile.mkdtemp(), "m")
    def test_cash_hand_values(self):
        self.assertAlmostEqual(P.cash(row(0)), 10 * 0.9 - 0.04)                       # yes win at .10
        self.assertAlmostEqual(P.cash(row(0, result="no")), -(10 * 0.10) - 0.04)       # yes loss
        self.assertAlmostEqual(P.cash(row(0, side="no", result="no", fill=0.90)), 10 * 0.9 - 0.04)   # NO at yes-fill .90: paid .10
        self.assertAlmostEqual(P.cash(row(0, side="no", result="yes", fill=0.90)), -(10 * 0.10) - 0.04)
        self.assertIsNone(P.cash(row(0, fee=None)))
    def test_under_100_no_read(self):
        r = P.run({"slotOrders": [row(i) for i in range(99)]}, self.m)
        self.assertTrue(r["verdict"].startswith("NO READ")); self.assertFalse(os.path.exists(self.m))
    def test_exclusions_counted_and_split(self):
        rows = [row(i) for i in range(100)] + [row(100, result="exit"), row(101, fee=None), row(102, strategy="EVENT830"), row(103, status="open")]
        r = P.run({"slotOrders": rows}, self.m)
        self.assertEqual((r["n"], r["excluded_exit"], r["excluded_unreadable"]), (100, 1, 1))
        self.assertEqual([w["rows"] for w in r["windows"]], [33, 33, 34])              # rows[i*n//3:(i+1)*n//3]
    def test_two_of_three(self):
        # windows of 33/33/34: make windows 1 and 2 all wins (PF inf), window 3 all losses (PF 0): 2 of 3 met = PROVEN
        rows = [row(i) for i in range(66)] + [row(i, result="no") for i in range(66, 100)]
        self.assertEqual(P.run({"slotOrders": rows}, self.m)["verdict"], "PROVEN")
        os.remove(self.m)
        rows = [row(i) for i in range(33)] + [row(i, result="no") for i in range(33, 100)]
        self.assertEqual(P.run({"slotOrders": rows}, self.m)["verdict"], "NOT YET")      # 1 of 3
    def test_pf_exactly_at_the_bar_uses_tolerance(self):
        self.assertTrue(1.3 - 1e-12 >= P.BAR - P.TOL)
        self.assertFalse(1.3 - 1e-6 >= P.BAR - P.TOL)
    def test_second_read_refused(self):
        rows = [row(i) for i in range(100)]
        P.run({"slotOrders": rows}, self.m)
        self.assertTrue(P.run({"slotOrders": rows}, self.m)["verdict"].startswith("REFUSED"))
    def test_fill_order_by_ts(self):
        rows = [row(i, result="no") for i in range(34)] + [row(i) for i in range(34, 100)]   # losses first, then wins, given out of order
        rows.reverse()
        r = P.run({"slotOrders": rows}, self.m)
        self.assertEqual(r["windows"][0]["pf"], 0.0)                                 # first third by ts is all losses
if __name__ == "__main__": unittest.main()
