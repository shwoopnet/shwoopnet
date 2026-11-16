#!/usr/bin/env python3
"""PERPFUNDCLK1 hand case (synthetic, no network). Print days 2026-11-09 (Mon) and 2026-11-10 (Tue), T = 21:00:00Z. Name KXNVDAPERP: previous rate (Nov 9) +0.0004 so the payer is the LONG
side; today's rate (Nov 10) -0.0002. Candles (bid, ask): T-60 min 100.00 / 100.02, T-5 min 99.48 / 99.50, T+1 min 99.60 / 99.62, T+31 min 99.90 / 99.92."""
import calendar, contextlib, csv, gzip, io, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpfundclk1 as F
import perpscalp2 as P

T = calendar.timegm((2026, 11, 10, 21, 0, 0))
T0 = calendar.timegm((2026, 11, 9, 21, 0, 0))


def write(root, sub, name, header, rows):
    os.makedirs(os.path.join(root, sub), exist_ok=True)
    with gzip.open(os.path.join(root, sub, name), "wt", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def fixture(names=("KXNVDAPERP",), rates=(0.0004, -0.0002), candles=True):
    root = tempfile.mkdtemp()
    iso = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))
    write(root, "funding", "2026-11-10.csv.gz", ["ticker", "funding_time", "funding_rate", "mark_price"],
          [[n, iso(tt), repr(r), "1"] for n in names for tt, r in ((T0, rates[0]), (T, rates[1]))])
    if candles:
        rows = []
        for n in names[:1]:
            for off, (b, a) in ((-3600, (100.00, 100.02)), (-1800, (99.9, 99.92)), (-300, (99.48, 99.50)), (60, (99.60, 99.62)), (31 * 60, (99.90, 99.92))):
                rows.append([n, T + off, repr(b), repr(a), "1"])
        write(root, "kalshi1m", "2026-11-10.csv.gz", ["ticker", "end_period_ts", "bid_close", "ask_close", "volume"], rows)
    return root


class Hand(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(F.N_CELLS, 10)                                     # A 4 + C 4 + B 2
        self.assertEqual(len(F.STOCKS), 9)

    def test_stage1_counts_from_funding_only(self):
        fu, el, cnt, med = F.stage1(fixture())
        self.assertEqual(cnt["prints_at_2100z"], 2)
        self.assertEqual(cnt["with_previous"], 1)
        self.assertEqual(cnt["nonzero_previous"], 1)
        self.assertEqual(el["KXNVDAPERP"], [(T, 0.0004)])
        self.assertEqual(cnt["print_days"], 2)
        self.assertAlmostEqual(cnt["trades_a_day_pooled"], 0.5)           # 1 eligible name-day over 2 print days: under 3 a day
        self.assertTrue(cnt["parked"])
        self.assertEqual(med, 0.0004)

    def test_parked_opens_no_candle_file(self):
        out = F.run(fixture())
        self.assertIn("PARKED", out["verdict"])
        self.assertNotIn("cells", out)

    def test_arm_a_short_hand_value(self):
        c, fu = P.load(fixture())
        n = c["KXNVDAPERP"]
        h = 0.0002
        tr = F.trade(n, fu["KXNVDAPERP"], -1, T - 3600, T - 300, h)
        en, ex = 100.00 * (1 - h), 99.50 * (1 + h)                          # short: entry at the bid, exit at the ask
        self.assertAlmostEqual(tr["net"], (en - ex) / en - 0.0024, 12)
        self.assertFalse(tr["crossed"])                                     # exit 5 minutes before the print: no funding

    def test_arm_b_long_hand_value(self):
        c, fu = P.load(fixture())
        n = c["KXNVDAPERP"]
        h = 0.0002
        tr = F.trade(n, fu["KXNVDAPERP"], 1, T + 60, T + 31 * 60, h)
        en, ex = 99.62 * (1 + h), 99.90 * (1 - h)
        self.assertAlmostEqual(tr["net"], (ex - en) / en - 0.0024, 12)
        self.assertFalse(tr["crossed"])                                     # entry after the print: the print is not inside the hold

    def test_arm_c_books_the_print(self):
        c, fu = P.load(fixture())
        n = c["KXNVDAPERP"]
        h = 0.0002
        tr = F.trade(n, fu["KXNVDAPERP"], -1, T - 3600, T + 31 * 60, h)
        en, ex = 100.00 * (1 - h), 99.92 * (1 + h)
        # a short pays a NEGATIVE rate: net = gross - 0.0024 - side x ... : funding_of = -side x rate = -(-1) x (-0.0002) = -0.0002
        self.assertAlmostEqual(tr["net"], (en - ex) / en - 0.0024 - 0.0002, 12)
        self.assertTrue(tr["crossed"])

    def test_exit_gap(self):
        c, fu = P.load(fixture())
        n = dict(c["KXNVDAPERP"])
        del n[T - 300]                                                                  # the planned exit candle is gone
        n[T - 480] = (99.7, 99.72, 1.0)                                                 # 3 minutes before the plan: not within 2 minutes
        self.assertIsNone(F.trade(n, fu["KXNVDAPERP"], -1, T - 3600, T - 300, 0.0))     # dropped, never bridged
        n[T - 420] = (99.6, 99.62, 1.0)                                                 # 2 minutes before the plan: used
        self.assertEqual(F.trade(n, fu["KXNVDAPERP"], -1, T - 3600, T - 300, 0.0)["x"], T - 420)
        n[T - 360] = (99.5, 99.52, 1.0)                                                 # 1 minute before the plan: preferred over the 2 minute one
        self.assertEqual(F.trade(n, fu["KXNVDAPERP"], -1, T - 3600, T - 300, 0.0)["x"], T - 360)

    def test_full_run_not_parked_with_nine_names(self):
        names = F.STOCKS
        root = fixture(names=names)
        out = F.run(root)
        self.assertNotIn("verdict", out)                                    # 9 eligible name-days over 2 print days = 4.5 a day
        self.assertEqual(len(out["cells"]), 10)
        self.assertEqual(out["m_total"], 6290670)
        self.assertEqual(out["stage1"]["eligible_name_days"], 9)
        # only KXNVDAPERP has candles: one trade per cell in A, C, B with the nz threshold; the median threshold keeps rate 0.0004 >= median 0.0004 too
        a = [r for r in out["cells"] if r["cell"] == ("A", 60, "nz")][0]
        self.assertEqual(a["TT"]["n"], 1)

    def test_header_first(self):
        import perpfundclk1_run as R
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            R.main(fixture(), 6290660)
        L = buf.getvalue().split("\n")
        h = json.loads(L[0])
        self.assertEqual((h["m_carried"], h["m_new"], h["m_total"]), (6290660, 10, 6290670))
        self.assertIn("stage1", json.loads(L[1]))


if __name__ == "__main__":
    unittest.main()
