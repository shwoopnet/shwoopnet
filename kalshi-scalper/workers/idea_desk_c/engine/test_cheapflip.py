#!/usr/bin/env python3
"""CHEAPFLIP hand case (synthetic, no network). One YES entry: polls at C-700 s (yes ask 0.10), C-600 s (yes bid 0.02, no bid 0.97: yes ask 0.03), then the yes bid climbs
0.03, 0.06 (size 8) at C-400, 0.09 (size 3) at C-300, 0.15 (size 9) at C-200; C-100 shows ask 0.03 again (under 120 s left: no entry). Result yes."""
import calendar, csv, gzip, io, contextlib, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cheapflip as C

CLOSE = calendar.timegm((2026, 11, 10, 15, 0, 0))
COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
ISO = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))


def brow(ticker, series, close, dt, yb, ys, nb, ns):
    r = {c: "" for c in COLS}
    r.update({"t_send_ms": (close + dt) * 1000, "t_recv_ms": (close + dt) * 1000 + 50, "ticker": ticker, "series": series, "close_time": ISO(close),
              "yes_bid_px_1": yb, "yes_bid_sz_1": ys, "no_bid_px_1": nb, "no_bid_sz_1": ns})
    return [r[c] for c in COLS]


def write(base, date, hhmm, book, cover):
    d = os.path.join(base, date, hhmm)
    os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, "book.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f); w.writerow(COLS); w.writerows(book)
    with gzip.open(os.path.join(d, "coverage.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f); w.writerow(["close_time", "series", "ticker", "result"]); w.writerows(cover)


def fixture(extra=False):
    base = tempfile.mkdtemp()
    t, s = "KXHYPE15M-26NOV101500-00", "KXHYPE15M"
    book = [brow(t, s, CLOSE, -700, "0.01", "5", "0.90", "3"), brow(t, s, CLOSE, -600, "0.02", "5", "0.97", "20"), brow(t, s, CLOSE, -500, "0.03", "4", "0.96", "9"),
            brow(t, s, CLOSE, -400, "0.06", "8", "0.93", "9"), brow(t, s, CLOSE, -300, "0.09", "3", "0.90", "9"), brow(t, s, CLOSE, -200, "0.15", "9", "0.84", "9"),
            brow(t, s, CLOSE, -100, "0.02", "5", "0.97", "20")]
    cover = [[ISO(CLOSE), s, t, "yes"]]
    if extra:                                                        # a window after the cut, and the same polls again in a second folder
        late = CLOSE + 10 * 86400
        book += [brow("KXHYPE15M-LATE", s, late, -600, "0.02", "5", "0.97", "20")]
        cover += [[ISO(late), s, "KXHYPE15M-LATE", "yes"]]
        write(base, "2026-11-10", "1600", book[:2], cover)           # a second folder repeats the first two polls
    write(base, "2026-11-10", "1500", book, cover)
    return base


class Hand(unittest.TestCase):
    def test_cells(self):
        self.assertEqual(C.N_CELLS, 9)

    def test_entry_rules(self):
        wins = C.read_windows([fixture()], {})
        w = list(wins.values())[0]
        e03 = C.entries(w, 0.03)
        self.assertEqual(e03["yes"]["a"], 0.03)                                    # first poll with ask in [0.01, 0.03] is C-600 (C-700 has ask 0.10)
        self.assertEqual(C.entries(w, 0.10)["yes"]["a"], 0.10)                     # the 10c band enters earlier, at C-700
        self.assertNotIn("no", e03)                                                # the NO ask is 1 - the yes bid: 0.99 to 0.85, never in band
        self.assertEqual(e03["yes"]["t"], (CLOSE - 600) * 1000 + 50)
        self.assertEqual(e03["yes"]["ask_sz"], 20)

    def test_table_numbers(self):
        out = C.run([fixture()])
        T = {(r["band"], r["k"]): r["pooled"] for r in out["table"]}
        p = T[(0.03, 2)]
        self.assertEqual((p["n"], p["reach_share"], p["median_touch_s"], p["bid_size_5_share_at_touch"]), (1, 1.0, 200.0, 1.0))
        self.assertEqual(T[(0.03, 3)]["median_touch_s"], 300.0)
        self.assertEqual(T[(0.03, 3)]["bid_size_5_share_at_touch"], 0.0)            # the bid size at the touch is 3
        self.assertEqual(T[(0.03, 5)]["median_touch_s"], 400.0)
        # a 0.03, h 0.01: cost 0.04, fee 0.03; k 2 sells at the bid 0.06 less 0.01 = 0.05, fee 0.04: 10 x 0.05 - 10 x 0.04 - 0.03 - 0.04
        self.assertAlmostEqual(p["net_per_trade_h1"], 0.03, 9)
        self.assertAlmostEqual(T[(0.03, 3)]["net_per_trade_h1"], 0.8 - 0.4 - 0.03 - 0.06, 9)       # proceeds 0.08, fee 0.06
        self.assertAlmostEqual(T[(0.03, 5)]["net_per_trade_h1"], 1.4 - 0.4 - 0.03 - 0.09, 9)       # proceeds 0.14, fee 0.09
        # a 0.10 band: entry at 0.10, 2x = 0.20 never reached (the bid tops out at 0.15): hold, result yes: 10 - 1.10 - fee(0.11) 0.07
        q = T[(0.10, 2)]
        self.assertEqual((q["n"], q["reach_share"], q["median_touch_s"]), (1, 0.0, None))
        self.assertAlmostEqual(q["net_per_trade_h1"], 10 - 1.10 - 0.07, 9)

    def test_cut_and_duplicates_counted(self):
        out = C.run([fixture(extra=True)])
        self.assertEqual(out["stats"]["rows_after_cut"], 1)
        self.assertEqual(out["stats"]["duplicate_polls"], 2)
        self.assertEqual(out["windows"], 1)

    def test_no_result_sold_counts_hold_dropped(self):
        base = tempfile.mkdtemp()
        t, s = "KXHYPE15M-A", "KXHYPE15M"
        book = [brow(t, s, CLOSE, -600, "0.01", "5", "0.97", "20"), brow(t, s, CLOSE, -400, "0.06", "8", "0.93", "9"), brow(t, s, CLOSE, 0, "0.50", "9", "0.50", "9")]
        write(base, "2026-11-10", "1500", book, [])
        out = C.run([base])
        T = {(r["band"], r["k"]): r["pooled"] for r in out["table"]}
        self.assertEqual(T[(0.03, 2)]["n"], 1)                                      # sold, no result needed
        self.assertEqual((T[(0.03, 5)]["n"], T[(0.03, 5)]["n_scored"], T[(0.03, 5)]["reach_share"], T[(0.03, 5)]["pf_h1"]), (1, 0, 0.0, None))   # stays in n, no net
        self.assertEqual(out["stats"]["no_result_by_series"], {"KXHYPE15M": 1})
        self.assertEqual(out["stats"]["polls_at_or_after_close"], 1)
        self.assertEqual(T[(0.03, 2)]["median_touch_s"], 200.0)

    def test_holds(self):
        self.assertEqual(C.held_by("KXGOLD15M", CLOSE), "H20")
        self.assertEqual(C.held_by("KXWTI15M", CLOSE), "H21")
        self.assertIsNone(C.held_by("KXWTI15M", 1798070400))
        self.assertEqual(C.held_by("KXEURUSD15M", CLOSE), "H21")
        self.assertIsNone(C.held_by("KXHYPE15M", CLOSE))
        base = tempfile.mkdtemp()
        s = "KXGOLD15M"; tk = "KXGOLD15M-X"
        write(base, "2026-11-10", "1500", [brow(tk, s, CLOSE, -600, "0.02", "5", "0.97", "20")], [[ISO(CLOSE), s, tk, "yes"]])
        out = C.run([base])
        self.assertEqual(out["windows"], 0)
        self.assertEqual(out["stats"]["windows_dropped_by_hold"], {"H20": {"KXGOLD15M": 1}})
        with self.assertRaises(ValueError):
            C.run([base], 6290660)

    def test_header_first(self):
        import cheapflip_run as R
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            R.main([fixture()])
        h = json.loads(buf.getvalue().split("\n")[0])
        self.assertEqual((h["m_carried"], h["m_new"], h["m_total"]), (7492484, 9, 7492493))


if __name__ == "__main__":
    unittest.main()
