import unittest, math
import oicore_all_second as O
C = 1_699_920_000; D = 86400
def cd(tk, close, oi_lvl, oi_sig, sig=(.5, .6), fill=(.5, .6), lvl=True):
    c = {}
    if lvl: c[(tk, close - 360)] = (None, None, oi_lvl)
    c[(tk, close - 180)] = (sig[0], sig[1], oi_sig); c[(tk, close - 120)] = (fill[0], fill[1], oi_sig)
    return c
def build():
    M = []; K = {}
    for i in range(1, 11):
        t = "A%d" % i; close = C + i * 1000; M.append((t, close, "yes", "S")); K.update(cd(t, close, 100, 100 + i))
    close = C + 11000; M.append(("A11", close, "yes", "S")); K.update(cd("A11", close, 100, 150, lvl=False))
    v0 = C + D; V = [("V1", 9, (.28, .30), (.30, .32), "yes"), ("V2", 10, (.68, .70), (.66, .68), "yes"), ("V3", 8, (.28, .30), (.30, .32), "yes"), ("V4", 12, (.03, .04), (.03, .04), "yes"), ("V5", 11, (.28, .30), (.30, .32), "yes"), ("V6", 9, (.48, .50), (.48, .50), "no")]
    for j, (t, r, sg, fl, res) in enumerate(V):
        close = v0 + 3600 * (j + 1) + (D if j >= 3 else 0); M.append((t, close, res, "S")); K.update(cd(t, close, 100, 100 + r, sg, fl, lvl=(t != "V5")))
    close = v0 + D + 3600 * 7; M.append(("V7", close, "yes", "S")); K.update(cd("V7", close, 100, 120, (.18, .20), (.20, .22)))
    return M, K, {"S": O.day(C)}
class T(unittest.TestCase):
    def test_hand_case(self):
        M, K, sp = build(); r = O.run(M, K, sp, floor_n=10)["S"]
        self.assertEqual(r["T"], 9); self.assertEqual(r["search_rises"], 10); self.assertEqual(r["no_signal"], {"band": 1, "no_candle": 1})
        v = r["windows"]["VALIDATE"]; self.assertEqual((v["n"], v["wins"], v["days"], v["signals_a_day"]), (4, 2, 2, 2.0))
        self.assertAlmostEqual(v["pf_1c"], 1.453 / .874, 12); self.assertAlmostEqual(v["pf_2c"], 1.431 / .894, 12); self.assertAlmostEqual(v["net_cents_1c"], .579 / 4 * 100, 9); self.assertAlmostEqual(v["net_cents_2c"], .537 / 4 * 100, 9)
    def test_floor_and_pooled(self):
        M, K, sp = build(); r = O.run(M, K, sp)             # real floor 20: 10 rises is too few
        self.assertIsNone(r["S"]["T"]); self.assertEqual(r["S"]["windows"]["VALIDATE"]["n"], 0)
    def test_pooled_equals_single(self):
        M, K, sp = build(); r = O.run(M, K, sp, floor_n=10); self.assertEqual(r["ALL"]["windows"], r["S"]["windows"])
    def test_two_series_own_split(self):
        M, K, sp = build(); M2 = [(t + "b", c + 5, res, "Z") for t, c, res, _ in M]; K2 = {(t + "b", e + 5): v for (t, e), v in K.items()}
        r = O.run(M + M2, {**K, **K2}, {"S": sp["S"], "Z": sp["S"]}, floor_n=10); self.assertEqual(r["ALL"]["windows"]["VALIDATE"]["n"], 8); self.assertEqual(r["Z"]["T"], 9)
    def test_cap_099(self): self.assertAlmostEqual(O.net("yes", .985, "yes", .02), 1 - .99 - O.fee_order(.99) / 10, 12)
    def test_nearest_rank(self):
        self.assertEqual(O.nearest_rank(list(range(1, 11)), .9), 9); self.assertEqual(O.nearest_rank(list(range(1, 21)), .9), 18); self.assertEqual(O.nearest_rank([5], .9), 5)
    def test_unreadable_oi(self):
        K = {("X", 1000 - 180): (.5, .6, float("nan")), ("X", 1000 - 360): (.5, .6, 1)}; self.assertIsNone(O.rise("X", 1000, K)); K[("X", 820)] = (.5, .6, True); self.assertIsNone(O.rise("X", 1000, K))
    def test_price_edges(self):
        for p, ok in ((.08, True), (.50, True), (.0799, False), (.5001, False)):
            K = {("X", 820): (p - .01, p, 1)}; self.assertEqual(O.entry("X", 1000, K)[0] == "ok", ok, p)
    def test_not_two_sided(self):
        K = {("X", 820): (.3, .3, 1)}; self.assertEqual(O.entry("X", 1000, K), ("no", "quote_signal"))
if __name__ == "__main__": unittest.main()
