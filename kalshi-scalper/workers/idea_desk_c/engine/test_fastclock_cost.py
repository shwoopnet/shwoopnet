#!/usr/bin/env python3
import csv, gzip, os, sys, tempfile, calendar, json, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastclock_cost as F

CLOSE = calendar.timegm((2026, 11, 10, 15, 0, 0))
SECRET = "9999.5"
def iso(t): return __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))

class T(unittest.TestCase):
    def test_nc15(self):
        root = tempfile.mkdtemp(); d = root + "/2026-11-10/1500"; os.makedirs(d)
        hdr = ["t_recv_ms", "series", "close_time", "result"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)]
        def row(ser, left, yb, nb):
            return [(CLOSE - left) * 1000, ser, iso(CLOSE), SECRET, yb, "", "", "", "", nb, "", "", "", ""]
        with gzip.open(d + "/book.csv.gz", "wt", newline="") as f:
            w = csv.writer(f); w.writerow(hdr)
            w.writerow(row("KXHYPE15M", 400, "0.40", "0.58"))        # spread 0.02, yes ask 0.42
            w.writerow(row("KXHYPE15M", 300, "0.50", "0.46"))        # spread 0.04, yes ask 0.54
            w.writerow(row("KXHYPE15M", 60, "0.10", "0.10"))         # under 120 s: not used
            w.writerow(row("KXGOLD15M", 400, "0.40", "0.58"))        # outside the wall
        o = F.nc15(root)
        self.assertEqual(o["rows_used"], 2)
        self.assertAlmostEqual(o["median_spread_cents"], 3.0, 6)
        self.assertEqual(o["rows_outside_wall_counted_not_parsed"], {"KXGOLD15M": 1})
        self.assertNotIn(SECRET, json.dumps(o))
        f1, f2 = F.fee_pc(0.42), F.fee_pc(0.54)
        self.assertAlmostEqual(o["median_fee_cents_per_contract_at_ask"], 100 * (f1 + f2) / 2, 6)

    def test_perps(self):
        root = tempfile.mkdtemp(); os.makedirs(root + "/kalshi1m")
        with gzip.open(root + "/kalshi1m/2026-11-10.csv.gz", "wt", newline="") as f:
            w = csv.writer(f); w.writerow(["ticker", "end_period_ts", "bid_close", "ask_close", "volume"])
            w.writerow(["KXBTCPERP", 1789603260, "99.9", "100.1", SECRET]); w.writerow(["KXBTCPERP", 1789603320, "99.8", "100.2", SECRET]); w.writerow(["KXBTCPERP", 1789603380, "100.2", "100.1", SECRET])
        o = F.perps(root)
        self.assertEqual(o["KXBTCPERP"]["candles"], 2)
        self.assertAlmostEqual(o["KXBTCPERP"]["median_spread_bp"], 1e4 * ((0.2 / 100) + (0.4 / 100)) / 2 * 1, 0)   # 20 bp and 40 bp, median 30
        self.assertAlmostEqual(o["KXBTCPERP"]["round_trip_taker_bp"], 24 + o["KXBTCPERP"]["median_spread_bp"], 9)
        self.assertNotIn(SECRET, json.dumps(o))

    def test_ingame(self):
        root = tempfile.mkdtemp(); d = root + "/2026-11-10/1500"; os.makedirs(d)
        with gzip.open(d + "/obs.csv.gz", "wt", newline="") as f:
            w = csv.writer(f); w.writerow(["t_recv_ms", "kind", "yes_bid", "yes_ask", "last_price", "volume"]); w.writerow([1, "ml", "0.50", "0.53", SECRET, SECRET]); w.writerow([2, "ml", "", "0.5", SECRET, SECRET])
        o = F.ingame(root)
        self.assertEqual(o["rows_used"], 1); self.assertAlmostEqual(o["median_spread_cents"], 3.0, 6); self.assertNotIn(SECRET, json.dumps(o))

if __name__ == "__main__":
    unittest.main()
