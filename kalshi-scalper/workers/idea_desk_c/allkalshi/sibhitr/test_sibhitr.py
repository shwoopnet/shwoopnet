#!/usr/bin/env python3
"""SIBHIT-R hand case (synthetic, no network)."""
import gzip, json, os, sys, tempfile, unittest, io, contextlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sibhitr_lib as L
import sibhitr_score as SC

iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
c = lambda ts, yb, ya: {"end_period_ts": ts, "yes_bid": {"close_dollars": str(yb)}, "yes_ask": {"close_dollars": str(ya)}}


def put(root, job, rows):
    d = os.path.join(root, "pull", job, "r1")
    os.makedirs(d)
    man = []
    for i, (row, body) in enumerate(rows, 1):
        with gzip.open(os.path.join(d, "%04d.json.gz" % i), "wt") as f:
            json.dump(body, f)
        man.append(dict(row, index=i, file="%04d.json.gz" % i))
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump({"status": "complete", "rows": man}, f)


class Hand(unittest.TestCase):
    def build(self, cursor=""):
        root = tempfile.mkdtemp()
        occF, occS = L.B.iso("2026-03-10T03:00:00"), L.B.iso("2026-03-11T03:00:00")
        ms = []
        for name, occ, nhit in (("FAST", occF, 3), ("SLOW", occS, 0)):
            for i in range(12):
                close = occ - 7000 if i < nhit else occ + 600
                ms.append({"ticker": "KXNBAPTS-26MAR%s-P%d-10" % (name, i), "event_ticker": "KXNBAPTS-26MAR" + name, "close_time": iso(close),
                           "occurrence_datetime": iso(occ), "result": "no" if (name == "FAST") == (i % 2 == 1) else "yes"})
        ms.append({"ticker": "KXNBAPTS-26APR20X-P0-10", "event_ticker": "KXNBAPTS-26APR20X", "close_time": "2026-04-20T03:00:00Z",
                   "occurrence_datetime": "2026-04-20T03:00:00Z", "result": "TRAP"})   # playoffs: outside the window
        put(root, "SIBHITR_LISTS_A", [({"id": "hist_KXNBAPTS", "page": 1}, {"markets": ms, "cursor": cursor})])
        TF, TS = occF - 3600, occS - 3600
        put(root, "SIBHITR_CANDLES_P1", [({"path": "/historical/markets/KXNBAPTS-26MARFAST-P3-10/candlesticks"}, {"candlesticks": [c(TF, .50, .52)]}),
                                         ({"path": "/historical/markets/KXNBAPTS-26MARFAST-P4-10/candlesticks"}, {"candlesticks": [c(TF, .58, .60)]}),
                                         ({"path": "/historical/markets/KXNBAPTS-26MARSLOW-P0-10/candlesticks"}, {"candlesticks": [c(TS, .38, .40)]})])
        return root

    def test_reverse(self):
        root = self.build()
        g = L.games(L.list_rows(root))
        self.assertEqual(sorted(g), ["KXNBAPTS-26MARFAST", "KXNBAPTS-26MARSLOW"])
        self.assertEqual(g["KXNBAPTS-26MARFAST"]["arm"], "HIGH")
        self.assertEqual(g["KXNBAPTS-26MARSLOW"]["arm"], "LOW")
        with contextlib.redirect_stdout(io.StringIO()):
            o = SC.main(root)
        # FAST P3: buy NO at 1-.50=.50, result 'no' (i odd) -> won: 1-.52 = .48 ; FAST P4: NO at .42, result 'yes' -> lost: -(.42+.02) = -.44
        self.assertEqual(o["R_FAST_NO"]["n"], 2)
        self.assertAlmostEqual(o["R_FAST_NO"]["raw"]["mean_c"], 2.0)
        # SLOW P0: buy YES at .40, result 'no' (SLOW, i even) -> lost: -(.40+.02) = -.42
        self.assertEqual(o["R_SLOW_YES"]["n"], 1)
        self.assertAlmostEqual(o["R_SLOW_YES"]["raw"]["mean_c"], -42.0)
        self.assertEqual(o["R_FAST_NO"]["bar"], "no evidence at n = 2")

    def test_cursor_but_window_covered(self):
        root = self.build(cursor="abc")      # the last page holds Mar 10 closes, not before Mar 1: still truncated
        with contextlib.redirect_stdout(io.StringIO()):
            o = SC.main(root)
        self.assertIn("stopped", o)
        root2 = tempfile.mkdtemp()
        put(root2, "SIBHITR_LISTS_A", [({"id": "hist_KXNBAPTS", "page": 1}, {"markets": [{"ticker": "KXNBAPTS-X-P0-10", "close_time": "2026-02-20T03:00:00Z"}], "cursor": "abc"})])
        self.assertFalse(L.truncated(root2))   # a last page reaching before the window start covers the window

    def test_truncated(self):
        root = self.build(cursor="abc")
        with contextlib.redirect_stdout(io.StringIO()):
            o = SC.main(root)
        self.assertIn("stopped", o)


class Sample(unittest.TestCase):
    def test_split(self):
        rows = []
        for gi in range(45):
            occ = L.B.iso("2026-03-10T03:00:00") + gi * 86400
            for i in range(12):
                rows.append(("KXNBAPTS-G%02d-P%d-10" % (gi, i), "KXNBAPTS-G%02d" % gi, occ + 600, occ))
        r, h = L.games(rows, "read"), L.games(rows, "heldout")
        self.assertEqual(len(r), 40)
        self.assertEqual(len(h), 5)
        self.assertFalse(set(r) & set(h))
        import hashlib
        want = sorted(("KXNBAPTS-G%02d" % gi for gi in range(45)), key=lambda e: (hashlib.md5(("SIBHITR-2026-11-16" + e).encode()).hexdigest(), e))[:40]
        self.assertEqual(sorted(r), sorted(want))


if __name__ == "__main__":
    unittest.main()
