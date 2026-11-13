"""Tests on invented rows only (no recorded data). Run: python3 -I kalshi-scalper/refine_tools/test_v1_resting_score.py"""
import csv, gzip, io, os, sys, tempfile, unittest, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v1_resting_score as S

BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
CT = calendar.timegm((2026, 11, 3, 12, 0, 0))  # inside the V1 dev block (invented market)

def brow(tk, t_ms, yb, nb):
    r = {c: "" for c in BOOK_COLS}
    r.update(t_send_ms=t_ms, t_recv_ms=t_ms, ticker=tk, series="KXBTC15M", close_time="x", yes_bid_px_1=yb, yes_bid_sz_1=10, no_bid_px_1=nb, no_bid_sz_1=10)
    return r

def write_gz(path, cols, rows):
    s = io.StringIO(); w = csv.DictWriter(s, fieldnames=cols); w.writeheader(); [w.writerow(r) for r in rows]
    with gzip.open(path, "wt") as f: f.write(s.getvalue())

def iso(ms): return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms // 1000)) + ".%03dZ" % (ms % 1000)

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.root = os.path.join(self.d, "r", "2026-11-03", "1200"); os.makedirs(self.root); self.out = os.path.join(self.d, "out")
        S.MARKER_DIR = os.path.join(self.d, "markers")
        self.hl = os.path.join(self.d, "heldout.md"); open(self.hl, "w").write("| Run folder | why |\n|---|---|\n| `kalshi-pull-data/2026-11-01T0000Z_1` | x |\n")
        S.HELDOUT_LIST = self.hl
        S.DEPTH1_RECORD = os.path.join(self.d, "DEPTH1_READ_MARKER.txt"); S.NC15DEPTH1_RECORD = os.path.join(self.d, "NC15.txt")
    def put_depth1(self, text="DEPTH1 READ MADE: 2026-11-14\n"): open(S.DEPTH1_RECORD, "w").write(text)
    def put_nc15(self, text=None): open(S.NC15DEPTH1_RECORD, "w").write(text if text is not None else "NC15DEPTH1 SCORER HASH: %s 2e595c54 CLEAN by Auditor B x\n" % S.NC15DEPTH1_FINAL_SHA256)
    def mk(self, books, trades, result="no"):
        write_gz(os.path.join(self.root, "book.csv.gz"), BOOK_COLS, books)
        write_gz(os.path.join(self.root, "trades.csv.gz"), ["ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side"], trades)
        write_gz(os.path.join(self.root, "coverage.csv.gz"), ["ticker", "result"], [{"ticker": "T1", "result": result}])
        sig = os.path.join(self.d, "sig.csv"); open(sig, "w").write("ticker,close_ts\nT1,%d\n" % CT)
        return sig
    def window(self, books, trades, result="no"):
        sig = self.mk(books, trades, result)
        book, trd, cov = S.load_run_folders(os.path.join(self.d, "r"))
        return S.one_window("V1", "T1", CT, book, trd, cov)
    def base(self):
        t0 = (CT - 178) * 1000 + 500
        # YES bid .10 -> NO ask .90 ; NO bid .85 -> YES ask .15: cheaper side YES at ask .15, band ok; our bid .10
        return t0, [brow("T1", t0, 0.10, 0.85)]
    def test_signal_and_no_fill_without_trade(self):
        t0, b = self.base()
        w = self.window(b + [brow("T1", t0 + 5000, 0.10, 0.85)], [])
        self.assertEqual((w["status"], w["side"], round(w["p_ask"], 2), round(w["p_bid"], 2), w["filled"]), ("signal", "yes", 0.15, 0.10, False))
    def test_fill_by_trade_strictly_through(self):
        t0, b = self.base()
        w = self.window(b, [{"ticker": "T1", "created_time": iso(t0 + 3000), "yes_price_dollars": 0.09, "count_fp": 5, "taker_outcome_side": "no"}])
        self.assertTrue(w["filled"])
    def test_touch_does_not_fill(self):
        t0, b = self.base()
        w = self.window(b, [{"ticker": "T1", "created_time": iso(t0 + 3000), "yes_price_dollars": 0.10, "count_fp": 5, "taker_outcome_side": "no"}])
        self.assertFalse(w["filled"])
    def test_fill_by_crossed_ask(self):
        t0, b = self.base()
        w = self.window(b + [brow("T1", t0 + 4000, 0.05, 0.90)], [])   # YES ask = 1 - .90 = .10 <= our .10
        self.assertTrue(w["filled"])
    def test_trade_after_cancel_does_not_fill(self):
        t0, b = self.base()
        late = (CT - 119) * 1000
        w = self.window(b + [brow("T1", (CT - 120) * 1000 + 100, 0.10, 0.85)], [{"ticker": "T1", "created_time": iso(late), "yes_price_dollars": 0.05, "count_fp": 5, "taker_outcome_side": "no"}])
        self.assertFalse(w["filled"])
    def test_no_bid_no_order(self):
        t0 = (CT - 178) * 1000 + 500
        w = self.window([brow("T1", t0, "", 0.85)], [])
        self.assertTrue(w.get("no_order"))
    def test_out_of_band(self):
        t0 = (CT - 178) * 1000 + 500
        w = self.window([brow("T1", t0, 0.50, 0.40)], [])  # YES ask .60, NO ask .50 -> NO side at .50 in band; make both out of band
        self.assertEqual(w["status"], "signal")
        w = self.window([brow("T1", t0, 0.02, 0.97)], [])  # YES ask .03: below .05
        self.assertEqual(w["status"], "out_of_band")
    def test_dev_refused_without_marker_and_read_once(self):
        t0, b = self.base(); sig = self.mk(b, [])
        args = ["--version", "V1", "--block", "dev", "--book-root", os.path.join(self.d, "r"), "--signals", sig, "--out", self.out]
        self.assertEqual(S.main(args), 2)
        self.put_depth1()
        self.assertEqual(S.main(args), 0)
        self.assertEqual(S.main(args), 2)
    def test_depth1_marker_content_checked(self):
        t0, b = self.base(); sig = self.mk(b, [])
        args = ["--version", "V1", "--block", "dev", "--book-root", os.path.join(self.d, "r"), "--signals", sig, "--out", self.out]
        self.put_depth1("anything\n")
        self.assertEqual(S.main(args), 2)
    def test_second_run_with_new_out_refused(self):
        t0, b = self.base(); sig = self.mk(b, [])
        self.put_depth1()
        args = ["--version", "V1", "--block", "dev", "--book-root", os.path.join(self.d, "r"), "--signals", sig]
        self.assertEqual(S.main(args + ["--out", self.out]), 0)
        self.assertEqual(S.main(args + ["--out", os.path.join(self.d, "out2")]), 2)
    def test_no_command_line_override_of_the_clock_or_records(self):
        for opt in ("--now", "--heldout-list", "--depth1-recorded", "--nc15depth1-hash"):
            with self.assertRaises(SystemExit):
                S.main(["--version", "V1", "--block", "forward", "--book-root", "x", "--signals", "y", "--out", "z", opt, "q"])
    def test_v2_early_read_and_record_required(self):
        t0, b = self.base(); sig = self.mk(b, [])
        args = ["--version", "V2", "--block", "dev", "--book-root", os.path.join(self.d, "r"), "--signals", sig, "--out", self.out]
        self.put_nc15()
        self.assertEqual(S.main(args, now="2026-12-04T12:00:00Z"), 2)   # block not closed
        os.remove(S.NC15DEPTH1_RECORD)
        self.assertEqual(S.main(args, now="2026-12-06T00:00:00Z"), 2)   # no record
        self.put_nc15("x\n")
        self.assertEqual(S.main(args, now="2026-12-06T00:00:00Z"), 2)   # wrong content
        self.put_nc15("NC15DEPTH1 SCORER HASH: " + "0" * 64 + " c CLEAN\n")
        self.assertEqual(S.main(args, now="2026-12-06T00:00:00Z"), 2)   # not the final hash
        self.put_nc15()
        self.assertEqual(S.main(args, now="2026-12-06T00:00:00Z"), 0)
    def test_heldout_run_refused(self):
        t0, b = self.base(); sig = self.mk(b, [])
        bad = os.path.join(self.d, "kalshi-pull-data", "2026-11-01T0000Z_1"); os.makedirs(bad)
        self.put_depth1()
        self.assertEqual(S.main(["--version", "V1", "--block", "dev", "--book-root", bad, "--signals", sig, "--out", self.out]), 2)
        os.remove(self.hl)   # unreadable list refuses everything
        self.assertEqual(S.main(["--version", "V1", "--block", "dev", "--book-root", os.path.join(self.d, "r"), "--signals", sig, "--out", self.out]), 2)
    def test_fraction_parsed(self):
        self.assertEqual(S.created_ms("2026-11-03T11:57:02.5Z") - S.created_ms("2026-11-03T11:57:02Z"), 500)
        self.assertEqual(S.created_ms("2026-11-03T11:57:02.123456Z") - S.created_ms("2026-11-03T11:57:02Z"), 123)
    def test_coverage_prefers_result_row(self):
        t0, b = self.base(); self.mk(b, [])
        write_gz(os.path.join(self.root, "coverage.csv.gz"), ["ticker", "result"], [{"ticker": "T1", "result": "no"}, {"ticker": "T1", "result": ""}])
        _, _, cov = S.load_run_folders(os.path.join(self.d, "r"))
        self.assertEqual(cov["T1"]["result"], "no")
    def _sig(self, p_ask, p_bid, win, filled):
        return {"p_ask": p_ask, "p_bid": p_bid, "win": win, "filled": filled, "ct": 0}
    def test_falsified_by_adverse_selection_alone(self):
        # (2) holds (version net far above the parent's) but the one missed window is a parent winner with no loss: adverse selection alone must FALSIFY
        sig = [self._sig(0.50, 0.10, True, True) for _ in range(20)] + [self._sig(0.50, 0.10, False, True) for _ in range(40)] + [self._sig(0.20, 0.10, True, False)]
        for i, s in enumerate(sig): s["ct"] = i
        lines = S.evaluate(sig, 7.0, "dev")
        self.assertTrue(any("(2) fails: no | adverse selection: yes => FALSIFIED" in l for l in lines))
        self.assertTrue([l for l in lines if l.startswith("VERDICT")][0].startswith("VERDICT (this block): FALSIFIED on development"))
        thin = S.evaluate(sig[:3] + sig[-1:], 7.0, "dev")
        self.assertTrue([l for l in thin if l.startswith("VERDICT")][0].startswith("VERDICT (this block): NOT_ENOUGH_DATA"))
    def test_falsified_by_net_alone(self):
        # no missed window, but the version's net is below the parent's at +0c: (2) fails => FALSIFIED
        sig = [self._sig(0.20, 0.90, True, True) for _ in range(3)] + [self._sig(0.20, 0.90, False, True)]
        for i, s in enumerate(sig): s["ct"] = i
        lines = S.evaluate(sig, 7.0, "dev")
        self.assertTrue(any("(2) fails: yes" in l and "=> FALSIFIED" in l for l in lines))
        self.assertTrue([l for l in lines if l.startswith("VERDICT")][0].startswith("VERDICT (this block): NOT_ENOUGH_DATA"))   # thin sample: information only
    def test_bar3_infinite_half_rulings(self):
        inf = float("inf"); nan = float("nan")
        # (vpf, parent pf +1c, fills, version net, parent net at +0c)
        self.assertEqual(S.bar3((inf, inf, 1, 0.5, 0.4), (2.0, 2.0, 1, 0.1, 0.1))[0], True)    # first both inf, second finite and equal: second decides, 0 >= 0
        self.assertEqual(S.bar3((1.0, 1.0, 1, 0.1, 0.1), (2.0, 1.0, 1, 0.1, 0.1))[0], True)    # finite: d2 1.0 >= d1 0.0
        self.assertEqual(S.bar3((2.0, 1.0, 1, 0.1, 0.1), (1.0, 1.0, 1, 0.1, 0.1))[0], False)   # finite: d2 0 < d1 1
        self.assertEqual(S.bar3((1.0, 1.0, 1, 0, 0), (inf, inf, 1, 0.3, 0.4))[0], False)      # second both inf, net lower: fails
        self.assertEqual(S.bar3((1.0, 1.0, 1, 0, 0), (inf, inf, 1, 0.4, 0.4))[0], True)       # second both inf, net not lower: passes
        self.assertEqual(S.bar3((1.0, 1.0, 1, 0, 0), (inf, 2.0, 1, 0.4, 0.4))[0], True)       # only version infinite: passes
        self.assertEqual(S.bar3((1.0, 1.0, 1, 0, 0), (2.0, inf, 1, 0.4, 0.4))[0], False)      # only parent infinite: fails
        self.assertEqual(S.bar3((nan, 1.0, 0, 0, 0), (2.0, 1.0, 1, 0.1, 0.1))[0], False)      # empty first half fails
        self.assertEqual(S.bar3((1.0, 1.0, 1, 0, 0), (nan, 1.0, 0, 0, 0))[0], False)          # empty second half fails
    def test_zero_bid_is_no_bid_and_no_ask(self):
        t0 = (CT - 178) * 1000 + 500
        w = self.window([brow("T1", t0, 0.10, 0.0)], [])      # NO bid 0.00: YES has no ask; NO ask .90 is out of band
        self.assertEqual(w["status"], "out_of_band")
        w = self.window([brow("T1", t0, 0.0, 0.85)], [])      # YES bid 0.00: no YES bid, YES ask .15 stands, no order
        self.assertTrue(w.get("no_order"))
    def test_half_split_sorted_by_close_then_ticker(self):
        a = [{"p_ask": 0.5, "p_bid": 0.4, "win": True, "filled": True, "ct": 10, "tk": "B"}, {"p_ask": 0.5, "p_bid": 0.4, "win": False, "filled": True, "ct": 10, "tk": "A"}, {"p_ask": 0.5, "p_bid": 0.4, "win": True, "filled": True, "ct": 5, "tk": "Z"}, {"p_ask": 0.5, "p_bid": 0.4, "win": True, "filled": True, "ct": 20, "tk": "C"}]
        l1 = S.evaluate(list(a), 7.0, "dev"); l2 = S.evaluate(list(reversed(a)), 7.0, "dev")
        self.assertEqual(l1, l2)
    def test_tolerance_on_bar_one(self):
        # a PF gap of exactly 0.10 minus 1e-10 counts as met (standing 1e-9 tolerance)
        self.assertGreaterEqual(0.10 - 1e-10, S.BAR_PF - S.TOL)
    def test_crossed_or_locked_quote_is_no_quote(self):
        t0 = (CT - 178) * 1000 + 500
        self.assertEqual(self.window([brow("T1", t0, 0.60, 0.45)], [])["status"], "crossed_quote")   # YES bid .60 above YES ask .55
        self.assertEqual(self.window([brow("T1", t0, 0.50, 0.50)], [])["status"], "crossed_quote")   # locked
        self.assertEqual(self.window([brow("T1", t0, 0.30, 0.70)], [])["status"], "crossed_quote")   # locked, float 1 - .7 = .30000000000000004 (standing 1e-9)
        self.assertEqual(self.window([brow("T1", t0, 0.10, 0.85)], [])["status"], "signal")           # legal two-sided quote
    def test_crossed_later_row_never_fills(self):
        t0, b = self.base()
        w = self.window(b + [brow("T1", t0 + 4000, 0.60, 0.95)], [])   # YES ask would be .05 (below our .10 bid) but the row is crossed
        self.assertFalse(w["filled"])
        w = self.window(b + [brow("T1", t0 + 4000, 0.05, 0.90)], [])   # a legal row with the same ask fills
        self.assertTrue(w["filled"])
    def test_labels_printed(self):
        self.assertIn("DEPTH1, CFRTI-B and CFRTI1-BTC", S.LABELS["V1"])
        self.assertEqual(S.LABELS["V2"], "not blind on EVENT830's forward windows")
    def test_forward_refused_before_date(self):
        t0, b = self.base(); sig = self.mk(b, [])
        args = ["--version", "V1", "--block", "forward", "--book-root", os.path.join(self.d, "r"), "--signals", sig, "--out", self.out]
        self.assertEqual(S.main(args, now="2026-12-20T00:00:00Z"), 2)
    def test_net_arithmetic(self):
        self.assertAlmostEqual(S.net(0.10, True, 0.0, 0.0), 0.90)
        self.assertAlmostEqual(S.net(0.10, False, 0.0, 0.0), -0.10)
        self.assertAlmostEqual(S.net(0.10, True, 0.01, 1.0), 1 - 0.11 - 0.07 * 0.11 * 0.89)

if __name__ == "__main__":
    unittest.main()
