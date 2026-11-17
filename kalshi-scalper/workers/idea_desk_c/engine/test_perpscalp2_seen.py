#!/usr/bin/env python3
"""Invented files only. Checks: only names and days are printed (a bid, ask, price, volume or rate planted in the files never appears), the manifest sha is the Nov 16 computation, and a
mismatch is REFUSED with nothing printed but the reason."""
import calendar, contextlib, csv, gzip, hashlib, io, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpscalp2_seen as S
import perpscalp2 as P

T0 = calendar.timegm((2026, 11, 9, 14, 35, 0))                       # EST Monday 09:35 ET
SECRET = "7777.777"


def mk():
    root = tempfile.mkdtemp()
    os.makedirs(root + "/kalshi1m"); os.makedirs(root + "/funding")
    with gzip.open(root + "/kalshi1m/2026-11-09.csv.gz", "wt", newline="") as f:
        w = csv.writer(f); w.writerow(["ticker", "end_period_ts", "bid_close", "ask_close", "volume"])
        for i in range(3):
            w.writerow(["KXNVDAPERP", T0 + 60 * i, SECRET, SECRET, SECRET])
        w.writerow(["KXNVDAPERP", P.END_EPOCH + 60, SECRET, SECRET, SECRET])          # after development end
        w.writerow(["KXNVDAPERP", P.H16_START, SECRET, SECRET, SECRET])               # H16
        w.writerow(["NOTANAME", T0, SECRET, SECRET, SECRET])
    with gzip.open(root + "/funding/2026-11-09.csv.gz", "wt", newline="") as f:
        w = csv.writer(f); w.writerow(["ticker", "funding_time", "funding_rate"]); w.writerow(["KXNVDAPERP", "2026-11-09T21:00:00Z", SECRET])
    with gzip.open(root + "/funding/all-history.csv.gz", "wt", newline="") as f:
        f.write("junk")
    return root


class T(unittest.TestCase):
    def test_pairs_and_no_values(self):
        root = mk(); o = S.seen(root)
        self.assertEqual(o["candle_days"], {"KXNVDAPERP": ["2026-11-09"]})
        self.assertEqual(o["funding_days"], {"KXNVDAPERP": ["2026-11-09"]})
        self.assertEqual((o["files_read"], o["files_skipped"], o["rows_not_used"]), (2, 1, {"after_development_end": 1, "h16_rows": 1}))
        self.assertNotIn(SECRET, json.dumps(o))
        self.assertEqual(o["regular_candles_by_timestamp"], {"KXNVDAPERP": 3})
        files = sorted([("kalshi1m/2026-11-09.csv.gz", P._sha(root + "/kalshi1m/2026-11-09.csv.gz")), ("funding/2026-11-09.csv.gz", P._sha(root + "/funding/2026-11-09.csv.gz"))])
        self.assertEqual(o["manifest_sha256"], hashlib.sha256(repr(files).encode()).hexdigest())

    def test_refusal_prints_nothing_else(self):
        root = mk(); buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = S.main(root, 168, "0" * 64, "KXETHPERP")
        self.assertEqual(rc, 2)
        self.assertTrue(buf.getvalue().startswith("REFUSED"))
        self.assertNotIn("2026-11-09", buf.getvalue())

    def test_accept_when_equal(self):
        root = mk(); o = S.seen(root); buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = S.main(root, o["files_read"], o["manifest_sha256"], ",".join(o["dropped_short_history"]))
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue())["counts_per_name"], {"KXNVDAPERP": 1})


if __name__ == "__main__":
    unittest.main()
