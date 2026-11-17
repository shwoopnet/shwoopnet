import math, unittest
import cheapflip_second as c

C = 1_000_000
def bids(*lv): return [(p, s) for p, s in lv] + [(None, None)] * (5 - len(lv))
def poll(before, yes=None, no=None): return (int((C - before) * 1000), "M", C, bids(*(yes or [])), bids(*(no or [])))
def market(extra=()):
    ps = [poll(300, no=[(0.97, 7)]), poll(250, yes=[(0.05, 4)], no=[(0.90, 1)]), poll(200, yes=[(0.06, 4)], no=[(0.90, 1)]), poll(100, yes=[(0.09, 8)], no=[(0.90, 1)]), poll(10, yes=[(0.04, 2)], no=[(0.90, 1)]), poll(-5, yes=[(0.99, 9)], no=[(0.01, 9)])]
    return {"M": ("KXHYPE15M", C, sorted(list(ps) + list(extra), key=lambda p: p[0]))}

class T(unittest.TestCase):
    def run_case(self, result, extra=()):
        ents, cnt = c.collect(market(extra), {"M": result} if result else {}); return ents, cnt
    def test_hand_case(self):
        ents, cnt = self.run_case("yes"); self.assertEqual(cnt["polls_at_or_after_close"], 1)
        yes = [e for e in ents if e["side"] == "yes"]; self.assertEqual(sorted(e["band"] for e in yes), [3, 5, 10]); e = yes[0]; self.assertEqual((e["a"], e["ask_size"]), (30, 7))
        self.assertEqual((e["touches"][2][0], e["touches"][2][1], e["touches"][2][2]), (100000, 60, 4)); self.assertEqual((e["touches"][3][0], e["touches"][3][2]), (200000, 8)); self.assertIsNone(e["touches"][5])
        n = c.trade_net
        self.assertAlmostEqual(n(30, 10, e["touches"][2], "yes", "yes"), 0.03, 12); self.assertAlmostEqual(n(30, 10, e["touches"][3], "yes", "yes"), 0.31, 12)
        self.assertAlmostEqual(n(30, 20, e["touches"][2], "yes", "yes"), -0.17, 12); self.assertAlmostEqual(n(30, 20, e["touches"][3], "yes", "yes"), 0.11, 12)
        self.assertAlmostEqual(n(30, 10, None, "yes", "yes"), 9.57, 12); self.assertAlmostEqual(n(30, 10, None, "no", "yes"), -0.43, 12); self.assertAlmostEqual(n(30, 10, None, "void", "yes"), -0.03, 12)
        self.assertAlmostEqual(n(30, 20, None, "yes", "yes"), 9.46, 12); self.assertAlmostEqual(n(30, 20, None, "no", "yes"), -0.54, 12); self.assertAlmostEqual(n(30, 20, None, "void", "yes"), -0.04, 12)
        self.assertIsNone(n(30, 10, None, None, "yes")); self.assertAlmostEqual(n(30, 10, e["touches"][2], None, "yes"), 0.03, 12)         # a sale needs no result
        rows = c.table([x for x in ents if x["side"] == "yes"], cnt); cell = [r for r in rows if r[0] == 3 and r[1] == 2][0][2]["POOLED"]
        self.assertEqual((cell["n"], cell["reach_share"], cell["median_touch_s"], cell["bid_size_5_share_at_touch"], cell["ask_size_5_share_at_entry"]), (1, 1.0, 100.0, 0.0, 1.0)); self.assertEqual(cell["pf_h1"], math.inf); self.assertAlmostEqual(cell["net_per_trade_h2"], -0.17, 12)
        cell3 = [r for r in rows if r[0] == 3 and r[1] == 3][0][2]["POOLED"]; self.assertEqual((cell3["median_touch_s"], cell3["bid_size_5_share_at_touch"]), (200.0, 1.0))
        cell5 = [r for r in rows if r[0] == 3 and r[1] == 5][0][2]["POOLED"]; self.assertEqual(cell5["reach_share"], 0.0); self.assertAlmostEqual(cell5["net_per_trade_h1"], 9.57, 12)
    def test_120_inclusive(self):
        base = lambda before: {"M": ("KXHYPE15M", C, [poll(before, no=[(0.98, 5)])])}
        self.assertIsNotNone(c.find_entries(base(120)["M"][2], C, "yes", 3)); self.assertIsNone(c.find_entries(base(119.999)["M"][2], C, "yes", 3))
    def test_band_edges(self):
        ps = [poll(300, no=[(0.96, 5)])]                      # ask 4c: in the 5c and 10c bands only
        self.assertIsNone(c.find_entries(ps, C, "yes", 3)); self.assertEqual(c.find_entries(ps, C, "yes", 5)[1], 40)
        self.assertEqual(c.find_entries([poll(300, no=[(0.99, 5)])], C, "yes", 3)[1], 10)         # an ask of 1c enters
        self.assertIsNone(c.find_entries([poll(300, no=[(1.0, 5)])], C, "yes", 3))          # ask 0 is below the band
        self.assertIsNone(c.find_entries([poll(300, no=[(0.991, 5)])], C, "yes", 3))        # 0.9 c is below the 1c floor
        self.assertIsNone(c.find_entries([poll(300, no=[(0.966, 5)])], C, "yes", 3))        # opposite bid 0.966 is a 3.4c ask: not in the 3c band
        self.assertEqual(c.find_entries([poll(300, no=[(0.966, 5)])], C, "yes", 5)[1], 34)  # but in the 5c band, a = 34 mills
        self.assertEqual(c.find_entries([poll(300, no=[(0.970, 5)])], C, "yes", 3)[1], 30)  # 0.970 is exactly 3.0c: in
    def test_touch_equality_and_strict_before_close(self):
        ps = [poll(300, no=[(0.97, 7)]), poll(200, yes=[(0.06, 1)]), (int((C + 1) * 1000), "M", C, bids((0.50, 9)), bids())]
        self.assertEqual(c.find_touch(ps, C, "yes", 0, 30, 2)[1], 60)                         # exactly 2 x 3c touches
        self.assertIsNone(c.find_touch([ps[0], ps[2]], C, "yes", 0, 30, 2))                   # a poll after the close never touches
    def test_poll_exactly_at_close(self):
        ps = [poll(300, no=[(0.97, 7)]), (C * 1000, "M", C, bids((0.50, 9)), bids())]
        self.assertIsNone(c.find_touch(ps, C, "yes", 0, 30, 2)); ents, cnt = c.collect({"M": ("KXHYPE15M", C, ps)}, {"M": "yes"}); self.assertEqual(cnt["polls_at_or_after_close"], 1)
    def test_floor_and_cap(self):
        self.assertAlmostEqual(c.trade_net(10, 20, (0, 20, 9), "yes", "yes"), 10 * (0.010 - 0.030) - c.fee(30) - c.fee(10), 12)       # bid 2c - 2c = 0: floored at 1c
        self.assertAlmostEqual(c.trade_net(990, 20, None, "yes", "yes"), 10 * (1 - 0.99) - c.fee(990), 12)                      # entry capped at 99c
    def test_no_side_and_best_bid(self):
        pl = poll(300, yes=[(0.96, 5)], no=[(None, None), (0.20, 3), (0.30, None)])      # NO ask = 100 - best YES bid = 4c; best NO bid is 20c (30c has no size)
        self.assertEqual(c.side_view(pl, "no")[:2], (40, 5)); self.assertEqual(c.side_view(pl, "no")[2:], (200, 3)); self.assertEqual(c.side_view(pl, "yes")[:2], (800, 3))
    def test_no_result_counts(self):
        ents, cnt = c.collect(market(), {}); rows = c.table(ents, cnt)
        self.assertEqual(cnt["windows_without_result"], 1); self.assertEqual(cnt["no_result_by_series"], {"KXHYPE15M": 1})
        r = [r for r in rows if r[0] == 3 and r[1] == 5][0][2]["POOLED"]; self.assertEqual((r["trades_h1"], r["n_scored"]), (0, 0))                  # the hold without a result is dropped
        r2 = [r for r in rows if r[0] == 3 and r[1] == 2][0][2]["POOLED"]; self.assertEqual(r2["trades_h1"], 1)                # sold: counts
        self.assertGreater(cnt["held_entries_without_result"]["KXHYPE15M"], 0)
    def test_ms_integer_median(self):
        ps = [(1794000000013, "M", 1794001000, bids(), bids((0.97, 7))), (1794000042000, "M", 1794001000, bids((0.06, 9)), bids()), (1794000043013, "M", 1794001000, bids((0.06, 9)), bids())]
        ents, cnt = c.collect({"M": ("KXHYPE15M", 1794001000, ps)}, {"M": "yes"}); e = [x for x in ents if x["side"] == "yes" and x["band"] == 3][0]; self.assertEqual(e["touches"][2][0], 41987)
        e2 = dict(e); e2["touches"] = {2: (42000, 6, 9), 3: None, 5: None}; self.assertEqual(c.cell([e, e2], 2)["median_touch_s"], (41987 + 42000) / 2 / 1000)
    def test_sub_cent_target_and_fee(self):
        ps = [poll(300, no=[(0.966, 7)]), poll(200, yes=[(0.067, 4)]), poll(100, yes=[(0.068, 4)])]; i, a, _s = c.find_entries(ps, C, "yes", 5); self.assertEqual(a, 34)
        self.assertEqual(c.find_touch(ps, C, "yes", i, a, 2)[0], 2)                      # 2 x 34 = 68 mills: 0.067 does not touch, 0.068 does
        self.assertAlmostEqual(c.trade_net(34, 10, (0, 68, 4), "yes", "yes"), 10 * (0.058 - 0.044) - c.fee(44) - c.fee(58), 12)
        self.assertEqual(c.fee(34), 0.03)                                                # 0.07 x 10 x 0.034 x 0.966 x 100 = 2.299 -> 3
    def test_median_even(self):
        self.assertEqual(c.median([1, 2, 3, 10]), 2.5); self.assertEqual(c.median([5, 1, 3]), 3)
