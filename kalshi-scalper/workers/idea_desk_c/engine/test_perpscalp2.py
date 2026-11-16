#!/usr/bin/env python3
"""PERPSCALP2 hand case (synthetic, no network). Name KXNVDAPERP, Tuesday 2026-11-10, candle k ends at 15:00Z + k minutes (10:00 ET + k minutes, EST).
mid alternates 100.0 (even k) and 100.1 (odd k) for k = 0..59, holds 100.1 for k = 60..63, k = 64 (11:04 ET) is the signal candle: mid 100.2, volume 20 (others 1);
k = 65..75 mid 100.2. bid = mid - 0.005, ask = mid + 0.005. Desk A's PERPSCALP1 numbers for the same shape: sigma1 = a x sqrt(60/59), a = ln(100.1/100)."""
import csv, gzip, math, os, sys, tempfile, unittest, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpscalp2 as P

T0 = calendar.timegm((2026, 11, 10, 15, 0, 0))
A = math.log(100.1 / 100.0)


def mids(extra=None):
    m = {}
    for k in range(0, 60):
        m[k] = 100.0 if k % 2 == 0 else 100.1
    for k in range(60, 64):
        m[k] = 100.1
    for k in range(64, 76):
        m[k] = 100.2
    return m


def fixture(dip=False, fund=None):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "kalshi1m"))
    os.makedirs(os.path.join(root, "funding"))
    with gzip.open(os.path.join(root, "kalshi1m", "2026-11-10.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "end_period_ts", "bid_close", "ask_close", "volume"])
        for k, mm in mids().items():
            b, a = mm - 0.005, mm + 0.005
            if dip and k == 66:
                b, a = 100.17, 100.18                               # the ask comes down through the resting bid 100.195 by more than the tick 0.01
            w.writerow(["KXNVDAPERP", T0 + 60 * k, "%.4f" % b, "%.4f" % a, 20 if k == 64 else 1])
    with gzip.open(os.path.join(root, "funding", "2026-11-10.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "funding_time", "funding_rate", "mark_price"])
        if fund is not None:
            w.writerow(["KXNVDAPERP", fund[0], fund[1], "1"])
    return root


class Clock(unittest.TestCase):
    def test_edt_and_est_days(self):
        d1 = P.et_min(calendar.timegm((2026, 10, 20, 13, 35, 0)))                  # EDT: 09:35 ET = 13:35Z
        d2 = P.et_min(calendar.timegm((2026, 11, 10, 14, 35, 0)))                  # EST: 09:35 ET = 14:35Z
        self.assertEqual((d1[1], d2[1]), (9 * 60 + 35, 9 * 60 + 35))
        self.assertEqual(P.et_min(calendar.timegm((2026, 10, 20, 19, 45, 0)))[1], 15 * 60 + 45)   # EDT: 15:45 ET = 19:45Z

    def test_holidays_and_early_close(self):
        import datetime
        self.assertIsNone(P.sess_end(datetime.date(2026, 11, 26)))
        self.assertIsNone(P.sess_end(datetime.date(2026, 12, 25)))
        self.assertEqual(P.sess_end(datetime.date(2026, 11, 27)), 12 * 60 + 45)
        self.assertEqual(P.sess_end(datetime.date(2026, 12, 24)), 12 * 60 + 45)
        self.assertEqual(P.sess_end(datetime.date(2026, 11, 10)), 15 * 60 + 45)

    def test_h16_rows_dropped_and_counted(self):
        root = fixture()
        with gzip.open(os.path.join(root, "kalshi1m", "2026-12-22.csv.gz"), "wt", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ticker", "end_period_ts", "bid_close", "ask_close", "volume"])
            w.writerow(["KXNVDAPERP", P.H16_START, "100.0", "100.1", "1"])
        dropped = {}
        c, fu = P.load(root, 1797897700, [], dropped)                              # an end epoch past H16 is cut to H16 - 1
        self.assertEqual(dropped["h16_rows"], 1)
        self.assertNotIn(P.H16_START, c["KXNVDAPERP"])


class Hand(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(P.N_CELLS, 168)
        self.assertEqual(len(P.EXITS), 6)
        self.assertEqual(len(P.NAMES), 14)
        self.assertEqual(P.LMAX["KXGOLDPERP"], 40.0)

    def test_signal_and_sigma(self):
        c, fu = P.load(fixture())
        t = T0 + 60 * 64
        s1 = P.sigma1(c["KXNVDAPERP"], t)
        self.assertAlmostEqual(s1, A * math.sqrt(60 / 59), 9)             # 0.00100794
        self.assertEqual(P.signal_times(c["KXNVDAPERP"], ("E6", "spike", 5), None), [(t, 1)])
        self.assertEqual(P.signal_times(c["KXNVDAPERP"], ("E7", "spike", 10), None), [(t, 1)])   # 20 >= 10 x 1
        self.assertEqual(P.signal_times(c["KXNVDAPERP"], ("E6", "spike", 25), None), [])         # 20 < 25 x 1: no signal

    def test_taker_trade(self):
        c, fu = P.load(fixture())
        n = c["KXNVDAPERP"]
        t = T0 + 60 * 64
        U = P.sigma1(n, t) * math.sqrt(10)
        self.assertAlmostEqual(U, 0.0031873, 6)
        h = 0.0002
        tr = P.build_trade(n, fu["KXNVDAPERP"], P.tick_of(n), t, 1, U, 100.2, 1.0, 1.0, 600, "TT", 0, h)
        # long: entry at candle 65 ask 100.205 x 1.0002 = 100.225041; no target (100.5194) or stop (99.8806) is met; time exit at candle 75 (600 s after 65):
        # bid 100.195 x 0.9998 = 100.174961; gross = 100.174961 / 100.225041 - 1; net = gross - 0.0012 - 0.0012 (no funding print)
        want = (100.195 * (1 - h)) / (100.205 * (1 + h)) - 1 - 0.0024
        self.assertAlmostEqual(tr["net"], want, 12)
        self.assertEqual((tr["e"], tr["x"]), (T0 + 60 * 65, T0 + 60 * 75))
        self.assertFalse(tr["crossed"])

    def test_target_hit(self):
        c, fu = P.load(fixture())
        n = c["KXNVDAPERP"]
        t = T0 + 60 * 64
        # a 0.0001 U makes the target 100.2 x (1 + 0.0001 x ...) tiny: candle 66 bid 100.195 is below it; use a negative-sized stop: stop above bid -> stop hit at candle 66
        tr = P.build_trade(n, fu["KXNVDAPERP"], P.tick_of(n), t, 1, 1e-6, 100.2, 1.0, 1.0, 600, "TT", 0, 0.0)
        self.assertEqual(tr["x"], T0 + 60 * 66)                              # stop = 100.2 x (1 - 1e-6) = 100.19980 > bid 100.195: stopped at the first later candle
        self.assertAlmostEqual(tr["net"], 100.195 / 100.205 - 1 - 0.0024, 12)

    def test_funding(self):
        fund = ("2026-11-10T16:10:00Z", 0.001)                                # between candle 65 (16:05Z) and 75 (16:15Z): a long pays 0.001
        c, fu = P.load(fixture(fund=fund))
        n = c["KXNVDAPERP"]
        t = T0 + 60 * 64
        tr = P.build_trade(n, fu["KXNVDAPERP"], P.tick_of(n), t, 1, 0.0031873, 100.2, 1.0, 1.0, 600, "TT", 0, 0.0)
        self.assertTrue(tr["crossed"])
        self.assertAlmostEqual(tr["net"], 100.195 / 100.205 - 1 - 0.0024 - 0.001, 12)

    def test_maker_fill(self):
        c, fu = P.load(fixture())
        n = c["KXNVDAPERP"]
        t = T0 + 60 * 64
        self.assertAlmostEqual(P.tick_of(n), 0.01, 9)
        self.assertIsNone(P.build_trade(n, fu["KXNVDAPERP"], 0.01, t, 1, 0.0031873, 100.2, 1.0, 1.0, 600, "MT", 5, 0.0))   # the ask never comes down to 100.185
        c, fu = P.load(fixture(dip=True))
        n = c["KXNVDAPERP"]
        tr = P.build_trade(n, fu["KXNVDAPERP"], 0.01, t, 1, 0.0031873, 100.2, 1.0, 1.0, 600, "MT", 5, 0.0)
        # the limit is candle 64's bid 100.195; candle 66 ask 100.18 <= 100.195 - 0.01 fills it there (N = 5 covers candles 65..69), entry at the limit, maker fee 5 bp in
        # exit at the time stop: bid at candle 76? none, so the last candle at or before k66 + 600 s = k76 is k75 bid 100.195: gross 0, net = -0.0005 - 0.0012
        self.assertEqual(tr["e"], T0 + 60 * 66)
        self.assertAlmostEqual(tr["net"], 100.195 / 100.195 - 1 - 0.0005 - 0.0012, 12)

    def test_run_header(self):
        out = P.run(fixture(), 6290660)
        self.assertEqual((out["m_carried"], out["m_new"], out["m_total"]), (6290660, 168, 6290828))
        self.assertEqual(len(out["cells"]), 168)
        self.assertIn("KXNVDAPERP", out["counts"]["dropped_short_history"])       # 76 regular-hours candles: under 600
        self.assertEqual(out["counts"]["valid_regular_candles"]["KXNVDAPERP"], 76)
        self.assertEqual(out["counts"]["files_read"], 2)
        self.assertEqual(len(out["counts"]["manifest_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
