"""Invented rows only. Run: python3 -I kalshi-scalper/refine_tools/test_oicore_proven.py"""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oicore_proven as P
def row(i, side="yes", result="yes", fill=0.10, fee=0.004, count=10, status="filled", strategy="OICORE"):
    return {"strategy": strategy, "status": status, "ts": "2026-11-%02dT%02d:00:00Z" % (1 + i // 24, i % 24), "side": side, "result": result, "avgFill": fill, "avgFee": fee, "count": count}
class T(unittest.TestCase):
    def setUp(self): self.m = os.path.join(tempfile.mkdtemp(), "mk")
    def test_cash_hand_values(self):
        self.assertAlmostEqual(P.cash(row(0)), 10 * 0.9 - 0.04)                       # yes win at .10
        self.assertAlmostEqual(P.cash(row(0, result="no")), -(10 * 0.10) - 0.04)       # yes loss
        self.assertAlmostEqual(P.cash(row(0, side="no", result="no", fill=0.90)), 10 * 0.9 - 0.04)   # NO at yes-fill .90: paid .10
        self.assertAlmostEqual(P.cash(row(0, side="no", result="yes", fill=0.90)), -(10 * 0.10) - 0.04)
        self.assertIsNone(P.cash(row(0, fee=None)))
    def test_under_100_no_read(self):
        r = P.run({"slotOrders": [row(i) for i in range(99)]}, self.m)
        self.assertTrue(r["verdict"].startswith("NO READ")); self.assertEqual(os.listdir(self.m) if os.path.exists(self.m) else [], [])
    def test_exclusions_counted_and_split(self):
        rows = [row(i) for i in range(100)] + [row(100, result="exit"), row(101, fee=None), row(102, strategy="EVENT830"), row(103, result=None)]
        r = P.run({"slotOrders": rows}, self.m)
        self.assertEqual((r["n"], r["excluded_exit"], r["excluded_unreadable"], r["open_unsettled"]), (100, 1, 1, 1))
        self.assertEqual([w["rows"] for w in r["windows"]], [33, 33, 34])              # rows[i*n//3:(i+1)*n//3]
    def test_two_of_three(self):
        # windows of 33/33/34: make windows 1 and 2 all wins (PF inf), window 3 all losses (PF 0): 2 of 3 met = PROVEN
        rows = [row(i) for i in range(66)] + [row(i, result="no") for i in range(66, 100)]
        self.assertEqual(P.run({"slotOrders": rows}, self.m)["verdict"], "PROVEN")
        for f in os.listdir(self.m): os.remove(os.path.join(self.m, f))
        rows = [row(i) for i in range(33)] + [row(i, result="no") for i in range(33, 100)]
        self.assertEqual(P.run({"slotOrders": rows}, self.m)["verdict"], "NOT YET")      # 1 of 3
    def test_pf_exactly_at_the_bar_uses_tolerance(self):
        self.assertTrue(1.3 - 1e-12 >= P.BAR - P.TOL)
        self.assertFalse(1.3 - 1e-6 >= P.BAR - P.TOL)
    def test_second_read_refused(self):
        rows = [row(i) for i in range(100)]
        P.run({"slotOrders": rows}, self.m)
        self.assertTrue(P.run({"slotOrders": rows}, self.m)["verdict"].startswith("REFUSED"))
    def test_read_points_100_then_150(self):
        bad = [row(i, result="no") for i in range(100)]                    # all losses: NOT YET
        self.assertEqual(P.run({"slotOrders": bad}, self.m)["verdict"], "NOT YET")
        r = P.run({"slotOrders": bad + [row(i, result="no") for i in range(100, 120)]}, self.m)
        self.assertTrue(r["verdict"].startswith("NO READ"))                 # 120 rows: the 150 read waits
        r = P.run({"slotOrders": bad + [row(i, result="no") for i in range(100, 150)]}, self.m)
        self.assertEqual((r["read_point"], r["verdict"]), (150, "NOT YET"))
        self.assertTrue(P.run({"slotOrders": bad + [row(i) for i in range(100, 160)]}, self.m)["verdict"].startswith("REFUSED"))
        self.assertEqual(sorted(os.listdir(self.m)), ["OICORE_PROVEN_READ_100_DONE", "OICORE_PROVEN_READ_150_DONE"])
    def test_proven_at_100_means_no_150_read(self):
        good = [row(i) for i in range(100)]
        self.assertEqual(P.run({"slotOrders": good}, self.m)["verdict"], "PROVEN")
        self.assertTrue(P.run({"slotOrders": good + [row(i) for i in range(100, 160)]}, self.m)["verdict"].startswith("REFUSED"))
    def test_each_read_point_uses_exactly_the_first_n_rows(self):
        # 130 rows: the first 100 (by ts) are all losses, the last 30 are wins; the 100 read must use only the first 100 (windows 33/33/34, all PF 0)
        rows = [row(i, result="no") for i in range(100)] + [row(i, result="yes") for i in range(100, 130)]
        r = P.run({"slotOrders": rows}, self.m)
        self.assertEqual((r["read_point"], r["n"], r["rows_used"]), (100, 130, 100))
        self.assertEqual([w["rows"] for w in r["windows"]], [33, 33, 34])
        self.assertEqual([w["pf"] for w in r["windows"]], [0.0, 0.0, 0.0]); self.assertEqual(r["verdict"], "NOT YET")
        # 170 rows later: the 150 read uses exactly the first 150 (windows 50/50/50), the last 20 never enter
        rows2 = rows + [row(i, result="no") for i in range(130, 150)] + [row(i, result="yes") for i in range(150, 170)]
        r = P.run({"slotOrders": rows2}, self.m)
        self.assertEqual((r["read_point"], r["rows_used"]), (150, 150))
        self.assertEqual([w["rows"] for w in r["windows"]], [50, 50, 50])
    def test_fill_order_by_ts(self):
        rows = [row(i, result="no") for i in range(34)] + [row(i) for i in range(34, 100)]   # losses first, then wins, given out of order
        rows.reverse()
        r = P.run({"slotOrders": rows}, self.m)
        self.assertEqual(r["windows"][0]["pf"], 0.0)                                 # first third by ts is all losses
if __name__ == "__main__": unittest.main()
