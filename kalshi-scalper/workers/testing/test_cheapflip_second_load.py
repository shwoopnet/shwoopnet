import csv, gzip, os, shutil, tempfile, unittest
import cheapflip_second_load as LD

H = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + LD.PX + LD.SZ + LD.NPX + LD.NSZ
def brow(t, tk, series, close, yes=(0.05, 3), no=(0.9, 4)):
    r = {"t_recv_ms": t, "ticker": tk, "series": series, "close_time": close}; r.update({k: "" for k in H}); r.update({"t_recv_ms": t, "ticker": tk, "series": series, "close_time": close})
    r["yes_bid_px_1"], r["yes_bid_sz_1"], r["no_bid_px_1"], r["no_bid_sz_1"] = yes[0], yes[1], no[0], no[1]
    return [r[k] for k in H]
def write(path, head, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f: w = csv.writer(f); w.writerow(head); w.writerows(rows)

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.allow = os.path.join(self.d, "allow.md"); open(self.allow, "w").write("x " + LD.ALLOW_MARK + " cheapflip_second_load.py " + LD.self_sha() + "\n")
        self.b = os.path.join(self.d, "nc15")
        write(self.b + "/2026-11-12/0000/book.csv.gz", H, [brow(1000, "KXHYPE15M-A", "KXHYPE15M", 2000), brow(1000, "KXHYPE15M-A", "KXHYPE15M", 2000), brow(2000, "KXETH15M-B", "KXETH15M", 2000), brow(3000, "KXBNB15M-C", "KXBNB15M", 1794787200), brow(4000, "KXBNB15M-D", "KXBNB15M", "2026-11-12T00:15:00Z")])
        write(self.b + "/2026-11-12/0000/coverage.csv.gz", ["ticker", "close_time", "result", "other"], [["KXHYPE15M-A", 2000, "yes", 1], ["KXHYPE15M-A", 2000, "no", 1], ["KXETH15M-B", 2000, "yes", 1]])
    def tearDown(self): shutil.rmtree(self.d)
    def test_load(self):
        mk, res, c, man = LD.load(self.b, self.allow)
        self.assertEqual(sorted(mk), ["KXBNB15M-D", "KXHYPE15M-A"]); self.assertEqual(len(mk["KXHYPE15M-A"][2]), 1); self.assertEqual(c["duplicate poll (first kept)"], 1)
        self.assertEqual(c["book row outside the series wall (not parsed)"], 1); self.assertEqual(c["book row of a market closing after the cut (dropped)"], 1)
        self.assertEqual(res, {"KXHYPE15M-A": "yes"}); self.assertEqual(c["conflicting result (first kept)"], 1); self.assertEqual(c["coverage row outside the series wall (not parsed)"], 1)
        self.assertEqual(mk["KXBNB15M-D"][1], LD.parse_close("2026-11-12T00:15:00Z")); self.assertEqual(man["files"], 2)
        self.assertEqual(mk["KXHYPE15M-A"][2][0][3][0], (0.05, 3.0)); self.assertEqual(mk["KXHYPE15M-A"][2][0][4][0], (0.9, 4.0)); self.assertEqual(mk["KXHYPE15M-A"][2][0][3][1], (None, None))
    def test_refuse(self):
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " cheapflip_second_load.py 00\n")
        with self.assertRaises(SystemExit): LD.load(self.b, self.allow)
    def test_missing_column(self):
        write(self.b + "/2026-11-13/0000/book.csv.gz", H[:-1], [])
        with self.assertRaises(SystemExit): LD.load(self.b, self.allow)
