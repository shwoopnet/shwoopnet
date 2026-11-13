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
        m = os.path.join(self.d, "marker"); open(m, "w").write("x")
        self.assertEqual(S.main(args + ["--depth1-recorded", m]), 0)
        self.assertEqual(S.main(args + ["--depth1-recorded", m]), 2)
    def test_forward_refused_before_date(self):
        t0, b = self.base(); sig = self.mk(b, [])
        args = ["--version", "V1", "--block", "forward", "--book-root", os.path.join(self.d, "r"), "--signals", sig, "--out", self.out, "--now", "2026-12-20T00:00:00Z"]
        self.assertEqual(S.main(args), 2)
    def test_net_arithmetic(self):
        self.assertAlmostEqual(S.net(0.10, True, 0.0, 0.0), 0.90)
        self.assertAlmostEqual(S.net(0.10, False, 0.0, 0.0), -0.10)
        self.assertAlmostEqual(S.net(0.10, True, 0.01, 1.0), 1 - 0.11 - 0.07 * 0.11 * 0.89)

if __name__ == "__main__":
    unittest.main()
